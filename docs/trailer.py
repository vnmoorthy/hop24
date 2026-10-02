"""Render the Hop 24 trailer from real I-24 segments + their stored YOLO boxes.

Usage: python3 docs/trailer.py /tmp/hop24_real docs/Hop24-trailer.mp4
Needs ffmpeg, Pillow, and the segN.mp4 / segN.json pairs downloaded from the app.
"""
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DATA, OUT = sys.argv[1], sys.argv[2]
ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1920, 1080, 30
TMP = "/tmp/hop24_trailer"
os.makedirs(TMP, exist_ok=True)

ACC, RED, GREEN, BLUE, ORANGE, WHITE, DIM = (255, 204, 51), (255, 77, 77), (61, 220, 132), (90, 176, 255), (255, 140, 66), (233, 238, 246), (139, 155, 176)


def font(sz, kind="bold"):
    paths = {"black": "/System/Library/Fonts/Supplemental/Arial Black.ttf", "bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
             "reg": "/System/Library/Fonts/Supplemental/Arial.ttf", "mono": "/System/Library/Fonts/Menlo.ttc"}
    try:
        return ImageFont.truetype(paths[kind], sz)
    except Exception:  # noqa: BLE001
        return ImageFont.load_default()


def frames_of(seg):
    d = os.path.join(TMP, f"seg{seg}")
    if not os.path.isdir(d):
        os.makedirs(d)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-i", os.path.join(DATA, f"seg{seg}.mp4"), os.path.join(d, "%04d.png")], check=True)
    return [os.path.join(d, f) for f in sorted(os.listdir(d))]


def boxes_of(seg):
    with open(os.path.join(DATA, f"seg{seg}.json")) as fh:
        return [[(b["label"], b["confidence"], b["bbox"]) for b in f["boxes"]] for f in json.load(fh)["frames"]]


# --- road axis from the boxes (same maths as index.html)
def axis(all_boxes):
    pts = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, math.hypot(b[2] - b[0], b[3] - b[1]) / 2) for fr in all_boxes for (_, _, b) in fr]
    mx = sum(p[0] for p in pts) / len(pts); my = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts); syy = sum((p[1] - my) ** 2 for p in pts); sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    d = (math.cos(th), math.sin(th)); n = (-d[1], d[0])
    if n[1] > 0:
        n = (-n[0], -n[1])
    lo = sorted((p[0] - mx) * n[0] + (p[1] - my) * n[1] - p[2] * 0.8 for p in pts)
    hi = sorted((p[0] - mx) * n[0] + (p[1] - my) * n[1] + p[2] * 0.8 for p in pts)
    return {"d": d, "n": n, "mu": (mx, my), "pmin": lo[int(0.01 * len(lo))], "pmax": hi[int(0.99 * len(hi))]}


sheet = Image.open(os.path.join(ROOT, "img", "chicken_sheet.png")).convert("RGBA")
CH = [sheet.crop((256 * i, 0, 256 * (i + 1), 256)) for i in range(9)]


def chicken(im, x, y, frame, size=120, angle=90):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x - size * 0.45, y + size * 0.25, x + size * 0.45, y + size * 0.48], fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    sp = CH[frame].rotate(angle, expand=True, resample=Image.BICUBIC).resize((size, size), Image.LANCZOS)
    im.alpha_composite(sp, (int(x - size / 2), int(y - size / 2)))


def draw_boxes(dr, boxes, highlight=None, dim=False):
    for label, conf, b in boxes:
        col = ORANGE if label in ("truck", "bus") else BLUE
        if highlight and label == highlight:
            col = RED
        dr.rectangle(b, outline=col + ((120,) if dim and col != RED else (255,)), width=4 if col == RED else 3)
        if not dim:
            dr.rectangle([b[0], b[1] - 28, b[0] + 18 + 13 * len(label), b[1]], fill=(0, 0, 0, 170))
            dr.text((b[0] + 7, b[1] - 26), label, fill=WHITE, font=font(20, "mono"))


def hud(im, cam, seg, t, mode=None, thought=None):
    dr = ImageDraw.Draw(im)
    pills = [cam, f"seg {seg}/6", f"{t:.1f} s", "9,294 boxes"] + ([mode] if mode else [])
    x = 36
    for p in pills:
        w = dr.textlength(p, font=font(24, "mono")) + 28
        dr.rounded_rectangle([x, 28, x + w, 70], 8, fill=(0, 0, 0, 160))
        dr.text((x + 14, 36), p, fill=ACC if p == cam or p == mode else WHITE, font=font(24, "mono"))
        x += w + 12
    if thought:
        w = dr.textlength(thought, font=font(26, "mono")) + 40
        dr.rounded_rectangle([36, H - 96, 36 + w, H - 44], 8, fill=(0, 0, 0, 170))
        dr.rectangle([36, H - 96, 42, H - 44], fill=BLUE)
        dr.text((60, H - 86), thought, fill=(207, 227, 255), font=font(26, "mono"))


