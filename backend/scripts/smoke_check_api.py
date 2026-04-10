import argparse
import getpass
import json
import os
import sys
from dataclasses import dataclass
from uuid import uuid4

import requests


@dataclass
class Check:
    name: str
    method: str
    path: str
    expected_status: int
    payload: dict | None = None
    requires_auth: bool = False


def run_check(base_url: str, check: Check, timeout: int, token: str | None = None) -> tuple[bool, str]:
    url = f"{base_url.rstrip('/')}{check.path}"
    headers = {"Authorization": f"Bearer {token}"} if token else None

    try:
        if check.method == "GET":
            response = requests.get(url, timeout=timeout, headers=headers)
        else:
            response = requests.post(url, json=check.payload or {}, timeout=timeout, headers=headers)
    except requests.RequestException as exc:
        return False, f"{check.name}: request error: {exc}"

    if response.status_code != check.expected_status:
        body = response.text[:300].replace("\n", " ")
        return (
            False,
            f"{check.name}: expected {check.expected_status}, got {response.status_code} at {check.path}. body={body}",
        )

    return True, f"{check.name}: ok ({response.status_code})"


def _request_json(method: str, url: str, timeout: int, payload: dict | None = None) -> tuple[int, dict | None, str]:
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=payload or {}, timeout=timeout)
    except requests.RequestException as exc:
        return 0, None, str(exc)

    body_text = response.text
    try:
        parsed = response.json()
    except ValueError:
        parsed = None

    return response.status_code, parsed, body_text


def _resolve_password(args: argparse.Namespace) -> str | None:
    if args.auth_password:
        return args.auth_password

    if args.auth_password_env:
        return os.getenv(args.auth_password_env)

    if args.prompt_auth_password:
        try:
            return getpass.getpass("Auth password: ")
        except Exception:
            return None

    return None


def resolve_auth_token(
    base_url: str,
    timeout: int,
    auth_mode: str,
    auth_email: str | None,
    auth_password: str | None,
    allow_bootstrap_create: bool,
) -> tuple[str | None, list[str]]:
    notes: list[str] = []
    if auth_mode == "none":
        notes.append("auth mode=none: skipping authenticated login flow")
        return None, notes

    login_url = f"{base_url.rstrip('/')}/api/v1/auth/login"
    bootstrap_url = f"{base_url.rstrip('/')}/api/v1/auth/bootstrap-status"
    register_url = f"{base_url.rstrip('/')}/api/v1/auth/register"

    if auth_email and auth_password:
        status_code, data, body_text = _request_json(
            "POST",
            login_url,
            timeout,
            payload={"email": auth_email, "password": auth_password},
        )
        if status_code == 200 and data and isinstance(data, dict):
            token = (((data.get("data") or {}).get("access_token")) if isinstance(data.get("data"), dict) else None)
            if token:
                notes.append("auth login succeeded using provided credentials")
                return token, notes
        message = body_text[:240].replace("\n", " ")
        notes.append(f"auth login failed with provided credentials (status={status_code}): {message}")
        if auth_mode == "required":
            return None, notes

    if not allow_bootstrap_create:
        notes.append("bootstrap user creation disabled (use --allow-bootstrap-create to enable)")
        return None, notes

    status_code, data, body_text = _request_json("GET", bootstrap_url, timeout)
    if status_code != 200 or not isinstance(data, dict):
        notes.append(
            f"bootstrap-status unavailable (status={status_code}): {body_text[:200].replace(chr(10), ' ')}"
        )
        return None, notes

    requires_bootstrap = bool(((data.get("data") or {}).get("requires_bootstrap")) if isinstance(data.get("data"), dict) else False)
    if not requires_bootstrap:
        notes.append("bootstrap not required and no valid credentials available")
        return None, notes

    email = f"smoke-admin-{uuid4().hex[:8]}@example.com"
    password = "SmokeCheckPass123!"
    status_code, data, body_text = _request_json(
        "POST",
        register_url,
        timeout,
        payload={"email": email, "password": password, "full_name": "Smoke Admin", "role": "admin"},
    )
    if status_code not in (200, 201):
        notes.append(f"bootstrap register failed (status={status_code}): {body_text[:240].replace(chr(10), ' ')}")
        return None, notes

    status_code, data, body_text = _request_json(
        "POST",
        login_url,
        timeout,
        payload={"email": email, "password": password},
    )
    if status_code == 200 and isinstance(data, dict):
        token = (((data.get("data") or {}).get("access_token")) if isinstance(data.get("data"), dict) else None)
        if token:
            notes.append("bootstrap auth user created and login succeeded")
            return token, notes

    notes.append(f"bootstrap login failed (status={status_code}): {body_text[:240].replace(chr(10), ' ')}")
    return None, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="SOAR backend API smoke checks")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--timeout", type=int, default=8, help="Request timeout in seconds")
    parser.add_argument(
        "--auth-mode",
        choices=["auto", "required", "none"],
        default="auto",
        help="auto: attempt login when creds are provided, then fall back to 401 checks; required: fail if auth is unavailable; none: skip auth",
    )
    parser.add_argument("--auth-email", default=None, help="Auth email for protected endpoint checks")
    parser.add_argument("--auth-password", default=None, help="Auth password for protected endpoint checks (less secure)")
    parser.add_argument("--auth-password-env", default=None, help="Environment variable name containing auth password")
    parser.add_argument("--prompt-auth-password", action="store_true", help="Prompt securely for auth password")
    parser.add_argument(
        "--allow-bootstrap-create",
        action="store_true",
        help="Allow smoke checks to create a bootstrap admin if no users exist (disabled by default)",
    )
    args = parser.parse_args()

    checks = [
        Check("Docs", "GET", "/docs", 200),
        Check("Health", "GET", "/api/v1/health", 200),
        Check("Incidents", "GET", "/api/v1/incidents?page=1&page_size=1", 200, requires_auth=True),
        Check("Playbooks", "GET", "/api/v1/playbooks", 200, requires_auth=True),
        Check(
            "Threat Intel Query",
            "POST",
            "/api/v1/threat-intel/query",
            200,
            payload={"indicator": "8.8.8.8", "indicator_type": "ip"},
            requires_auth=True,
        ),
    ]

    auth_password = _resolve_password(args)
    token, auth_notes = resolve_auth_token(
        args.base_url,
        args.timeout,
        args.auth_mode,
        args.auth_email,
        auth_password,
        args.allow_bootstrap_create,
    )

    if args.auth_mode == "required" and token is None:
        print(
            json.dumps(
                {
                    "base_url": args.base_url,
                    "checks": len(checks),
                    "auth_mode": args.auth_mode,
                    "auth_resolved": False,
                    "notes": auth_notes,
                }
            )
        )
        print("SMOKE_CHECK_RESULT: FAILED")
        return 1

    for check in checks:
        if check.requires_auth and token is None:
            check.expected_status = 401

    print(
        json.dumps(
            {
                "base_url": args.base_url,
                "checks": len(checks),
                "auth_mode": args.auth_mode,
                "auth_resolved": token is not None,
                "notes": auth_notes,
            }
        )
    )

    failures = []
    for check in checks:
        ok, message = run_check(args.base_url, check, args.timeout, token=token)
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
