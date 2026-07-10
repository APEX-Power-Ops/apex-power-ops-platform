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

`evidence/updownup_proof.txt` - a faithful mini-prod fixture on a throwaway **PostgreSQL 16** database (disposable
`postgres:16-alpine`, matching prod's major; the pre-HOLD run used PG17/`apex-dev-pg`), covering: forward apply of
A1/A2/A3 (in-migration asserts pass); post-state (anon+authenticated no privilege on all verbs; 8 authenticated
policies dropped, 6 service_all retained; 6 comments read RETIRED; 2 scratch tables relocated to `archive` and
de-exposed; **`archive` schema postgres-owned + anon/auth no USAGE**; `apex_tcc_runtime` grants unchanged); rollback
restoring a **tracked-object fingerprint match** - NOT a complete database-state restore: the now-empty `archive`
schema, its comment, and its default-privilege grants intentionally survive rollback (A3 rollback does not
`DROP SCHEMA archive`) and are out of the tracked-object fingerprint scope; re-apply (up-down-UP idempotency); the
7-table variant (guarded `mcp_external_action_audits`), where the rollback deliberately leaves the born-exposed 7th
table **HARDENED (fail-closed)** rather than re-exposing it - so the only baseline<->restored fingerprint delta is
exactly that table's ACL, and the governed 6+2 surface round-trips exactly; and a NEGATIVE atomicity case (a
membership leak makes an A1 assert fail -> the whole action rolls back with no partial state). Harness + fixture:
`evidence/tests/` (the harness resolves every input by absolute path from its own location - runnable from any cwd,
container overridable via `SP01_PGC`). Harness `shellcheck -s sh` = rc 0.

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

## 7. Delta review (post-HOLD verdict, 2026-07-10)

A focused final review of `10cc549b` returned **HOLD merge** with 6 findings (3 High, 3 Medium). All six are folded
into this delta; every finding was accepted on the merits (none over-ruled). Independent of the two prior IRP passes,
the reviewer also re-ran all three up/down/up cases and applied A1/A2/A3 directly against a disposable PG16 container
(`auth policies=0 . archive move=true . anon SELECT=false`), confirming the forward SQL is runtime-correct for the
modeled 6+2 prod shape; that stands.

| HOLD finding | Fix (this delta) | Evidence |
| --- | --- | --- |
| **HOLD-F1 (High)** drift guard promised in design (1b.4) but absent from the diff | New import-safe pure evaluator `apps/control-plane-api/scripts/schema_drift_acl.py` + `check_schema_drift.py` now runs 3 live queries: (a) a boundary marker (the 6 core tables' RETIRED-01b-auth comment), (b) the anon/authenticated `has_table_privilege` matrix over the 6 tables + 2 views (+ guarded 7th), (c) the public SECURITY DEFINER mcp-view scan. The anon/auth no-privilege assertion is enforced ONLY once the boundary is applied (so it does not false-alarm during the merge->apply window); the 1b.5 definer-view allowlist (exactly the 2 summary views; count in {0,2}) is a standing invariant. **1b.4 + 1b.5 = DELIVERED.** | `tests/test_schema_drift_acl.py` (12 pass: leak detection, boundary gating, allowlist); live PG16 validation of all 3 queries -> pre-apply `boundary_applied=f, leaks=64` (reported, NOT failed - correct), post-apply `boundary_applied=t, leaks=0`, definer views = exactly the 2 accepted. |
| **HOLD-F2 (High)** committed harness referenced 6 uncommitted aliases (`000012_A1.sql`, ...); reviewer had to symlink | `run_updownup_test.sh` now resolves `SCRIPT_DIR`/`REPO_ROOT` from its own location and maps every action to its real canonical migration path; scratch output goes to a `mktemp` dir; a preflight fails fast on any missing input or unreachable container; container overridable via `SP01_PGC`. | Re-run from the tests dir with zero manual setup -> `=== UPDOWNUP: ALL PASS ===` (RC 0). CI still covers syntax-compile only (unchanged); an automated PG16 harness job is named as a follow-on, not folded here (broader control-plane-CI change). |
| **HOLD-F3 (High)** guarded 7th-table `GRANT ALL` in A1/A2 rollbacks could over-grant / re-expose if the table is created after apply | Removed the speculative `to_regclass`-guarded 7th-table re-grant from BOTH rollbacks. Rollback now restores only the 6+2 objects the forward migration actually revoked. On a substrate where the 7th exists and was hardened, rollback leaves it hardened (fail-closed) - it can never re-expose. | CASE 2: "guarded 7th STAYS hardened (0/8) after down [fail-closed]"; the only baseline<->restored fingerprint delta is exactly the 16 7th-table ACL lines. |
| **HOLD-F4 (Medium)** `git diff --check` failed (trailing whitespace + EOF blanks in the 2 Codex memos) | Stripped per-line trailing whitespace + normalized EOF to a single newline in `codex-design-audit.md` and `codex-sql-audit.md`. | `git diff <base>...HEAD --check` clean after commit. |
| **HOLD-F5 (Medium)** "byte-identical" overstated (excludes the surviving `archive` schema/comment/default-privs) | Reworded section 5 above + harness `ok` messages to "tracked-object fingerprint match", and named the intentional schema-level residue explicitly. | Section 5; harness case1/case2 messages. |
| **HOLD-F6 (Medium)** A3 asserted table privileges but not schema posture | A3 assert block now also checks `archive` is postgres-owned and anon/authenticated hold no effective USAGE/CREATE (`::text`-safe appends, avoiding the malformed-array-literal class from section 5). | A3 migration assert; harness post_up_checks: "archive schema postgres-owned + anon/auth NO USAGE (A3 schema posture) = t". |

**Reconciliation note (disclosed):** a concurrent operator edit (VS Code Remote-SSH on the host) had independently
fixed the same six findings. Per operator direction the two fix-sets were reconciled **best-of-both**: the operator's
stronger elements were adopted - the drift checker's boundary-applied gating + the 1b.5 definer-view allowlist
(check_schema_drift.py), A3's explicit `ALTER SCHEMA archive OWNER TO postgres` (better F6 idempotency than a bare
`CREATE ... AUTHORIZATION`), and the A1/A2-rollback operator `RAISE NOTICE` hints; refactored to keep the ACL/allowlist
logic in the import-safe, unit-tested `schema_drift_acl.py`. The shellcheck-clean self-contained harness (with the
`delta-is-exactly-the-7th` assertion) and the disposable-DB PG16 proof are retained.

**Delta review limitation (disclosed):** this delta was authored + self-verified (12 unit tests + the disposable-DB
PG16 up/down/up proof + the 3-query live drift validation + shellcheck rc0 + compileall); it has not been put through a
fresh independent cross-engine (Codex) pass. The changes are additive/mechanical over an already dual-IRP'd base, and
the operator's standing gate holds: **all production writes remain HELD** pending explicit per-action write-GO.
Production authority still attaches to the reviewed, committed bytes at the new SHA.
