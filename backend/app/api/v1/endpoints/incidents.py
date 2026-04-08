from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_db
from app.models.incident import Incident
from app.models.playbook_execution import PlaybookExecution
from app.schemas.alert import IncidentResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/incidents", dependencies=[Depends(require_roles("admin", "analyst"))])


def _risk_label(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _risk_confidence(score: int, degraded: bool) -> str:
    if score >= 80 and not degraded:
        return "strong"
    if score >= 45:
        return "moderate"
    return "weak"


def _timeline(incident: Incident, latest_execution: PlaybookExecution | None) -> list[dict]:
    created_at = incident.created_at
    queued_at = incident.created_at
    running_at = latest_execution.started_at if latest_execution else None
    completed_at = latest_execution.finished_at if latest_execution else incident.playbook_last_run_at

    return [
        {
            "step": "created",
            "status": "completed",
            "timestamp": created_at,
        },
        {
            "step": "queued",
            "status": "completed",
            "timestamp": queued_at,
        },
        {
            "step": "running",
            "status": "completed" if running_at else "pending",
            "timestamp": running_at,
        },
        {
            "step": "completed",
            "status": "completed" if completed_at else "pending",
            "timestamp": completed_at,
        },
    ]


@router.get("", response_model=ApiResponse)
def list_incidents(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    playbook_status: str | None = Query(default=None),
    source: str | None = Query(default=None),
    incident_type: str | None = Query(default=None, alias="type"),
    q: str | None = Query(default=None),
) -> ApiResponse:
    query = db.query(Incident)

    if severity:
        query = query.filter(func.lower(Incident.severity) == severity.lower())
    if status:
        query = query.filter(func.lower(Incident.status) == status.lower())
    if playbook_status:
        query = query.filter(func.lower(Incident.playbook_status) == playbook_status.lower())
    if source:
        query = query.filter(func.lower(Incident.source) == source.lower())
    if incident_type:
        lowered = f"%{incident_type.lower()}%"
        query = query.filter(func.lower(Incident.title).like(lowered))
    if q:
        lowered = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(Incident.title).like(lowered),
                func.lower(func.coalesce(Incident.description, "")).like(lowered),
                func.lower(Incident.source).like(lowered),
            )
        )

    total = query.count()
    incidents = (
        query.order_by(Incident.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    serialized = [IncidentResponse.model_validate(incident).model_dump(mode="json") for incident in incidents]

    return ApiResponse(
        message="Incidents fetched successfully",
        data={
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": serialized,
        },
    )


@router.get("/{incident_id}", response_model=ApiResponse)
def get_incident_detail(incident_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    executions = (
        db.query(PlaybookExecution)
        .filter(PlaybookExecution.incident_id == incident_id)
        .order_by(PlaybookExecution.created_at.desc())
        .all()
    )
    latest_execution = executions[0] if executions else None

    playbook_result = incident.playbook_result if isinstance(incident.playbook_result, dict) else {}
    report = playbook_result.get("report") if isinstance(playbook_result.get("report"), dict) else {}
    threat_intel = report.get("threat_intel") if isinstance(report.get("threat_intel"), dict) else {}
    response_taken = report.get("response_taken") if isinstance(report.get("response_taken"), list) else []

    duration_ms = playbook_result.get("execution_duration_ms") if isinstance(playbook_result, dict) else None
    if duration_ms is None and latest_execution and latest_execution.started_at and latest_execution.finished_at:
        duration_ms = int((latest_execution.finished_at - latest_execution.started_at).total_seconds() * 1000)

    risk_score = int(playbook_result.get("risk_score", 0)) if isinstance(playbook_result, dict) else 0
    execution_steps = []
    if isinstance(playbook_result, dict) and isinstance(playbook_result.get("execution_steps"), list):
        execution_steps = playbook_result["execution_steps"]

    execution_logs: list[dict] = []
    if latest_execution and latest_execution.logs:
        for index, line in enumerate(latest_execution.logs.splitlines(), start=1):
            if not line.strip():
                continue
            execution_logs.append(
                {
                    "step": f"step_{index}",
                    "message": line,
                    "timestamp": latest_execution.finished_at or latest_execution.started_at or incident.updated_at,
                }
            )

    serialized_executions = [
        {
            "id": execution.id,
            "task_id": execution.task_id,
            "playbook_name": execution.playbook_name,
            "status": execution.status,
            "logs": execution.logs,
            "error_message": execution.error_message,
            "result": execution.result,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
            "created_at": execution.created_at,
        }
        for execution in executions
    ]

    return ApiResponse(
        message="Incident detail fetched successfully",
        data={
            "incident": IncidentResponse.model_validate(incident).model_dump(mode="json"),
            "timeline": _timeline(incident, latest_execution),
            "playbook_execution": {
                "current_status": incident.playbook_status,
                "execution_duration_ms": duration_ms,
                "steps": execution_steps,
                "logs": execution_logs,
                "history": serialized_executions,
            },
            "threat_intelligence": {
                "results": threat_intel,
                "degraded": bool(playbook_result.get("degraded_threat_intel")) if isinstance(playbook_result, dict) else False,
                "provider_errors": playbook_result.get("provider_errors", {}) if isinstance(playbook_result, dict) else {},
            },
            "risk_scoring": {
                "score": risk_score,
                "label": _risk_label(risk_score),
                "confidence": _risk_confidence(
                    risk_score,
                    bool(playbook_result.get("degraded_threat_intel")) if isinstance(playbook_result, dict) else False,
                ),
            },
            "automated_actions": response_taken,
        },
    )


@router.get("/{incident_id}/executions", response_model=ApiResponse)
def get_incident_executions(incident_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    executions = (
        db.query(PlaybookExecution)
        .filter(PlaybookExecution.incident_id == incident_id)
        .order_by(PlaybookExecution.created_at.desc())
        .all()
    )

    items = [
        {
            "id": execution.id,
            "task_id": execution.task_id,
            "playbook_name": execution.playbook_name,
            "status": execution.status,
            "logs": execution.logs,
            "error_message": execution.error_message,
            "result": execution.result,
            "started_at": execution.started_at,
            "finished_at": execution.finished_at,
            "created_at": execution.created_at,
        }
        for execution in executions
    ]

    return ApiResponse(
        message="Incident executions fetched successfully",
        data={
            "incident_id": incident_id,
            "total": len(items),
            "items": items,
        },
    )
