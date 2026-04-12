# PROJECT RISK REGISTER PHASE 9

Date: 2026-04-10

## 1) Scope
This phase consolidates technical and operational risks identified across Phases 5-8 into a single prioritized register with remediation actions, ownership lanes, and acceptance criteria.

Source phases used:
- Phase 5 (frontend architecture and integration)
- Phase 6 (ops workflow matrix)
- Phase 7 (testing confidence map)
- Phase 8 (artifact governance)

## 2) Scoring Model
Risk score uses a 1-5 scale:
- Likelihood (L): probability of occurrence
- Impact (I): business/security/availability effect
- Score: `L x I` (max 25)

Priority bands:
- Critical: 20-25
- High: 14-19
- Medium: 8-13
- Low: 1-7

## 3) Consolidated Risk Register
| ID | Risk | Domain | L | I | Score | Priority | Current Evidence | Primary Mitigation | Owner Lane |
|---|---|---|---:|---:|---:|---|---|---|---|
| R-001 | No automated artifact retention cleanup for JSON/PDF reports | Security/Operations | 4 | 5 | 20 | Critical | Phase 8 reports retention policy is defined but not enforced | Implement scheduled cleanup with dry-run/apply and audit output | Backend + Ops |
| R-002 | Sensitive incident data duplicated in filesystem and DB payloads | Security/Data Governance | 4 | 5 | 20 | Critical | `playbook_result` stores report payload while files are also persisted | Add data minimization + retention coordination for DB and files | Backend/Data |
| R-003 | Frontend auth shell (AuthContext/ProtectedRoute/AppRoutes) lacks direct tests | Quality/Reliability | 4 | 4 | 16 | High | Phase 7 identified low-medium confidence in auth/routing shell | Add focused frontend auth and route-guard test suite | Frontend |
| R-004 | RBAC negative-path coverage incomplete (401 vs 403 matrix) | Security/Quality | 4 | 4 | 16 | High | Phase 7 backlog calls out missing route-wide authorization matrix | Add backend role matrix tests for protected endpoints | Backend |
| R-005 | Real Celery/Redis failure behavior under load not integration-tested | Reliability/Scalability | 3 | 5 | 15 | High | Async behavior largely verified via monkeypatch/simulated paths | Add integration tests with real broker and transient failure injection | Backend + Ops |
| R-006 | Redaction policy exists but not enforced in report generation | Security/Compliance | 3 | 5 | 15 | High | Phase 8 defines redaction standards only at policy layer | Add `full` and `redacted` report profiles and denylist checks | Backend |
| R-007 | Report access audit events not uniformly captured | Security/Auditability | 3 | 4 | 12 | Medium | Phase 8 prescribes auditing but implementation gaps remain | Emit structured audit logs on create/read/export/purge flows | Backend + Ops |
| R-008 | Environment/documentation drift can cause unsafe run procedures | Operations/Change Mgmt | 3 | 4 | 12 | Medium | Multiple run paths and evolving scripts across phases | Single-source runbook sections + versioned command matrix ownership | Ops |
| R-009 | Frontend page-local API orchestration increases regression surface | Maintainability | 3 | 3 | 9 | Medium | Phase 5 notes no domain service layer beyond axios client | Introduce feature service modules for endpoint orchestration | Frontend |
| R-010 | JSDOM chart warnings may hide rendering regressions | Quality | 2 | 3 | 6 | Low | Dashboard tests pass with known warning noise | Add visual/snapshot confidence checks and warning budget policy | Frontend QA |

## 4) Priority Execution Queue
### Wave 1 (Immediate: this sprint)
1. R-001: Implement artifact cleanup automation and schedule.
2. R-002: Define and enforce retention parity for DB payload + file artifacts.
3. R-003: Add frontend auth/guard/routing tests.
4. R-004: Add backend RBAC negative-path coverage.

### Wave 2 (Next sprint)
1. R-005: Real queue integration and failure-injection tests.
2. R-006: Redacted report mode implementation.
3. R-007: Report access/purge audit logging standardization.

### Wave 3 (Hardening)
1. R-008: Documentation drift controls and ownership.
2. R-009: Frontend API service-layer refactor.
3. R-010: Chart rendering confidence enhancement.

## 5) Mitigation Backlog (Actionable)
### A) Artifact cleanup automation (R-001)
Deliverables:
- `backend/scripts/cleanup_reports.py`
- Flags: `--reports-dir`, `--retention-days`, `--dry-run`, `--apply`, `--json-audit-log`
- Deterministic output including incident IDs and deleted file counts

Acceptance checks:
- Dry-run lists candidate files without deletion.
- Apply mode purges only expired artifacts.
- Audit output records run timestamp and deletion summary.

### B) Dual-storage risk control (R-002)
Deliverables:
- Retention policy mapping for `incident.playbook_result` and execution records.
- Optional DB pruning task for aged payload fields where legally permitted.
- Schema guard to prevent Restricted fields from persisting.

Acceptance checks:
- DB and filesystem retention windows aligned by environment.
- Legal-hold exception path documented and testable.

### C) Frontend auth/route tests (R-003)
Deliverables:
- Tests for bootstrap success/failure, token expiry logout, unauthorized redirect.
- Tests for role authorization across `admin` and `analyst` routes.

Acceptance checks:
- Auth shell confidence rises from Low-Medium to Medium-High.
- CI fails on auth route regressions.

### D) RBAC negative-path matrix (R-004)
Deliverables:
- Parameterized backend tests by role and endpoint group.
- Assertions for expected 401/403 outcomes.

Acceptance checks:
- Protected endpoints have explicit denial-path tests.
- Unauthorized access regressions are caught pre-merge.

## 6) Residual Risk After Planned Mitigations
Expected risk profile after Wave 1+2 completion:
- Critical risks reduced to High/Medium bands.
- Highest remaining exposure shifts to performance and maintainability rather than immediate confidentiality gaps.

## 7) Governance and Ownership Cadence
- Weekly risk review in engineering standup.
- Risk owner updates include status (`open`, `mitigating`, `accepted`, `closed`) and evidence links.
- Any newly discovered Critical risk triggers immediate hotfix triage and runbook update.

## 8) Phase 9 Exit Criteria
- A ranked risk register is published and accepted.
- Top 4 risks have implementation-ready backlog items.
- Each top risk has explicit owner lane and acceptance checks.
- Phase 10 can proceed with a stable roadmap and measurable closure criteria.

## 9) Phase 9 Status
Status: Complete (risk register consolidated and prioritized).
Ready for Phase 10: Yes (final master knowledge pack and closure synthesis).
