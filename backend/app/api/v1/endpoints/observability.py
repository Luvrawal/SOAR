from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.core.auth import require_roles
from app.core.observability import observability_store
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/observability", dependencies=[Depends(require_roles("admin"))])


def _label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _render_prometheus_text(metrics: dict) -> str:
    lines: list[str] = []

    lines.append("# HELP soar_requests_total Total HTTP requests observed by API.")
    lines.append("# TYPE soar_requests_total counter")
    lines.append(f"soar_requests_total {int(metrics.get('total_requests', 0))}")

    lines.append("# HELP soar_request_errors_total Total HTTP 5xx responses observed by API.")
    lines.append("# TYPE soar_request_errors_total counter")
    lines.append(f"soar_request_errors_total {int(metrics.get('total_errors', 0))}")

    lines.append("# HELP soar_request_error_rate_percent Percentage of requests ending with 5xx.")
    lines.append("# TYPE soar_request_error_rate_percent gauge")
    lines.append(f"soar_request_error_rate_percent {float(metrics.get('error_rate_pct', 0.0))}")

    lines.append("# HELP soar_request_latency_avg_ms Average request latency in milliseconds.")
    lines.append("# TYPE soar_request_latency_avg_ms gauge")
    lines.append(f"soar_request_latency_avg_ms {float(metrics.get('avg_latency_ms', 0.0))}")

    lines.append("# HELP soar_uptime_seconds API process uptime in seconds.")
    lines.append("# TYPE soar_uptime_seconds gauge")
    lines.append(f"soar_uptime_seconds {int(metrics.get('uptime_seconds', 0))}")

    lines.append("# HELP soar_requests_by_status_total Requests grouped by HTTP status code.")
    lines.append("# TYPE soar_requests_by_status_total counter")
    for status, count in metrics.get("requests_by_status", {}).items():
        lines.append(f'soar_requests_by_status_total{{status="{_label_value(str(status))}"}} {int(count)}')

    lines.append("# HELP soar_requests_by_method_total Requests grouped by HTTP method.")
    lines.append("# TYPE soar_requests_by_method_total counter")
    for method, count in metrics.get("requests_by_method", {}).items():
        lines.append(f'soar_requests_by_method_total{{method="{_label_value(str(method))}"}} {int(count)}')

    lines.append("# HELP soar_requests_by_route_total Requests grouped by route template.")
    lines.append("# TYPE soar_requests_by_route_total counter")
    for route, count in metrics.get("requests_by_route", {}).items():
        lines.append(f'soar_requests_by_route_total{{route="{_label_value(str(route))}"}} {int(count)}')

    return "\n".join(lines) + "\n"


@router.get("/metrics", response_model=ApiResponse)
def get_metrics() -> ApiResponse:
    return ApiResponse(
        message="Observability metrics fetched successfully",
        data={"metrics": observability_store.snapshot()},
    )


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
def get_metrics_prometheus() -> PlainTextResponse:
    metrics = observability_store.snapshot()
    payload = _render_prometheus_text(metrics)
    return PlainTextResponse(content=payload, media_type="text/plain; version=0.0.4")
