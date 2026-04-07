from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.playbook_execution import PlaybookExecution
from app.schemas.common import ApiResponse
from fastapi import Depends

router = APIRouter(prefix="/playbooks")

PLAYBOOKS = [
    {
        "id": "brute-force-detection",
        "name": "Brute Force Detection Playbook",
        "type": "brute-force",
        "mitre_technique": "T1110 - Brute Force",
        "steps": ["Receive alert", "Enrich source IP", "Calculate risk", "Respond", "Generate report"],
    },
    {
        "id": "phishing-detection",
        "name": "Phishing Detection Playbook",
        "type": "phishing",
        "mitre_technique": "T1566 - Phishing",
        "steps": ["Receive alert", "Enrich URL", "Calculate risk", "Respond", "Generate report"],
    },
    {
        "id": "malware-detection",
        "name": "Malware Detection Playbook",
        "type": "malware",
        "mitre_technique": "T1204/T1027 - Malware Execution/Obfuscation",
        "steps": ["Receive alert", "Enrich hash", "Calculate risk", "Respond", "Generate report"],
    },
    {
        "id": "network-anomaly-detection",
        "name": "Network Anomaly Detection Playbook",
        "type": "network-anomaly",
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

    return {
        "total_runs": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": round((success_count / total) * 100, 2) if total else 0.0,
        "avg_execution_ms": round(sum(durations) / len(durations), 2) if durations else None,
        "last_run": last_run,
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
            "mitre_technique": playbook["mitre_technique"],
            "steps": playbook["steps"],
            **stats,
        },
    )
