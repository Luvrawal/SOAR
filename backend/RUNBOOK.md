# SOAR Backend Runbook

## Purpose
Operational guide for running, validating, and rolling back the SOAR backend stack.

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

## Health Validation
1. API health:
   - `curl http://localhost:8000/api/v1/health`
2. Simulation smoke check:
   - `curl -X POST "http://localhost:8000/api/v1/simulations/brute-force?count=20"`
3. Summary check:
   - `curl "http://localhost:8000/api/v1/simulations/summary?limit=5"`

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
