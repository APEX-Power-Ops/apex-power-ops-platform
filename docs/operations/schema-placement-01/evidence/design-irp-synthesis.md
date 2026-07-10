# IRP Synthesis - Schema-Placement Packet 01 (Audit / Deep / cross-engine)

Date: 2026-07-10. Substrate: prod fxoyniqnrlkxfligbxmg. Artifact: 2026-07-10-schema-placement-01-public-lockdown-design.md (DRAFT).
Engines: Claude IRP grounded-audit (8 agents, 6 probes + adversarial refute + verdict; ~880k tokens, 112 tool calls, prod+repo grounded) + Codex cross-engine (codex exec, repo-grounded) + controller prod grounding.
Raw memos: Codex -> host /tmp/codex_sp01_out.md ; Claude -> tasks/w7s88icsa.output.

## VERDICT: BLOCK as written. Unanimous re-scope.
The clean first slice collapses from 28 objects to exactly 2 inert scratch tables. Every other in-scope
cluster carries a live consumer / structural coupling the no-choreography SET SCHEMA mechanism breaks.

## Convergence (all three engines)
- mcp_* is a LIVE control-plane-api backend (schema-qualified public.mcp_* direct SQL) -> SET SCHEMA breaks prod.
- ai_* is wired to 10 anon/authenticated-EXECUTE SECURITY INVOKER RPC functions -> moving it breaks a live RPC surface.
- tcc_*_pre_rebuild is NOT "dead archive": kept tcc_test_plans has 8 inbound FKs into it (repo marks pre_rebuild must_keep).
- The urgent, complete, NON-breaking security fix is revoke + definer-view neutralization, which needs NO schema move.
- Only _009_rollback_snapshot + _phase3_load_manifest are cleanly relocatable now.

## CRITICAL findings
- C1 ai_* RPC break: 10 funcs (create_task/claim_task/handoff_task/...) prosecdef=false, proconfig=NULL, reference
  ai_* UNQUALIFIED, anon+authenticated EXECUTE. SET SCHEMA -> runtime resolution failure. BOTH spec safety nets blind:
  pg_depend does not record function-body->table refs; app-grep finds no callsites (callers are runtime agents via anon key).
- C2 ai_tasks trigger break (Claude-unique, adversarial): trigger ai_tasks_status_logged -> log_task_status_change()
  INSERTs ai_task_history UNQUALIFIED, no search_path pin. Moving ai_tasks breaks writes for EVERY caller incl.
  privileged/service_role/bypassrls. Defeats "relocate but keep working for privileged connection."
- C3 mcp_* live backend: RW public.mcp_* across queue.py:61 / sync.py:135,207,218 / worker.py ~493-930 /
  router.py (incl. reads mcp_task_packet_summary_v:690, mcp_job_run_summary_v:1254); check_schema_drift.py expects
  them in public; CREATE TABLE IF NOT EXISTS public.mcp_* bootstrap (Codex) would RECREATE empty shells post-move.
- C4 atomicity illusion (Claude-unique): mcp_* is 5 pg_depend components (only intra FK job_runs->local_action_queue),
  each a separate write-GO, but the app spans all 5 in single code paths -> the FIRST component move already breaks the
  app; plus SET SCHEMA takes ACCESS EXCLUSIVE contending with the live writer.

## HIGH findings
- Ha mcp_* is a revoke/view problem, not placement: RLS ON on all 6, no policy admits anon; SOLE anon leak = the 2
  SECURITY DEFINER summary views. Minimal fix = neutralize the 2 views (revoke anon SELECT or -> security_invoker) + revoke grants.
- Hb authenticated over-read: authenticated can read mcp_task_packets/review_decisions/validation_artifacts/lane_priorities (role policies).
- Hc Bucket-2 premise false: tcc_test_plans (kept, must_keep, 0 rows) 8 inbound FKs into pre_rebuild -> relocating to
  a schema named `archive` while a kept table depends on it is incoherent + blocks any future archive DROP.
- Hd scope/metric dishonesty: 28 -> 2 clean. Section 8 "no Data-API consumer broken" is technically-true-but-misleading:
  the breaking consumers are direct-SQL (mcp) + anon-RPC (ai), not the Data API.
