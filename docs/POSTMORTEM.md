# Postmortem: Controlled High Error Rate Incident

## Summary

A controlled failure was introduced into the `sre-reliability-lab` application by enabling `FAIL_MODE=true`.

During the incident, the `/work` endpoint returned HTTP 500 responses while `/ready` continued returning HTTP 200.

Prometheus detected the elevated error rate, and the `HighErrorRate` alert progressed from pending to firing.

The failure mode was disabled, the application recovered, and the alert automatically resolved after the Prometheus lookback window cleared.

## Impact

During the controlled incident:

- `/work` returned HTTP 500 responses.
- `/ready` continued returning HTTP 200.
- The service remained reachable.
- Kubernetes continued treating the Pod as ready.

No real users or production systems were affected because this was a local reliability test.

## Detection

Prometheus detected the incident using the `HighErrorRate` alert.

The alert condition was:

- More than 20% of `/work` requests return HTTP 5xx responses over a 2-minute window.
- The condition remains true for at least 1 minute.

Observed alert lifecycle:

```text
Inactive
→ Pending
→ Firing
→ Resolved
```

## Root Cause

The incident was intentionally triggered by setting the application's `FAIL_MODE` environment variable to `true`.

When failure mode is enabled, the `/work` endpoint intentionally returns HTTP 500 responses so failure detection and recovery procedures can be tested.

## Resolution

Failure mode was disabled through Helm:

```bash
helm upgrade sre-reliability-lab \
  ./helm/sre-reliability-lab \
  --namespace sre-lab \
  --set image.tag=0.1.0 \
  --set env.FAIL_MODE=false
```

Kubernetes rolled out the updated Deployment.

Recovery was verified by confirming that:

- The application Pod was `1/1 Running`.
- `/ready` returned HTTP 200.
- `/work` returned HTTP 200.
- `HighErrorRate` was no longer active.

## Lessons Learned

Application-level monitoring was necessary because the Pod could remain healthy and ready while the `/work` endpoint was returning errors.

The Prometheus `for` duration prevented a brief error spike from immediately becoming a firing alert.

The 2-minute lookback window also meant the alert remained active briefly after the application itself recovered.

Monitoring both infrastructure health and application behavior provides a more complete picture of service reliability.

## Follow-Up Actions

- Maintain the `HighErrorRate` runbook alongside the alert definition.
- Keep the controlled `FAIL_MODE` mechanism for repeatable reliability testing.
- Keep the availability SLO visible in Grafana.
- Continue storing monitoring and alert configuration in version control.
