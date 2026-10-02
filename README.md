# Hop 24

A video agent game on the VAST Builders Challenge stack: cross a real I-24 highway clip as a pixel chicken.
Collisions come from the archive's own YOLO detections (`/videos/detections`), the kill-cam reads the
Cosmos caption stored in VastDB (`/videos/metadata`), and "Find my killer" runs one hybrid search
(`/search`) across every highway camera and shows the VastDB SQL it executed.

Stdlib-only Python backend + one HTML page, built for the `deploy-app-no-registry` skill
(python:3.12-slim, code in a ConfigMap, Ingress path `/app`).

## Deploy on the team cluster (from the VM)

```bash
cd ~ && git clone https://github.com/vnmoorthy/hop24.git && cp -r hop24/tools/hop24 ~/vast-builders-challenge/tools/hop24
```

Then tell Cursor:

> Deploy tools/hop24 to /app with the deploy-app-no-registry skill, exactly the way hello-app was deployed
> (kubectl in ~/.local/bin, KUBECONFIG=/config/team-10-k8s.yaml, Secret VSS_URL=http://video-backend-service:8000,
> app name hop24, port 8080). Replace the hello-app Ingress at /app. Confirm /app/health and /app/levels return
> JSON and report the output of /app/levels briefly.

## Update loop without redeploying

The pod self-updates from this repo: `GET /app/reload?key=hop` downloads the latest `main.py` + `index.html`
from GitHub and restarts in place. It also tries once at start-up. If the pod has no internet access, redeploy
with the ConfigMap as usual.

## Local demo

```bash
HOP24_MOCK=1 PORT=8080 python3 tools/hop24/main.py   # synthetic clip, needs ffmpeg
```

## Keys

Space start · arrows hop · B boxes · C calibrate road band (click top edge, then bottom edge) · R retry
