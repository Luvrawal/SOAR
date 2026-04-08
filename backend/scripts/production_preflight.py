import argparse
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import Settings, production_safety_issues


def main() -> int:
    parser = argparse.ArgumentParser(description="SOAR production preflight validator")
    parser.add_argument(
        "--env-file",
        default=".env.production",
        help="Path to production environment file (default: .env.production)",
    )
    args = parser.parse_args()

    cfg = Settings(_env_file=args.env_file, _env_file_encoding="utf-8")
    issues = production_safety_issues(cfg)

    if issues:
        print("PRODUCTION_PREFLIGHT: FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("PRODUCTION_PREFLIGHT: PASSED")
    print(f"Environment: {cfg.ENVIRONMENT}")
    print(f"CORS origins: {cfg.BACKEND_CORS_ORIGINS}")
    print(f"Security headers enabled: {cfg.SECURITY_HEADERS_ENABLED}")
    print(f"HSTS forced: {cfg.FORCE_HTTPS_HSTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
