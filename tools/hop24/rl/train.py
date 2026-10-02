#!/usr/bin/env python3
"""Train the Hop 24 autopilot with tabular Q-learning on an offline simulator built from the
archive's own YOLO detections, and log the run to Weights & Biases.

The simulator replays the stored per-frame boxes of every highway chunk (30 fps) with the same
geometry the browser uses: road axis fitted by PCA of box centres, 8 hops across the road,
44 px chicken on a 1280x720 canvas, collision against the inscribed ellipse of a box, velocity
from nearest-neighbour box matching between frames (no access to future frames). The learned
Q-table is exported to policy.json, which index.html loads for the AUTOPILOT.

Usage:
  python3 train.py --boxes /path/to/segment_jsons --out ../policy.json [--episodes 6000]
  WANDB_API_KEY is read from the environment (set on the team VM); without it, --no-wandb or
  WANDB_MODE=offline still works.
"""
import argparse
import glob
import json
import math
import os
import random
import re
import time
from collections import defaultdict

W, H, FPS = 1280, 720, 30
CH = 44                 # chicken size (canvas px)
MARGIN = 16             # safety margin used in the look-ahead
BINS = [0.3, 0.6, 1.0, 1.5]  # eta bins (s); index 4 = nothing predicted within 1.5 s
ACTIONS = ["hold", "hop", "back"]
HOP_COOLDOWN = 8        # frames (~0.26 s), same as the browser
HWY_SPEED = 900         # px/s assumed for boxes with no velocity estimate (same as the browser)
CAM_RE = re.compile(r"(scene\d+_p\d+c\d+)_chunk_(\d+)_segment_(\d+)_of_(\d+)")


# ---------------------------------------------------------------- data
def load_chunks(folder):
    """-> {(camera, chunk): [frames...]} with frames = list of (label, conf, [x1,y1,x2,y2]) in canvas px."""
    chunks = defaultdict(dict)
    for p in glob.glob(os.path.join(folder, "*.json")):
        m = CAM_RE.search(os.path.basename(p))
        if not m:
            continue
        cam, ch, seg = m.group(1), int(m.group(2)), int(m.group(3))
        with open(p) as fh:
            d = json.load(fh)
        sx, sy = W / d.get("width", 1920), H / d.get("height", 1080)
        frames = []
        for f in d["frames"]:
            frames.append([(b["label"], b["confidence"], [b["bbox"][0] * sx, b["bbox"][1] * sy, b["bbox"][2] * sx, b["bbox"][3] * sy])
                           for b in f.get("boxes", []) if b["label"] != "person"])
        chunks[(cam, ch)][seg] = frames
    out = {}
    for key, segs in chunks.items():
        out[key] = [fr for s in sorted(segs) for fr in segs[s]]
    return out


def fit_axis(frames):
    pts = []
    for i in range(0, len(frames), 3):
        for _, _, b in frames[i]:
            pts.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, math.hypot(b[2] - b[0], b[3] - b[1]) / 2))
    if len(pts) < 40:
        return {"d": (1, 0), "n": (0, -1), "mu": (W / 2, H / 2), "pmin": -H * 0.35, "pmax": H * 0.28}
    mx = sum(p[0] for p in pts) / len(pts); my = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts); syy = sum((p[1] - my) ** 2 for p in pts); sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    d = (math.cos(th), math.sin(th)); n = (-d[1], d[0])
    if n[1] > 0:
        n = (-n[0], -n[1])
    lo = sorted((p[0] - mx) * n[0] + (p[1] - my) * n[1] - p[2] * 0.8 for p in pts)
    hi = sorted((p[0] - mx) * n[0] + (p[1] - my) * n[1] + p[2] * 0.8 for p in pts)
    return {"d": d, "n": n, "mu": (mx, my), "pmin": lo[int(0.01 * len(lo))], "pmax": hi[int(0.99 * len(hi))]}


