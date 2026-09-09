import os
import time

from fastapi import FastAPI, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(title="SRE Reliability Lab", version="0.1.0")

REQUESTS = Counter(
    "sre_lab_requests_total",
    "Total HTTP requests handled by the lab service",
    ["path", "status"],
)
LATENCY = Histogram(
    "sre_lab_request_duration_seconds",
    "Request latency in seconds",
    ["path"],
)


def fail_mode_enabled() -> bool:
    return os.getenv("FAIL_MODE", "false").lower() == "true"


@app.get("/health")
def health() -> dict[str, str]:
    REQUESTS.labels(path="/health", status="200").inc()
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response) -> dict[str, str]:
    if fail_mode_enabled():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        REQUESTS.labels(path="/ready", status="503").inc()
        return {"status": "not-ready"}

    REQUESTS.labels(path="/ready", status="200").inc()
    return {"status": "ready"}


@app.get("/work")
def work(response: Response) -> dict[str, str]:
    started = time.perf_counter()
    try:
        if fail_mode_enabled():
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            REQUESTS.labels(path="/work", status="500").inc()
            return {"status": "error", "message": "controlled failure enabled"}

        REQUESTS.labels(path="/work", status="200").inc()
        return {"status": "ok"}
    finally:
        LATENCY.labels(path="/work").observe(time.perf_counter() - started)


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
