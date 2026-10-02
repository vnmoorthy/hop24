## What this changes

<!-- One or two sentences. Link the issue if there is one. -->

## How it was tested

- [ ] `python -m py_compile tools/hop24/main.py tools/hop24/rl/train.py tools/hop24/seg/masks.py`
- [ ] Mock server (`HOP24_MOCK=1 PORT=8080 python3 tools/hop24/main.py`): `/health`, `/levels`, `/policy.json` return 200
- [ ] Played a full splat → manhunt → report flow (mock or live)

## Checklist

- [ ] `main.py` still imports only the Python standard library
- [ ] `index.html` is still a single file (no external scripts)
- [ ] ConfigMap payload (`main.py index.html sprite.png blood.png policy.json masks__*.json`) is under 1,000,000 bytes
- [ ] No `*.pt` weights, W&B debug logs, tokens or passwords added
- [ ] `policy.json` changed → training command and eval numbers below
- [ ] `masks__*.json` changed → segments, `--every`, `--imgsz` below
- [ ] README / CHANGELOG updated if routes or behaviour changed

## Numbers / notes

<!-- Eval results, payload size, anything a reviewer should verify. -->
