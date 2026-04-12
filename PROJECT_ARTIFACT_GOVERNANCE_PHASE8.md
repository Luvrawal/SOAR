# PROJECT ARTIFACT GOVERNANCE PHASE 8

## 1) Scope and Goal
This phase defines data governance controls for SOAR incident artifacts generated and stored by the backend reporting flow. The goal is to reduce data exposure risk while preserving forensic and operational value.

Primary artifact classes in scope:
- Incident JSON reports (`INC-*.json`)
- Incident PDF reports (`INC-*.pdf`)
- Playbook execution payloads persisted into incident records

## 2) Observed Current State (Evidence-Based)
### 2.1 Artifact generation and storage
- Report generator persists PDFs to a configurable directory from `SOAR_REPORTS_DIR` (default runtime directory `./reports`).
- Test utility in reporter scans JSON files in the same reports directory and bulk-generates PDFs.
- Runtime configuration exposes `SOAR_REPORTS_DIR` in settings.

### 2.2 Artifact content sensitivity
Sample report artifacts currently include:
- attacker IP, target IP, target port
- attempted usernames
- alert severity and risk scoring
- threat-intelligence lookups and provider diagnostics
- response action timeline and incident handling details

These fields qualify as operationally sensitive security telemetry and should be treated as Confidential by policy.

### 2.3 Application persistence overlap
- `playbook_service` stores report structures into `incident.playbook_result` and execution records, creating both file-based and database-resident copies of sensitive data.

## 3) Data Classification Policy
### 3.1 Classification levels
- Public: no security relevance (not expected for incident artifacts).
- Internal: non-sensitive operational metadata.
- Confidential: incident telemetry, IOC context, response actions, investigative notes.
- Restricted: secrets, credentials, auth tokens, private keys (must not be present in artifacts).

### 3.2 Classification assignment for this project
- All JSON/PDF incident artifacts: Confidential.
- All playbook result payloads in DB: Confidential.
- Any token/credential material, if encountered: Restricted and policy violation.

## 4) Retention and Lifecycle Controls
### 4.1 Recommended retention windows
- Development: 7 days (short-lived debugging value).
- Staging: 14 days (release validation and incident replay).
- Production: 30 days default, extendable by case/legal hold.

### 4.2 Lifecycle states
- Active: newly generated and frequently accessed.
- Warm: aged artifacts still inside retention period.
- Expired: past retention threshold and eligible for purge.
- Legal hold: exempt from purge until hold release.

### 4.3 Purge strategy
- Daily scheduled cleanup of expired JSON/PDF artifacts.
- Coordinated DB cleanup policy for stale execution payloads, unless tied to open investigations.
- Purge operations must be auditable (count deleted, incident IDs, timestamp, operator/service identity).

## 5) Access Control and Handling Requirements
### 5.1 Directory hardening
- Keep `SOAR_REPORTS_DIR` outside publicly served web roots.
- Restrict filesystem permissions to service account and designated operators only.
- Disallow world-readable permissions in all environments.

### 5.2 Access model
- Principle of least privilege for report reads.
- Separate operator role for incident-report access from general API consumers.
- If report download endpoints are introduced, require authenticated and authorized access with explicit audit logging.

### 5.3 Transport and sharing
- Never share raw report files over insecure channels.
- For ticketing/chat exports, share redacted summaries by default.
- Full artifact sharing requires explicit incident-response approval.

## 6) Redaction and Data Minimization
### 6.1 Immediate redaction standards
Before external sharing or low-trust distribution:
- Mask internal target IPs and hostnames.
- Minimize usernames list to count and sample where possible.
- Truncate low-value telemetry fields that do not affect decision-making.

### 6.2 Generation-time minimization (recommended enhancement)
- Add optional report profile modes:
  - `full` (internal IR use)
  - `redacted` (cross-team sharing)
- Ensure Restricted data is excluded by construction (denylist and schema validation checks).

## 7) Security and Compliance Controls
### 7.1 Integrity and provenance
- Include generation timestamp and immutable incident ID in both JSON and PDF.
- Optionally add checksum manifest for stored artifacts to detect tampering.

### 7.2 Confidentiality controls
- At-rest encryption for storage volume in production environments.
- Backup encryption and retention parity with primary artifact policy.

### 7.3 Operational logging
- Log creation, read, export, and purge events for artifacts.
- Keep audit trail retention at or above artifact retention baseline.

## 8) Implementation Plan (Phase 8 Deliverables)
### 8.1 Policy deliverables (completed in this phase)
- Defined classification model for incident artifacts.
- Defined retention windows and lifecycle transitions.
- Defined minimum access-control and handling standards.
- Defined redaction baseline for outbound sharing.

### 8.2 Engineering follow-ups (Phase 9 inputs)
1. Add cleanup automation script for `SOAR_REPORTS_DIR` with dry-run mode and audit log output.
2. Add optional redacted report generation path in reporter flow.
3. Add report-access audit events in API paths that expose artifacts.
4. Align DB retention for `playbook_result` payload size and age.
5. Add runbook SOP section for legal hold and incident-case retention exceptions.

## 9) Operator Runbook Commands (Proposed)
Use these command patterns after adding cleanup tooling:

```bash
# Dry-run: identify expired report artifacts
python scripts/cleanup_reports.py --reports-dir ./reports --retention-days 30 --dry-run

# Execute purge with audit output
python scripts/cleanup_reports.py --reports-dir ./reports --retention-days 30 --apply
```

## 10) Acceptance Criteria for Phase 8
- Governance policy explicitly maps to current artifact generation/storage behavior.
- Sensitive fields in current reports are recognized and classified.
- Retention, access, redaction, and purge controls are documented with enforceable intent.
- Clear engineering backlog items are produced for implementation in later phases.

## 11) Risks Remaining After Phase 8
- No automated retention enforcement is currently present.
- Dual storage (filesystem + DB payload copies) can increase exposure surface.
- Redaction is policy-defined but not yet enforced in code paths.

## 12) Phase 8 Status
Status: Complete (documentation and governance baseline established).
Ready for Phase 9: Yes (risk register and remediation prioritization).
