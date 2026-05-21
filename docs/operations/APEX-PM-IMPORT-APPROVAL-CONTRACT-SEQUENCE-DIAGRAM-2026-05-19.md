# APEX PM Import Approval Contract Sequence Diagram

Date: 2026-05-19
Status: Active reference artifact
Scope: Project Miner import candidate approval contract, persistence boundary, and later import handoff

## Purpose

This artifact captures the repo-governed Project Miner approval flow as a Mermaid sequence diagram.

It is intentionally narrower than the broader PM workflow runbook:

1. candidate read
2. admission plan
3. approval contract
4. storage plan
5. approval status readback
6. approval persistence
7. later separate import packet

Primary implementation sources:

1. `apps/mutation-seam/app/project_import_admission_plan.py`
2. `apps/mutation-seam/app/project_import_approval_contract.py`
3. `apps/mutation-seam/app/project_import_approval_storage_plan.py`
4. `apps/mutation-seam/app/project_import_approval_persistence.py`
5. `apps/mutation-seam/migrations/003_pm_import_candidate_approvals.sql`
6. `apps/operations-web/app/pm-review/import-intake/page.tsx`

## Mermaid

```mermaid
sequenceDiagram
  participant PM as PM User
  participant UI as Operations Web Import Intake
  participant Reads as Mutation Seam Reads
  participant Candidate as Import Candidate
  participant Plan as Admission Plan
  participant Contract as Approval Contract
  participant Storage as Storage Plan
  participant Status as Approval Status
  participant Write as Approval Mutation Route
  participant Table as pm_import_candidate_approvals
  participant Import as Later Import Packet

  PM->>UI: Open import-intake workbench
  UI->>Reads: GET project-import-candidate
  Reads->>Candidate: Load candidate from planning-source preview
  Candidate-->>Reads: Candidate payload
  Reads-->>UI: Candidate payload

  UI->>Reads: GET project-import-admission-plan
  Reads->>Plan: Build admission gate
  Plan-->>Reads: Shape fingerprint, idempotency key, no-go checks
  Reads-->>UI: Admission plan

  UI->>Reads: GET project-import-approval-contract
  Reads->>Contract: Build approval payload contract
  Contract-->>Reads: Required fields, permitted decisions, validator rules
  Reads-->>UI: Approval contract

  UI->>Reads: GET project-import-approval-storage-plan
  Reads->>Storage: Build storage decision plan
  Storage-->>Reads: Table, route, insert-only lifecycle
  Reads-->>UI: Storage plan

  UI->>Reads: GET project-import-approval-status
  Reads->>Status: Classify current approval state
  Status-->>Reads: No record, current, stale, returned, or rejected
  Reads-->>UI: Approval status

  Note over PM,UI: PM reviews candidate, warnings, and no-go posture

  alt Approval persistence admitted
    PM->>Write: POST project-import-approvals
    Write->>Contract: Validate payload against current candidate identity
    Contract-->>Write: Pass or fail
    alt Validation passes
      Write->>Table: Insert canonical approval row
      Table-->>Write: Stored approval record
      Write-->>PM: mutation_id and audit_event_id
    else Validation fails
      Write-->>PM: Reject payload, no row written
    end
  else Approval persistence not admitted
    UI-->>PM: Read-only review only
  end

  UI->>Reads: GET project-import-approval-status
  Reads->>Status: Reclassify approval state
  Status-->>UI: Current approval classification

  Note over Import,Table: Later import packet may consume approved current record
  Note over Import,Table: Approval persistence is separate from project import
```

## Interpretation Notes

1. Approval persistence is not project import.
2. The canonical approval state lives in `seam.pm_import_candidate_approvals`, not in audit history alone.
3. Candidate identity includes candidate id, candidate version, source fingerprint, shape fingerprint, and idempotency key.
4. A later import packet may consume an approved current record, but this artifact does not admit that import write path.
5. Browser-local intake review remains a separate no-live preparation surface until the approval mutation route is explicitly admitted.