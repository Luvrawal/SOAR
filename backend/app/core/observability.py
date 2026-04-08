from __future__ import annotations

from collections import defaultdict, deque
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock


_correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(value: str) -> None:
    _correlation_id_var.set(value)


def get_correlation_id() -> str | None:
    return _correlation_id_var.get()


def record_trace_event(
    stage: str,
    message: str,
    correlation_id: str | None = None,
    attributes: dict | None = None,
) -> None:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "message": message,
        "correlation_id": correlation_id,
        "attributes": attributes or {},
    }
    observability_store.record_trace_event(event)


@dataclass
class ObservabilityStore:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_requests: int = 0
    total_errors: int = 0
    total_latency_ms: float = 0.0
    by_status: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_route: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_method: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    recent_events: deque[dict] = field(default_factory=lambda: deque(maxlen=100))
    recent_trace_events: deque[dict] = field(default_factory=lambda: deque(maxlen=200))
    lock: Lock = field(default_factory=Lock)

    def record_trace_event(self, event: dict) -> None:
        with self.lock:
            self.recent_trace_events.appendleft(event)

    def record(
        self,
        method: str,
        route: str,
        status_code: int,
        latency_ms: float,
        correlation_id: str | None = None,
    ) -> None:
        status_key = str(status_code)
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method.upper(),
            "route": route,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 2),
            "correlation_id": correlation_id,
        }
        with self.lock:
            self.total_requests += 1
            self.total_latency_ms += latency_ms
            self.by_status[status_key] += 1
            self.by_route[route] += 1
            self.by_method[method.upper()] += 1
            self.recent_events.appendleft(event)
            if status_code >= 500:
                self.total_errors += 1

    def snapshot(self) -> dict:
        with self.lock:
            avg_latency = round(self.total_latency_ms / self.total_requests, 2) if self.total_requests else 0.0
            uptime_s = int((datetime.now(timezone.utc) - self.started_at).total_seconds())
            error_rate = round((self.total_errors / self.total_requests) * 100, 2) if self.total_requests else 0.0
            return {
                "started_at": self.started_at.isoformat(),
                "uptime_seconds": uptime_s,
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate_pct": error_rate,
                "avg_latency_ms": avg_latency,
                "requests_by_status": dict(self.by_status),
                "requests_by_route": dict(self.by_route),
                "requests_by_method": dict(self.by_method),
                "recent_events": list(self.recent_events),
                "recent_trace_events": list(self.recent_trace_events),
            }


observability_store = ObservabilityStore()
