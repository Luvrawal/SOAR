from datetime import datetime, timezone
import logging
from time import perf_counter
import traceback

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.playbook_execution import PlaybookExecution
from app.soar.main import run_playbook as run_soar_playbook

logger = logging.getLogger(__name__)


PHASE7_EXECUTION_STEPS = [
    {"id": "receive_alert", "name": "Receive alert"},
    {"id": "enrich", "name": "Enrich indicators"},
    {"id": "risk_score", "name": "Calculate risk"},
    {"id": "respond", "name": "Execute response"},
    {"id": "report", "name": "Generate report"},
]


def _step_states(status: str, started_at: datetime | None = None, finished_at: datetime | None = None, error: str | None = None) -> list[dict[str, str | None]]:
    normalized = status.lower()
    start_iso = started_at.isoformat() if started_at else None
    finish_iso = finished_at.isoformat() if finished_at else None
    steps: list[dict[str, str | None]] = []

    for index, template in enumerate(PHASE7_EXECUTION_STEPS):
        if normalized == "running":
            step_status = "completed" if index == 0 else ("running" if index == 1 else "pending")
            timestamp = start_iso if index <= 1 else None
        elif normalized == "success":
            step_status = "completed"
            timestamp = finish_iso if index == len(PHASE7_EXECUTION_STEPS) - 1 else start_iso
        elif normalized == "failed":
            step_status = "failed" if index == len(PHASE7_EXECUTION_STEPS) - 1 else "completed"
            timestamp = finish_iso if step_status == "failed" else start_iso
        else:
            step_status = "pending"
            timestamp = None

        steps.append(
            {
                "id": template["id"],
                "name": template["name"],
                "status": step_status,
                "timestamp": timestamp,
                "detail": error if step_status == "failed" else None,
            }
        )

    return steps


def _build_playbook_alert(incident: Incident) -> dict[str, str | dict | None]:
    raw_alert = incident.raw_alert or {}

    if isinstance(raw_alert, dict) and raw_alert.get("alert_type") and raw_alert.get("details"):
        return {
            "alert_type": str(raw_alert.get("alert_type")),
            "severity": str(raw_alert.get("severity") or incident.severity).upper(),
            "timestamp": str(raw_alert.get("timestamp") or incident.created_at.isoformat()),
            "source": str(raw_alert.get("source") or incident.source),
            "details": raw_alert.get("details") if isinstance(raw_alert.get("details"), dict) else {},
        }

    details = raw_alert if isinstance(raw_alert, dict) else {}
    return {
        "alert_type": str(raw_alert.get("alert_type") if isinstance(raw_alert, dict) else incident.source).upper(),
        "severity": str(incident.severity).upper(),
        "timestamp": incident.created_at.isoformat(),
        "source": incident.source,
        "details": details,
    }


def run_playbook(incident: Incident) -> dict[str, str | int | bool | dict]:
    started_at = perf_counter()
    alert_payload = _build_playbook_alert(incident)
    report = run_soar_playbook(alert_payload)

    if not report:
        return {
            "incident_id": incident.id,
            "success": False,
            "error": "unsupported_alert_type",
            "alert_type": alert_payload.get("alert_type", "unknown"),
            "execution_duration_ms": int((perf_counter() - started_at) * 1000),
        }

    threat_intel = report.get("threat_intel", {}) if isinstance(report, dict) else {}
    provider_errors = {
        provider: str(data.get("error"))
        for provider, data in threat_intel.items()
        if isinstance(data, dict) and data.get("error")
    }

    return {
        "incident_id": incident.id,
        "success": True,
        "playbook": str(report.get("playbook_name", "unknown")),
        "severity": str(report.get("severity", "unknown")),
        "risk_score": int(report.get("risk_score", 0)),
        "execution_duration_ms": int((perf_counter() - started_at) * 1000),
        "degraded_threat_intel": bool(provider_errors),
        "provider_errors": provider_errors,
        "report": report,
    }


def execute_playbook_for_incident(
    db: Session, incident_id: int, task_id: str | None = None
) -> dict[str, str | int | bool]:
    started_at = perf_counter()
    incident = db.get(Incident, incident_id)
    if incident is None:
        logger.warning("Incident not found for playbook execution", extra={"incident_id": incident_id, "task_id": task_id})
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
        result={"execution_steps": _step_states(status="running", started_at=datetime.now(timezone.utc))},
    )
    db.add(execution)

    incident.playbook_status = "running"
    db.commit()
    db.refresh(execution)

    try:
        logger.info(
            "Starting playbook execution",
            extra={"incident_id": incident_id, "task_id": task_id, "source": incident.source},
        )
        result = run_playbook(incident=incident)
        finished_at = datetime.now(timezone.utc)
        result["execution_steps"] = _step_states(status="success", started_at=execution.started_at, finished_at=finished_at)

        incident.playbook_result = result
        incident.playbook_status = "success" if bool(result.get("success")) else "failed"
        incident.playbook_last_run_at = finished_at

        if isinstance(result.get("report"), dict):
            report = result["report"]
            incident.status = str(report.get("status", incident.status)).lower()
            incident.severity = str(report.get("severity", incident.severity)).lower()

        execution.result = result
        execution.playbook_name = str(result.get("playbook", execution.playbook_name))
        execution.status = incident.playbook_status
        execution.finished_at = finished_at
        duration_ms = int((perf_counter() - started_at) * 1000)
        execution.logs = (execution.logs or "") + f"\nExecution completed in {duration_ms} ms"

        db.commit()
        db.refresh(incident)

        logger.info(
            "Playbook execution finished",
            extra={
                "incident_id": incident_id,
                "task_id": task_id,
                "playbook_status": incident.playbook_status,
                "incident_status": incident.status,
                "execution_duration_ms": duration_ms,
            },
        )

        return result
    except Exception as exc:
        finished_at = datetime.now(timezone.utc)
        incident.playbook_status = "failed"
        incident.status = "failed"
        incident.playbook_last_run_at = finished_at

        execution.status = "failed"
        execution.error_message = str(exc)
        execution.finished_at = finished_at
        duration_ms = int((perf_counter() - started_at) * 1000)
        execution.logs = (execution.logs or "") + f"\nExecution failed in {duration_ms} ms"
        execution.result = {
            "incident_id": incident_id,
            "success": False,
            "error": str(exc),
            "execution_duration_ms": duration_ms,
            "execution_steps": _step_states(
                status="failed",
                started_at=execution.started_at,
                finished_at=finished_at,
                error=str(exc),
            ),
        }

        db.commit()

        logger.exception(
            "Playbook execution failed",
            extra={"incident_id": incident_id, "task_id": task_id, "execution_duration_ms": duration_ms},
        )

        return {
            "incident_id": incident_id,
            "success": False,
            "error": str(exc),
            "execution_duration_ms": duration_ms,
            "trace": traceback.format_exc(limit=5),
        }
