---
dispatch_id: 2026-05-30-cc-d012-relay-orm-hygiene
target: CC
priority: 2
from: Desktop
created_at: 2026-05-31
authority: gated
predecessor: 2026-05-30-cc-d012-orm-repoint
closeout: ops/agents/handoffs/2026-05-30-d012-relay-orm-hygiene-closeout.md
---

# Decision-012 — final hygiene: repoint the dead relay ORM models off the dropped `work.tcc_relay_*` names + zero-stale-refs sweep

**Lane:** Decision-012 close-out hygiene. **Not a live regression** — Desktop verified the live relay path (`/relay/plot-tcc`) works via raw SQL on `tcc.relay_*`, and the calc-engine relay ORM models (`packages/calc-engine/src/apex_calc_engine/models/relay.py`) are dead code (imported only as type annotations in `relay_dispatch.py`; no query caller). But they still **textually reference the dropped `work.tcc_relay_*` back-compat views** — a latent landmine if ever resurrected. This dispatch repoints them and proves **zero references to any retired name remain anywhere in active code**. **CODE-ONLY; reversible; no DB DDL.** Follow the inbox lifecycle (claim-push BEFORE editing).

## Scope
1. **`packages/calc-engine/src/apex_calc_engine/models/relay.py`** — repoint all 21 relay models the same way the ETU/breaker/TMT models were repointed:
   - `__tablename__ = 'tcc_relay_X'` → `__tablename__ = 'relay_X'` + `__table_args__ = {'schema': 'tcc'}` (merge if a tuple/dict already exists).
   - `ForeignKey('work.tcc_relay_X.col')` → `ForeignKey('tcc.relay_X.col')`.
   - Any `relationship()`/`primaryjoin`/`secondary` bare or `work.`-qualified old relay names → `tcc.relay_*`.
   - Confirm `relay_dispatch.py` still imports/type-checks cleanly after (it only uses these as annotations).
2. **Final zero-stale-refs sweep (report).** Across **active** code only — `apps/control-plane-api/{services,models,config.py,main.py}` and `packages/calc-engine/src` (EXCLUDE `migrations/`, `_archive/`, `__pycache__`, and historical one-off scripts) — grep for ANY remaining reference to:
   - the 60 dropped view names (`public.tcc_*` / `work.tcc_relay_*` qualified, and bare `tcc_*`/`tcc_relay*` in `__tablename__`/`ForeignKey`/raw SQL),
   - the 11 dropped tables.
   Expected after the relay repoint: **0** in active runtime code. List anything that remains with file:line + classification (live vs comment/docstring vs historical-script). Comments/docstrings → update for hygiene; historical `migrations/*.py` → leave (note them).

## Execute (gated)
1. **Claim** (`git mv` pending→claimed, push) BEFORE editing.
2. Repoint `models/relay.py`; run the sweep; fix any other live stragglers found.
3. **Local validation:** `configure_mappers()` with API + calc-engine models loaded together → PASS (relay mappers now resolve `tcc.relay_*`); run the calc-engine + relay test subset; report pass counts.
4. **Commit + push** (scoped `git add` of the repointed files + closeout). Render autodeploys.
5. **Post-deploy sanity (no regression):** relay parity probe 6/6; `GET /relay/sections` 200; `POST /relay/plot-tcc {"td_section_source_id":5075}` → 200 `status:"supported"` with a real curve; ETU parity 3/0 evaluate-warnings 0; breaker `catalog/status` 63/17831. Any FAIL → `git revert`, report.

## Guardrails
- **Code-only, hygiene.** No DB DDL, no view recreation. Schema-qualification only.
- Scoped `git add`. DSN out-of-band; no `.env*` contents.

## Closeout
Record: the `models/relay.py` repoint, the full zero-stale-refs sweep result (active code = 0 retired-name refs, with any comment/historical exceptions classified), local mapper-config + test results, commit hash, deploy confirmation, and the post-deploy sanity table. Then `git mv` claimed→done, commit, push, return to Desktop. **On PASS, Decision-012 is CLOSED — `tcc.*` is the sole TCC catalog and no active code references any retired name.**
