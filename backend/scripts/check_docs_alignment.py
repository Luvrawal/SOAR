import argparse
import json
import sys
from pathlib import Path

REQUIRED_COMMAND_SNIPPETS = [
    "python scripts/smoke_check_api.py",
    "python scripts/production_preflight.py",
    "python scripts/cleanup_reports.py",
    "python scripts/cleanup_db_payloads.py",
    "python -m pytest -q",
]


def _read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Missing documentation file: {path}")
    return path.read_text(encoding="utf-8")


def check_alignment(runbook_path: Path, matrix_path: Path) -> dict:
    runbook_text = _read_text(runbook_path)
    matrix_text = _read_text(matrix_path)

    missing_in_runbook: list[str] = []
    missing_in_matrix: list[str] = []

    for snippet in REQUIRED_COMMAND_SNIPPETS:
        if snippet not in runbook_text:
            missing_in_runbook.append(snippet)
        if snippet not in matrix_text:
            missing_in_matrix.append(snippet)

    payload = {
        "runbook_path": str(runbook_path),
        "matrix_path": str(matrix_path),
        "required_snippets": REQUIRED_COMMAND_SNIPPETS,
        "missing_in_runbook": missing_in_runbook,
        "missing_in_matrix": missing_in_matrix,
        "aligned": not missing_in_runbook and not missing_in_matrix,
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check backend docs alignment for critical command snippets")
    parser.add_argument(
        "--runbook-path",
        default="RUNBOOK.md",
        help="Path to backend runbook",
    )
    parser.add_argument(
        "--matrix-path",
        default="GO_LIVE_COMMAND_MATRIX.md",
        help="Path to backend go-live command matrix",
    )

    args = parser.parse_args(argv)

    try:
        payload = check_alignment(Path(args.runbook_path), Path(args.matrix_path))
    except FileNotFoundError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2

    print(json.dumps(payload))
    return 0 if payload["aligned"] else 1


if __name__ == "__main__":
    sys.exit(main())
