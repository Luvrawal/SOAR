from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts import cleanup_reports


def _write_report(path: Path, age_days: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    modified_at = datetime.now(timezone.utc) - timedelta(days=age_days)
    ts = modified_at.timestamp()
    os.utime(path, (ts, ts))


def test_run_cleanup_dry_run_does_not_delete(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    old_json = reports_dir / "INC-OLD-1.json"
    old_pdf = reports_dir / "INC-OLD-1.pdf"
    fresh_json = reports_dir / "INC-NEW-1.json"

    _write_report(old_json, age_days=40)
    _write_report(old_pdf, age_days=40)
    _write_report(fresh_json, age_days=2)

    payload = cleanup_reports.run_cleanup(reports_dir, retention_days=30, apply=False)

    assert payload["mode"] == "dry-run"
    assert payload["expired_count"] == 2
    assert payload["deleted_count"] == 0
    assert payload["incident_ids"] == ["INC-OLD-1"]
    assert old_json.exists()
    assert old_pdf.exists()
    assert fresh_json.exists()


def test_run_cleanup_apply_deletes_only_expired(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    old_json = reports_dir / "INC-OLD-2.json"
    old_pdf = reports_dir / "INC-OLD-2.pdf"
    fresh_pdf = reports_dir / "INC-NEW-2.pdf"

    _write_report(old_json, age_days=31)
    _write_report(old_pdf, age_days=31)
    _write_report(fresh_pdf, age_days=1)

    payload = cleanup_reports.run_cleanup(reports_dir, retention_days=30, apply=True)

    assert payload["mode"] == "apply"
    assert payload["expired_count"] == 2
    assert payload["deleted_count"] == 2
    assert payload["delete_errors"] == []
    assert not old_json.exists()
    assert not old_pdf.exists()
    assert fresh_pdf.exists()


def test_main_writes_audit_file(tmp_path: Path, capsys):
    reports_dir = tmp_path / "reports"
    old_json = reports_dir / "INC-OLD-3.json"
    _write_report(old_json, age_days=35)

    audit_path = tmp_path / "logs" / "cleanup_audit.json"
    exit_code = cleanup_reports.main(
        [
            "--reports-dir",
            str(reports_dir),
            "--retention-days",
            "30",
            "--dry-run",
            "--json-audit-log",
            str(audit_path),
        ]
    )

    captured = capsys.readouterr()
    stdout_payload = json.loads(captured.out.strip())
    audit_payload = json.loads(audit_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert stdout_payload["expired_count"] == 1
    assert audit_payload["expired_count"] == 1
    assert audit_payload["mode"] == "dry-run"


def test_main_rejects_conflicting_modes(capsys):
    exit_code = cleanup_reports.main(["--dry-run", "--apply"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Choose either --dry-run or --apply" in captured.out
