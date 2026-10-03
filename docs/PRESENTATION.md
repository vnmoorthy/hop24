# Hop 24 — 3-minute presentation storyboard

10 slides, 3:00 total. Slides 3, 4, 6, 7 and 9 are LIVE in the app; everything else is a static slide.
Every number below comes from the live team-10 archive or the code in `tools/hop24/`. Do not inflate them on stage.

A note on "real video": the stage footage in Hop 24 is real I-24 Nashville camera video streamed from the VAST archive, not an animation. The only drawn elements are the chicken sprite sheet, the green FastSAM silhouettes over the stored boxes, and the blood sprite sheet at impact; the video frames are untouched. Say this out loud on slide 3 — it is the single biggest "wait, really?" moment and it is true.

Timing budget (speak at ~165 wpm; this is brisk, so rehearse with a timer):

| # | Slide | Time | Mode |
|---|-------|------|------|
| 1 | Title | 0:00-0:16 | slide |
| 2 | Problem | 0:16-0:34 | slide |
| 3 | The idea / the game | 0:34-0:56 | LIVE |
| 4 | Kill-cam | 0:56-1:16 | LIVE |
| 5 | The archive already knew | 1:16-1:32 | slide |
| 6 | Manhunt | 1:32-1:54 | LIVE |
| 7 | Incident report | 1:54-2:10 | LIVE |
| 8 | Sharpen the archive / re-describe | 2:10-2:26 | slide (+ one optional click) |
| 9 | Autopilot | 2:26-2:44 | LIVE |
| 10 | Architecture + next | 2:44-3:00 | slide |

---

## Opening line (lands in 5 seconds)

> "This is a real highway in Nashville. I am going to cross it as a chicken, and when a truck kills me, the archive is going to find that truck on every camera."

## Closing line

> "Hop 24: the archive's own detections are the physics, one query covers every camera, and the agent can already cross on its own. The data was always there. We just gave it something to do."

---

## Slide 1 — Title  (0:00-0:16)

**On screen:** `docs/img/hero.jpg` full-bleed (1600x900). Title "HOP 24", subtitle "cross a real highway · the archive is watching". Team 10, one line: built on VAST AI OS + NVIDIA Cosmos + VastDB.

**Spoken (48 words):**
"This is a real highway in Nashville. I am going to cross it as a chicken, and when a truck kills me, the archive is going to find that truck on every camera. We are Team 10. This is Hop 24, a video agent built on the VAST stack you gave us this morning."

**Gesture / click:** Stand still, let the hero image do the work. Advance on "this morning".

**Fallback:** none needed; static slide.

---

## Slide 2 — Problem  (0:16-0:34)

**On screen:** Three plain lines, big type:
- 414 video chunks indexed. 30 of them are I-24 highway, 3 cameras on one pole.
- Captions, YOLO boxes, 256-dim vectors, all sitting in VastDB.
- Nobody looks at any of it until something goes wrong.

**Spoken (52 words):**
"Here is the archive you built for us: 414 chunks, three highway cameras on one pole, every five seconds captioned by Cosmos, every frame boxed by YOLO, every segment embedded in VastDB. It is all there. And it does nothing until something goes wrong and a human starts scrubbing footage. We wanted the archive to act."

**Gesture / click:** Point at the third line on "nothing".

**Fallback:** none; static slide.

---

## Slide 3 — The idea / the game  (0:34-0:56)  LIVE

**On screen:** Switch to the browser. App open on the venue URL, chunk_0003 on p1c2 selected, intro overlay visible (`intro.jpg` is what this looks like). Press space. Hop with the arrow keys, two or three hops into traffic. YOLO boxes are ON (B). Inside every box a green vehicle silhouette is drawn (FastSAM mask, prompted by the stored box); the HUD pill reads `silhouettes · FastSAM`.

**Spoken (69 words):**
"So we made it a game. This is not an animation, this is real I-24 footage streaming from the archive. Every box is a YOLO detection the pipeline already stored. The road axis is fitted from those boxes. The chicken is a sprite sheet, the only thing we drew. Collision is the green outline: FastSAM, prompted by the stored box, gives the vehicle's silhouette. The archive is the physics."

**Gesture / click:** Press `space` on "made it a game". Hop `↑` twice on "real I-24 footage". Point at a green silhouette on "the green outline". Point at the `silhouettes · FastSAM` pill on "FastSAM".

