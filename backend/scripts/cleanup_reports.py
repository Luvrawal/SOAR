import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPORT_SUFFIXES = {".json", ".pdf"}
INCIDENT_PREFIX = "INC-"
logger = logging.getLogger(__name__)


@dataclass
class ReportCandidate:
    path: Path
    incident_id: str
    modified_at: datetime


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_incident_id(file_path: Path) -> str | None:
    stem = file_path.stem
    if not stem.startswith(INCIDENT_PREFIX):
        return None
    return stem


def _collect_candidates(reports_dir: Path, cutoff: datetime) -> list[ReportCandidate]:
    candidates: list[ReportCandidate] = []

    if not reports_dir.exists() or not reports_dir.is_dir():
        return candidates

    for entry in reports_dir.iterdir():
        if not entry.is_file() or entry.suffix.lower() not in REPORT_SUFFIXES:
            continue

        incident_id = _parse_incident_id(entry)
        if not incident_id:
            continue

        modified_at = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
        if modified_at <= cutoff:
            candidates.append(
                ReportCandidate(
                    path=entry,
                    incident_id=incident_id,
                    modified_at=modified_at,
                )
            )

    return sorted(candidates, key=lambda item: (item.incident_id, item.path.name))


def _emit_audit_payload(payload: dict, audit_target: str | None) -> None:
    if not audit_target:
        return

    if audit_target == "-":
        print(json.dumps(payload))
        return

    target = Path(audit_target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_cleanup(reports_dir: Path, retention_days: int, apply: bool, now: datetime | None = None) -> dict:
    reference_time = now or _utc_now()
    cutoff = reference_time - timedelta(days=retention_days)
    candidates = _collect_candidates(reports_dir=reports_dir, cutoff=cutoff)

    incidents: dict[str, list[str]] = {}
    for candidate in candidates:
        incidents.setdefault(candidate.incident_id, []).append(candidate.path.name)

    deleted_files: list[str] = []
    delete_errors: list[dict[str, str]] = []

    if apply:
        for candidate in candidates:
            try:
                candidate.path.unlink()
                deleted_files.append(str(candidate.path))
            except OSError as exc:
                delete_errors.append({"file": str(candidate.path), "error": str(exc)})

    payload = {
        "reports_dir": str(reports_dir),
        "retention_days": retention_days,
        "mode": "apply" if apply else "dry-run",
        "run_at": reference_time.isoformat(),
        "cutoff_at": cutoff.isoformat(),
        "expired_count": len(candidates),
        "incident_ids": sorted(incidents.keys()),
        "expired_by_incident": {incident_id: sorted(files) for incident_id, files in sorted(incidents.items())},
        "deleted_count": len(deleted_files),
        "deleted_files": deleted_files,
        "delete_errors": delete_errors,
        "success": len(delete_errors) == 0,
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cleanup expired SOAR incident report artifacts")
    parser.add_argument("--reports-dir", default="./reports", help="Directory containing INC-*.json/pdf reports")
    parser.add_argument("--retention-days", type=int, default=30, help="Retention window in days")
    parser.add_argument("--dry-run", action="store_true", help="List expired files without deleting")
    parser.add_argument("--apply", action="store_true", help="Delete expired files")
    parser.add_argument(
        "--json-audit-log",
        default=None,
        help="Write audit JSON to file path or '-' for stdout",
    )

    args = parser.parse_args(argv)

    if args.retention_days < 0:
        print("retention-days must be >= 0")
        return 2

    if args.dry_run and args.apply:
        print("Choose either --dry-run or --apply, not both")
        return 2

    apply = bool(args.apply)
    reports_dir = Path(args.reports_dir)
    payload = run_cleanup(
        reports_dir=reports_dir,
        retention_days=args.retention_days,
        apply=apply,
    )

    logger.info(
        "artifact_filesystem_cleanup_completed",
        extra={
            "mode": payload["mode"],
            "retention_days": payload["retention_days"],
            "expired_count": payload["expired_count"],
            "deleted_count": payload["deleted_count"],
            "success": payload["success"],
        },
    )

    print(json.dumps(payload))
    _emit_audit_payload(payload=payload, audit_target=args.json_audit_log)

    if not payload["success"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
