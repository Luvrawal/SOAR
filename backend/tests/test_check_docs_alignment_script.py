from __future__ import annotations

import json
from pathlib import Path

from scripts import check_docs_alignment


def test_check_alignment_passes_with_required_commands(tmp_path: Path):
    runbook = tmp_path / "RUNBOOK.md"
    matrix = tmp_path / "GO_LIVE_COMMAND_MATRIX.md"

    content = "\n".join(check_docs_alignment.REQUIRED_COMMAND_SNIPPETS)
    runbook.write_text(content, encoding="utf-8")
    matrix.write_text(content, encoding="utf-8")

    payload = check_docs_alignment.check_alignment(runbook, matrix)

    assert payload["aligned"] is True
    assert payload["missing_in_runbook"] == []
    assert payload["missing_in_matrix"] == []


def test_check_alignment_reports_missing_entries(tmp_path: Path):
    runbook = tmp_path / "RUNBOOK.md"
    matrix = tmp_path / "GO_LIVE_COMMAND_MATRIX.md"

    runbook.write_text("python scripts/smoke_check_api.py", encoding="utf-8")
    matrix.write_text("python scripts/production_preflight.py", encoding="utf-8")

    payload = check_docs_alignment.check_alignment(runbook, matrix)

    assert payload["aligned"] is False
    assert "python scripts/production_preflight.py" in payload["missing_in_runbook"]
    assert "python scripts/smoke_check_api.py" in payload["missing_in_matrix"]


def test_main_returns_error_on_missing_file(capsys):
    exit_code = check_docs_alignment.main(["--runbook-path", "missing.md", "--matrix-path", "missing2.md"])
    captured = capsys.readouterr()

    assert exit_code == 2
    parsed = json.loads(captured.out)
    assert "Missing documentation file" in parsed["error"]