**Fallback:** If the stream does not start within 3 seconds, show `docs/img/intro.jpg` then `docs/img/splat.jpg` and say "the venue network is being shy; this is the same screen". Keep the same words.

---

## Slide 4 — Kill-cam  (0:56-1:16)  LIVE

**On screen:** Hop into a truck or car on purpose. Screen shakes. Slow-motion (0.35x) letterboxed replay of the last 2.4 s with the killer tracked in red. When the replay ends, a 12-frame blood burst (a sprite sheet) plays at the point of contact and the last frame stays on the road as a stain. The Kill-cam card then shows the cropped evidence frame, re-captured about 60 ms after the burst settles, with camera, segment, time, class and confidence burned in (`replay.jpg`, `splat.jpg`).

**Spoken (62 words):**
"And there it is. Watch the replay: the last two point four seconds, slow motion, the killer tracked in red. The impact leaves blood where the silhouette touched me, and the evidence frame is re-captured once it settles: camera, segment, timestamp, class, confidence, all burned in. The footage itself is untouched. The vehicle that hit me is whatever YOLO put in that box."

**Gesture / click:** Hop `↑` into the nearest lane with traffic on "and there it is". Point at the red box during the replay. Point at the stain on "leaves blood". Point at the Kill-cam card on "evidence frame".

**Fallback:** If the replay stalls (video seek fails), the banner still shows "SPLAT · killed by a <class>"; show `docs/img/replay.jpg` for the slow-mo and keep going. If no collision happens within two hops, press `R` and hop again; do not wait more than 5 seconds.

---

## Slide 5 — The archive already knew  (1:16-1:32)

**On screen:** Slide with two columns. Left: the stored caption of the killer's segment (copy the actual text shown in the Kill-cam card at rehearsal time; do not paraphrase). Right, three facts:
- 180 highway captions in the archive
- 141 mention a vehicle colour
- 48 say which lane, 0 give a lane number

**Spoken (50 words):**
"The moment I die, the agent reads the stored Cosmos description for that exact five-second segment. The archive already knew what hit me: a colour, a vehicle type, sometimes a lane. We checked all 180 highway captions: 141 name a colour, only 48 say which lane, none give a lane number. Remember that gap."

**Gesture / click:** Point at the caption on "already knew". Tap the "48" on "only 48".

**Fallback:** none; static slide. If the live caption on slide 4 said "(no description stored for this segment)", say "this segment's caption had not been written yet; here is a neighbouring one" and show the slide text.

---

## Slide 6 — Manhunt  (1:32-1:54)  LIVE

**On screen:** Back in the app. Click "Find my killer across cameras". Card 2 appears: the query (colour word nearest the vehicle noun in the caption + noun, e.g. "white semi-truck"), the corridor view p1c1 | p1c2 | p1c3 with sightings grouped per camera, the strongest sighting on another camera highlighted, and a collapsible "VastDB query the backend ran" showing the real SQL (`manhunt.jpg`).

**Spoken (62 words):**
"Now the agent goes looking. One click. It pulls the colour and the vehicle type out of the caption, builds a query, and runs a single hybrid search in VastDB: caption vectors plus visual vectors, text weight point six, filtered to this camera corridor. Results come back grouped by camera. Strongest match on another camera gets highlighted. And here is the exact SQL VastDB ran."

**Gesture / click:** Click "Find my killer" on "one click". Point at the highlighted sighting on "strongest match". Expand the SQL `details` on "exact SQL". If time allows, click one sighting to jump to that segment, then press Escape.

**Fallback:** If `/investigate` errors or takes more than 4 seconds, show `docs/img/manhunt.jpg` and say "in rehearsal 'white semi truck' returned ten hits, every one containing 'white'; here is that run." Do not retry live more than once.

---

## Slide 7 — Incident report  (1:54-2:10)  LIVE

**On screen:** Click "File incident report". The modal shows event, camera/time, detection, archive description, query issued, sightings per camera, last seen, recommended action, evidence frame and SQL (`report.jpg`). Scroll it once, slowly. Buttons: download HTML, copy as text, print.

**Spoken (48 words):**
"Then it files the paperwork. Event, camera and time, the detection, the archive's description, the query it issued, every sighting with a score, where the vehicle was last seen, a recommended action, and the evidence frame. Downloadable, printable. Thirty seconds ago this was a chicken getting hit."

