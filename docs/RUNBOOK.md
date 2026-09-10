# Runbook: HighErrorRate

## Purpose

This runbook describes how to investigate and recover from the `HighErrorRate` alert for the `/work` endpoint.

## Alert Condition

The alert fires when more than 20% of `/work` requests return HTTP 5xx responses over a 2-minute window and the condition remains true for at least 1 minute.

## Initial Checks

Check the application Pod:

```bash
kubectl get pods -n sre-lab

```

Check the Deployment:

```bash
kubectl get deployment sre-reliability-lab -n sre-lab
```

Start a local port-forward to the application Service in a separate terminal:

```bash
kubectl port-forward -n sre-lab \
  service/sre-reliability-lab 8001:8000
```

Verify readiness:

```bash
curl -i http://127.0.0.1:8001/ready
```

Verify the workload endpoint:

```bash
curl -i http://127.0.0.1:8001/work
```

## Prometheus Checks

Check whether the alert is active:

```bash
curl -sG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=ALERTS{alertname="HighErrorRate"}' \
  | python3 -m json.tool
```

Check the current 5xx error ratio:

```promql
sum(increase(sre_lab_requests_total{path="/work",status=~"5.."}[2m]))
/
clamp_min(
  sum(increase(sre_lab_requests_total{path="/work"}[2m])),
  1
)
```

## Recovery

If controlled failure mode is enabled, disable it:

```bash
kubectl set env deployment/sre-reliability-lab \
  -n sre-lab \
  FAIL_MODE=false
```

Wait for the rollout:

```bash
kubectl rollout status deployment/sre-reliability-lab \
  -n sre-lab \
  --timeout=120s
```

Verify the new Pod is healthy:

```bash
kubectl get pods -n sre-lab
```

Verify `/ready` and `/work` return HTTP 200.

## Resolution Verification

After the 2-minute Prometheus lookback window clears, verify that the alert is no longer active:

```bash
curl -sG 'http://127.0.0.1:9090/api/v1/query' \
  --data-urlencode 'query=ALERTS{alertname="HighErrorRate"}' \
  | python3 -m json.tool
```

Expected result:

```json
"result": []
```
