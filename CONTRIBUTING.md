# Contributing to Hop 24

Hop 24 is a one-day hackathon build (VAST Builders Challenge, 2 Oct 2026) that we want to keep
small, honest and runnable. Pull requests are welcome; the rules below keep the deployable part
of the repo deployable.

## Run locally (mock mode)

The backend is Python 3.12 standard library only. Mock mode renders a synthetic clip once with
`ffmpeg` (four lanes of coloured rectangles whose boxes follow the same equations the page
expects) and fakes `/investigate`, `/redescribe` and the fresh caption, so the whole
splat → manhunt → report → re-describe flow can be rehearsed without the cluster.

```bash
brew install ffmpeg            # or: sudo apt-get install -y ffmpeg
HOP24_MOCK=1 PORT=8080 python3 tools/hop24/main.py
# open http://localhost:8080/
```

To replay real segments offline, put `segNN.mp4` / `segNN.json` pairs (as downloaded from the app)
in a folder and add `HOP24_LOCALDATA=/path/to/segments`. To run against the VSS backend set
`VSS_URL`, `VSS_USERNAME`, `VSS_PASSWORD` instead of `HOP24_MOCK`.

Quick smoke test of a running server:

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8080/levels | head -c 300
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/policy.json
```

## Regenerate vehicle silhouettes (`tools/hop24/seg/masks.py`)

Collisions test the chicken against a vehicle silhouette, not its bounding box. `masks.py` runs
FastSAM (ultralytics `FastSAM-s.pt`) prompted by the archive's stored YOLO boxes, matches the
returned masks back to the boxes by overlap, simplifies each to a polygon of at most 14 points and
writes `tools/hop24/masks__<segment>.json`. The page fetches `GET /masks?source=<segment>` and
falls back to the inscribed ellipse of the box when no file exists (404).

```bash
pip install ultralytics opencv-python numpy
cd tools/hop24/seg
python3 masks.py --video /path/seg1.mp4 --boxes /path/seg1.json \
  --out ../masks__<segment_source_name>.json --every 3 --imgsz 768
```

Notes:

- `--every 3` and `--imgsz 768` are what the shipped masks were made with (72–94 KB per
  5 s segment, 50 mask frames). The script defaults are `--every 2`, `--imgsz 1024`.
- The pod has no GPU; the shipped masks were precomputed on a laptop and committed.
- `--detector rfdetr` re-detects vehicles with RF-DETR (`pip install rfdetr`) instead of using the
  stored boxes. It is optional and was not used for the shipped masks.
- Model weights (`*.pt`) are git-ignored. ultralytics downloads `FastSAM-s.pt` into the working
  directory on first use; never commit it.
- The output file name must be `masks__` + the segment's source name exactly as `/levels` reports it.

## Retrain the autopilot (`tools/hop24/rl/train.py`) and sync to W&B

The autopilot is a tabular Q-learning policy trained on an offline simulator built from the stored
detections of all 30 highway chunks, with the same geometry the browser uses. The export is
`tools/hop24/policy.json`, served at `/policy.json` and looked up live by the page.

```bash
pip install wandb
export WANDB_API_KEY=...                     # or WANDB_MODE=offline, or --no-wandb
python3 tools/hop24/rl/train.py --boxes /path/to/segment_jsons --out tools/hop24/policy.json
# optional: --episodes 9000 --alpha 0.15 --gamma 0.97 --seed 7
```

- `--boxes` is a folder of per-segment detection JSON files (the sidecar format normalised by
  `/boxes`). Use all 30 highway chunks; the shipped policy was trained on 27,000 frames.
- Every run logs to the W&B project `hop24-autopilot` (override with `WANDB_PROJECT_HOP24`):
  `train/*` every 100 episodes, `eval/*` every 1,000, `baseline/*` in the summary, and
  `policy.json` as the artifact `hop24-autopilot-policy`.
- If you trained offline, sync afterwards: `wandb sync tools/hop24/rl/wandb/offline-run-*`.
- Report the evaluation numbers the script prints (600 random starts with a fixed seed, learned
  vs rule-based, per camera; it is a same-data comparison on the training chunks, not a held-out
  test) in your PR. If the new policy is worse on a camera, say so.

## Render the trailer (`docs/trailer.py`)

```bash
pip install Pillow                           # plus ffmpeg on PATH
python3 docs/trailer.py /path/to/real_segments docs/Hop24-trailer.mp4
```

The input folder holds `segN.mp4` / `segN.json` pairs downloaded from the app. The script draws
the stored boxes over the real frames and composes the 37 s trailer at 1920x1080, 30 fps.
`docs/img/demo.gif` is a short loop cut from it.

## Coding style

- **Backend is stdlib only.** `tools/hop24/main.py` imports nothing outside the Python 3.12
  standard library. It runs unchanged from a Kubernetes ConfigMap on `python:3.12-slim`; there is
  no Docker build and no `pip install` on the pod. Keep it that way.
- **Single-file page.** `tools/hop24/index.html` is one HTML file with its CSS and JS inline. No
  bundler, no framework, no external script tags.
- **ConfigMap payload under 1 MiB.** The deployable set is `main.py`, `index.html`, `sprite.png`,
  `blood.png`, `policy.json` and the `masks__*.json` files. Check it before you push:

  ```bash
  cd tools/hop24 && cat main.py index.html sprite.png blood.png policy.json masks__*.json | wc -c
  ```

  It is about 916 KB today. `rl/` and `seg/` are tooling and must never be added to the ConfigMap.
- Tooling scripts (`rl/train.py`, `seg/masks.py`, `docs/trailer.py`) may use third-party packages;
  say which ones in the module docstring.
- No secrets in the repo. Credentials come from environment variables only (see `SECURITY.md`).
- Be concrete in docs and commit messages: numbers that were measured, features that exist.
  Do not describe behaviour the live app cannot show.

## PR checklist

- [ ] `python -m py_compile tools/hop24/main.py tools/hop24/rl/train.py tools/hop24/seg/masks.py` passes
- [ ] Mock server starts and `/health`, `/levels`, `/policy.json` return 200
- [ ] `main.py` still imports only the standard library
- [ ] ConfigMap payload is under 1,000,000 bytes
- [ ] No `*.pt` weights, W&B logs, tokens or passwords committed
- [ ] If `policy.json` changed: training command and eval numbers are in the PR description
- [ ] If `masks__*.json` changed: which segments, `--every` and `--imgsz` used
- [ ] README / CHANGELOG updated if behaviour or routes changed
