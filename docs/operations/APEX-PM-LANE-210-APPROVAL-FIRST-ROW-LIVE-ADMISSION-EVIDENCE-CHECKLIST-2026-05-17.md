# APEX PM Lane 210 - Approval First-Row Live-Admission Evidence Checklist

Date: 2026-05-17
Status: Completed no-code PM checklist lane
Scope: Project Miner Temp Power first approval-row evidence, admission gate clarity, and live-write stop conditions

## Purpose

PM Lane 210 converts the refreshed PM Lane 208 executor prompt and PM Lane 209 stop-drill result into a concise evidence checklist for the future first approval-row live-admission decision.

This lane does not admit the live write. It gives Jason and the VS Code Codex coordinator a plain review surface for deciding whether the first approval-row executor should remain stopped or whether Jason wants to provide the exact PM Lane 142 admission phrase in a later lane.

## Live Admission Boundary

The only phrase that can admit the future live approval POST remains:

`I explicitly admit PM Lane 142 live approval POST and first approval-row creation for the current Project Miner Temp Power import candidate.`

The phrase appearing in this document, PM Lane 208, PM Lane 209, or historical guardrail text does not count as admission.

PM Lane 210 did not provide that phrase as current admission and performed no hosted checks, browser live-route access, approval POST, approval-row creation, project import, or downstream PM business-state mutation.

## Evidence Checklist

Before any future first approval-row POST is admitted, the executor closeout must be able to show the following evidence.

### Admission Gate

1. Exact PM Lane 142 phrase provided as current instruction outside quoted guardrail or historical text.
2. Source prompt and coordinator instruction recorded in the closeout.
3. If the phrase is absent, paraphrased, quoted only as guardrail text, or ambiguous, the executor stops with `STOPPED_NO_LIVE_ADMISSION`.

### Source Floor

1. Current repo commit recorded.
2. Worktree is clean except coordinator-approved unrelated residue.
3. PM Lane 208 refreshed executor prompt is the active prompt unless superseded by a newer VS Code Codex coordinator prompt.

### Candidate Identity

1. Current Project Miner Temp Power import candidate identity confirmed.
2. Candidate source fingerprint confirmed.
3. Candidate shape fingerprint confirmed.
4. Warning-code acceptance confirmed.
5. Human no-go acknowledgement coverage confirmed.

### PM Decision And Notes

1. Explicit PM decision value is nonempty.
2. PM review notes are nonempty.
3. Approval-status readback context is present.
4. Live-gate preflight context is present.

### Local Zero-Mutation Proof

1. Local mocked browser validation is green.
2. Unmocked `/api/v1/mutations/**` calls fail in the local smoke.
3. Approval envelope matches the PM Lane 141 contract.
4. Project import controls remain absent.
5. No product code is changed unless a later coordinator packet authorizes it.

### Hosted Readiness Proof

1. Hosted smokes are green only after the exact phrase is admitted.
2. Approval-status GET is available.
3. Existing hosted services are used:
   - `https://operations.apexpowerops.com`
   - `https://mutation-seam.apexpowerops.com`
4. No new hosted service, DNS widening, auth widening, ingress widening, or secret rotation is introduced by the first-row lane.

### Pre-Write Row Proof

1. Pre-submit approval record count for the current candidate is `0`.
2. If count is not `0`, live POST stops until the duplicate/idempotency posture is classified.

### Live Approval Write Proof

1. Browser approval submission path is used, not direct SQL.
2. Exactly one live POST is sent to `/api/v1/mutations/project-import-approvals`.
3. Response shows:
   - `status: accepted`
   - `entity_type: pm_import_candidate_approval`
   - `action_type: persist_import_approval`
   - `new_state.import_authority: not_admitted`

### Idempotency Proof

1. The exact same payload is submitted once as an idempotent replay.
2. Replay does not create a second approval row.

### Readback Proof

1. Approval-status readback matches the submitted PM decision.
2. Approval-status readback is captured without exposing secrets.

### Downstream Non-Mutation Proof

1. Project count unchanged.
2. Workpackage count unchanged.
3. Task count unchanged.
4. Apparatus count unchanged.
5. Assignment count unchanged.
6. Schedule/status count unchanged.
7. Durable field record count unchanged.
8. Production tracking count unchanged.

### Secret-Free Closeout

1. No secrets printed.
2. No secrets copied into repo files.
3. No secrets committed, pushed, summarized, or pasted into handoffs.
4. Closeout records only secret-free evidence and command outcomes.

## Stop Conditions

The future live approval lane must stop before any POST if any of these are true:

1. Exact PM Lane 142 phrase is absent, paraphrased, quoted only in guardrails/history, or not clearly current.
2. Repo source floor or worktree residue cannot be classified.
3. Candidate identity, source fingerprint, or shape fingerprint cannot be confirmed.
4. Warning-code acceptance or human no-go acknowledgement is missing.
5. PM decision value or PM review notes are missing.
6. Local mocked browser proof is not green.
7. Local unmocked mutation blocking fails.
8. Approval envelope differs from PM Lane 141 contract.
9. Hosted smokes fail after admission or approval-status GET is unavailable.
10. Hosted proof would require new services or DNS/auth/ingress/secret widening.
11. Pre-submit approval count is not `0`.
12. The path would use direct SQL instead of browser approval submission.
13. Any project import or downstream PM/field/production/customer/finance mutation would occur.
14. Any secret would be exposed or stored in repo-visible artifacts.

## Sidecar Use

VS Code Codex retained PM lane technical authority and final repo integration authority. Read-only sidecar Mill inspected the current PM approval first-row surfaces and returned checklist sections, stop conditions, live-branch ambiguity, and a next-lane recommendation.

Mill made no edits, staged nothing, and did not access hosted services, live routes, Supabase, Render, Vercel, Olares, or secrets.

## Next PM Direction

Default remains no live approval POST.

The next safe lane is:

`PM Lane 211 - Approval First-Row Live-Admission Readiness Review Packet`

PM Lane 211 should package this checklist into a Jason-reviewable decision packet while still performing no live POST unless the exact PM Lane 142 phrase is explicitly provided as current admission.