# ---------------------------------------------------------------- simulator
class Env:
    def __init__(self, chunks):
        self.chunks = chunks
        self.keys = sorted(chunks)
        self.axes = {k: fit_axis(v) for k, v in chunks.items()}

    def proj(self, a, x, y):
        return (x - a["mu"][0]) * a["n"][0] + (y - a["mu"][1]) * a["n"][1]

    def spawn(self, a):
        p = a["pmin"] - CH * 1.1
        cand = []
        for t in range(-2500, 2501, 10):
            x = a["mu"][0] + a["n"][0] * p + a["d"][0] * t - CH / 2; y = a["mu"][1] + a["n"][1] * p + a["d"][1] * t - CH / 2
            if x > 4 and y > 4 and x + CH < W - 4 and y + CH < H - 4:
                cand.append((x, y))
        x, y = cand[len(cand) // 2] if cand else (20, H - CH - 6)
        reach = a["pmax"] + 12
        for k in range(0, 4000, 4):
            px, py = x + CH / 2 + a["n"][0] * k, y + CH / 2 + a["n"][1] * k
            if px < CH / 2 or py < CH / 2 or px > W - CH / 2 or py > H - CH / 2:
                reach = min(reach, self.proj(a, px, py) - 6); break
        return x, y, reach

    def reset(self, key=None, start=None):
        self.key = key or random.choice(self.keys)
        self.frames = self.chunks[self.key]
        self.a = self.axes[self.key]
        self.step_len = (self.a["pmax"] - self.a["pmin"]) / 8
        self.x, self.y, self.goal = self.spawn(self.a)
        self.t = start if start is not None else random.randint(0, max(0, len(self.frames) - 400))
        self.t0 = self.t
        self.prev = []
        self.last_hop = -99
        self.hops = 0
        self._track()
        return self.state()

    # velocity by nearest-neighbour matching against the previous frame (same as index.html)
    def _track(self):
        cur = []
        for label, conf, b in self.frames[self.t]:
            x, y, w, h = b[0], b[1], b[2] - b[0], b[3] - b[1]
            cx, cy = x + w / 2, y + h / 2
            best, bd = None, max(70, w)
            for q in self.prev:
                dd = math.hypot(q["cx"] - cx, q["cy"] - cy)
                if dd < bd:
                    bd, best = dd, q
            if best:
                vx, vy = (cx - best["cx"]) * FPS, (cy - best["cy"]) * FPS
                if best["known"]:
                    vx, vy = 0.5 * vx + 0.5 * best["vx"], 0.5 * vy + 0.5 * best["vy"]
                known = True
            else:
                vx = vy = 0; known = False
            cur.append({"label": label, "x": x, "y": y, "w": w, "h": h, "cx": cx, "cy": cy, "vx": vx, "vy": vy, "known": known})
        self.prev = cur

    def eta(self, px, py):
        """earliest predicted overlap of any box with the cell at (px,py), sampled every 0.1 s up to 1.5 s."""
        a = self.a
        best = None
        for q in self.prev:
            vx, vy = q["vx"], q["vy"]
            if not q["known"]:
                toward = 1 if ((px - q["x"]) * a["d"][0] + (py - q["y"]) * a["d"][1]) >= 0 else -1
                vx, vy = a["d"][0] * HWY_SPEED * toward, a["d"][1] * HWY_SPEED * toward
            for k in range(0, 16):
                t = k * 0.1
                bx, by = q["x"] + vx * t, q["y"] + vy * t
                if bx < px + CH + MARGIN and bx + q["w"] > px - MARGIN and by < py + CH + MARGIN and by + q["h"] > py - MARGIN:
                    if best is None or t < best:
                        best = t
                    break
        return best

    @staticmethod
    def bin(eta):
        if eta is None:
            return 4
        for i, b in enumerate(BINS):
            if eta < b:
                return i
        return 4

    def cells(self):
        a, s = self.a, self.step_len
        return (self.x, self.y), (self.x + a["n"][0] * s, self.y + a["n"][1] * s), (self.x - a["n"][0] * s, self.y - a["n"][1] * s)

    def state(self):
        """(eta bin here, next lane, lane after next, previous lane, progress bucket, cooldown) — mirrored in index.html."""
        a, s = self.a, self.step_len
        here, nxt, back = self.cells()
        nxt2 = (self.x + a["n"][0] * 2 * s, self.y + a["n"][1] * 2 * s)
        cool = 1 if self.t - self.last_hop < HOP_COOLDOWN else 0
        prog = min(2, max(0, self.hops) // 3)
        return (self.bin(self.eta(*here)), self.bin(self.eta(*nxt)), self.bin(self.eta(*nxt2)), self.bin(self.eta(*back)), prog, cool)

    def hits(self):
        for q in self.prev:
            bx, by, rx, ry = q["x"] + q["w"] / 2, q["y"] + q["h"] / 2, max(6, q["w"] / 2 * 0.94), max(6, q["h"] / 2 * 0.94)
            for fx, fy in ((0.5, 0.5), (0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)):
                px, py = self.x + CH * fx, self.y + CH * fy
                if ((px - bx) / rx) ** 2 + ((py - by) / ry) ** 2 <= 1:
                    return q["label"]
        return None

    def step(self, action):
        a = self.a
        reward = -0.04
        if action != 0 and self.t - self.last_hop >= HOP_COOLDOWN:
            sgn = 1 if action == 1 else -1
            nx, ny = self.x + a["n"][0] * self.step_len * sgn, self.y + a["n"][1] * self.step_len * sgn
            self.x, self.y = max(0, min(W - CH, nx)), max(0, min(H - CH, ny))
            self.last_hop = self.t
            self.hops += sgn
            reward += 0.5 if sgn > 0 else -0.6
        # advance one frame
        self.t += 1
        if self.t >= len(self.frames):
            return self.state(), -2.0, True, "timeout"
        self._track()
        if self.hops > 0 and self.hits():          # grace until the first hop, like the browser
            return self.state(), -10.0, True, "dead"
        if self.proj(a, self.x + CH / 2, self.y + CH / 2) > self.goal:
            return self.state(), 10.0, True, "crossed"
        if self.t - self.t0 > 20 * FPS:
            return self.state(), -2.0, True, "timeout"
        return self.state(), reward, False, None


def heuristic(env):
    """The rule-based agent shipped before training: hop if the next cell is clear for 0.65 s, dodge back if threatened."""
    here, nxt, back = env.cells()
    e_here, e_next = env.eta(*here), env.eta(*nxt)
    if env.t - env.last_hop < HOP_COOLDOWN:
        return 0
    if e_next is None or e_next >= 0.65:
        return 1
    if e_here is not None and (env.eta(*back) is None):
        return 2
    return 0


def evaluate(env, policy_fn, episodes, seed=1):
    random.seed(seed)
    res = defaultdict(int); steps = []; per_cam = defaultdict(lambda: [0, 0])
    for _ in range(episodes):
        s = env.reset(); done = False
        while not done:
            s, r, done, why = env.step(policy_fn(env, s))
        res[why] += 1; steps.append(env.t - env.t0)
        per_cam[env.key[0]][0] += why == "crossed"; per_cam[env.key[0]][1] += 1
    return {"crossed": res["crossed"] / episodes, "dead": res["dead"] / episodes, "timeout": res["timeout"] / episodes,
            "mean_seconds": sum(steps) / len(steps) / FPS, "per_camera": {c: v[0] / v[1] for c, v in per_cam.items()}}


# ---------------------------------------------------------------- training
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boxes", required=True)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "policy.json"))
    ap.add_argument("--episodes", type=int, default=9000)
    ap.add_argument("--alpha", type=float, default=0.15)
    ap.add_argument("--gamma", type=float, default=0.97)
    ap.add_argument("--no-wandb", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    random.seed(args.seed)

    chunks = load_chunks(args.boxes)
    env = Env(chunks)
    print(f"{len(chunks)} chunks, {sum(len(v) for v in chunks.values())} frames, cameras: {sorted({k[0] for k in chunks})}")

    run = None
    if not args.no_wandb:
        try:
            import wandb
            run = wandb.init(project=os.environ.get("WANDB_PROJECT_HOP24", "hop24-autopilot"), job_type="train",
                             config={"algorithm": "tabular Q-learning", "episodes": args.episodes, "alpha": args.alpha, "gamma": args.gamma,
                                     "state": "eta bins (here,next,next2,back) x progress x cooldown", "bins_s": BINS, "actions": ACTIONS,
                                     "chunks": len(chunks), "frames": sum(len(v) for v in chunks.values()), "fps": FPS,
                                     "hop_cooldown_frames": HOP_COOLDOWN, "margin_px": MARGIN, "assumed_speed_px_s": HWY_SPEED,
                                     "reward": "+10 crossed, -10 dead, -2 timeout, +0.5 hop, -0.6 back, -0.04/frame"})
        except Exception as e:  # noqa: BLE001
            print("W&B disabled:", e)

    baseline = evaluate(env, lambda e, s: heuristic(e), 400)
    print("baseline heuristic:", baseline)
    if run:
        run.summary["baseline/crossed"] = baseline["crossed"]; run.summary["baseline/dead"] = baseline["dead"]; run.summary["baseline/mean_seconds"] = baseline["mean_seconds"]

    Q = defaultdict(lambda: [0.0, 0.0, 0.0])
    eps_hi, eps_lo = 1.0, 0.05
    window = defaultdict(int); wsteps = []; wreward = []
    t_start = time.time()
    for ep in range(1, args.episodes + 1):
        eps = max(eps_lo, eps_hi - (eps_hi - eps_lo) * ep / (0.7 * args.episodes))
        s = env.reset(); done = False; total = 0.0
        while not done:
            a = random.randrange(3) if random.random() < eps else max(range(3), key=lambda i: Q[s][i])
            s2, r, done, why = env.step(a)
            target = r if done else r + args.gamma * max(Q[s2])
            Q[s][a] += args.alpha * (target - Q[s][a])
            s = s2; total += r
        window[why] += 1; wsteps.append(env.t - env.t0); wreward.append(total)
        if ep % 100 == 0:
            n = sum(window.values())
            m = {"episode": ep, "epsilon": eps, "train/crossed": window["crossed"] / n, "train/dead": window["dead"] / n, "train/timeout": window["timeout"] / n,
                 "train/mean_reward": sum(wreward) / len(wreward), "train/mean_seconds": sum(wsteps) / len(wsteps) / FPS, "q/states": len(Q)}
            print(f"ep {ep:5d} eps {eps:.2f} crossed {m['train/crossed']:.2f} dead {m['train/dead']:.2f} timeout {m['train/timeout']:.2f} reward {m['train/mean_reward']:.2f} states {len(Q)}")
            if run:
                run.log(m, step=ep)
            window.clear(); wsteps.clear(); wreward.clear()
        if ep % 1000 == 0 and run:
            ev = evaluate(env, lambda e, s: max(range(3), key=lambda i: Q[s][i]), 300, seed=ep)
            run.log({"eval/crossed": ev["crossed"], "eval/dead": ev["dead"], "eval/mean_seconds": ev["mean_seconds"]}, step=ep)

    final = evaluate(env, lambda e, s: max(range(3), key=lambda i: Q[s][i]), 600, seed=99)
    baseline = evaluate(env, lambda e, s: heuristic(e), 600, seed=99)  # same seed as the learned policy for a fair comparison
    print("baseline (same seed):", baseline)
    print("learned policy:", final)
    policy = {"version": 1, "algorithm": "tabular Q-learning", "bins_s": BINS, "actions": ACTIONS, "hop_cooldown_frames": HOP_COOLDOWN,
              "margin_px": MARGIN, "assumed_speed_px_s": HWY_SPEED, "q": {",".join(map(str, k)): [round(v, 4) for v in q] for k, q in Q.items()},
              "meta": {"episodes": args.episodes, "chunks": len(chunks), "trained_seconds": round(time.time() - t_start, 1),
                       "eval": final, "baseline": baseline, "wandb_run": run.url if run else None, "wandb_name": run.name if run else None}}
    with open(args.out, "w") as fh:
        json.dump(policy, fh, indent=1)
    print("wrote", args.out, "states", len(Q))
    if run:
        run.summary["eval/crossed"] = final["crossed"]; run.summary["eval/dead"] = final["dead"]; run.summary["eval/mean_seconds"] = final["mean_seconds"]
        try:
            art = wandb.Artifact("hop24-autopilot-policy", type="policy", metadata=policy["meta"]); art.add_file(args.out); run.log_artifact(art)
        except Exception as e:  # noqa: BLE001
            print("artifact skipped:", e)
        run.finish()


if __name__ == "__main__":
    main()
