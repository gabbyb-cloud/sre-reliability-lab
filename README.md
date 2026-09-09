# SRE Reliability Lab

A deliberately small, fully local SRE portfolio lab focused on Kubernetes operations, infrastructure as code, observability, SLOs, alerting, and incident response.

## Why this project exists

The lab is not another backend application. The service is intentionally tiny so the engineering focus stays on operating it reliably.

## Locked scope

1. Tiny FastAPI service
2. Docker container
3. Local Kubernetes with kind
4. Helm deployment
5. Minimal Terraform
6. Prometheus + Grafana
7. One availability SLO
8. One `HighErrorRate` alert
9. One controlled incident
10. One runbook + one blameless postmortem

Everything runs for $0.

## Phase 1 — Tiny observable service

Current endpoints:

- `GET /health` — liveness endpoint
- `GET /ready` — readiness endpoint
- `GET /work` — workload endpoint used for reliability experiments
- `GET /metrics` — Prometheus metrics

Set `FAIL_MODE=true` to simulate controlled service failure without crashing the process.

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open another terminal:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/work
curl http://127.0.0.1:8000/metrics | head
```

### Run the controlled failure locally

```bash
FAIL_MODE=true uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then:

```bash
curl -i http://127.0.0.1:8000/ready
curl -i http://127.0.0.1:8000/work
```

Expected: `/ready` returns `503` and `/work` returns `500`.

## Next phase

Containerize and run this service in a local kind Kubernetes cluster, then add liveness/readiness probes and demonstrate automatic pod recovery.
