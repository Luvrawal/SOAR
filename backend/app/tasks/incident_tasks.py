import logging
from time import perf_counter

from app.db.session import SessionLocal
from app.services.playbook_service import execute_playbook_for_incident
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.incident_tasks.process_incident")
def process_incident(incident_id: int) -> dict[str, int | str | bool]:
    started_at = perf_counter()
    logger.info("Processing incident asynchronously", extra={"incident_id": incident_id})
    db = SessionLocal()
    try:
        task_id = process_incident.request.id
        logger.info("Celery task accepted", extra={"incident_id": incident_id, "task_id": task_id})
        result = execute_playbook_for_incident(db=db, incident_id=incident_id, task_id=task_id)
        logger.info(
            "Celery task completed",
            extra={
                "incident_id": incident_id,
                "task_id": task_id,
                "success": bool(result.get("success")),
                "execution_duration_ms": int((perf_counter() - started_at) * 1000),
            },
        )
        return result
    finally:
        db.close()
