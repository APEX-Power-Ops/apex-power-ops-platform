# IRP Audit Record — disposition checker + collector

**Mode:** Audit · **Depth:** Deep · **Subject:** `check_disposition.py` + `collect_disposition.py`
+ `disposition.schema.json`, disposition-ledger lane. **Engines:** 4 Claude grounded probes +
adversarial regression pass (Workflow `irp-grounded-audit`, run `wf_5f47622e-512`) **and** Codex
`gpt-5.5` xhigh (`codex exec review --base main`, isolated detached worktree). This tool gates a
one-shot read-only PROD census + downstream irreversible schema moves, so the review prioritized
fail-closed behavior, value-silence, and false-green resistance.

## Round-1 audit (against `651c9d20`)

**Cross-engine delta:** Codex found the single most severe issue (the destructive-delete
null-vacuity) that all Claude probes missed; the Claude probes found the most systemic issue
(`found_consumers` counts edges not consumers) plus a cluster of enumeration/robustness gaps Codex
didn't reach. Complementary — neither engine alone was sufficient.

Findings, and their resolution in the correction commit that followed:

| # | Sev | Finding (engine) | Resolution |
|---|-----|------------------|-----------|
| 1 | Critical | `retention_disposition: null` (and retain/compat) pass the gate — JSON-Schema `required`/`properties` are vacuous on a null instance (Codex) | `type:object` added to delete/retain/compat then-clauses; +4 contract negatives |
| 2 | High | `found_consumers` counts EVERY edge incl. the relation's own seq/trigger/policy + outbound FKs (Claude ×3) | SQL `is_consumer` flag per edge; `found_consumers` counts consumers only; full inventory kept in `dependent_objects`; +2 collector tests; PG16-proven |
| 3 | High | `database_deps` can be set `not_applicable` to neutralize the machine signal (Claude adversarial) | checker requires `database_deps.state==observed` for a resolved conclusion; +1 negative |
| 4 | High | `target_objects` not bound to `target_schema`; compat lacked `target_schema` (Codex) | schema requires compat `target_schema`; checker SP025 binds every target_object's prefix; SP012 scoped to canonical promotion; +2 negatives |
| 5 | High | delete `recovery_proof` accepts a scheme token (`urn:`/`ta:`/`query:`) that skips file resolution — the delete baseline itself used `query:backup` (Codex) | checker requires a delete's `recovery_proof` to be a filesystem artifact under an approved root; +1 negative |
| 6 | High | project binding `ref in labels` accepts `db.<ref>.attacker.example` / pooler-user on any host (Claude/Codex) | strict anchor to `db.<ref>.supabase.co` OR `*.pooler.supabase.com`+`postgres.<ref>`; psycopg conninfo parser (URL + libpq keyword); +anchoring tests |
| 7 | Med | `FOR ALL TABLES`/schema-level publications + inheritance/partition children uncounted (Claude) | `pubs_all`/`pubs_schema`/`inherits_children` CTEs added; PG16-proven |
| 8 | Med | `write_snapshot` outside `main`'s try/except → uncaught traceback not fail-closed `2`; wrong-kind doc crashes checker (Claude) | write wrapped → exit 2; checker validates each doc's `kind` (SP001); +2 tests |

All resolved under `uv.lock`: contract 49 / checker 43 / collector 28, plus PG16.13 catalog SQL
execution proof (`evidence/pg16-sql-validation-2026-07-11.md`).

## Outstanding — for operator decision (NOT in the ratified tranche)

**F1 (High, design): the checker trusts a self-attested, UNSIGNED snapshot.** `guard_passed`,
`transaction_read_only`, `project_ref`, and the entire `consumer_evidence` block are plain writable
JSON; `query_bundle_sha256` hashes only the SQL text; SP024 only string-compares `project_ref` to a
value the operator also supplies. So a hand-authored snapshot with `guard_passed:true` and fabricated
evidence validates and can carry a delete/archive GREEN. The offline checker fundamentally cannot
verify a snapshot was produced by a genuine read-only census without either (a) the collector SIGNING
the snapshot (HMAC/detached signature the checker verifies), or (b) an explicit pipeline-integrity
guarantee that the checker only ever ingests the collector's own immutable output. This is out of
band from the three files and was surfaced by the Round-1 re-audit; it is a design call, not silently
implemented. **Recommendation:** decide (a) vs (b) before the checker is trusted to authorize a
destructive action; it does not block the read-only census GO itself.

## Verdict
Round-1 correction closes findings 1–8 with adversarial negatives per bypass and a PG16 execution
proof. The census GO, push, and PR remain HELD pending the operator's ratification and the F1
decision. A Round-2 re-audit (Codex + Claude) runs against the correction commit before any census.
