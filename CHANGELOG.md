# Changelog

All notable changes to Hop 24 are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Autopilot learns from live runs.** Each finished autopilot run posts its per-frame
  `(state, action, moved)` trail to `POST /experience`; the backend applies the Q-learning update from
  `rl/train.py` to the policy and `/policy.json` serves the updated table, so the next run uses it. The
  learned table is kept in `HOP24_LEARN_DIR` (default `/tmp/hop24-learn`).

## [1.0.0] - 2026-10-02

Hackathon build for the VAST Builders Challenge ("Real-Time Video Agents Hack - SF"), Team 10.

### Added

- **Game.** Cross a real 30 s I-24 Nashville clip (3 cameras on one pole, 10 chunks each, six
  5 s segments per chunk) as a chicken on a 1280x720 canvas. The road axis is fitted from the stored
  YOLO11 detections themselves (PCA of box centres); 8 hops across; keyboard controls
  (Space, arrows, A, B, C, R, Esc).
- **Collisions from the archive.** Every hit comes from the stored detections sidecar, overlaid
  frame-synchronously; grace period until the first hop.
- **Vehicle silhouettes.** `seg/masks.py` runs FastSAM prompted by the stored YOLO boxes and writes
  `masks__<segment>.json` (polygons of at most 14 points, every 3rd frame). The page matches a polygon
  to the live box by IoU, shifts it by the box's motion, draws it in green and tests the chicken's
  5 body points with point-in-polygon. Falls back to the inscribed ellipse of the box when no mask
  file exists. Shipped for all 6 segments of `scene1_p1c2 chunk_0003`. Optional `--detector rfdetr`.
- **Sprite sheets.** `sprite.png` (9 frames: 8-frame hop cycle + splat) and `blood.png` (12 frames:
  burst + spreading pool). The blood burst plays at the point of contact after the replay and the
  last frame stays as a stain; the evidence frame is re-captured after it settles.
- **Kill-cam.** Slow-motion (0.35x) letterboxed replay of the last 2.4 s with the killer's class
  tracked in red, then a cropped evidence frame with camera, segment, time, class and confidence
  burned in.
- **Manhunt.** `POST /investigate` builds a query from the stored Cosmos caption (colour word nearest
  the vehicle noun + noun) and runs one hybrid `/search` with `camera_id = i24_cam-1`; results are
  grouped per camera in a corridor view, the strongest sighting on another camera is highlighted and
  the VastDB SQL is shown. Click a sighting to watch that segment.
- **Incident report.** Generated client-side (event, camera/time, detection, archive description,
  query, sightings, last seen, recommended action, evidence frame, SQL). Download as HTML, copy as
  text, print.
- **Sharpen the archive.** `POST /redescribe` sends the chunk through `/dashboard/reingest` with an
  investigator prompt; `GET /redescribe?job=` polls; "Re-read caption" shows the new description.
- **Rule-based autopilot.** Nearest-neighbour box matching gives per-vehicle velocity; the agent hops
  only if no box is predicted to overlap the next cell within 0.65 s, dodges back when threatened,
  and shows its reasoning in a thought line.
- **Learned autopilot (RL).** `rl/train.py`: tabular Q-learning on an offline simulator built from
  the stored detections of all 30 highway chunks (27,000 frames), 9,000 episodes, logged to the
  Weights & Biases project `hop24-autopilot` with `policy.json` as an artifact. Served at
  `/policy.json`; the page looks the state up live and falls back to the rule-based agent for
  unseen states. Evaluation on 600 random starts (same seed, same 30 chunks it trained on):
  40.7% crossed vs 38.8% rule-based (p1c2 46.2% vs 31.3%; p1c3 53.4% vs 64.0%, worse).
- **Backend** (`main.py`, Python stdlib only): login with re-login on 401; `GET /`, `/health`,
  `/levels`, `/boxes`, `/stream` (Range pass-through proxy), `/caption` (`?fresh=1`), `/sprite.png`,
  `/blood.png`, `/masks?source=`, `/policy.json`, `/scores`, `/redescribe?job=`, `/reload?key=`;
  `POST /investigate`, `/redescribe`, `/score`. In-memory scoreboard.
- **Mock mode** (`HOP24_MOCK=1`) with synthetic ffmpeg footage and faked investigate / redescribe;
  `HOP24_LOCALDATA` for replaying downloaded real segments offline.
- **Self-update.** `GET /reload?key=` fetches `main.py`, `index.html`, `sprite.png`, `blood.png` and
  `policy.json` from GitHub and re-execs; also tried once at start-up.
- **Docs.** README, `docs/present.html` (10-slide animated presentation), `docs/Hop24-deck.pptx`,
  `docs/Hop24-trailer.mp4` (37 s, rendered by `docs/trailer.py` from real segments and stored boxes),
  `docs/PRESENTATION.md` (3-minute storyboard), screenshots and `demo.gif` in `docs/img/`.
- Repository hygiene: CONTRIBUTING, CHANGELOG, SECURITY, CODE_OF_CONDUCT, issue and PR templates,
  CI workflow, GitHub Pages landing page (`docs/index.html`). MIT license.

### Known limitations

- Manhunt returns description-similar segments (candidate sightings), not re-identification.
- The collision is staged; the agent's job starts after it. No crashes exist in the dataset.
- Re-describe takes minutes through the pipeline and is pre-run for demos.
- No direct W&B Inference, Weave or Cosmos calls at runtime; everything read was produced by the
  pipeline and stored in VastDB.
- Only one pole (3 cameras) of the I-24 corridor is in the team archive.
- Masks are precomputed on a laptop (the pod has no GPU) and exist for one chunk.

[1.0.0]: https://github.com/vnmoorthy/hop24/releases/tag/v1.0.0
