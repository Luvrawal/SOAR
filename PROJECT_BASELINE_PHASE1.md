# Phase 1 Implementation: System Baseline and Scope Lock

Date: 2026-04-10

## Objective
Establish an authoritative baseline for what this repository runs today, what components are active, and what must be validated before deeper implementation phases.

## Repository Domains
- backend: FastAPI API, SQLAlchemy models, Alembic migrations, Celery tasks, embedded SOAR engine.
- frontend: React + Vite dashboard client.
- playbook/soar-platform: standalone SOAR implementation/reference package.
- backend/reports: generated JSON incident report artifacts.

## Active Runtime Topology (Authoritative)
Source of truth: backend/docker-compose.yml

Expected services:
- api (container_name: soar_api)
- worker (container_name: soar_worker)
- db (container_name: soar_db)
- redis (container_name: soar_redis)

Ports:
- API: 8000
- PostgreSQL: 5432
- Redis: 6379

Queue model used by Celery worker:
- playbook_default
- playbook_email
- playbook_endpoint
- playbook_file

## Startup and Request Entry Points
- API process entry: backend/Dockerfile -> uvicorn app.main:app --host 0.0.0.0 --port 8000
- FastAPI app assembly: backend/app/main.py
- API mount prefix: settings.API_V1_PREFIX (default /api/v1)
- Middleware chain:
  - request observability + correlation id header
  - security headers middleware

## Runtime Status Snapshot (Captured During Phase 1)
Checks executed:
- Initial check: HTTP probe to http://localhost:8000/api/v1/health -> failed (connection refused/unreachable)
- Initial check: local listener check on TCP 8000 -> no process listening
- Initial check: docker compose commands -> Docker daemon unavailable on local named pipe
- Recovery check after Docker restart:
	- docker compose up -d --build -> api/worker/db/redis started
	- docker compose exec api alembic upgrade head -> migration context healthy
	- GET /api/v1/health -> HTTP 200 with success payload
	- smoke_check_api.py -> passed in auth-aware mode

Interpretation:
- Phase start had runtime outage due to Docker daemon not active.
- Current state is healthy and reachable after Docker daemon recovery.

## Documentation Reality Check
Observed mismatch:
- Root README claims frontend is not included.
- Repository actually contains a complete frontend app under frontend/.

Observed dual-SOAR implementation:
- backend/app/soar is integrated directly into backend services/tasks.
- playbook/soar-platform appears to be standalone/original reference implementation.

Phase 1 decision:
- Treat backend/app/soar as runtime-canonical path unless explicitly overridden.
- Keep playbook/soar-platform tracked as secondary/reference until a hard ownership decision is made.

## Commands to Bring System to Known-Good Baseline
From backend/:

1) Start services
	docker compose up -d --build

2) Confirm containers
	docker compose ps

3) Apply schema
	docker compose exec api alembic upgrade head

4) Validate health
	curl http://localhost:8000/api/v1/health

5) Run smoke checks
	python scripts/smoke_check_api.py --base-url http://localhost:8000

6) Optional demo data
	python scripts/seed_demo_data.py --base-url http://localhost:8000 --count 20

## Phase 1 Deliverables Completed
- Runtime topology identified and locked.
- Startup path confirmed at process and framework entry points.
- Active vs reference SOAR boundaries identified.
- Reachability failure captured and resolved with reproducible checks.
- Recovery command sequence documented.
- Smoke checks upgraded to auth-aware behavior and validated.

## Exit Criteria for Phase 1
Phase 1 status: COMPLETE

Validated:
- docker compose ps shows api, worker, db, redis running.
- GET /api/v1/health returns HTTP 200.
- migrations run without error at current head.
- smoke checks pass for environment policy.

## Next Phase
Phase 2: Backend execution path map (router groups, endpoint auth model, service boundaries, and exception flow) with endpoint-by-endpoint traceability.
