# Security

Hop 24 keeps no secrets in the repository. The backend reads `VSS_URL`, `VSS_USERNAME` and
`VSS_PASSWORD` from environment variables (a Kubernetes Secret on the team cluster), logs in to the
VSS REST API itself and keeps the JWT in process memory; video, detections and search results are
proxied so the token never reaches the browser. `WANDB_API_KEY` is likewise read from the
environment by `tools/hop24/rl/train.py` only. Model weights (`*.pt`) and W&B debug logs are
git-ignored; the one committed offline run under `tools/hop24/rl/wandb/` holds metrics and the
policy artifact only, no key. The self-update route `GET /reload?key=` is gated by `HOP24_RELOAD_KEY`
(default `hop`); change it on any deployment that is reachable from the public internet.

If you find a vulnerability (a leaked credential, a route that exposes the upstream token, a way to
make the backend fetch arbitrary URLs, an injection through captions or search results), please open
a GitHub issue at https://github.com/vnmoorthy/hop24/issues with the label `security` and enough
detail to reproduce it. Do not include working credentials in the issue. This is a hackathon
project maintained in spare time, so there is no bug bounty and no guaranteed response time, but
reports are read and fixed in the open.