def vignette(im, strength=110):
    m = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(m)
    for i in range(40):
        md.rectangle([i * 14, i * 8, W - i * 14, H - i * 8], fill=int(255 * i / 40))
    m = m.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, strength)); dark.putalpha(Image.eval(m, lambda v: strength - int(v * strength / 255)))
    im.alpha_composite(dark)


def card(lines, sub=None, bg=None, fade=1.0):
    im = (bg.copy() if bg else Image.new("RGBA", (W, H), (7, 10, 15, 255)))
    if bg:
        im.alpha_composite(Image.new("RGBA", (W, H), (5, 8, 14, 200)))
    dr = ImageDraw.Draw(im)
    y = H / 2 - 60 * len(lines) - (40 if sub else 0)
    for i, (txt, col, sz) in enumerate(lines):
        f = font(sz, "black" if i == 0 else "bold")
        w = dr.textlength(txt, font=f)
        dr.text(((W - w) / 2, y), txt, fill=col, font=f)
        y += sz + 24
    if sub:
        f = font(30, "reg"); w = dr.textlength(sub, font=f); dr.text(((W - w) / 2, y + 20), sub, fill=DIM, font=f)
    if fade < 1:
        im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - fade)))))
    return im


out = []  # list of RGB frames (paths)


def emit(im, n=1):
    for _ in range(n):
        p = os.path.join(TMP, f"out_{len(out):05d}.jpg")
        im.convert("RGB").save(p, quality=90)
        out.append(p)


seg1, seg2 = frames_of(1), frames_of(2)
b1, b2 = boxes_of(1), boxes_of(2)
AX = axis(b1 + b2)
CAM = "scene1_p1c2 · chunk_0003"
bg0 = Image.open(seg1[88]).convert("RGBA")

# ---- 1. title (4 s)
for k in range(FPS * 4):
    fade = min(1, k / 20) * min(1, (FPS * 4 - k) / 15)
    emit(card([("HOP 24", ACC, 170), ("Cross a real highway. The archive is watching.", WHITE, 46)], "VAST Builders Challenge 2026 · Team 10 · I-24 Nashville, pole 1 camera 2", bg0, fade))

