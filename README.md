# SRE Reliability Lab

A fully local, $0 Site Reliability Engineering lab demonstrating containerization, Kubernetes operations, Helm, infrastructure as code, observability, SLOs, alerting, controlled failure injection, incident response, and recovery verification.

[![Validate](https://github.com/gabbyb-cloud/sre-reliability-lab/actions/workflows/validate.yml/badge.svg)](https://github.com/gabbyb-cloud/sre-reliability-lab/actions/workflows/validate.yml)

The application itself is intentionally small so the focus stays on operating and observing a service reliably.

## What this project demonstrates

- Containerizing a Python FastAPI service with Docker
- Running Kubernetes locally with kind
- Packaging and deploying the application with Helm
- Configuring Kubernetes liveness and readiness probes
- Exposing Prometheus application metrics
- Discovering the application with a `ServiceMonitor`
- Monitoring the service with Prometheus and Grafana
- Defining a 99% availability SLO
- Creating a `HighErrorRate` Prometheus alert
- Injecting a controlled HTTP 500 failure
- Observing an alert transition from pending to firing
- Recovering the service and verifying alert resolution
- Documenting operational response with a runbook
- Writing a blameless incident postmortem
- Managing an existing Kubernetes namespace with Terraform
- Validating Python, Docker, Helm, and Terraform changes with GitHub Actions

## Architecture

```text
FastAPI
   |
   v
Docker image
   |
   v
kind Kubernetes cluster
   |
   +--> Helm Deployment
   |       |
   |       v
   |      Pod
   |       |
   |       v
   |   Kubernetes Service
   |       |
   |       v
   |    /metrics
   |
   +--> ServiceMonitor
           |
           v
       Prometheus
           |
           +--> PromQL
           |
           +--> HighErrorRate alert
           |
           v
         Grafana
           |
           v
     99% Availability SLO
```

## Application endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Liveness check |
| `GET /ready` | Readiness check |
| `GET /work` | Workload endpoint used for reliability testing |
| `GET /metrics` | Prometheus metrics endpoint |

The application exposes:

- `sre_lab_requests_total`
- `sre_lab_request_duration_seconds`

## Run locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify the endpoints:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
curl -i http://127.0.0.1:8000/work
curl http://127.0.0.1:8000/metrics
```

## Build the Docker image

```bash
docker build -t sre-reliability-lab:local .
```

The container uses Python 3.12 and exposes port `8000`.

## Local Kubernetes with kind

Create the local Kubernetes cluster:

```bash
kind create cluster --name sre-lab
```

Load the locally built image into the kind node:

```bash
kind load docker-image sre-reliability-lab:local --name sre-lab
```

kind runs Kubernetes nodes as Docker containers, allowing the full lab to run locally without paid cloud infrastructure.

## Deploy with Helm

The Helm chart is stored under:

```text
helm/sre-reliability-lab/
```

Install the application:

```bash
helm install sre-reliability-lab \
  helm/sre-reliability-lab \
  --namespace sre-lab \
  --create-namespace
```

Verify the Deployment:

```bash
kubectl get pods -n sre-lab
kubectl get services -n sre-lab
```

Expected Pod state:

```text
READY   STATUS    RESTARTS
1/1     Running   0
```

The chart also configures:

- Liveness probe using `/health`
- Readiness probe using `/ready`
- ClusterIP Service on port `8000`
- Prometheus `ServiceMonitor`
- `HighErrorRate` Prometheus rule

## Monitoring

The lab uses `kube-prometheus-stack` for Prometheus, Grafana, Alertmanager, kube-state-metrics, and node-exporter.

Install it with:

```bash
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts

helm repo update

helm install monitoring \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

Verify monitoring components:

```bash
kubectl get pods -n monitoring
```

The application `ServiceMonitor` instructs Prometheus to scrape:

```text
/metrics
```

on the application's named `http` port.

Prometheus successfully discovers the application target as:

```text
UP
```

## Availability SLO

The lab defines one availability objective:

> At least 99% of `/work` requests should return a successful HTTP 2xx response.

### SLI

The service level indicator measures:

```text
successful /work requests
-------------------------
total /work requests
```

For the local low-traffic lab, the Grafana panel uses a 15-minute request window:

```promql
100 *
sum(increase(sre_lab_requests_total{path="/work",status=~"2.."}[15m]))
/
sum(increase(sre_lab_requests_total{path="/work"}[15m]))
```

Grafana displays the result in the:

```text
Work Endpoint Availability
```

panel.

Threshold:

```text
< 99%  = SLO missed
>= 99% = SLO met
```

## HighErrorRate alert

The lab includes a Prometheus alert named:

```text
HighErrorRate
```

The alert triggers when more than 20% of `/work` requests return HTTP 5xx responses over a 2-minute window and the condition remains true for at least 1 minute.

The rule is stored in the Helm chart and version-controlled with the application.

Alert lifecycle demonstrated during testing:

```text
Inactive
   |
   v
Pending
   |
   v
Firing
   |
   v
Resolved
```

## Controlled failure injection

The service supports controlled failure testing through the `FAIL_MODE` environment variable.

Normal behavior:

```text
FAIL_MODE=false

/ready -> HTTP 200
/work  -> HTTP 200
```

Failure behavior:

```text
FAIL_MODE=true

/ready -> HTTP 200
/work  -> HTTP 500
```

Keeping `/ready` healthy during the test allows the service to remain reachable while Prometheus observes application-level failures.

Enable failure mode:

```bash
kubectl set env deployment/sre-reliability-lab \
  -n sre-lab \
  FAIL_MODE=true
```

Disable failure mode:

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

During the controlled incident, sustained HTTP 500 traffic caused `HighErrorRate` to transition to:

```text
firing
```

After failure mode was disabled and the Prometheus lookback window cleared, the alert returned no active results.

## Incident response

Operational documentation is stored under:

```text
docs/
├── RUNBOOK.md
└── POSTMORTEM.md
```

### Runbook

`docs/RUNBOOK.md` documents how to:

- Inspect the Pod and Deployment
- Port-forward to the service
- Verify `/ready` and `/work`
- Inspect the Prometheus error ratio
- Disable controlled failure mode
- Verify rollout recovery
- Confirm alert resolution

### Postmortem

`docs/POSTMORTEM.md` documents the controlled incident, including:

- Impact
- Detection
- Root cause
- Resolution
- Verification
- Lessons learned
- Follow-up actions

## Terraform

Terraform is intentionally minimal in this lab.

It manages the existing:

```text
sre-lab
```

Kubernetes namespace using the HashiCorp Kubernetes provider.

Configuration:

```text
terraform/main.tf
```

Initialize Terraform:

```bash
cd terraform
terraform init
```

The namespace already existed before Terraform was introduced, so it was adopted into Terraform state:

```bash
terraform import kubernetes_namespace_v1.sre_lab sre-lab
```

Verify infrastructure state:

```bash
terraform plan
```

Expected result:

```text
No changes. Your infrastructure matches the configuration.
```

This demonstrates adopting existing infrastructure into Terraform management without deleting or recreating it.

## Continuous validation

GitHub Actions validates changes on pushes and pull requests targeting `main`.

The workflow checks:

- Python source compilation
- Docker image build
- Helm chart linting
- Terraform formatting
- Terraform initialization and validation

This keeps the repository's application, container, chart, and infrastructure configuration continuously verifiable without requiring paid cloud infrastructure.

## Project structure

```text
sre-reliability-lab/
├── .github/
│   └── workflows/
│       └── validate.yml
├── app/
│   └── main.py
├── docs/
│   ├── POSTMORTEM.md
│   └── RUNBOOK.md
├── helm/
│   └── sre-reliability-lab/
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── terraform/
│   └── main.tf
├── .dockerignore
├── .gitignore
├── Dockerfile
├── LOCKED_SCOPE.md
├── README.md
└── requirements.txt
```

## Reliability exercise demonstrated

This lab completes an end-to-end reliability workflow:

```text
Deploy
  |
  v
Observe
  |
  v
Define SLO
  |
  v
Detect elevated errors
  |
  v
Alert
  |
  v
Investigate
  |
  v
Recover
  |
  v
Verify
  |
  v
Document
```

The project is intentionally small, local, repeatable, and focused on core SRE practices rather than application complexity.

## Cost

The development and reliability lab runs entirely locally using free and open-source tooling.

**Development cost: $0**
