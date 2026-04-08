import logging
from time import perf_counter

from app.core.config import settings
from app.core.observability import record_trace_event, set_correlation_id
from app.db.session import SessionLocal
from app.services.playbook_service import execute_playbook_for_incident
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.tasks.incident_tasks.process_incident",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=settings.CELERY_RETRY_BACKOFF_SECONDS,
    retry_jitter=True,
    retry_kwargs={"max_retries": settings.CELERY_TASK_MAX_RETRIES},
)
def process_incident(self, incident_id: int, correlation_id: str | None = None) -> dict[str, int | str | bool]:
    started_at = perf_counter()
    task_correlation_id = correlation_id or self.request.id
    set_correlation_id(task_correlation_id)
    logger.info(
        "Processing incident asynchronously",
        extra={"incident_id": incident_id, "correlation_id": task_correlation_id},
    )
    record_trace_event(
        stage="task.start",
        message="Celery task started",
        correlation_id=task_correlation_id,
        attributes={"incident_id": incident_id, "task_id": self.request.id},
    )
    db = SessionLocal()
    try:
        task_id = self.request.id
        logger.info(
            "Celery task accepted",
            extra={"incident_id": incident_id, "task_id": task_id, "correlation_id": task_correlation_id},
        )
        try:
            result = execute_playbook_for_incident(db=db, incident_id=incident_id, task_id=task_id)
            duration_ms = int((perf_counter() - started_at) * 1000)
            logger.info(
                "Celery task completed",
                extra={
                    "incident_id": incident_id,
                    "task_id": task_id,
                    "success": bool(result.get("success")),
                    "execution_duration_ms": duration_ms,
                    "correlation_id": task_correlation_id,
                },
            )
            record_trace_event(
                stage="task.success",
                message="Celery task completed successfully",
                correlation_id=task_correlation_id,
                attributes={
                    "incident_id": incident_id,
                    "task_id": task_id,
                    "duration_ms": duration_ms,
                    "success": bool(result.get("success")),
                },
            )
            return result
        except Exception as exc:
            duration_ms = int((perf_counter() - started_at) * 1000)
            record_trace_event(
                stage="task.error",
                message="Celery task execution raised an exception",
                correlation_id=task_correlation_id,
                attributes={
                    "incident_id": incident_id,
                    "task_id": task_id,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                },
            )
            raise
    finally:
        db.close()
