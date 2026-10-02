---
name: Feature request
about: Propose something the agent, the game or the tooling should do
title: "[feature] "
labels: enhancement
---

**Problem**
What is missing or awkward today?

**Proposal**
What should happen instead? Which part: page (`index.html`), backend (`main.py`),
silhouettes (`seg/masks.py`), autopilot (`rl/train.py`), docs?

**Constraints to keep in mind**
- Backend stays Python stdlib only; page stays a single HTML file.
- ConfigMap payload stays under 1 MiB.
- Everything the agent reads must come from the archive (VastDB / VSS REST), not invented data.

**Evidence** (optional)
Numbers, screenshots, or a link to a segment that shows the need.