**Gesture / click:** Click "File incident report" on "files the paperwork". Scroll with the trackpad through the table; stop on the evidence frame. Press Escape on "chicken getting hit".

**Fallback:** The report is generated client-side from state already in the page, so it only fails if slide 4 failed. In that case show `docs/img/report.jpg` and say the same words.

---

## Slide 8 — Sharpen the archive / re-describe  (2:10-2:26)

**On screen:** Slide: left, the stock caption for the killer's segment (same text as slide 5). Right, the investigator caption that came back from the pre-run re-describe job (copy the real text from "Re-read caption" during the pre-demo checklist). Under it, the prompt summary: type, colour, lane number from the left shoulder, direction, trailer, lane changes with time. Footer: "DataEngine: detector → reasoner → embedder → VastDB writer".

Optional live click if the pre-run completed in this tab: click "Re-read caption" in card 3 and let the fresh description replace the stock one on screen.

**Spoken (55 words):**
"Here is the catch: search can only find what the caption says, and the stock prompt rarely says which lane. So the agent re-describes the clip through your DataEngine pipeline with an investigator's prompt: type, colour, lane number, direction, trailer, lane changes with timestamps. It takes minutes, so we ran it before walking up. Same clip, sharper archive, better next search."

**Gesture / click:** Point at the left caption on "rarely says which lane", then the right one on "same clip, sharper archive". If clicking "Re-read caption" live, do it on "same clip".

**Fallback:** If the pre-run job did not complete, keep this as a pure slide and say "it was still running when we walked up; this is the output from an earlier run". Never start a new re-describe job on stage.

---

## Slide 9 — Autopilot  (2:26-2:44)  LIVE

**On screen:** Back in the app on the same chunk. Press `A`. The HUD pill reads `AUTOPILOT · RL policy` and the thought line shows the Q-table lookup live (`RL · here clear · next 0.4s · +2 clear · back clear · lane 3/8 → hop (Q …)`); unseen states fall back to the rule-based agent ("next lane clear for 0.65 s → hop", "hold · truck crossing the next lane …"). It crosses, or it dies; both are fine.

Numbers (600 random chunk/start-time episodes, same seed for both policies, on the same 30 chunks the policy trained on; `tools/hop24/rl/train.py`): learned 40.7% crossed vs rule-based 38.8% overall; on p1c2 (this camera) 46.2% vs 31.3%; on p1c3 the learned policy is worse (53.4% vs 64.0%). 9,000 episodes of tabular Q-learning, 241 s on a laptop, every run logged to Weights & Biases project `hop24-autopilot`.

**Spoken (64 words):**
"Last thing. Press A and the agent crosses with a policy it learned. We built a simulator from the archive's own detections of all thirty clips, trained it with Q-learning, and logged every run to Weights and Biases. No peeking at future frames. Learned beats rule-based: 41 versus 39 percent of random starts overall, 46 versus 31 on this camera. It still dies sometimes. That is the proof."

**Gesture / click:** Press `A` on "press A". Point at the `AUTOPILOT · RL policy` pill on "policy it learned". Point at the thought line on "no peeking". If it dies, say "see, honest" and move on; do not retry.

**Fallback:** If the stream will not play, show `docs/img/crossed.jpg` (the CROSSED banner from a real autopilot run) and read the same words.

---

## Slide 10 — Architecture + next  (2:44-3:00)

**On screen:** One diagram, left to right:
`Browser (canvas, 1280x720)` → `Hop 24 backend (Python stdlib, ~580 lines)` → `VSS REST API` → `VastDB vss-collection / S3 segments`.
Side labels: Cosmos3-Reason captions, Cosmos Embed1 vectors, YOLO11s boxes, DataEngine reingest. Three "next" bullets: more poles of the I-24 corridor; let the agent choose its own re-describe prompt per incident; track a vehicle across segments, not just find look-alikes.

**Spoken (68 words):**
"Under the hood it is one HTML page and a stdlib Python proxy; everything it reads, your pipeline made: Cosmos captions, Embed1 vectors, YOLO boxes, VastDB. Next: more poles, and true tracking across segments. Hop 24: the archive's own detections are the physics, one query covers every camera, and the agent can already cross on its own. The data was always there. We just gave it something to do."

(If running long, cut "Next: more poles, and true tracking across segments.")