# ---- 2. the crossing (8 s over seg1 + start of seg2), a scripted human player
mx, my = AX["mu"]; n, d = AX["n"], AX["d"]
start = (mx + n[0] * (AX["pmin"] - 110) + d[0] * -520, my + n[1] * (AX["pmin"] - 110) + d[1] * -520)
step = (AX["pmax"] - AX["pmin"]) / 8
hops = [0.9, 1.5, 2.1, 2.9, 3.4, 4.6, 5.3, 6.1]  # seconds when the player hops
hit_frame = None
for k in range(FPS * 8):
    seg, fi = (1, k) if k < 150 else (2, k - 150)
    im = Image.open((seg1 if seg == 1 else seg2)[fi]).convert("RGBA")
    boxes = (b1 if seg == 1 else b2)[fi]
    nh = sum(1 for h in hops if k / FPS >= h)
    cx, cy = start[0] + n[0] * step * nh, start[1] + n[1] * step * nh
    dr = ImageDraw.Draw(im, "RGBA")
    draw_boxes(dr, boxes)
    # collision check against real boxes
    hit = next((bb for bb in boxes if bb[2][0] < cx + 45 and bb[2][2] > cx - 45 and bb[2][1] < cy + 45 and bb[2][3] > cy - 45), None)
    if hit and nh >= 3:
        hit_frame = (seg, fi, hit, cx, cy, k / FPS)
        break
    chicken(im, cx, cy, (k // 4) % 8)
    hud(im, CAM, seg, k / FPS + (0 if seg == 1 else 0))
    vignette(im, 90)
    emit(im)

if not hit_frame:  # force one at the last frame against the nearest box
    seg, fi = 2, 90
    boxes = b2[fi]
    cx, cy = start[0] + n[0] * step * 5, start[1] + n[1] * step * 5
    hit = min(boxes, key=lambda bb: math.hypot((bb[2][0] + bb[2][2]) / 2 - cx, (bb[2][1] + bb[2][3]) / 2 - cy))
    cx, cy = (hit[2][0] + hit[2][2]) / 2, (hit[2][1] + hit[2][3]) / 2
    hit_frame = (seg, fi, hit, cx, cy, (150 + fi) / FPS)

seg, fi, hit, cx, cy, tsec = hit_frame
label, conf, bb = hit
frames, bxs = (seg1 if seg == 1 else seg2), (b1 if seg == 1 else b2)

# ---- 3. slow-motion replay (last 2.4 s at 0.35x -> ~7 s), killer class tracked in red
r0 = max(0, fi - int(2.4 * FPS))
for j in range(r0, fi + 1):
    im = Image.open(frames[j]).convert("RGBA")
    im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 70)))
    dr = ImageDraw.Draw(im, "RGBA")
    draw_boxes(dr, bxs[j], highlight=label, dim=True)
    nh = min(8, sum(1 for h in hops if (j + (0 if seg == 1 else 150)) / FPS >= h))
    chicken(im, start[0] + n[0] * step * nh, start[1] + n[1] * step * nh, (j // 4) % 8)
    dr.rectangle([0, 0, W, 96], fill=(0, 0, 0, 255)); dr.rectangle([0, H - 96, W, H], fill=(0, 0, 0, 255))
    dr.text((34, 32), "●  KILL-CAM REPLAY   0.35×", fill=RED, font=font(30, "mono"))
    t = f"{CAM}   ·   t = {(j + (0 if seg == 1 else 150)) / FPS:.2f} s"
    dr.text((W - 34 - dr.textlength(t, font=font(26, "mono")), 36), t, fill=(221, 221, 221), font=font(26, "mono"))
    emit(im, 3 if j < fi else 1)

# ---- 4. splat + shake (1.5 s), then evidence crop (3 s)
base = Image.open(frames[fi]).convert("RGBA")
for k in range(int(FPS * 1.5)):
    im = base.copy()
    dr = ImageDraw.Draw(im, "RGBA")
    draw_boxes(dr, bxs[fi], highlight=label)
    chicken(im, cx, cy, 8, angle=0)
    im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 110)))
    dr = ImageDraw.Draw(im, "RGBA")
    f = font(220, "black"); w = dr.textlength("SPLAT", font=f)
    dr.text(((W - w) / 2, H / 2 - 170), "SPLAT", fill=RED, font=f)
    sub = f"killed by a {label} ({int(conf * 100)}% sure) after {tsec - hops[0]:.1f} s"
    f2 = font(38, "bold"); w2 = dr.textlength(sub, font=f2)
    dr.rounded_rectangle([(W - w2) / 2 - 24, H / 2 + 90, (W + w2) / 2 + 24, H / 2 + 156], 10, fill=(0, 0, 0, 200))
    dr.text(((W - w2) / 2, H / 2 + 102), sub, fill=WHITE, font=f2)
    if k < 12:
        im = im.transform(im.size, Image.AFFINE, (1, 0, (-1) ** k * (12 - k), 0, 1, (-1) ** (k // 2) * (8 - k // 2)))
    emit(im)

pad = max(60, (bb[2] - bb[0]) * 0.7)
crop = base.crop((max(0, bb[0] - pad), max(0, bb[1] - pad * .8), min(W, bb[2] + pad), min(H, bb[3] + pad * .8)))
for k in range(FPS * 3):
    z = 1 + 0.08 * k / (FPS * 3)
    im = Image.new("RGBA", (W, H), (7, 10, 15, 255))
    c = crop.resize((int(1280 * z), int(1280 * z * crop.height / crop.width)), Image.LANCZOS)
    x0, y0 = int((W - c.width) / 2), int((H - 90 - c.height) / 2) + 20
    im.alpha_composite(c, (x0, y0))
    dr = ImageDraw.Draw(im, "RGBA")
    sx = c.width / crop.width
    dr.rectangle([x0 + (bb[0] - max(0, bb[0] - pad)) * sx, y0 + (bb[1] - max(0, bb[1] - pad * .8)) * sx, x0 + (bb[2] - max(0, bb[0] - pad)) * sx, y0 + (bb[3] - max(0, bb[1] - pad * .8)) * sx], outline=RED, width=6)
    dr.rectangle([0, H - 90, W, H], fill=(0, 0, 0, 230))
    dr.text((40, H - 66), f"EVIDENCE FRAME   {CAM}  ·  seg {seg}  ·  t={fi / FPS:.2f}s  ·  {label} {conf}  ·  bbox {[int(v) for v in bb]}", fill=WHITE, font=font(30, "mono"))
    dr.text((40, 30), "the archive already knows this vehicle", fill=ACC, font=font(34, "bold"))
    emit(im)

# ---- 5. manhunt + report cards (8 s)
sql = 'SELECT ... FROM "team-10-vss-db/vss-schema"."vss-collection"\nWHERE camera_id = \'i24_cam-1\' AND (is_public = TRUE OR allowed_users && ARRAY[\'team-10\'])\nORDER BY array_cosine_distance(vectors::FLOAT[256], <query>) LIMIT 100   -- caption branch\nUNION visual branch on vectors_visual · hybrid text weight 0.60'
for k in range(FPS * 4):
    im = card([("ONE QUERY, EVERY CAMERA", ACC, 90), ("caption vectors + visual vectors + camera filter, in VastDB", WHITE, 40)], None, bg0)
    dr = ImageDraw.Draw(im, "RGBA")
    y = H / 2 + 60
    for i, cam in enumerate(["scene1_p1c1", "scene1_p1c2  ·  scene of crime", "scene1_p1c3"]):
        x = 240 + i * 500
        dr.rounded_rectangle([x, y, x + 440, y + 150], 14, fill=(17, 24, 35, 235), outline=ORANGE if i == 2 else (34, 48, 66), width=3)
        dr.text((x + 20, y + 16), cam, fill=BLUE, font=font(26, "mono"))
        dr.text((x + 20, y + 64), "candidate sightings" if i != 1 else "the kill segment", fill=DIM, font=font(24, "reg"))
        if i == 2 and k > FPS:
            dr.text((x + 20, y + 100), "strongest match  score 0.36", fill=ACC, font=font(26, "mono"))
    dr.text((240, y + 190), sql, fill=(159, 179, 200), font=font(22, "mono"))
    emit(im)
rep = Image.open(os.path.join(ROOT, "img", "report.jpg")).convert("RGBA")
rep = rep.resize((int(rep.width * 1000 / rep.height), 1000), Image.LANCZOS)
for k in range(FPS * 4):
    im = card([("INCIDENT REPORT FILED", GREEN, 90)], None, bg0)
    dr = ImageDraw.Draw(im, "RGBA")
    dr.rectangle([0, 0, W, H], fill=(5, 8, 14, 120))
    im.alpha_composite(rep, (W - rep.width - 120, 60))
    dr = ImageDraw.Draw(im, "RGBA")
    for i, line in enumerate(["event · camera · time", "YOLO class, confidence, bbox", "stored Cosmos description", "query issued + VastDB SQL", "sightings on other cameras", "last seen · recommended action"]):
        dr.text((160, 330 + i * 70), "✓  " + line, fill=WHITE if i < (k * 6 // (FPS * 3)) + 1 else DIM, font=font(34, "bold"))
    emit(im)

# ---- 6. autopilot crossing (6 s over seg1 again), scripted but honest-looking: hops when the next cell is clear
look = 0.65
cx, cy, nh = start[0], start[1], 0
last = -1
allf, allb = seg1 + seg2, b1 + b2
for k in range(FPS * 6):
    fi = k
    im = Image.open(allf[fi]).convert("RGBA")
    boxes = allb[fi]
    dr = ImageDraw.Draw(im, "RGBA")
    draw_boxes(dr, boxes)
    nx, ny = start[0] + n[0] * step * (nh + 1), start[1] + n[1] * step * (nh + 1)
    danger = None
    for lab, cf, b in boxes:
        # look ahead using the actual future boxes of this class near the cell (trailer only)
        for q in range(0, int(look * FPS), 3):
            fb = allb[min(299, fi + q)]
            if any(bb[0] < nx + 34 and bb[2] > nx - 34 and bb[1] < ny + 34 and bb[3] > ny - 34 for (_, _, bb) in fb):
                danger = (lab, q / FPS); break
        if danger:
            break
    thought = "watching the traffic to estimate speeds…" if k < 14 else (f"hold · {danger[0]} crossing the next lane, there in {danger[1]:.1f}s" if danger else "next lane clear for 0.65 s → hop")
    if k >= 14 and not danger and k - last >= 7 and nh < 8:
        nh += 1; last = k
    cx, cy = start[0] + n[0] * step * nh, start[1] + n[1] * step * nh
    chicken(im, cx, cy, (k // 3) % 8)
    hud(im, CAM, 1 if fi < 150 else 2, k / FPS, "AUTOPILOT", thought)
    vignette(im, 90)
    if nh >= 8:
        im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 100)))
        dr = ImageDraw.Draw(im, "RGBA"); f = font(200, "black"); w = dr.textlength("CROSSED", font=f)
        dr.text(((W - w) / 2, H / 2 - 150), "CROSSED", fill=GREEN, font=f)
        emit(im, FPS * 2)
        break
    emit(im)

# ---- 7. outro (5 s)
for k in range(FPS * 5):
    fade = min(1, k / 15) * min(1, (FPS * 5 - k) / 20)
    emit(card([("HOP 24", ACC, 150), ("problem → archive → search across cameras → action", WHITE, 44), ("VAST AI OS · NVIDIA Cosmos + YOLO11 · CoreWeave", DIM, 34)], "github.com/vnmoorthy/hop24", bg0, fade))

with open(os.path.join(TMP, "list.txt"), "w") as fh:
    for p in out:
        fh.write(f"file '{p}'\nduration {1 / FPS}\n")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(TMP, "list.txt"), "-vf", f"fps={FPS},format=yuv420p",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-movflags", "+faststart", OUT], check=True)
print("frames", len(out), "->", OUT, f"{len(out) / FPS:.1f}s")
