from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import requests

SIMULATION_TYPES = ["brute-force", "phishing", "malware", "network-anomaly"]


def request_json(method: str, url: str, timeout: int = 60, **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method=method, url=url, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response.json()


def seed(base_url: str, count: int, timeout: int) -> None:
    total_incidents = 0

    print("Seeding demo data...")
    for simulation_type in SIMULATION_TYPES:
        url = f"{base_url}/api/v1/simulations/{simulation_type}"
        payload = request_json("POST", url, timeout=timeout, params={"count": count})

        data = payload.get("data") or {}
        created = int(data.get("incidents_created", 0))
        generated = int(data.get("alerts_generated", 0))
        total_incidents += created

        print(f"- {simulation_type}: alerts_generated={generated}, incidents_created={created}")

    summary_url = f"{base_url}/api/v1/simulations/summary"
    summary = request_json("GET", summary_url, timeout=timeout, params={"limit": 5})

    print("\nSummary snapshot:")
    print(json.dumps(summary.get("data", {}), indent=2))
    print(f"\nTotal incidents created in this run: {total_incidents}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed simulation incidents for demo/dashboard use.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for API")
    parser.add_argument("--count", type=int, default=20, help="Count passed to each simulation endpoint")
    parser.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds")
    args = parser.parse_args()

    if args.count < 1:
        print("count must be >= 1", file=sys.stderr)
        return 2

    try:
        seed(base_url=args.base_url.rstrip("/"), count=args.count, timeout=args.timeout)
        return 0
    except requests.RequestException as exc:
        print(f"Seeding failed due to HTTP error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Seeding failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
