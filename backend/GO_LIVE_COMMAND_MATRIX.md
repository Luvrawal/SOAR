# SOAR Backend Go-Live Command Matrix

## Purpose
Single reference for environment-specific startup, validation, and rollback commands.

## Drift Control Check
Validate command parity with runbook before go-live:
1. `python scripts/check_docs_alignment.py --runbook-path RUNBOOK.md --matrix-path GO_LIVE_COMMAND_MATRIX.md`

## Development
1. `cd backend`
2. `docker compose up -d --build`
3. `docker compose exec api alembic upgrade head`
4. Optional profile mode for share-safe artifacts:
	- PowerShell: `$env:SOAR_REPORT_PROFILE='redacted'`
5. `python scripts/smoke_check_api.py --base-url http://localhost:8000`
6. Optional authenticated check (secure env var form):
	- PowerShell: `$env:SOAR_SMOKE_AUTH_PASSWORD='your_password'; python scripts/smoke_check_api.py --base-url http://localhost:8000 --auth-mode required --auth-email <admin_email> --auth-password-env SOAR_SMOKE_AUTH_PASSWORD`
7. Retention dry-run (dev policy = 7 days):
	- `python scripts/cleanup_reports.py --reports-dir ./reports --retention-days 7 --dry-run --json-audit-log -`
8. DB payload retention dry-run (dev policy = 7 days):
	- `python scripts/cleanup_db_payloads.py --retention-days 7 --dry-run --json-audit-log -`
9. `python -m pytest -q`

## Staging
1. `cd backend`
2. `cp .env.production.example .env.staging`
3. Update staging-specific values in `.env.staging`
4. `python scripts/production_preflight.py --env-file .env.staging`
5. `docker compose --env-file .env.staging up -d --build`
6. `docker compose --env-file .env.staging exec api alembic upgrade head`
7. `python scripts/smoke_check_api.py --base-url http://localhost:8000`
8. Optional authenticated check (secure env var form):
	- PowerShell: `$env:SOAR_SMOKE_AUTH_PASSWORD='your_password'; python scripts/smoke_check_api.py --base-url http://localhost:8000 --auth-mode required --auth-email <admin_email> --auth-password-env SOAR_SMOKE_AUTH_PASSWORD`
9. Retention dry-run (staging policy = 14 days):
	- `python scripts/cleanup_reports.py --reports-dir ./reports --retention-days 14 --dry-run --json-audit-log -`
10. DB payload retention dry-run (staging policy = 14 days):
	- `python scripts/cleanup_db_payloads.py --retention-days 14 --dry-run --json-audit-log -`
11. `curl "http://localhost:8000/api/v1/observability/metrics"`
12. `curl "http://localhost:8000/api/v1/observability/metrics/prometheus"`

## Production
1. `cd backend`
2. `cp .env.production.example .env.production`
3. Update all secrets/origins/host values in `.env.production`
4. `python scripts/production_preflight.py --env-file .env.production`
5. `docker compose --env-file .env.production up -d --build`
6. `docker compose --env-file .env.production exec api alembic upgrade head`
7. `python scripts/smoke_check_api.py --base-url http://localhost:8000`
8. Optional authenticated check (secure env var form):
	- PowerShell: `$env:SOAR_SMOKE_AUTH_PASSWORD='your_password'; python scripts/smoke_check_api.py --base-url http://localhost:8000 --auth-mode required --auth-email <admin_email> --auth-password-env SOAR_SMOKE_AUTH_PASSWORD`
9. Retention apply (production policy = 30 days):
	- `python scripts/cleanup_reports.py --reports-dir ./reports --retention-days 30 --apply --json-audit-log ./reports/cleanup-audit.json`
10. DB payload retention apply (production policy = 30 days):
	- `python scripts/cleanup_db_payloads.py --retention-days 30 --apply --json-audit-log ./reports/db-payload-cleanup-audit.json`
11. `curl "http://localhost:8000/api/v1/simulations/queue-metrics?window_hours=24"`
12. `curl "http://localhost:8000/api/v1/observability/metrics/prometheus"`

## Dedicated Queue Workers (Optional)
1. `celery -A app.tasks.celery_app.celery_app worker -Q playbook_default -n default_worker@%h --concurrency=4`
2. `celery -A app.tasks.celery_app.celery_app worker -Q playbook_email -n email_worker@%h --concurrency=4`
3. `celery -A app.tasks.celery_app.celery_app worker -Q playbook_endpoint -n endpoint_worker@%h --concurrency=4`
4. `celery -A app.tasks.celery_app.celery_app worker -Q playbook_file -n file_worker@%h --concurrency=4`

## Fast Rollback
1. `git checkout <last-known-good-tag-or-commit>`
2. `cd backend`
3. `docker compose down`
4. `docker compose up -d --build`
5. `docker compose exec api alembic upgrade head`
6. `python scripts/smoke_check_api.py --base-url http://localhost:8000`