- He residual anon RPC + oracle blindness: the 10 anon-EXECUTE INVOKER funcs are a live anon read+WRITE RPC surface
  the plan never revokes; advisor's definer-function lint does not catch invoker funcs; Section 9 oracle has no /rpc/ probe.

## MEDIUM (spec-quality) findings
- M1 6.3 defaults the 2 mcp summary views to DROP but router.py READS both -> invert the lean (moot if mcp_* pulled).
- M3 open-Q3 logic inverted (direct-SQL is what breaks, not PostgREST). M4 mcp_* mislabeled RLS-off (they are RLS-ON).
- M5 ALTER DEFAULT PRIVILEGES on a fresh schema is a no-op (revokes never-granted privs); durable backstop = keep schema
  off exposed list + per-object REVOKE. M6 moved objects RETAIN anon relacl through SET SCHEMA -> per-object REVOKE is
  LOAD-BEARING (incl. views), not defense-in-depth. M7 dropped-view rollback via pg_get_viewdef omits owner/reloptions/relacl.

## Affirmed SOUND (do not over-correct)
- SET SCHEMA is metadata-only -> no scale risk on the 100k-row tcc tables. View-dependency closure complete.
  Kept-definer re-leak vector empty IF all in-scope views move atomically with their bases. Non-super postgres owns all
  28 + createrole/bypassrls/db-owner (capability holds; execute the DDL probe in P0). Cleared: no publication membership,
  no pg_cron, no other DB-internal function consumer, full inbound-FK sweep done. The 2 scratch tables are fully inert.

## Cross-engine delta
- Codex-unique: CREATE TABLE IF NOT EXISTS public.mcp_* bootstrap re-creates empty shells post-move; must_keep migration marker.
- Claude-unique: C2 trigger break; C4 5-components atomicity illusion; ADP no-op + per-object-REVOKE load-bearing (M5/M6);
  rollback capture omits owner/reloptions/relacl (M7); oracle needs NOTIFY pgrst reload + /rpc probe; mcp_* RLS-ON correction.
- Controller-grounding-unique: ai_knowledge is a clean orphan (0 dep refs, 0 rows) -> candidate 3rd safe relocate object;
  all 10 ai_* funcs confirmed anon+authenticated EXECUTE.

## Unverified / decisive unknowns (settle before P1)
1. Do agents actually invoke the 10 ai_* RPCs at runtime via the anon/authenticated key? Callers live outside the repo;
   grep cannot prove them dead; anon+auth EXECUTE strongly implies an intended external caller. MOST decisive.
2. control-plane-api's DB connection role (inferred privileged non-anon; not DSN-verified - value-silent).
3. CREATE SCHEMA / ALTER DEFAULT PRIVILEGES execution for non-super postgres (capability affirmed via pg_roles, not executed).
4. tcc_test_plans / tcc_test_results live-vs-dead (operator/product call; both 0 rows, zero repo refs).

## Operator decisions to surface (leans)
1. Re-scope packet 01 -> (01a) relocate 2 inert scratch tables to `archive` (+ ai_knowledge iff P0 confirms no writer);
   (01b) separate revoke-only + definer-view-neutralization hardening pass over the exposed clusters, NO schema moves;
   defer mcp_* / ai_* / tcc_pre_rebuild to choreographed packets. LEAN: strongly yes (unanimous).
2. Make revoke-hardening the PRIMARY urgent security fix (not belt-and-suspenders). LEAN: yes.
3. Before any ai_* work: settle unknown #1 + require search_path pin / schema-qualification on log_task_status_change. LEAN: yes.
4. Settle tcc_test_plans/tcc_test_results disposition BEFORE touching pre_rebuild. LEAN: decide first.
5. Fix spec framing + oracle: re-characterize exposure as read+write+RPC; add /rpc/ probe + has_function_privilege('anon',
   ...,'EXECUTE')=false assert + NOTIFY pgrst reload; relabel mcp_* RLS-on; soften ADP claim; promote per-object REVOKE to
   load-bearing (incl. views); extend rollback capture to owner+reloptions+relacl. LEAN: yes.
