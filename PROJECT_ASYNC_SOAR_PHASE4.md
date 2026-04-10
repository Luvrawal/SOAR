# Phase 4 Implementation: Async Orchestration and SOAR Flow

Date: 2026-04-10

## Scope
This phase maps asynchronous processing from incident creation to playbook completion, including queue routing rules, Celery reliability settings, retry behavior, task lifecycle events, and observability trace points.

## Celery Runtime Model
From `app/tasks/celery_app.py`:
- Broker/result backend built from config helper functions.
- JSON serialization enforced for task payloads/results.
- UTC enabled.
- Reliability settings:
  - `worker_prefetch_multiplier=1`
  - `task_acks_late=True`
  - `task_reject_on_worker_lost=True`
- Queue topology:
  - `playbook_default`
  - `playbook_email`
  - `playbook_endpoint`
  - `playbook_file`
- Worker concurrency controlled by `CELERY_WORKER_CONCURRENCY`.

## Ingestion to Queue Routing
From `app/services/alert_service.py`:
1. API/simulation inserts incident row first.
2. Service computes queue metrics and capacity/pressure state.
3. Service picks queue by incident raw alert/source heuristics:
   - phishing/email -> email queue
   - malware/file/hash -> file queue
   - network/brute/ip -> endpoint queue
   - else -> default queue
4. Service enqueues `process_incident` with incident id and correlation id.
5. If queue enqueue fails, incident remains persisted and trace event marks failure.

Queue observability payload includes:
- backlog, utilization_pct, pressure, over-capacity state
- per-queue totals and status breakdowns
- throughput/failure-rate estimates by queue
- worker runbook command suggestions

## Worker Task Lifecycle
From `app/tasks/incident_tasks.py`:
- `process_incident` is a bound Celery task with auto-retry.
- Retry policy:
  - `autoretry_for=(Exception,)`
  - `retry_backoff=settings.CELERY_RETRY_BACKOFF_SECONDS`
  - jitter enabled
  - max retries from `CELERY_TASK_MAX_RETRIES`

Execution sequence:
1. Resolve correlation id (propagated or task id).
2. Emit `task.start` trace event.
3. Open dedicated DB session.
4. Call `execute_playbook_for_incident`.
5. On success emit `task.success` trace event.
6. On exception emit `task.error` trace event and re-raise for retry behavior.
7. Always close DB session.

## Playbook Execution Persistence Flow
From `app/services/playbook_service.py`:
1. Load incident by id; return not found payload if missing.
2. Create `PlaybookExecution` row with status `running` and initial execution steps.
3. Update incident `playbook_status=running` and commit.
4. Build playbook alert shape and run SOAR playbook orchestrator.
5. On success:
   - write normalized result into `incident.playbook_result`
   - set incident playbook status and last run time
   - optionally update incident severity/status from report
   - finalize execution row (`result`, `status`, `finished_at`, logs, playbook_name)
   - commit
6. On failure:
   - mark incident and execution failed
   - persist failure metadata and execution steps
   - commit

Audit guarantee:
- Execution row is created before running external logic, preserving traceability for failures.

## SOAR Orchestrator Selection Logic
From `app/soar/main.py`:
- `identify_attack_type` infers playbook class from `alert_type` + details hints.
- `run_playbook` instantiates one of:
  - BruteForcePlaybook
  - PhishingPlaybook
  - MalwarePlaybook
  - NetworkAnomalyPlaybook
- Generates PDF report when report payload exists.
- Returns `None` for unknown attack type.

Integration boundary note:
- Backend runtime calls embedded SOAR orchestrator under `backend/app/soar`.

## Threat Intelligence Enrichment Behavior
From `app/soar/utils/threat_intel.py`:
- Uses configurable request timeout/retry/backoff settings.
- Returns degraded structured responses when keys are missing.
- Provider call failures are transformed into structured error results.
- Playbook result stores provider errors and degraded flag.

## Observability and Correlation Tracking
From `app/core/observability.py` and middleware/task hooks:
- Correlation id stored in context var and propagated to events.
- API middleware records request metrics and correlation id.
- Async task records trace events (`task.start`, `task.success`, `task.error`).
- Queue enqueue path records `queue.enqueue` or `queue.enqueue_failed`.
- Store is in-memory with bounded recent event queues.

## End-to-End Async Sequence (Reference)
1. Client calls alerts/simulations endpoint.
2. Incident persists in DB.
3. Incident routed to queue and task submitted.
4. Worker accepts task and records trace start.
5. Worker executes playbook pipeline.
6. Incident + execution records updated to success/failed terminal state.
7. Dashboard endpoints read incident/playbook/queue/observability aggregates.

## Operational Controls Exposed by Async Layer
- Queue pressure and capacity inspection via simulations queue-metrics endpoint.
- Worker split-by-queue commands available from queue metrics output.
- Retry and concurrency knobs configurable via environment.

## Phase 4 Deliverables Completed
- Queue topology and routing heuristics documented.
- Celery reliability/retry semantics documented.
- Worker task and persistence lifecycle documented.
- SOAR playbook dispatch path documented.
- Correlation and trace event propagation documented.

## Next Phase
Phase 5: Frontend architecture and integration mapping to backend contracts, including route guards, polling, and endpoint consumption matrix.
