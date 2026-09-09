# Locked Scope — SRE Reliability Lab

## Goal
Build the smallest credible, fully free SRE portfolio lab that closes the user's remaining hands-on gaps for Associate SRE / SRE I / Platform Engineer I roles.

## Must include
- Tiny FastAPI service
- Docker
- Local Kubernetes with kind
- Helm deployment
- Minimal Terraform managing one Kubernetes resource (target: `sre-lab` namespace)
- Prometheus + Grafana via kube-prometheus-stack
- One availability SLO
- One `HighErrorRate` alert
- One controlled failure/recovery incident
- One runbook
- One short blameless postmortem

## Explicitly out of scope
- Paid cloud
- PostgreSQL or Redis
- Frontend or authentication
- Microservices
- PagerDuty/OpsGenie
- Multiple incidents/runbooks/postmortems
- Load-test suite
- Autoscaling
- AI incident tooling

## Cost constraint
$0 development cost. Everything must run locally or use free tooling already available.
