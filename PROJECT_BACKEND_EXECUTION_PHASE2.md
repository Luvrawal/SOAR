# Phase 2 Implementation: Backend Execution Path Map

Date: 2026-04-10

## Scope
This phase documents the backend request lifecycle end-to-end: process entry, FastAPI bootstrap, middleware sequence, route mounting, auth/RBAC enforcement, endpoint groups, and exception handling behavior.

## Runtime Entry and Application Assembly
- Container command: uvicorn starts `app.main:app` on port 8000.
- App construction occurs in `create_application()` and exports module-level `app` object.
- Startup safety gate runs first via `validate_production_safety()`.
- CORS is attached with origins from config helper.
- Exception handlers are registered globally.
- API router is mounted under `/api/v1`.

## Router Composition
Top-level chaining:
1. `app.main` includes `api_router` with `/api/v1` prefix.
2. `app/api/router.py` includes `v1_router`.
3. `app/api/v1/router.py` mounts endpoint routers by domain tags.

Mounted endpoint domains:
- health
- auth
- alerts
- incidents
- observability
- playbooks
- simulations
- threat-intel

## Request Middleware Chain
Order in `app/main.py`:
1. Request observability middleware
   - Generates/propagates `X-Correlation-ID`.
   - Measures request latency.
   - Records method/route/status/latency in observability store.
2. Security headers middleware
   - Adds anti-sniff, anti-frame, referrer, and permissions headers.
   - Adds HSTS only when configured.

## Auth and RBAC Flow
Auth primitives from `app/core/auth.py`:
- Token source: `HTTPBearer(auto_error=False)`.
- `get_current_user`:
  - Requires bearer token.
  - Decodes JWT.
  - Resolves DB user by `sub` claim.
  - Rejects invalid, expired, missing, or inactive users with 401.
- `get_current_user_optional`:
  - Returns `None` when token missing.
- `require_roles(*roles)`:
  - Wraps `get_current_user` and enforces role membership.
  - Returns 403 on insufficient role.

## Endpoint Access Matrix
Public routes:
- GET `/api/v1/health`
- GET `/api/v1/auth/bootstrap-status`
- POST `/api/v1/auth/login`
- POST `/api/v1/auth/register` (bootstrap-only anonymous; admin-auth required once users exist)

Authenticated routes:
- GET `/api/v1/auth/me` (any authenticated user)
- GET `/api/v1/auth/roles/check` (admin)

Admin or analyst routes:
- POST `/api/v1/alerts`
- GET `/api/v1/incidents`
- GET `/api/v1/incidents/{incident_id}`
- GET `/api/v1/incidents/{incident_id}/executions`
- POST `/api/v1/simulations/{simulation_type}`
- GET `/api/v1/simulations/summary`
- GET `/api/v1/simulations/queue-metrics`
- POST `/api/v1/threat-intel/query`

Admin-only routes:
- GET `/api/v1/playbooks`
- GET `/api/v1/playbooks/{playbook_id}/stats`
- GET `/api/v1/playbooks/{playbook_id}/executions`
- GET `/api/v1/observability/metrics`
- GET `/api/v1/observability/metrics/prometheus`

## Domain Handler Boundaries
- Alerts endpoint delegates incident creation/queueing to `create_incident_from_alert` in `alert_service`.
- Incidents endpoints are DB-centric and assemble timeline/execution/risk/threat-intel views.
- Simulations endpoint generates synthetic alerts and reuses the same alert ingestion service path.
- Playbooks endpoints expose static playbook catalog plus execution/stat aggregates from DB.
- Observability endpoint serializes in-memory counters and Prometheus text.
- Threat-intel endpoint delegates provider enrichment and risk summary scoring.

## Exception Model and API Error Contract
Global handlers in `app/core/error_handlers.py`:
- `AppException` -> structured JSON error with explicit status and app error code.
- `RequestValidationError` -> 422 with `validation_error` code and Pydantic details.
- `SQLAlchemyError` -> 500 with `database_error` code and server-side logging.
- Generic `Exception` -> 500 with `internal_error` code and server-side logging.

Custom exception classes in `app/core/exceptions.py`:
- `AuthenticationException` -> 401, `authentication_error`.
- `AuthorizationException` -> 403, `authorization_error`.

## Request Execution Sequence (Typical Protected Endpoint)
1. Request enters FastAPI app.
2. Observability middleware starts timer and correlation id.
3. Security middleware wraps downstream handler.
4. Router resolves endpoint.
5. Dependency chain resolves DB session and role dependency.
6. JWT decoded and user loaded.
7. Endpoint handler executes business logic / service calls.
8. Response returned and security headers applied.
9. Observability middleware records metrics and attaches `X-Correlation-ID`.
10. Any raised app/validation/db/unhandled exception is normalized by global handlers.

## Validation Snapshot for Phase 2
Live checks already completed in this session:
- Stack running under docker compose.
- Health endpoint returns 200.
- Auth-aware smoke checks pass with correct protected-route behavior.

## Phase 2 Deliverables Completed
- Backend router hierarchy mapped.
- Middleware and auth flow documented with execution order.
- Endpoint access matrix documented.
- Exception model and normalized API error behavior documented.
- Domain service boundaries identified for next data-flow phase.

## Next Phase
Phase 3: Data layer and persistence map (config precedence, DB URL resolution, model relationships, migration lineage, and write/read paths through services/tasks).
