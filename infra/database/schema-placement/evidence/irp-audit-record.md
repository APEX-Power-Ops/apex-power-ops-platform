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

## Round-2 re-audit (against `212fca7b`)

Same engines (Claude workflow `wf_4420a233-e48` + Codex `gpt-5.5` xhigh). Found **9 more** real
defects — several were narrow variations of the null-vacuity class, and one (over-broad compat SP012
exemption) was introduced BY the Round-1 correction. Codex proved the promote gap by executing a test.
All resolved on `212fca7b`'s successor commit:

| Finding (engine) | Resolution |
|------------------|-----------|
| promote + `has_consumers` + `compatibility_contract:null` false-greens (Codex, EXECUTED) | schema requires a real (type:object, required=true) compat for has_consumers promote; +neg |
| promote allows `exposure_policy:null` (Claude adversarial) | promote requires a non-null exposure posture; +neg |
| compat SP012-skip too broad — `target_schema:'evil'` passes (Codex + Claude, my Round-1 regression) | compat `target_schema` must equal `public`; +neg |
| manifest `required_observations: consumer_evidence` silently dropped (Codex) | enforced: every consumer dim observed/N-A when required; +neg |
| non-finite `max_staleness_hours`/`minimum_consumer_window_hours` (NaN/Inf) defeat SP008/SP009 (Codex) | SP015 rejects non-finite gate numbers; JSON loader rejects NaN/Inf; +neg |
| delete `recovery_proof` = empty file passes (Claude) | checker requires a NON-EMPTY resolved artifact; +neg |
| DSN `hostaddr` bypasses the host bind (Claude) | reject any DSN carrying `hostaddr`; +test |
| `FOR ALL TABLES` publications over-count views/matviews/foreign tables (Claude) | `pubs_all`/`pubs_schema` filtered to relkind r/p; PG16-proven (v_foo → 0 pub edges) |
| empty `--schemas` emits misleading empty census (Claude) | fail closed (exit 2) before any DB work; +test |
| stale committed bundle hash in the dev transcript (Codex) | dev transcript marked superseded; PG16 transcript records current bundle `065d49e0…` |

Regression-green under `uv.lock`: contract 51 / checker 47 / collector 29; PG16.13 re-validated.

## Outstanding — OPERATOR DECISIONS (design; not unilaterally changed)

1. **F1 — unsigned snapshot** (dominant residual): the offline checker cannot bind a snapshot to a
   genuine read-only census without a collector SIGNATURE or an explicit pipeline-integrity guarantee.
2. **Destructive-delete evidence floor:** SP022 lets the three compensating consumer dimensions
   (static_repo / runtime_logs / external_clients) each be waived via `not_applicable`, so a delete
   can green on database_deps(0) + operator_declaration alone. Decide how many dims must be *genuinely
   observed* for an irreversible delete.
3. **Evidence-file TOCTOU:** the gate validates `recovery_proof`/evidence files at CHECK time; the
   later apply reads them. Binding the validated bytes (a pinned checksum) ties into the F1 signing
   decision.
4. **compat consumer gate:** compat does not require a `consumer_disposition`, so SP022/SP013 never
   run for it (unlike archive, which forces `no_consumer`, and promote, which runs SP013). compat is
   additive (a public compat view) and now destination-pinned to `public`, so risk is low — but
   decide whether compat should require consumer evidence or at least an explicit conclusion.

## Verdict
Two adversarial cross-engine rounds drove 8 + 9 = 17 fixes with a negative test per reproduced
bypass and PG16 execution proofs. The remaining items (1–3) are design decisions, not code defects.
**Census GO, push, and PR remain HELD** pending the operator's ratification and those decisions.
Further code-only rounds show diminishing returns until F1 and the delete-floor policy are decided.
