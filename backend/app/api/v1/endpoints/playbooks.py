from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_db
from app.models.playbook_execution import PlaybookExecution
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/playbooks", dependencies=[Depends(require_roles("admin"))])

PLAYBOOKS = [
    {
        "id": "brute-force-detection",
        "name": "Brute Force Detection Playbook",
        "type": "brute-force",
        "version": "1.2.0",
        "is_active": True,
        "owner": "SOC Engineering",
        "mitre_technique": "T1110 - Brute Force",
        "steps": ["Receive alert", "Enrich source IP", "Calculate risk", "Respond", "Generate report"],
    },
    {
        "id": "phishing-detection",
        "name": "Phishing Detection Playbook",
        "type": "phishing",
        "version": "1.2.0",
        "is_active": True,
        "owner": "SOC Engineering",
        "mitre_technique": "T1566 - Phishing",
        "steps": ["Receive alert", "Enrich URL", "Calculate risk", "Respond", "Generate report"],
    },
    {
        "id": "malware-detection",
        "name": "Malware Detection Playbook",
        "type": "malware",
        "version": "1.2.0",
        "is_active": True,
        "owner": "SOC Engineering",
        "mitre_technique": "T1204/T1027 - Malware Execution/Obfuscation",
        "steps": ["Receive alert", "Enrich hash", "Calculate risk", "Respond", "Generate report"],
    },
    {
        "id": "network-anomaly-detection",
        "name": "Network Anomaly Detection Playbook",
        "type": "network-anomaly",
        "version": "1.2.0",
        "is_active": True,
        "owner": "SOC Engineering",
        "mitre_technique": "T1071/T1030 - C2 Communication/Data Exfiltration",
        "steps": ["Receive alert", "Enrich source IP", "Calculate risk", "Respond", "Generate report"],
    },
]


def _aggregate_stats(db: Session, playbook_name: str) -> dict:
    executions = db.query(PlaybookExecution).filter(PlaybookExecution.playbook_name == playbook_name).all()
    total = len(executions)
    success_count = sum(1 for execution in executions if execution.status == "success")
    failed_count = sum(1 for execution in executions if execution.status == "failed")

    durations = []
    for execution in executions:
        result = execution.result if isinstance(execution.result, dict) else {}
        duration = result.get("execution_duration_ms")
        if isinstance(duration, int):
            durations.append(duration)

    last_run = max((execution.finished_at or execution.started_at for execution in executions), default=None)
    latest_execution = max(
        executions,
        key=lambda execution: execution.finished_at or execution.started_at,
        default=None,
    )
    latest_steps = []
    if latest_execution and isinstance(latest_execution.result, dict):
        raw_steps = latest_execution.result.get("execution_steps")
        if isinstance(raw_steps, list):
            latest_steps = raw_steps

    return {
        "total_runs": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": round((success_count / total) * 100, 2) if total else 0.0,
        "avg_execution_ms": round(sum(durations) / len(durations), 2) if durations else None,
        "last_run": last_run,
        "latest_execution_steps": latest_steps,
    }


def _serialize_execution(execution: PlaybookExecution) -> dict:
    result = execution.result if isinstance(execution.result, dict) else {}
    steps = result.get("execution_steps") if isinstance(result.get("execution_steps"), list) else []

    return {
        "id": execution.id,
        "task_id": execution.task_id,
        "playbook_name": execution.playbook_name,
        "status": execution.status,
        "started_at": execution.started_at,
        "finished_at": execution.finished_at,
        "error_message": execution.error_message,
        "execution_duration_ms": result.get("execution_duration_ms"),
        "execution_steps": steps,
    }


@router.get("", response_model=ApiResponse)
def list_playbooks(db: Session = Depends(get_db)) -> ApiResponse:
    items = []
    for playbook in PLAYBOOKS:
        stats = _aggregate_stats(db, playbook["name"])
        items.append({**playbook, **stats})

    return ApiResponse(
        message="Playbooks fetched successfully",
        data={
            "total": len(items),
            "items": items,
        },
    )


@router.get("/{playbook_id}/stats", response_model=ApiResponse)
def get_playbook_stats(playbook_id: str, db: Session = Depends(get_db)) -> ApiResponse:
    playbook = next((item for item in PLAYBOOKS if item["id"] == playbook_id), None)
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")

    stats = _aggregate_stats(db, playbook["name"])

    return ApiResponse(
        message="Playbook stats fetched successfully",
        data={
            "id": playbook["id"],
            "name": playbook["name"],
            "type": playbook["type"],
            "version": playbook["version"],
            "is_active": playbook["is_active"],
            "owner": playbook["owner"],
            "mitre_technique": playbook["mitre_technique"],
            "steps": playbook["steps"],
            **stats,
        },
    )


@router.get("/{playbook_id}/executions", response_model=ApiResponse)
def get_playbook_executions(
    playbook_id: str,
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    since_hours: int | None = Query(default=None, ge=1, le=24 * 30),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    playbook = next((item for item in PLAYBOOKS if item["id"] == playbook_id), None)
    if playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")

    query = db.query(PlaybookExecution).filter(PlaybookExecution.playbook_name == playbook["name"])

    if status:
        query = query.filter(PlaybookExecution.status == status.lower())

    if since_hours is not None:
        since_ts = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        query = query.filter(PlaybookExecution.started_at >= since_ts)

    total = query.count()
    executions = (
        query.order_by(PlaybookExecution.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    serialized = [_serialize_execution(execution) for execution in executions]
    latest_success = next((item for item in serialized if item["status"] == "success"), None)
    latest_failed = next((item for item in serialized if item["status"] == "failed"), None)

    return ApiResponse(
        message="Playbook executions fetched successfully",
        data={
            "playbook_id": playbook_id,
            "page": page,
            "page_size": page_size,
            "total": len(serialized),
            "total_all": total,
            "filters": {
                "status": status,
                "since_hours": since_hours,
                "page": page,
                "page_size": page_size,
            },
            "items": serialized,
            "latest_success": latest_success,
            "latest_failed": latest_failed,
        },
    )
