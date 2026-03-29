import logging

from app.db.session import SessionLocal
from app.services.playbook_service import execute_playbook_for_incident
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.incident_tasks.process_incident")
def process_incident(incident_id: int) -> dict[str, int | str | bool]:
    logger.info("Processing incident asynchronously", extra={"incident_id": incident_id})
    db = SessionLocal()
    try:
        task_id = process_incident.request.id
        result = execute_playbook_for_incident(db=db, incident_id=incident_id, task_id=task_id)
        return result
    finally:
        db.close()
