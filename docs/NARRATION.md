# Hop 24 — what to say, in order

Audio of this script: `docs/Hop24-narration.mp3` (synthetic voice, for rehearsal). Speak it in your own words; keep the beats.
Running time at a brisk pace: about 4 minutes 30 seconds including the play phase. The slides are `docs/present.html`
(or https://vnmoorthy.github.io/hop24/present.html): slide 1 is the QR code, `→` advances, `L` opens the live app, `F` is fullscreen.

---

## 0. While the judges walk up — slide 1 (QR code, live scoreboard)  [about 45 seconds]

"Before I say anything, please scan this. It opens on your phone. Tap to start, swipe up to hop.
You are crossing Interstate 24 in Nashville — real footage, real traffic — and every car that kills you is a real detection
the pipeline stored in VastDB this morning. The scoreboard on screen is live. Go ahead, I'll wait ten seconds."

(Watch the scoreboard fill. Call out a name: "…someone just got flattened by a semi. Good.")

## 1. Explain the game while they play — stay on slide 1, or press L for the big screen  [about 40 seconds]

"Here is what you are actually playing. This is not an animation. The video is streamed from the VAST archive.
The boxes are YOLO detections that the DataEngine pipeline already wrote for every frame — nine thousand of them in this
thirty-second clip. We fit the road from those boxes, so the chicken always spawns on the near shoulder and has to cross
eight lanes of real traffic. And you don't die on a box: we cut every vehicle's outline with FastSAM, prompted by the stored
boxes, so you die when you touch metal. The chicken is the only thing we drew. The archive is the physics."

## 2. Slide 2 — title  [10 seconds]

"We are Team 10. This is Hop 24: a video agent that watches real footage and does something with it.
When a truck gets you, the archive is going to find that truck on every camera."

## 3. Slide 3 — the problem  [20 seconds]

"Here is the archive you gave us: four hundred and fourteen chunks, three highway cameras on one pole, every five seconds
captioned by Cosmos, every frame boxed by YOLO, every segment embedded in VastDB. It is all there, and nobody looks at any of
it until something goes wrong. We wanted the archive to act."

## 4. Slide 4 — the idea  [15 seconds]

"So we made the trigger a game. A collision is a concrete, timestamped event with a known vehicle, and the room understands
it in two seconds. Everything after the splat is the agent doing an investigator's job."

## 5. Slide 5 — kill-cam  (press L, play, die)  [25 seconds]

"Watch the replay. The last two point four seconds in slow motion, the killer tracked in red, blood at the point of contact.
On the right, the evidence frame: camera, segment, timestamp, class, confidence, all burned in.
Nothing here was staged. The vehicle that hit me is whatever YOLO put in that box."

## 6. Slide 6 — the archive already knew  [15 seconds]

"The moment I die, the agent reads the stored Cosmos description of that exact five-second segment.
We checked all one hundred and eighty highway captions: one hundred and forty-one name a colour, only forty-eight say which
lane, none give a lane number. Remember that gap."

## 7. Slide 7 — manhunt  (press L, click "Find my killer")  [25 seconds]

"One click. The agent pulls the colour and vehicle type out of the caption, builds a query, and runs a single hybrid search in
VastDB — caption vectors plus visual vectors, filtered to this corridor. Results come back grouped by camera, the strongest
sighting on another camera is highlighted, and here is the exact SQL that VastDB ran. These are candidate sightings; an
investigator confirms. We don't claim re-identification."

## 8. Slide 8 — incident report  (click "File incident report")  [15 seconds]

"Then it files the paperwork: event, camera and time, detection, the archive's description, the query, every sighting with a
score, last seen, recommended action, the evidence frame. Downloadable, printable. Thirty seconds ago this was a chicken."

## 9. Slide 9 — sharpen the archive  [20 seconds]

"The catch: search can only find what the caption says, and the stock prompt rarely says which lane. So the agent
re-describes the clip through your DataEngine pipeline with an investigator's prompt — type, colour, lane number, direction,
trailer, lane changes with timestamps. It takes minutes, so we ran it before walking up. Same clip, sharper archive."

## 10. Slide 10 — autopilot  (press L, press A)  [30 seconds]

"Last feature. Press A and the agent crosses by itself — with a policy it learned. We built a simulator from the archive's
own detections of all thirty clips and trained it with Q-learning; every run is logged to Weights and Biases.
No peeking: it only sees the boxes up to the current frame. Learned beats rule-based — forty-one versus thirty-nine percent of
random starts overall, forty-six versus thirty-one on this camera, and honestly worse on camera three. It still dies
sometimes. That is the proof it isn't scripted."

## 11. Slide 11 — architecture  [35 seconds]

"Under the hood, left to right. The browser is one HTML page: a canvas, two video elements, the road axis fitted from the
boxes, silhouette collision, the Q-table lookup, the kill-cam and the report.
Behind it a Python backend with no dependencies: it holds the JWT, proxies the video, and exposes levels, boxes, masks,
captions, the manhunt search, the re-describe job and the policy.
That talks to the VSS REST API — stream, detections, metadata, hybrid search, re-ingest — which sits on VAST AI OS:
the five-second segments in S3, one VastDB table holding captions, text and visual vectors, YOLO boxes and metadata, and the
DataEngine pipeline that wrote all of it using YOLO11, Cosmos Reason and Cosmos Embed on CoreWeave.
Two offline tools feed it: FastSAM, prompted by the stored boxes, produces the silhouettes; and the simulator plus Q-learning
produces the policy, tracked in Weights and Biases. Everything the agent reads, your pipeline made."

## 12. Slide 12 — close  [15 seconds]

"Problem, archive, search across cameras, action. The archive's own detections are the physics. One query covers every
camera. The agent can already cross on its own. The data was always there — we just gave it something to do.
Scoreboard says… [read the leader]. Thank you."

---

### If a judge asks
- **Is the autopilot peeking?** No — it sees boxes up to the current frame, estimates speed from the previous frame, hops only if the next lane is predicted clear; the Q-table was trained the same way. It gets killed sometimes.
- **Is that really the vehicle outline?** FastSAM prompted by the stored YOLO box, matched back by overlap, precomputed for the demo clip on a laptop because the pod has no GPU; other clips fall back to the box's inscribed ellipse.
- **Where does the blood come from?** A sprite drawn at the contact point. Nothing in the footage is altered.
- **What does VAST do?** Everything the agent reads lives in VAST: segments in S3, rows in VastDB, hybrid search returning its own SQL, re-describe through DataEngine. We didn't build a database or a pipeline; we gave yours an agent.
- **W&B?** Training of the autopilot is tracked in W&B (metrics, evaluations, the policy as an artifact). The app does not call W&B Inference or Weave at runtime — that's the next step.
