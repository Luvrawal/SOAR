"""Background tasks package."""

from app.tasks.celery_app import celery_app
from app.tasks.incident_tasks import process_incident

__all__ = ["celery_app", "process_incident"]
