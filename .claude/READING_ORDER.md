# READING_ORDER.md

Boot sequence for any AI executor or human entering this repo. Read in the order listed.

1. `apex-power-ops-platform/REPO_PASSPORT.md` — front-door contract (12 sections).
2. `apex-power-ops-platform/.claude/MASTER.md` — repo-scope authority and per-repo declarations.
3. Authority docs declared in passport §3 "Authority order" — read in declared order. Anchor: `docs/authority/README.md` Strategic Authority Order.
4. `apex-power-ops-platform/ops/agents/packets/active/` — currently in-flight packets.
5. `apex-power-ops-platform/ops/agents/packets/blocked/` — currently blocked packets.
6. Most recent `apex-power-ops-platform/ops/agents/handoffs/<latest>-handoff.md` — most recent closeout.
7. `apex-power-ops-platform/.claude/PLATFORM/PROTOCOLS_AND_NOMENCLATURE.md` — framework conventions (this repo IS the canonical platform substrate; framework lives at `.claude/PLATFORM/`).

If a required surface is absent, record that truthfully in the repo passport current frontier or the packet handoff. Do not invent maturity.
