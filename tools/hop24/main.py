#!/usr/bin/env python3
"""Hop 24 - a video agent game on the VAST video search stack.

Stdlib only so it runs unchanged in python:3.12-slim from a ConfigMap
(see .cursor/skills/deployment/deploy-app-no-registry). Routes live at /
because the Ingress strips the /app prefix.

Env: PORT, VSS_URL (in-cluster: http://video-backend-service:8000),
VSS_USERNAME, VSS_PASSWORD. Optional: HOP24_MOCK=1 for a local demo with
synthetic footage, HOP24_RAW=<raw github dir url> for /reload self-update.
"""
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8080"))
VSS_URL = os.environ.get("VSS_URL", "").rstrip("/")
VSS_USER = os.environ.get("VSS_USERNAME", "")
VSS_PASS = os.environ.get("VSS_PASSWORD", "")
API = VSS_URL + "/api/v1"
MOCK = os.environ.get("HOP24_MOCK") == "1"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.environ.get("HOP24_RAW", "https://raw.githubusercontent.com/vnmoorthy/hop24/refs/heads/main/tools/hop24/")
RELOAD_KEY = os.environ.get("HOP24_RELOAD_KEY", "hop")
UPDATE_DIR = "/tmp/hop24"

CAMERA_RE = re.compile(r"(scene\d+_p\d+c\d+)")
SEG_RE = re.compile(r"_segment_(\d+)_of_(\d+)")
COLOURS = ["white", "black", "silver", "gray", "grey", "red", "blue", "green", "yellow",
           "orange", "brown", "tan", "beige", "dark", "maroon", "gold", "teal"]

