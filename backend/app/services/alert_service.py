import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.observability import get_correlation_id, record_trace_event
from app.models.incident import Incident
from app.schemas.alert import AlertCreate
from app.tasks.incident_tasks import process_incident

logger = logging.getLogger(__name__)


def _queue_catalog() -> dict[str, str]:
    return {
        "default": settings.CELERY_QUEUE_DEFAULT,
        "email": settings.CELERY_QUEUE_EMAIL,
        "endpoint": settings.CELERY_QUEUE_ENDPOINT,
        "file": settings.CELERY_QUEUE_FILE,
    }


def _worker_runbook_commands() -> list[str]:
    commands: list[str] = []
    for label, queue_name in _queue_catalog().items():
        commands.append(
            "celery -A app.tasks.celery_app.celery_app worker "
            f"-Q {queue_name} -n {label}_worker@%h --concurrency={settings.CELERY_WORKER_CONCURRENCY}"
        )
    return commands


def get_queue_metrics(db: Session, window_hours: int = 24) -> dict[str, int | float | bool | str | dict | list]:
    pending_count = int(
        db.query(func.count(Incident.id))
        .filter(func.lower(Incident.playbook_status) == "pending")
        .scalar()
        or 0
    )
    running_count = int(
        db.query(func.count(Incident.id))
        .filter(func.lower(Incident.playbook_status) == "running")
        .scalar()
        or 0
    )

    backlog = pending_count + running_count
    capacity = settings.PLAYBOOK_QUEUE_CAPACITY
    utilization_pct = round((backlog / capacity) * 100, 2) if capacity > 0 else 0.0

    pressure = "low"
    if utilization_pct >= 90:
        pressure = "critical"
    elif utilization_pct >= 70:
        pressure = "high"
    elif utilization_pct >= 40:
        pressure = "medium"

    queue_names = _queue_catalog()
    per_queue: dict[str, dict[str, int | float]] = {
        queue_name: {
            "total": 0,
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "throughput_per_hour": 0.0,
            "failure_rate_pct": 0.0,
        }
        for queue_name in queue_names.values()
    }

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    recent_incidents = db.query(Incident).filter(Incident.created_at >= cutoff).all()
    for incident in recent_incidents:
        queue_name = _queue_for_incident(incident)
        if queue_name not in per_queue:
            per_queue[queue_name] = {
                "total": 0,
                "pending": 0,
                "running": 0,
                "success": 0,
                "failed": 0,
                "throughput_per_hour": 0.0,
                "failure_rate_pct": 0.0,
            }

        status = str(incident.playbook_status or "pending").lower()
        queue_bucket = per_queue[queue_name]
        queue_bucket["total"] = int(queue_bucket["total"]) + 1
        if status in {"pending", "running", "success", "failed"}:
            queue_bucket[status] = int(queue_bucket[status]) + 1

    for queue_name, queue_bucket in per_queue.items():
        total = int(queue_bucket["total"])
        failures = int(queue_bucket["failed"])
        queue_bucket["throughput_per_hour"] = round(total / max(window_hours, 1), 2)
        queue_bucket["failure_rate_pct"] = round((failures / total) * 100, 2) if total else 0.0

    return {
        "pending": pending_count,
        "running": running_count,
        "backlog": backlog,
        "capacity": capacity,
        "utilization_pct": utilization_pct,
        "is_over_capacity": backlog >= capacity if capacity > 0 else False,
        "pressure": pressure,
        "worker_concurrency": settings.CELERY_WORKER_CONCURRENCY,
        "task_max_retries": settings.CELERY_TASK_MAX_RETRIES,
        "retry_backoff_seconds": settings.CELERY_RETRY_BACKOFF_SECONDS,
        "window_hours": window_hours,
        "queues": queue_names,
        "per_queue": per_queue,
        "worker_runbook": _worker_runbook_commands(),
    }


def _queue_for_incident(incident: Incident) -> str:
    raw_alert = incident.raw_alert if isinstance(incident.raw_alert, dict) else {}
    alert_type = str(raw_alert.get("alert_type", "")).lower()
    source = str(incident.source or "").lower()

    if "phish" in alert_type or "email" in source:
        return settings.CELERY_QUEUE_EMAIL
    if "malware" in alert_type or "file" in source or "hash" in alert_type:
        return settings.CELERY_QUEUE_FILE
    if "network" in alert_type or "brute" in alert_type or "ip" in alert_type:
        return settings.CELERY_QUEUE_ENDPOINT
    return settings.CELERY_QUEUE_DEFAULT


def _enqueue_incident_task(incident_id: int, queue_name: str, correlation_id: str | None = None) -> None:
    if hasattr(process_incident, "apply_async"):
        process_incident.apply_async(
            args=(incident_id,),
            kwargs={"correlation_id": correlation_id},
            queue=queue_name,
        )
    else:
        process_incident.delay(incident_id)


def create_incident_from_alert(db: Session, alert: AlertCreate) -> Incident:
    incident = Incident(
        title=alert.title,
        description=alert.description,
        source=alert.source,
        severity=alert.severity,
        status="open",
        raw_alert=alert.raw_alert,
        created_by=alert.created_by,
    )
    try:
        db.add(incident)
        db.commit()
        db.refresh(incident)
    except SQLAlchemyError as exc:
        db.rollback()
        raise AppException(
            status_code=500,
            message="Failed to persist incident",
            error_code="incident_persistence_failed",
            details={"reason": str(exc.__class__.__name__)},
        ) from exc

    # Trigger asynchronous processing pipeline after persistence succeeds.
    correlation_id = get_correlation_id()
    queue_metrics = get_queue_metrics(db)
    route_queue = _queue_for_incident(incident)
    if bool(queue_metrics.get("is_over_capacity")):
        logger.warning(
            "Playbook queue capacity threshold reached",
            extra={
                "incident_id": incident.id,
                "backlog": queue_metrics.get("backlog"),
                "capacity": queue_metrics.get("capacity"),
            },
        )

    try:
        _enqueue_incident_task(incident.id, route_queue, correlation_id=correlation_id)
        record_trace_event(
            stage="queue.enqueue",
            message="Incident queued for asynchronous playbook execution",
            correlation_id=correlation_id,
            attributes={
                "incident_id": incident.id,
                "queue": route_queue,
                "backlog": queue_metrics.get("backlog"),
            },
        )
    except Exception:
        logger.exception("Failed to enqueue incident processing task", extra={"incident_id": incident.id})
        record_trace_event(
            stage="queue.enqueue_failed",
            message="Failed to enqueue incident for playbook execution",
            correlation_id=correlation_id,
            attributes={"incident_id": incident.id, "queue": route_queue},
        )

    return incident
