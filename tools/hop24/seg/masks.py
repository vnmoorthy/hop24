#!/usr/bin/env python3
"""Vehicle silhouettes for Hop 24 collisions: FastSAM, prompted by the archive's own YOLO boxes.

For every frame of a segment, each stored box is handed to FastSAM as a box prompt; the returned mask is
simplified to a short polygon (video pixel coordinates). The game then tests the chicken against the
vehicle's silhouette instead of its bounding rectangle, so brushing the empty corner of a box is not a hit.

Usage:
  python3 masks.py --video seg1.mp4 --boxes seg1.json --out masks/<segment>.json [--every 2] [--model FastSAM-s.pt]
Optional: --detector rfdetr re-detects vehicles with RF-DETR (pip install rfdetr) instead of using the stored boxes.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np


def simplify(mask, max_pts=14):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs:
        return None
    c = max(cs, key=cv2.contourArea)
    if cv2.contourArea(c) < 40:
        return None
    eps = 0.01 * cv2.arcLength(c, True)
    p = cv2.approxPolyDP(c, eps, True)
    while len(p) > max_pts:
        eps *= 1.5
        p = cv2.approxPolyDP(c, eps, True)
    return [[int(x), int(y)] for x, y in p.reshape(-1, 2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--boxes", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--every", type=int, default=2, help="process every Nth frame (the game interpolates by nearest frame)")
    ap.add_argument("--model", default="FastSAM-s.pt")
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--detector", default="archive", choices=["archive", "rfdetr"])
    args = ap.parse_args()

    from ultralytics import FastSAM
    sam = FastSAM(args.model)
    det = None
    if args.detector == "rfdetr":
        from rfdetr import RFDETRBase  # optional
        det = RFDETRBase()

    with open(args.boxes) as fh:
        bx = json.load(fh)
    frames = {f["frame_index"]: f for f in bx["frames"]}
    cap = cv2.VideoCapture(args.video)
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = {"source": bx.get("source"), "width": W, "height": H, "every": args.every, "model": os.path.basename(args.model),
           "prompt": "archive YOLO boxes" if det is None else "rf-detr boxes", "frames": []}
    i = 0
    while True:
        ok, img = cap.read()
        if not ok:
            break
        if i % args.every == 0:
            f = frames.get(i)
            boxes = []
            if det is not None:
                import supervision as sv  # noqa: F401
                d = det.predict(img[:, :, ::-1], threshold=0.4)
                boxes = [{"label": "vehicle", "confidence": float(c), "bbox": [float(v) for v in b]} for b, c in zip(d.xyxy, d.confidence)]
            elif f:
                boxes = [b for b in f["boxes"] if b["label"] != "person"]
            polys = []
            if boxes:
                r = sam(img, bboxes=[b["bbox"] for b in boxes], imgsz=args.imgsz, conf=0.25, iou=0.7, retina_masks=True, verbose=False)[0]
                masks = list(r.masks.data.cpu().numpy()) if r.masks is not None else []
                masks = [cv2.resize(m.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) if m.shape != (H, W) else m.astype(np.uint8) for m in masks]
                areas = [max(1, int(m.sum())) for m in masks]
                for b in boxes:  # FastSAM does not return masks in prompt order: pick the mask that lives inside this box
                    x0, y0, x1, y1 = [max(0, int(v)) for v in b["bbox"]]
                    best, score = None, 0.0
                    for m, ar in zip(masks, areas):
                        inside = int(m[y0:y1, x0:x1].sum())
                        sc = inside / ar
                        if inside > 0 and sc > score:
                            best, score = m, sc
                    poly = None
                    if best is not None and score > 0.5:
                        sub = np.zeros_like(best, dtype=np.uint8); sub[max(0, y0 - 4):y1 + 4, max(0, x0 - 4):x1 + 4] = 1
                        poly = simplify(best & sub)
                    polys.append({"label": b["label"], "bbox": [round(v) for v in b["bbox"]], "poly": poly})
            out["frames"].append({"frame_index": i, "time_sec": round(i / 30.0, 3), "polys": polys})
            if i % 30 == 0:
                print(f"frame {i}: {len(polys)} silhouettes", file=sys.stderr, flush=True)
        i += 1
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print("wrote", args.out, os.path.getsize(args.out), "bytes,", len(out["frames"]), "frames")


if __name__ == "__main__":
    main()
