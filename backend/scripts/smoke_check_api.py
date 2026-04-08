import argparse
import json
import sys
from dataclasses import dataclass

import requests


@dataclass
class Check:
    name: str
    method: str
    path: str
    expected_status: int
    payload: dict | None = None


def run_check(base_url: str, check: Check, timeout: int) -> tuple[bool, str]:
    url = f"{base_url.rstrip('/')}{check.path}"

    try:
        if check.method == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=check.payload or {}, timeout=timeout)
    except requests.RequestException as exc:
        return False, f"{check.name}: request error: {exc}"

    if response.status_code != check.expected_status:
        body = response.text[:300].replace("\n", " ")
        return (
            False,
            f"{check.name}: expected {check.expected_status}, got {response.status_code} at {check.path}. body={body}",
        )

    return True, f"{check.name}: ok ({response.status_code})"


def main() -> int:
    parser = argparse.ArgumentParser(description="SOAR backend API smoke checks")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--timeout", type=int, default=8, help="Request timeout in seconds")
    args = parser.parse_args()

    checks = [
        Check("Docs", "GET", "/docs", 200),
        Check("Health", "GET", "/api/v1/health", 200),
        Check("Incidents", "GET", "/api/v1/incidents?page=1&page_size=1", 200),
        Check("Playbooks", "GET", "/api/v1/playbooks", 200),
        Check(
            "Threat Intel Query",
            "POST",
            "/api/v1/threat-intel/query",
            200,
            payload={"indicator": "8.8.8.8", "indicator_type": "ip"},
        ),
    ]

    print(json.dumps({"base_url": args.base_url, "checks": len(checks)}))

    failures = []
    for check in checks:
        ok, message = run_check(args.base_url, check, args.timeout)
        print(message)
        if not ok:
            failures.append(message)

    if failures:
        print("SMOKE_CHECK_RESULT: FAILED")
        return 1

    print("SMOKE_CHECK_RESULT: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
