# Phase 5 Implementation: Frontend Architecture and Integration Map

Date: 2026-04-10

## Scope
This phase documents the frontend runtime architecture, route/role model, API integration contract, polling behavior, feature-level endpoint usage, and quality/tooling setup.

## Runtime and Bootstrap
Entry sequence:
1. React app mounts in StrictMode with BrowserRouter in `frontend/src/main.jsx`.
2. Root app composes `AuthProvider` around route tree in `frontend/src/App.jsx`.
3. Route tree is rendered by `AppRoutes` with lazy loaded pages and Suspense fallback.

Runtime stack:
- React 19 + React DOM 19
- React Router 7
- Axios for API client
- Recharts for data visualization
- Tailwind utility styling

## Route and Access Control Model
Route composition in `frontend/src/app/AppRoutes.jsx`:
- Public:
  - `/login`
  - `/unauthorized`
- Protected app shell (within `AppLayout`):
  - `/` dashboard (admin, analyst)
  - `/incidents` (admin, analyst)
  - `/incidents/:incidentId` (admin, analyst)
  - `/playbooks` (admin)
  - `/threat-intelligence` (admin, analyst)
  - `/simulation-lab` (admin, analyst)
  - `/settings` (admin)

Guard logic in `frontend/src/components/routing/ProtectedRoute.jsx`:
- While auth bootstraps: loading state
- Unauthenticated: redirect to `/login`
- Wrong role: redirect to `/unauthorized`

## Layout, Navigation, and Shared UI State
App shell in `frontend/src/components/layout/AppLayout.jsx`:
- Sidebar (role-aware nav)
- Topbar (global search + logout)
- Backend status banner (health polling)
- Outlet for routed pages

Role-aware nav in `frontend/src/components/layout/Sidebar.jsx`:
- Menu items filtered against `user.role`
- Collapsible desktop sidebar state

Global search in `frontend/src/app/SearchContext.jsx`:
- Shared query state used by topbar and feature pages
- Topbar query routing heuristic:
  - IOC-like input (dot/http/colon) routes to Threat Intelligence
  - otherwise routes to Incidents

## Authentication and Session Lifecycle
Auth context in `frontend/src/app/AuthContext.jsx`:
- Stores token/user in localStorage keys:
  - `soar_auth_token`
  - `soar_auth_user`
- Bootstraps existing session using `GET /auth/me`
- Login uses `POST /auth/login`
- Register uses `POST /auth/register`
- Logout clears storage and can hard redirect to `/login`

## API Client Contract
Axios client in `frontend/src/lib/api.js`:
- Base URL resolution:
  - `VITE_API_BASE_URL` env var
  - fallback `http://localhost:8000/api/v1`
- Request interceptor:
  - injects bearer token when available
- Response interceptor:
  - stores `X-Correlation-ID`
  - normalizes connectivity and 404 messages
  - handles 401 session-expiry redirect when auth token exists

## Polling and Freshness Model
Reusable hook in `frontend/src/hooks/usePolling.js`:
- Default interval from localStorage key `soc.pollingMs`
- Bounds interval to 1000..15000 ms
- Used by dashboard, incidents, incident detail, and playbooks

Backend reachability banner in `frontend/src/components/layout/BackendStatusBanner.jsx`:
- Polls `/health` every 10 seconds
- Shows warning banner with expected endpoint when unreachable

## Feature to Endpoint Matrix
### Login and bootstrap
- `GET /auth/bootstrap-status` (login page bootstrap hint)
- `POST /auth/login`
- `POST /auth/register`
- `GET /auth/me`

### Dashboard
- `GET /simulations/summary?limit=50`
- `GET /incidents?page=1&page_size=50`
- `GET /observability/metrics`
- `GET /simulations/queue-metrics?window_hours=24`
- quick actions: `POST /simulations/{type}`

### Incidents list/detail
- `GET /incidents` (filters: status/severity/type/q)
- `GET /incidents/{incidentId}`

### Playbooks
- `GET /playbooks`
- `GET /playbooks/{id}/stats`
- `GET /playbooks/{id}/executions`

### Threat intelligence
- `POST /threat-intel/query`

### Simulation lab
- `POST /simulations/{simulationType}`

### Settings
- no backend call; updates `soc.pollingMs` in localStorage

## Page-Level Data Flow Notes
- Dashboard tolerates partial endpoint failure using Promise.allSettled and queue fallback derivation.
- Incidents page synchronizes global search query with local filter state.
- Incident detail composes timeline, execution, threat intel, risk, and actions from single detail response.
- Playbooks page combines three independent datasets (catalog, stats, executions) and computes drift metrics client-side.
- Threat intel page infers indicator type and tracks in-session query history.
- Simulation lab triggers backend generation and navigates to latest created incident when available.

## Tooling and Quality Setup
Build/dev:
- Vite with manual chunk strategy in `frontend/vite.config.js`
- Scripts in `frontend/package.json`: `dev`, `build`, `preview`, `lint`, `test`, `test:watch`

Testing:
- Vitest + jsdom + Testing Library setup in `frontend/vitest.config.js`
- Existing tests cover Dashboard, Playbooks, Simulation Lab, Threat Intel pages

Linting:
- ESLint flat config in `frontend/eslint.config.js`
- React hooks and react-refresh rule sets enabled

## Integration and Operational Risks
1. API call logic is mostly page-local; there is no domain service layer beyond shared axios client.
2. Authenticated route UX depends on backend role consistency (`admin`/`analyst`).
3. Root and frontend docs remain partially inconsistent with current implementation maturity.
4. Some critical frontend modules have no direct test coverage yet (AuthContext, ProtectedRoute, AppRoutes, Incident pages).

## Phase 5 Deliverables Completed
- Frontend runtime architecture mapped end-to-end.
- Route-level role policy documented.
- API contract and endpoint consumption matrix documented.
- Polling, session, and error-handling behavior documented.
- Build/test/lint and current coverage posture documented.

## Next Phase
Phase 6: operational workflow matrix consolidation across backend and frontend (local/dev/staging/prod run paths, checks, and failure recovery).
