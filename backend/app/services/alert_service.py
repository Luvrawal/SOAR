import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.incident import Incident
from app.schemas.alert import AlertCreate
from app.tasks.incident_tasks import process_incident

logger = logging.getLogger(__name__)


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
    try:
        process_incident.delay(incident.id)
    except Exception:
        logger.exception("Failed to enqueue incident processing task", extra={"incident_id": incident.id})

    return incident
