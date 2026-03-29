from datetime import datetime, timezone
import traceback

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.playbook_execution import PlaybookExecution


def run_playbook(incident_id: int) -> dict[str, str | int | bool]:
    # Placeholder integration point for teammate-owned playbook engine.
    return {
        "incident_id": incident_id,
        "playbook": "default_triage",
        "action_taken": "enrichment_completed",
        "success": True,
    }


def execute_playbook_for_incident(
    db: Session, incident_id: int, task_id: str | None = None
) -> dict[str, str | int | bool]:
    incident = db.get(Incident, incident_id)
    if incident is None:
        return {
            "incident_id": incident_id,
            "success": False,
            "message": "incident_not_found",
        }

    execution = PlaybookExecution(
        incident_id=incident_id,
        task_id=task_id,
        playbook_name="default_triage",
        status="running",
        logs="Execution started",
    )
    db.add(execution)

    incident.playbook_status = "running"
    db.commit()
    db.refresh(execution)

    try:
        result = run_playbook(incident_id=incident_id)

        incident.playbook_result = result
        incident.playbook_status = "success" if bool(result.get("success")) else "failed"
        incident.playbook_last_run_at = datetime.now(timezone.utc)

        execution.result = result
        execution.status = incident.playbook_status
        execution.finished_at = datetime.now(timezone.utc)
        execution.logs = (execution.logs or "") + "\nExecution completed"

        db.commit()
        db.refresh(incident)

        return result
    except Exception as exc:
        incident.playbook_status = "failed"
        incident.playbook_last_run_at = datetime.now(timezone.utc)

        execution.status = "failed"
        execution.error_message = str(exc)
        execution.finished_at = datetime.now(timezone.utc)
        execution.logs = (execution.logs or "") + "\nExecution failed"
        execution.result = {
            "incident_id": incident_id,
            "success": False,
            "error": str(exc),
        }

        db.commit()

        return {
            "incident_id": incident_id,
            "success": False,
            "error": str(exc),
            "trace": traceback.format_exc(limit=5),
        }
