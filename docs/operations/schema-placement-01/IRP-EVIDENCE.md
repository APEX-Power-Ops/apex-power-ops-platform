# Schema-Placement Packet 01 - IRP / Cross-Engine Review Evidence (2026-07-10)

Substrate: prod Supabase `fxoyniqnrlkxfligbxmg` (managed non-super `postgres`).
Gate state at PR open: **design + SQL reviewed; ALL production writes HELD** pending explicit per-action operator
write-GO. This PR carries the reviewed bytes so production authority can attach to committed artifacts. NOT for merge
until CI is green and the operator ratifies the SHA/diff.

## 1. Action -> exact file mapping (each = one independent `psql -v ON_ERROR_STOP=1 -f <file>` invocation)

| Action | Forward file | Rollback file |
| --- | --- | --- |
| A1 (01b-core) | `apps/control-plane-api/supabase/migrations/20260710_000012_harden_mcp_public_exposure_core.sql` | `...20260710_000012_harden_mcp_public_exposure_core.rollback.sql` |
| A2 (01b-auth) | `apps/control-plane-api/supabase/migrations/20260710_000013_retire_mcp_authenticated_contract.sql` | `...20260710_000013_retire_mcp_authenticated_contract.rollback.sql` |
| A3 (01a) | `infra/database/migrations/schema-placement/20260710_000001_archive_relocate_scratch.sql` | `...20260710_000001_archive_relocate_scratch.rollback.sql` |

Three actions, THREE distinct forward files (not two) - each is a self-contained `BEGIN ... <asserts> ... COMMIT` and
runs as one independent `psql -f`. Apply order/discipline: **A1 then A2 in the same operating window** (between them an
`authenticated` JWT can still cross-user-read the definer summary views - do NOT report the surface closed after A1
alone), then A3. Apply via raw `psql` ONLY (NOT the Supabase CLI runner or MCP `apply_migration`, which would nest the
embedded transaction and defeat the "failed assert aborts with no partial state" guarantee).

## 2. Review process (two cross-engine passes, Claude + Codex each time)

- **Design IRP (Deep, Audit):** blocked v1 (over-scoped relocate lane); produced the rescoped 01a/01b + deferred
  01c/01d design. Codex raw memo: `evidence/codex-design-audit.md`; consolidated synthesis (incl. the Claude 8-agent
  grounded-audit findings): `evidence/design-irp-synthesis.md`.
- **SQL IRP (Deep, Audit):** this packet's exact SQL. Codex raw memo: `evidence/codex-sql-audit.md`. The Claude
  grounded-audit's reconciled findings are captured in full in section 3 below (the workflow ran 8 agents; its
  APPLY-SAFE verdict + 9 findings F1-F9 are folded in). Reconciled verdict below.

## 3. SQL review - reconciled verdict + rev-2 disposition

**Verdict: SQL is correct and non-breaking; no fix was a correctness defect.** Codex opened at BLOCK; the Claude
grounded-audit downgraded its two strictest points with prod evidence: (a) `pg_attribute.attacl` is EMPTY on all
objects and `anon`/`authenticated` are members of no role, so the (now-fixed) SELECT-only assert gaps had NO live
false-pass path; (b) the deployed-role proof is IMMATERIAL to A1/A2 - `anon`/`authenticated` are PostgREST GUC roles,
so revoking them cannot affect the control-plane's direct/`bypassrls` DSN connection (only the deferred 6b needs that
proof). Both engines confirmed: REVOKEs never name `postgres`/`service_role`/`apex_tcc_runtime`; non-super `postgres`
has sufficient privilege for every statement; the DROP-policy set matches prod verbatim; rollback policies are
faithful to migration 000008.

Findings folded into rev 2 (the committed SQL):
- A2/A3 asserts now loop all four verbs (SELECT/INSERT/UPDATE/DELETE) + cover the guarded 7th (was SELECT-only).
- Action 1 definer-view assert -> `count IN (0,2)` (survives a later 6b re-apply); its comment scoped to the 2 views.
- A2 rollback re-issues the 6 EXACT original comments (verbatim from 000008) + guarded 7th re-grant.
- Filenames -> `000012/000013` (000010/000011 already exist in the control-plane lane).
- Header pins raw `psql`, one action per invocation.
- Rollback blocks guard `current_user = postgres` (grantor fidelity).

## 4. Review limitations (disclosed)

- **1 of 8 Claude SQL-audit agents errored** (`no-unintended-breakage` probe hit the StructuredOutput retry cap after
  5 attempts). Its NON-BREAKING conclusion was captured in its last tool summary, and the adversarial regression-hunt
  pass plus the other 6 facets covered breakage thoroughly (control-plane role targeting, RLS-after-drop, interim
  sequencing), so coverage held - but the structured finding from that one facet was not returned.
- **Codex model drift:** the host Codex CLI's default rotated to `gpt-5.6-sol` (unsupported by the installed CLI); the
  SQL audit was run with an explicit `-m gpt-5.5` pin. (Tooling drift to reconcile in the codex-exec-host runbook.)
- **Read-only mandate:** neither audit executed the SQL; catalog/text-level correctness was verified, and the
  disposable-DB proof (section 5) exercises actual execution.

## 5. Disposable-DB up/down/up proof

`evidence/updownup_proof.txt` - a faithful mini-prod fixture on a throwaway PostgreSQL 17 database
(`apex-dev-pg`), covering: forward apply of A1/A2/A3 (in-migration asserts pass); post-state (anon+authenticated no
privilege on all verbs; 8 authenticated policies dropped, 6 service_all retained; 6 comments read RETIRED; 2 scratch
tables relocated to `archive` and de-exposed; `apex_tcc_runtime` grants unchanged); rollback restoring a byte-identical
baseline (privileges, policy-name set, comments, scratch schema); re-apply (up-down-UP idempotency); the 7-table
variant (guarded `mcp_external_action_audits`); and a NEGATIVE atomicity case (a membership leak makes an A1 assert
fail -> the whole action rolls back with no partial state). Harness + fixture: `evidence/tests/`.

**The proof caught a BLOCKING bug that both SQL-text IRP passes missed** (this is the value of the execution gate):
the assert DO-blocks appended a bare string literal to a `text[]` (`objs := objs || 'archive._009_rollback_snapshot'`),
which PostgreSQL resolves as array-concatenation and rejects at RUNTIME - `ERROR: malformed array literal`. This
aborted A3 on EVERY apply (it appends the archived object names) and A1/A2 whenever the guarded 7th table exists.
Neither the Claude grounded-audit (which returned APPLY-SAFE) nor the Codex audit detected it - both were
read-only/static and cannot see a plpgsql type-resolution error that only manifests on execution. Fix: `::text`
cast on each appended literal (A1 x1, A2 x1, A3 x6). The transcript above is the GREEN re-run against the FIXED
files (RC=0, all three cases). Lesson: a disposable-DB up/down/up proof is not redundant with cross-engine SQL
review - it catches a class of defect static review structurally cannot.

## 6. IMPORTANT residual disclosure (review F1)

This packet closes anon reach on ONLY 2 of the **31** anon-reachable public `SECURITY DEFINER` views on prod. **29
same-class anon leaks remain OPEN and untouched** - including financial/operations views (`v_scope_financials`,
`v_projects_full`, `v_master_operations`, `v_tcc_*`). This packet does NOT materially close the project-wide anon
Data-API surface; those 29 are pre-existing and out of scope here. **Recommendation: a separate, higher-priority
definer-view-hardening packet** before the program's "62 public ERRORs -> 0" north-star is claimed.