**Gesture / click:** Sweep left to right across the diagram on "one HTML page … VastDB". Stop moving for the closing line. Say "thank you" after it, not before.

**Fallback:** none; static slide.

---

## Pre-demo checklist (do this in order, 15 minutes before)

0. **Open the presentation:** `docs/present.html`, served by a range-capable static server (python's `http.server` cannot seek the trailer video; e.g. `npx serve docs` or `caddy file-server`) or the published URL `https://vnmoorthy.github.io/hop24/present.html`. Press `F` for fullscreen; `←`/`→` move between the 10 slides; `L` opens the live app in a new tab. Confirm the title slide plays the trailer.
1. **Clear localStorage first.** In the browser devtools on the app origin: `localStorage.clear()`. This removes any saved road-edge calibration (`hop24.axis.*`) so the road axis is fitted from the detections live, which is what you say on slide 3. Do this BEFORE the next step; do not reload the tab afterwards.
2. **Open the app on the venue URL:** `http://video-lab-team-10.cosmos.vastdata.com/app` (or press `L` in the presentation). Keep `https://team-10-app.thecosmoslabs.com/app/` open in a second tab as the public fallback.
3. **Wait for "loading the archive…" to finish** on the intro overlay (the `/levels` call parses 3 cameras x 10 chunks).
4. **Pick p1c2 in the camera chips and chunk_0003 in the chunk selector.** This is the chunk the autopilot numbers (2.2 s crossing) were measured on, and the only chunk with precomputed FastSAM silhouettes (all 6 segments); other chunks fall back to an ellipse inside the box.
4a. **Confirm the HUD pills:** after the stream starts, the HUD must show `silhouettes · FastSAM` (green; means `/masks` loaded for this segment) and `AUTOPILOT · RL policy` once you press `A` (means `/policy.json` loaded). If either is missing, the ConfigMap is stale: redeploy, or hit `/reload?key=` and refresh.
5. **Player name:** type the judge's company into the "player name" field (it is the scoreboard name; keep it short so the scoreboard row fits).
6. **Pre-run re-describe, 10 minutes before:** click "Re-describe this clip" in card 3 and watch the progress bar until "completed · 6/6 segments". It takes minutes. Then click "Re-read caption" once, copy the fresh text into slide 8. **Keep this tab open and do not reload it:** the "Re-read caption" button only enables in the tab where the job was polled.
7. **Zoom the browser to 110%** (cmd + once or twice) so the Kill-cam card and thought line read from the back of the room. Check the 1280x720 stage still fits without a horizontal scrollbar.
8. **Sound off** on the laptop (system mute). The app has no audio, but the venue mic will pick up notifications.
9. **Boxes ON** (the "Boxes" button should be lit; press `B` if not). Judges need to see the detections to believe slide 3.
10. **One dry run:** space, hop, die, "Find my killer", "File incident report", Escape, `A`. Confirm the manhunt returns hits and the SQL expands. Press `R` to reset. Then leave the intro overlay up for slide 3.
11. **Fallback images open in a viewer**, in this order: `intro.jpg`, `splat.jpg`, `replay.jpg`, `manhunt.jpg`, `report.jpg`, `crossed.jpg`, (all in `docs/img/`).
12. Close every other tab, notifications off, Do Not Disturb on, power connected.

---

## Likely judge questions and answers

**Is the autopilot peeking at the future?**
No. It only sees the boxes already drawn for the current frame and the previous ~0.3 s. It matches each box to its nearest neighbour in the previous frame to estimate velocity, bins the time-to-arrival of the current, next, next-but-one and previous lanes into a state, and looks that state up in the learned Q-table (hold / hop / back). States it never saw during training fall back to the rule-based agent: extrapolate 0.65 s ahead, hop only if no predicted box overlaps the next cell. Boxes with no velocity estimate are assumed to be at highway speed. It gets killed sometimes; that is the proof.

**Is the RL honest? What did it actually learn?**
Tabular Q-learning (`tools/hop24/rl/train.py`) on an offline simulator built from the stored detections of all 30 highway chunks, 27,000 frames, with the app's exact geometry: PCA road axis, 8 hops across, ellipse collision, the same velocity estimator. 9,000 episodes, 241 s on a laptop. Evaluated against the rule-based agent on 600 random starts with the same seed (same 30 chunks it trained on, so a same-data comparison, not a held-out test): 40.7% crossed vs 38.8% overall; 46.2% vs 31.3% on p1c2; 24.5% vs 23.6% on p1c1; and worse on p1c3, 53.4% vs 64.0%. Every run is logged to Weights & Biases (project `hop24-autopilot`, policy exported as the `hop24-autopilot-policy` artifact). A two-point overall gain is modest; the per-camera split is the honest picture.

**Is that really the vehicle outline?**
Yes, within the limits of a small segmentation model. `tools/hop24/seg/masks.py` runs FastSAM (`FastSAM-s.pt`) prompted by the archive's stored YOLO boxes, matches each mask back to its box by overlap, and simplifies it to a polygon of at most 14 points, every 3rd frame. The page picks the nearest mask frame, matches it to the live box by IoU, shifts it by the box's motion since that frame, draws it green and tests the chicken's five body points against it. The masks were precomputed on a laptop for the demo chunk (p1c2 chunk_0003, all 6 segments); the pod has no GPU. Other chunks fall back to an ellipse inside the box.

**Where does the blood come from?**
A 12-frame sprite sheet (`tools/hop24/blood.png`: a burst of droplets, then a spreading pool) drawn on the canvas at the point of contact after the slow-motion replay ends; the last frame stays on the road as a stain. Nothing in the footage is altered; the video frames come straight from the archive. The evidence frame is re-captured once the burst settles so the report shows the scene as it ended.

**Is this re-identification? Are you claiming that is the same truck on the other camera?**
No, and we say so on the report. The search returns description-similar segments ("candidate sightings"), ranked by hybrid similarity, filtered to the corridor. An investigator still has to confirm. That is why the re-describe step exists: the stock captions rarely say which lane, and lane plus colour plus trailer narrows candidates a lot.

**What does VAST do here?**
Everything we read lives in VAST: the 5-second segments in S3, the per-segment rows in the VastDB `vss-collection` table (caption, text vector, visual vector, YOLO detections, camera metadata), and the hybrid search that returns its own SQL. The re-describe step is a DataEngine reingest job (segmenter → detector → reasoner → embedder → VastDB writer) with a custom prompt. Our backend is a 580-line stdlib proxy on top of the VSS REST API; we did not build a database or a pipeline, we gave yours an agent.

**Why a game?**
Because a collision is a concrete, timestamped event with a known vehicle, and the room understands it in two seconds. The game is the staging; the agent's work starts after the hit: read the caption, search every camera, file the report, sharpen the archive. The same loop applies to any trigger event in the footage. It also forced us to use the stored detections as physics, which is a stress test of the archive's quality on every frame.

**What about W&B?**
The autopilot policy is trained with Q-learning on a simulator built from the stored detections, and every training run is logged to Weights & Biases (crossing/death rates, reward, evaluations, the exported policy as an artifact). The app does not call W&B Inference or Weave at runtime; the next step is letting an LLM write the investigator prompt and the report narrative per incident and tracing those calls in Weave.

**Did the crash actually happen in the footage?**
No. There are no crashes in the dataset. The hit-and-run framing is a scenario built around a real detection at a real timestamp; the chicken is the only fiction.

**How much of the corridor do you cover?**
One pole, three cameras (p1c1, p1c2, p1c3), ten 30-second chunks each, 30 fps, 1920x1080. All highway clips share `camera_id = i24_cam-1`, so the "every camera" search is a corridor filter, and more poles would just be more rows.

**How heavy are the detections?**
150 frames per 5-second segment; about 1,430 boxes in one segment and 9,294 across one 30-second chunk. Classes seen: car, truck, bus (semis sometimes read as "bus", which is why the autopilot is label-agnostic).



## Links to have open
- W&B training report: https://wandb.ai/vnmoorthy-amperes-ai/sandbox/reports/Hop-24-autopilot-Q-learning-on-the-archive-detections--VmlldzoxODA0Nzk1Nw (public mirror: https://wandb.ai/vastdata/hop24-autopilot/reports/Hop-24-autopilot---Q-learning-on-the-archive-detections--VmlldzoxODA0Nzc4OA==)
- Live app: https://team-10-app.thecosmoslabs.com/app/ · Presentation: https://vnmoorthy.github.io/hop24/present.html · Repo: https://github.com/vnmoorthy/hop24
