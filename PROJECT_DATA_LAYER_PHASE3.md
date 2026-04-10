# Phase 3 Implementation: Data Layer and Persistence Map

Date: 2026-04-10

## Scope
This phase documents data-layer behavior end-to-end: configuration precedence, database URL resolution, SQLAlchemy session lifecycle, ORM model relationships, migration lineage, and concrete write/read paths used by API and worker flows.

## Configuration and Connection Resolution
Settings source:
- Pydantic settings load from `.env` with defaults.

Database URL precedence:
1. Use `SQLALCHEMY_DATABASE_URI` when provided.
2. Else build PostgreSQL DSN from `POSTGRES_*` values.

Constructed fallback format:
- `postgresql+psycopg2://<user>:<password>@<host>:<port>/<db>`

Operational implication:
- Local compose defaults point host to `db` service.
- External environments can override with full URI safely.

## Engine and Session Lifecycle
From `app/db/session.py`:
- Engine is process-global with `pool_pre_ping=True`.
- Session factory: `SessionLocal(autocommit=False, autoflush=False)`.
- Request/task DB access pattern uses explicit session lifetime and close in `finally`.

Two execution contexts:
1. API request context
   - Injected through dependency `get_db()`.
2. Celery worker context
   - Task creates `SessionLocal()` directly and closes in `finally`.

## Metadata Registration for Migrations
From `app/db/base.py`:
- Imports all ORM models into `Base` metadata namespace.
- Ensures Alembic autogenerate/metadata comparison sees complete schema.

## ORM Entities and Relationships
### users
Core columns:
- id (PK)
- email (unique/indexed)
- password_hash
- role (`admin` or `analyst`)
- full_name
- is_active
- created_at

Relationship:
- `users` one-to-many `incidents` via `Incident.created_by`.

### incidents
Core columns:
- id (PK)
- title, description, source, severity
- status (default `open`)
- playbook_status (default `pending`)
- raw_alert (JSON)
- playbook_result (JSON)
- created_by (FK -> users.id, nullable)
- created_at, updated_at, playbook_last_run_at

Relationships:
- many-to-one `created_by_user` -> users
- one-to-many `executions` -> playbook_executions

### playbook_executions
Core columns:
- id (PK)
- incident_id (FK -> incidents.id, indexed)
- task_id (indexed)
- playbook_name
- status
- logs
- result (JSON)
- error_message
- started_at, finished_at, created_at

Relationship:
- many-to-one `incident` -> incidents

## Migration Lineage and Schema Evolution
Alembic environment:
- `alembic/env.py` injects runtime URL from app config and binds `Base.metadata`.

Revision chain:
1. `20260330_0001`
   - Creates `users` and `incidents` base tables.
2. `20260330_0002`
   - Adds `playbook_status`, `playbook_result`, `playbook_last_run_at` to incidents.
3. `20260330_0003`
   - Creates `playbook_executions` table and indexes.
4. `20260408_0004`
   - Adds `password_hash` and `role` to users.

Compatibility note:
- Migration `0004` uses server defaults for non-null backfill safety (`!` and `analyst`) when applied to existing rows.

## Persistence Touchpoints by Flow
### A) Alert ingestion write path
Endpoint:
- POST `/api/v1/alerts`

Write operations in `create_incident_from_alert`:
1. Insert new `Incident` with `status=open` and raw payload.
2. Commit and refresh incident.
3. Compute queue metrics from incident table.
4. Enqueue async processing task (no additional DB writes in this step).

Failure behavior:
- SQLAlchemy errors rollback and raise structured app error (`incident_persistence_failed`).

### B) Simulation write path
Endpoint:
- POST `/api/v1/simulations/{simulation_type}`

Write operations:
- For each generated simulated alert, reuse same ingestion service path above.
- Results in N incident inserts + N Celery enqueue attempts.

### C) Worker/playbook write path
Task:
- `process_incident`

Persistence path in `execute_playbook_for_incident`:
1. Read incident by id.
2. Insert `PlaybookExecution` row with `running` status and initial execution steps.
3. Update incident `playbook_status=running` and commit.
4. Run playbook.
5. On success:
   - Update incident `playbook_result`, `playbook_status`, `playbook_last_run_at`.
   - Optionally update incident `status` and `severity` from report.
   - Update execution row (`result`, `status`, `finished_at`, logs, final playbook name).
   - Commit.
6. On failure:
   - Update incident status fields to failed state.
   - Update execution with failure details/result/logs.
   - Commit.

### D) Read-heavy endpoints
- `/incidents` and `/incidents/{id}` query incidents and (detail) playbook executions.
- `/playbooks*` queries playbook_executions for aggregate stats and history.
- `/simulations/summary` and `/simulations/queue-metrics` aggregate incident table states.

## Transaction Semantics and Consistency Notes
- API/service writes use explicit commit boundaries.
- Worker flow intentionally creates execution row before running playbook, preserving an audit trail even when execution fails later.
- Queue enqueue happens after incident persistence, avoiding orphan queue tasks referencing non-existent incidents.
- If enqueue fails, incident still persists and trace event marks enqueue failure.

## Identified Data-Layer Risks
1. Potential naming drift:
   - Execution rows start with `default_triage` then later overwrite with report playbook name.
   - Playbooks API stat aggregation keys on fixed human-readable names.
2. No explicit DB-level enum constraints for status/severity fields.
3. JSON fields are flexible, so schema-level validation relies on app logic.

## Validation Snapshot for Phase 3
- Migrations executed successfully at current head in live stack.
- Health endpoint and smoke checks confirmed application can access DB-dependent paths.

## Phase 3 Deliverables Completed
- Config and DB URL precedence documented.
- Session lifecycle documented for API and Celery worker contexts.
- ORM relationships and table responsibilities documented.
- Migration lineage documented with operational implications.
- Write/read persistence paths traced across alerts, simulations, and playbook processing.

## Next Phase
Phase 4: Async orchestration and SOAR execution flow (queue routing, retry semantics, runbook commands, and observability trace points).