_token = {"value": None}
_lock = threading.Lock()
_cache = {}
SCORES = []


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- VSS client
def login(force=False):
    with _lock:
        if _token["value"] and not force:
            return _token["value"]
        body = json.dumps({"username": VSS_USER, "password": VSS_PASS}).encode()
        req = urllib.request.Request(API + "/auth/login", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            _token["value"] = json.loads(r.read())["access_token"]
        return _token["value"]


def api(method, path, body=None, params=None, retry=True):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + login(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 401 and retry:
            login(force=True)
            return api(method, path, body, params, retry=False)
        raise


def find_list(d, keys=("items", "videos", "results", "chunks", "entries", "data")):
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for k in keys:
            if isinstance(d.get(k), list):
                return d[k]
        for v in d.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def deep_find(d, key):
    if isinstance(d, dict):
        if key in d and isinstance(d[key], (str, int, float)):
            return d[key]
        for v in d.values():
            r = deep_find(v, key)
            if r is not None:
                return r
    elif isinstance(d, list):
        for v in d:
            r = deep_find(v, key)
            if r is not None:
                return r
    return None


def explore_all():
    out, off = [], 0
    while True:
        d = api("GET", "/videos/explore", params={"scope": "all", "limit": 100, "offset": off})
        items = find_list(d)
        out += items
        total = d.get("total") if isinstance(d, dict) else None
        if not items or (total is not None and off + 100 >= total) or off > 3000:
            break
        off += 100
    return out


def seg_sources(item):
    """Ordered segment URIs of a parent chunk, from its timeline."""
    segs = []
    tl = item.get("timeline") or item.get("segments") or []
    for s in tl:
        src = s if isinstance(s, str) else (s.get("source") or s.get("segment_source")
                                            or s.get("preview_source") or s.get("s3_uri"))
        if not src:
            continue
        m = SEG_RE.search(src)
        segs.append((int(m.group(1)) if m else len(segs) + 1, src))
    segs.sort()
    return [s for _, s in segs]


def levels():
    c = _cache.get("levels")
    if c and time.time() - c[0] < 600:
        return c[1]
    lv = []
    for it in explore_all():
        ov = it.get("original_video") or ""
        fn = it.get("filename") or ov.rsplit("/", 1)[-1]
        m = CAMERA_RE.search(fn)
        if not m:
            continue
        segs = seg_sources(it)
        if not segs:
            continue
        lv.append({"camera": m.group(1), "filename": fn, "original_video": ov,
                   "segments": segs, "n": len(segs)})
    lv.sort(key=lambda x: x["filename"])
    _cache["levels"] = (time.time(), lv)
    return lv


def boxes(source):
    key = "box:" + source
    if key in _cache:
        return _cache[key]
    d = api("GET", "/videos/detections", params={"source": source})
    frames = d.get("frames") if isinstance(d, dict) else d
    if frames is None and isinstance(d, dict):
        for v in d.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and \
                    ("frame_index" in v[0] or "time_sec" in v[0]):
                frames = v
                break
    frames = frames or []
    shape = None
    out, xywh_votes, norm_votes = [], 0, 0
    for f in frames:
        if not shape and f.get("shape"):
            shape = f["shape"]
        dets = None
        for k in ("detections", "boxes", "objects", "dets"):
            if isinstance(f.get(k), list):
                dets = f[k]
                break
        if dets is None:
            for v in f.values():
                if isinstance(v, list) and v and isinstance(v[0], dict) and "bbox" in v[0]:
                    dets = v
                    break
        bb = []
        for o in dets or []:
            b = o.get("bbox") or o.get("box") or o.get("xyxy")
            if not b or len(b) < 4:
                continue
            b = [float(x) for x in b[:4]]
            if b[2] <= b[0] or b[3] <= b[1]:
                xywh_votes += 1
            if max(b) <= 1.0:
                norm_votes += 1
            bb.append([o.get("label") or o.get("class") or o.get("name") or "obj",
                       round(float(o.get("confidence", o.get("score", 0))), 3), b])
        t = f.get("time_sec")
        if t is None:
            t = float(f.get("frame_index", len(out))) / 30.0
        out.append({"t": float(t), "b": bb})
    shape = shape or [1080, 1920]
    h, w = float(shape[0]), float(shape[1])
    nb = sum(len(x["b"]) for x in out)
    for fr in out:
        for box in fr["b"]:
            b = box[2]
            if norm_votes == nb and nb:
                b = [b[0] * w, b[1] * h, b[2] * (w if xywh_votes else w), b[3] * (h if xywh_votes else h)]
            if xywh_votes:
                b = [b[0], b[1], b[0] + b[2], b[1] + b[3]]
            box[2] = [round(v, 1) for v in b]
    res = {"frames": out, "shape": [h, w], "count": nb, "format": "xywh" if xywh_votes else "xyxy"}
    _cache[key] = res
    return res


def caption(source):
    key = "cap:" + source
    if key in _cache:
        return _cache[key]
    try:
        d = api("GET", "/videos/metadata", params={"source": source})
        txt = deep_find(d, "reasoning_content") or ""
    except Exception as e:  # noqa: BLE001
        txt = ""
        log("caption failed", e)
    _cache[key] = txt
    return txt


def build_query(label, cap):
    """Colour word nearest to the vehicle label in the caption, plus the label."""
    cap = cap or ""
    label = (label or "vehicle").lower()
    names = {"truck": ["semi-truck", "semi", "truck", "tractor-trailer", "trailer"],
             "car": ["car", "sedan", "suv", "hatchback"], "bus": ["bus"]}.get(label, [label])
    best = None
    for n in names:
        for m in re.finditer(re.escape(n), cap, re.I):
            window = cap[max(0, m.start() - 45):m.start()]
            cols = [c for c in COLOURS if re.search(r"\b" + c + r"\b", window, re.I)]
            if cols:
                best = cols[-1]
                break
        if best:
            break
    if not best:
        anyc = [c for c in COLOURS if re.search(r"\b" + c + r"\b", cap, re.I)]
        best = anyc[0] if anyc else None
    noun = {"truck": "semi-truck", "car": "car", "bus": "bus"}.get(label, label)
    return (best + " " + noun) if best else noun


def investigate(label, cap, query=None):
    q = query or build_query(label, cap)
    d = api("POST", "/search", body={"query": q, "top_k": 15, "llm_top_n": 0,
                                     "min_similarity": 0.15, "include_public": True,
                                     "metadata_filters": {"camera_id": "i24_cam-1"}})
    hits = []
    for r in d.get("results", []):
        src = r.get("source") or ""
        m = CAMERA_RE.search(src)
        hits.append({"source": src, "camera": m.group(1) if m else "?",
                     "score": round(float(r.get("similarity_score", 0)), 3),
                     "caption": (r.get("reasoning_content") or "")[:400]})
    return {"query": q, "sql": d.get("sql_query"), "hits": hits}


# ---------------------------------------------------------------- mock mode
MOCK_DIR = "/tmp/hop24_mock"


def mock_levels():
    return [{"camera": "scene1_p1c2", "filename": "mock_scene1_p1c2_chunk_0000.mp4",
             "original_video": "mock", "n": 2,
             "segments": ["mock://seg1.mp4", "mock://seg2.mp4"]}]


def mock_boxes(source):
    fast = source.endswith("seg2.mp4")
    frames = []
    for i in range(150):
        t = i / 30.0
        bb = []
        for lane, (y, speed, w, h, lab) in enumerate([(300, 420, 140, 70, "car"), (430, -520, 240, 90, "truck"),
                                                      (560, 380, 150, 70, "car"), (690, -600, 150, 70, "car")]):
            sp = speed * (1.6 if fast else 1.0)
            x = (sp * t + lane * 500) % 2200 - 150 if sp > 0 else 2050 - ((-sp * t + lane * 500) % 2200)
            bb.append([lab, 0.9, [x, y, x + w, y + h]])
        frames.append({"t": t, "b": bb})
    return {"frames": frames, "shape": [1080, 1920], "count": 600, "format": "xyxy"}


def mock_video(source):
    """Render the mock clip with ffmpeg once; boxes above follow the same equations."""
    os.makedirs(MOCK_DIR, exist_ok=True)
    fast = source.endswith("seg2.mp4")
    path = os.path.join(MOCK_DIR, "seg2.mp4" if fast else "seg1.mp4")
    if os.path.exists(path):
        return path
    k = 1.6 if fast else 1.0
    lanes = [(300, 420, 140, 70, "white"), (430, -520, 240, 90, "red"), (560, 380, 150, 70, "silver"), (690, -600, 150, 70, "blue")]
    inputs = ["-f lavfi -i color=c=0x556b2f:s=1920x1080:d=5:r=30"]
    chain, prev = ["[0:v]drawbox=x=0:y=250:w=1920:h=530:color=0x303030:t=fill[bg]"], "bg"
    for lane, (y, sp, w, h, col) in enumerate(lanes):
        sp *= k
        inputs.append(f"-f lavfi -i color=c={col}:s={w}x{h}:d=5:r=30")
        xe = f"mod({sp}*t+{lane*500},2200)-150" if sp > 0 else f"2050-mod({-sp}*t+{lane*500},2200)"
        out = f"v{lane}"
        chain.append(f"[{prev}][{lane+1}:v]overlay=x='{xe}':y={y}:eval=frame:shortest=1[{out}]")
        prev = out
    cmd = (f"ffmpeg -loglevel error -y {' '.join(inputs)} -filter_complex \"{';'.join(chain)}\" -map '[{prev}]' "
           f"-pix_fmt yuv420p -movflags +faststart {path}")
    os.system(cmd)
    return path


# ---------------------------------------------------------------- self update
def self_update():
    if not RAW:
        return None
    os.makedirs(UPDATE_DIR, exist_ok=True)
    for f in ("main.py", "index.html"):
        with urllib.request.urlopen(RAW + f + "?t=" + str(int(time.time())), timeout=15) as r:
            data = r.read()
        with open(os.path.join(UPDATE_DIR, f), "wb") as fh:
            fh.write(data)
    return UPDATE_DIR


def exec_updated(path):
    time.sleep(0.5)
    os.execv(sys.executable, [sys.executable, os.path.join(path, "main.py")])


# ---------------------------------------------------------------- http
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quieter
        if "/stream" not in (args[0] if args else ""):
            log(self.address_string(), fmt % args)

    def _json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path, ctype):
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _range_file(self, path):
        size = os.path.getsize(path)
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            start = int(a) if a else max(0, size - int(b))
            end = int(b) if b and a else end
        end = min(end, size - 1)
        self.send_response(206 if rng else 200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        if rng:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(65536, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    def _proxy_stream(self, source):
        for attempt in (0, 1):
            url = API + "/videos/stream?" + urllib.parse.urlencode({"source": source, "token": login(force=bool(attempt))})
            headers = {}
            if self.headers.get("Range"):
                headers["Range"] = self.headers["Range"]
            try:
                resp = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120)
                break
            except urllib.error.HTTPError as e:
                if e.code == 401 and attempt == 0:
                    continue
                self.send_error(e.code, "upstream stream error")
                return
        self.send_response(resp.status)
        for h in ("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "ETag", "Last-Modified"):
            v = resp.headers.get(h)
            if v:
                self.send_header(h, v)
        if not resp.headers.get("Accept-Ranges"):
            self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        try:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            resp.close()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        p = u.path.rstrip("/") or "/"
        try:
            if p == "/":
                return self._file(os.path.join(HERE, "index.html"), "text/html; charset=utf-8")
            if p == "/health":
                return self._json({"status": "ok", "mock": MOCK, "file": __file__})
            if p == "/levels":
                return self._json({"levels": mock_levels() if MOCK else levels()})
            src = (q.get("source") or [""])[0]
            if p == "/boxes":
                return self._json(mock_boxes(src) if MOCK else boxes(src))
            if p == "/caption":
                txt = ("A white semi-truck and a red truck travel in opposite directions on a four-lane highway; "
                       "two cars follow in the right lanes.") if MOCK else caption(src)
                return self._json({"source": src, "caption": txt})
            if p == "/stream":
                return self._range_file(mock_video(src)) if MOCK else self._proxy_stream(src)
            if p == "/scores":
                return self._json({"scores": SCORES[-20:]})
            if p == "/reload":
                if (q.get("key") or [""])[0] != RELOAD_KEY:
                    return self._json({"error": "bad key"}, 403)
                path = self_update()
                self._json({"status": "updated, restarting", "path": path})
                threading.Thread(target=exec_updated, args=(path,), daemon=True).start()
                return
            self.send_error(404)
        except Exception as e:  # noqa: BLE001
            log("GET error", p, repr(e))
            try:
                self._json({"error": repr(e)}, 500)
            except Exception:  # noqa: BLE001
                pass

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        p = u.path.rstrip("/") or "/"
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:  # noqa: BLE001
            body = {}
        try:
            if p == "/score":
                SCORES.append({"name": str(body.get("name", "anon"))[:24], "result": body.get("result"),
                               "seconds": body.get("seconds"), "camera": body.get("camera"), "ts": time.time()})
                return self._json({"ok": True, "scores": SCORES[-20:]})
            if p == "/investigate":
                if MOCK:
                    return self._json({"query": build_query(body.get("label"), body.get("caption")),
                                       "sql": "SELECT ... FROM \"team-x-vss-db/vss-schema\".\"vss-collection\" WHERE camera_id = 'i24_cam-1' ORDER BY distance LIMIT 100",
                                       "hits": [{"source": "mock://seg2.mp4", "camera": "scene1_p1c3", "score": 0.41, "caption": "A red truck in the left lane."},
                                                {"source": "mock://seg1.mp4", "camera": "scene1_p1c1", "score": 0.35, "caption": "Traffic flows freely."}]})
                return self._json(investigate(body.get("label"), body.get("caption"), body.get("query")))
            self.send_error(404)
        except Exception as e:  # noqa: BLE001
            log("POST error", p, repr(e))
            self._json({"error": repr(e)}, 500)


def main():
    if not MOCK and RAW and os.environ.get("HOP24_AUTOUPDATE", "1") == "1" and not HERE.startswith(UPDATE_DIR):
        try:
            path = self_update()
            log("self-update ok, exec", path)
            os.execv(sys.executable, [sys.executable, os.path.join(path, "main.py")])
        except Exception as e:  # noqa: BLE001
            log("self-update skipped:", repr(e))
    ThreadingHTTPServer.allow_reuse_address = True
    ThreadingHTTPServer.daemon_threads = True
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), H)
    log(f"hop24 listening on {PORT} mock={MOCK} from {HERE}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
