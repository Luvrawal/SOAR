# SOAR Backend Runbook

## Purpose
Operational guide for running, validating, and rolling back the SOAR backend stack.

## Handoff References
- Release notes snapshot: `RELEASE_NOTES_PHASE10.md`
- Environment-specific rollout commands: `GO_LIVE_COMMAND_MATRIX.md`

## Prerequisites
- Docker and Docker Compose
- Backend env file at `backend/.env`

## Start Stack
1. `cd backend`
2. `docker compose up -d --build`
3. `docker compose ps`

Expected services:
- `soar_api`
- `soar_worker`
- `soar_db`
- `soar_redis`

## Apply Migrations
1. `docker compose exec api alembic upgrade head`

## Release Readiness Checklist
1. Prepare production env file from template:
  - `cp .env.production.example .env.production`
2. Run production preflight checks:
  - `python scripts/production_preflight.py --env-file .env.production`
3. Verify test baseline:
  - `python -m pytest -q`
4. Verify smoke checks on running stack:
  - `python scripts/smoke_check_api.py --base-url http://localhost:8000`
  - For authenticated protected-route verification:
    - `python scripts/smoke_check_api.py --base-url http://localhost:8000 --auth-mode required --auth-email <admin_email> --auth-password <admin_password>`
5. Verify observability endpoints:
  - `curl "http://localhost:8000/api/v1/observability/metrics"`
  - `curl "http://localhost:8000/api/v1/observability/metrics/prometheus"`

## Health Validation
1. Automated smoke check (recommended first):
  - `python scripts/smoke_check_api.py --base-url http://localhost:8000`
  - Notes:
    - Default mode (`--auth-mode auto`) verifies public endpoints and validates protected endpoints as `401` when credentials are unavailable.
    - Use `--auth-mode required` with admin credentials to assert protected endpoints return `200`.
2. API health:
  - `curl http://localhost:8000/api/v1/health`
3. Simulation smoke check:
  - `curl -X POST "http://localhost:8000/api/v1/simulations/brute-force?count=20"`
4. Summary check:
  - `curl "http://localhost:8000/api/v1/simulations/summary?limit=5"`
5. Queue metrics check (24h window):
  - `curl "http://localhost:8000/api/v1/simulations/queue-metrics?window_hours=24"`
6. Observability JSON metrics (admin):
  - `curl "http://localhost:8000/api/v1/observability/metrics"`
7. Prometheus metrics export (admin):
  - `curl "http://localhost:8000/api/v1/observability/metrics/prometheus"`

## Operational Checks
- Worker logs:
  - `docker compose logs worker --tail=200`
- API logs:
  - `docker compose logs api --tail=200`
- DB logs:
  - `docker compose logs db --tail=200`

Success indicators:
- Celery task accepted and completed logs exist
- `playbook_status` transitions from `pending` to `success` or `failed`
- `playbook_result` exists for processed incidents
- Queue metrics include non-empty `per_queue` counters and `worker_runbook` commands

## Queue-Specific Worker Guidance
Use dedicated workers to isolate queue classes under load:
1. Default queue:
  - `celery -A app.tasks.celery_app.celery_app worker -Q playbook_default -n default_worker@%h --concurrency=4`
2. Email queue:
  - `celery -A app.tasks.celery_app.celery_app worker -Q playbook_email -n email_worker@%h --concurrency=4`
3. Endpoint queue:
  - `celery -A app.tasks.celery_app.celery_app worker -Q playbook_endpoint -n endpoint_worker@%h --concurrency=4`
4. File queue:
  - `celery -A app.tasks.celery_app.celery_app worker -Q playbook_file -n file_worker@%h --concurrency=4`

## Demo Data Seeding
Use the seed utility for dashboard/demo data:
1. `cd backend`
2. `python scripts/seed_demo_data.py --base-url http://localhost:8000 --count 20`

## Common Failure Modes
- Missing threat intel API keys:
  - Expected behavior: processing still succeeds in degraded mode
  - Check `playbook_result.degraded_threat_intel` and `provider_errors`
- Queue unavailable:
  - Symptom: incidents created but no playbook progress
  - Verify `redis` and `worker` container health and logs
- DB migration mismatch:
  - Symptom: API errors on persistence or missing columns
  - Re-run `alembic upgrade head`

## Dashboard Platform Operations Troubleshooting
If the dashboard shows `n/a` for queue/observability cards:
1. Verify route availability on the live backend instance:
  - `curl "http://localhost:8000/openapi.json"`
  - Confirm paths include `/api/v1/simulations/queue-metrics` and `/api/v1/observability/metrics`
2. Rebuild/restart backend services from current source:
  - `docker compose down`
  - `docker compose up -d --build api worker db redis`
3. Verify auth behavior:
  - Unauthenticated calls to queue/summary/observability should return `401`
  - Analyst role should receive `403` on observability route
  - Admin role should receive `200` on observability route
4. Check API logs during dashboard load:
  - `docker compose logs api --tail=120`
  - Confirm `GET /api/v1/simulations/summary?limit=50`, `GET /api/v1/simulations/queue-metrics?window_hours=24`, and `GET /api/v1/observability/metrics`
5. Frontend recovery steps:
  - Hard refresh browser (`Ctrl+F5`)
  - Re-authenticate if token is stale

## Rollback Procedure
If a deployment introduces regressions:
1. `git checkout <last-known-good-tag-or-commit>`
2. `cd backend`
3. `docker compose down`
4. `docker compose up -d --build`
5. `docker compose exec api alembic upgrade head`
6. Re-run health and smoke checks

## Safe Shutdown
- `docker compose down`
- To remove volumes as well: `docker compose down -v`
