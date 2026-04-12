import argparse
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.models.incident import Incident
from app.models.playbook_execution import PlaybookExecution

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _build_incident_pruned_payload(incident: Incident, pruned_at: datetime) -> dict:
    return {
        "retention_pruned": True,
        "pruned_at": pruned_at.isoformat(),
        "previous_playbook_status": incident.playbook_status,
        "incident_status": incident.status,
        "playbook_last_run_at": _as_utc(incident.playbook_last_run_at).isoformat()
        if incident.playbook_last_run_at
        else None,
    }


def _build_execution_pruned_payload(execution: PlaybookExecution, pruned_at: datetime) -> dict:
    return {
        "retention_pruned": True,
        "pruned_at": pruned_at.isoformat(),
        "status": execution.status,
        "finished_at": _as_utc(execution.finished_at).isoformat() if execution.finished_at else None,
    }


def run_db_payload_cleanup(
    retention_days: int,
    apply: bool,
    statuses: list[str] | None = None,
    now: datetime | None = None,
) -> dict:
    normalized_statuses = [status.strip().lower() for status in (statuses or ["closed", "failed"]) if status.strip()]
    reference_time = now or _utc_now()
    cutoff = reference_time - timedelta(days=retention_days)

    db = SessionLocal()
    try:
        incident_candidates = (
            db.query(Incident)
            .filter(Incident.playbook_result.isnot(None))
            .filter(Incident.playbook_last_run_at.isnot(None))
            .all()
        )
        incident_candidates = [
            incident
            for incident in incident_candidates
            if incident.status.lower() in normalized_statuses
            and (_as_utc(incident.playbook_last_run_at) or reference_time) <= cutoff
        ]

        execution_candidates = (
            db.query(PlaybookExecution)
            .filter(PlaybookExecution.result.isnot(None))
            .filter(PlaybookExecution.finished_at.isnot(None))
            .all()
        )
        execution_candidates = [
            execution
            for execution in execution_candidates
            if execution.status.lower() in normalized_statuses
            and (_as_utc(execution.finished_at) or reference_time) <= cutoff
        ]

        pruned_at = _utc_now()
        pruned_incident_ids: list[int] = []
        pruned_execution_ids: list[int] = []

        if apply:
            for incident in incident_candidates:
                incident.playbook_result = _build_incident_pruned_payload(incident, pruned_at)
                pruned_incident_ids.append(incident.id)

            for execution in execution_candidates:
                execution.result = _build_execution_pruned_payload(execution, pruned_at)
                pruned_execution_ids.append(execution.id)

            db.commit()

        payload = {
            "mode": "apply" if apply else "dry-run",
            "retention_days": retention_days,
            "status_filter": normalized_statuses,
            "run_at": reference_time.isoformat(),
            "cutoff_at": cutoff.isoformat(),
            "incident_candidates": [incident.id for incident in incident_candidates],
            "execution_candidates": [execution.id for execution in execution_candidates],
            "incident_pruned_count": len(pruned_incident_ids),
            "execution_pruned_count": len(pruned_execution_ids),
            "incident_pruned_ids": pruned_incident_ids,
            "execution_pruned_ids": pruned_execution_ids,
            "success": True,
        }
        return payload
    finally:
        db.close()


def _emit_audit_payload(payload: dict, audit_target: str | None) -> None:
    if not audit_target:
        return
    if audit_target == "-":
        print(json.dumps(payload))
        return

    target_path = Path(audit_target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cleanup aged incident/playbook DB payloads")
    parser.add_argument("--retention-days", type=int, default=30, help="Retention window in days")
    parser.add_argument("--statuses", default="closed,failed", help="Comma-separated status filter")
    parser.add_argument("--dry-run", action="store_true", help="Analyze candidates without mutating records")
    parser.add_argument("--apply", action="store_true", help="Apply payload pruning")
    parser.add_argument(
        "--json-audit-log",
        default=None,
        help="Write JSON audit to file path or '-' for stdout",
    )

    args = parser.parse_args(argv)

    if args.retention_days < 0:
        print("retention-days must be >= 0")
        return 2

    if args.dry_run and args.apply:
        print("Choose either --dry-run or --apply, not both")
        return 2

    statuses = [status.strip() for status in args.statuses.split(",") if status.strip()]
    apply = bool(args.apply)

    payload = run_db_payload_cleanup(
        retention_days=args.retention_days,
        apply=apply,
        statuses=statuses,
    )

    logger.info(
        "artifact_db_cleanup_completed",
        extra={
            "mode": payload["mode"],
            "retention_days": payload["retention_days"],
            "status_filter": payload["status_filter"],
            "incident_pruned_count": payload["incident_pruned_count"],
            "execution_pruned_count": payload["execution_pruned_count"],
        },
    )

    print(json.dumps(payload))
    _emit_audit_payload(payload, args.json_audit_log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
