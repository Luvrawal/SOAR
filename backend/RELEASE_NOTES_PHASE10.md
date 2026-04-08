# SOAR Backend Release Notes (Phase 10)

## Scope
This release snapshot captures implementation progress from security hardening through observability and production readiness.

## Completed Phase Highlights

### Phase 5: Authentication and RBAC
- JWT authentication flow added (`/auth/register`, `/auth/login`, `/auth/me`).
- Backend role enforcement for admin and analyst routes.
- Frontend protected routes and role-scoped navigation.

### Phase 6: Threat Scoring
- Centralized threat scoring service with score, severity, confidence, and factors.
- Threat-intel query and incident detail payloads include richer risk metadata.
- UI renders confidence and scoring factors.

### Phase 7: Playbook Visibility
- Versioned playbook catalog metadata (owner, active, version).
- Playbook execution step-state model (`receive_alert`, `enrich`, `risk_score`, `respond`, `report`).
- Execution history endpoint with filters and pagination.
- UI drilldown for latest failed vs successful step comparison.

### Phase 8: Queue Scaling and Routing
- Queue metrics and pressure tracking endpoint.
- Celery safety tuning (`acks_late`, `worker_prefetch_multiplier=1`, worker-lost rejection).
- Source-based queue routing (`default`, `email`, `endpoint`, `file`).
- Retry and backoff policies configurable through environment.

### Phase 9: Observability and Correlation
- Request correlation IDs propagated and exposed via `X-Correlation-ID`.
- In-memory observability metrics store with route/method/status counters.
- Admin JSON metrics endpoint and Prometheus exposition endpoint.
- Recent API event stream and queue/task trace lifecycle stream.
- Dashboard operations panel surfaces queue metrics, error rate, latency, and event streams.

### Phase 10: Production Hardening and Handoff
- Production safety startup validation (`DEBUG`, wildcard CORS, default JWT secret checks).
- Security response headers middleware and optional strict HSTS.
- Production env template (`.env.production.example`).
- Automated preflight validator (`scripts/production_preflight.py`).
- Runbook release checklist and go-live command references.

## Backward Compatibility Notes
- Existing API routes remain available.
- New observability routes are admin-protected.
- Simulation and playbook response payloads now include additional metrics fields but maintain prior top-level structures.

## Known Operational Notes
- Threat intel providers can enter degraded mode under timeout/rate-limit conditions.
- Dashboard chart tests may emit expected jsdom layout warnings in CI (non-failing).

## Validation Summary
- Backend automated tests passing.
- Frontend automated tests passing.
- Production preflight script validated against production example env.
