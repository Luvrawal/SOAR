# Phase 6 Implementation: Operational Workflow Matrix

Date: 2026-04-10

## Scope
This phase consolidates operational workflows across backend and frontend for local, staging, and production runs, including startup, validation, troubleshooting, and rollback paths.

## Runtime Topology (Backend)
From `backend/docker-compose.yml`:
- api: FastAPI service (`soar_api`) on host port 8000
- worker: Celery worker (`soar_worker`) consuming multiple queues
- db: PostgreSQL 16 (`soar_db`) on host port 5432
- redis: Redis 7 (`soar_redis`) on host port 6379

Queue classes:
- playbook_default
- playbook_email
- playbook_endpoint
- playbook_file

## Local Development Workflow
### Backend local cycle
1. `cd backend`
2. `docker compose up -d --build`
3. `docker compose ps`
4. `docker compose exec api alembic upgrade head`
5. `python scripts/smoke_check_api.py --base-url http://localhost:8000`
6. Optional authenticated smoke check (secure env var form):
   - PowerShell:
     - `$env:SOAR_SMOKE_AUTH_PASSWORD='your_password'`
     - `python scripts/smoke_check_api.py --base-url http://localhost:8000 --auth-mode required --auth-email <admin_email> --auth-password-env SOAR_SMOKE_AUTH_PASSWORD`
7. `python -m pytest -q`

### Frontend local cycle
1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. Optional quality checks:
   - `npm run lint`
   - `npm run test`

Frontend API binding:
- `VITE_API_BASE_URL` from `frontend/.env.example`
- default expected value: `http://localhost:8000/api/v1`

## Staging Workflow
1. `cd backend`
2. `cp .env.production.example .env.staging`
3. Set staging secrets and hosts in `.env.staging`
4. `python scripts/production_preflight.py --env-file .env.staging`
5. `docker compose --env-file .env.staging up -d --build`
6. `docker compose --env-file .env.staging exec api alembic upgrade head`
7. `python scripts/smoke_check_api.py --base-url http://localhost:8000`
8. Optional secure authenticated smoke check (same env var pattern)
9. `curl "http://localhost:8000/api/v1/observability/metrics"`
10. `curl "http://localhost:8000/api/v1/observability/metrics/prometheus"`

## Production Workflow
1. `cd backend`
2. `cp .env.production.example .env.production`
3. Set production secrets/origins/hosts in `.env.production`
4. `python scripts/production_preflight.py --env-file .env.production`
5. `docker compose --env-file .env.production up -d --build`
6. `docker compose --env-file .env.production exec api alembic upgrade head`
7. `python scripts/smoke_check_api.py --base-url http://localhost:8000`
8. Optional secure authenticated smoke check (same env var pattern)
9. `curl "http://localhost:8000/api/v1/simulations/queue-metrics?window_hours=24"`
10. `curl "http://localhost:8000/api/v1/observability/metrics/prometheus"`

## Validation Matrix
### API and platform checks
- Baseline smoke: `scripts/smoke_check_api.py`
  - Non-mutating default mode
  - Protected routes validated as 401 without token
- Required auth smoke mode:
  - Must resolve valid token or fail
- Health endpoint:
  - `GET /api/v1/health`
- Simulation checks:
  - trigger + summary + queue metrics
- Observability checks:
  - JSON and Prometheus endpoints

### Data and migration checks
- Alembic at head via `alembic upgrade head`
- Persistence sanity by creating simulation incidents and inspecting summary counts

### Frontend checks
- Lint and test suites in `frontend`
- Runtime connectivity via backend status banner (polls `/health`)

## Operational Utilities
### Production preflight
Script: `backend/scripts/production_preflight.py`
- Validates production safety policy before rollout:
  - `DEBUG=false`
  - JWT secret overridden
  - CORS not wildcard in production

### Demo seeding
Script: `backend/scripts/seed_demo_data.py`
- Triggers all simulation types and prints summary snapshot

### Smoke checks
Script: `backend/scripts/smoke_check_api.py`
- Modes:
  - `auto` (default): non-mutating, best-effort auth if creds provided
  - `required`: fails if protected checks cannot authenticate
  - `none`: skip auth attempts
- Secure password handling:
  - `--auth-password-env`
  - `--prompt-auth-password`

## Troubleshooting Workflow
1. Confirm service/container health (`docker compose ps`)
2. Inspect logs (`docker compose logs api|worker|db`)
3. Verify route exposure (`/openapi.json`)
4. Re-run smoke and focused curl checks
5. Check auth role behavior for restricted endpoints
6. Hard refresh frontend and re-authenticate if stale token

Common failure signatures:
- Queue unavailable: incidents persist but playbook progression stalls
- Migration mismatch: DB persistence/column errors
- Missing threat intel keys: degraded mode with provider_errors but execution may still succeed

## Rollback Workflow
1. `git checkout <last-known-good-tag-or-commit>`
2. `cd backend`
3. `docker compose down`
4. `docker compose up -d --build`
5. `docker compose exec api alembic upgrade head`
6. Re-run health and smoke checks

## Safe Shutdown
- `docker compose down`
- Full teardown including volumes: `docker compose down -v`

## Phase 6 Deliverables Completed
- Unified backend+frontend run matrix across environments
- Validation checklist and guardrails consolidated
- Secure smoke-check operational standard documented
- Recovery and rollback flow standardized

## Next Phase
Phase 7: testing and confidence map (coverage matrix by subsystem, residual risk scoring, and test-gap prioritization).
