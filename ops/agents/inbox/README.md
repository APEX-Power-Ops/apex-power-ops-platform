# Dispatch Inbox — executor self-serve queue

Routing queue for the APEX dev-residency multi-instance model. It removes the **operator-as-relay**: Desktop authors dispatches here; executors (CC, Codex, Cowork) drain their **own** inbox at session start instead of the operator copy-pasting each one.

Established 2026-05-29 (dispatch-delivery design). This is a lightweight routing layer — **separate** from `ops/agents/packets/` (the document archive). Do not entangle the two.

## Lifecycle — the directory IS the state
- `pending/` — dispatches awaiting an executor (the queue).
- `claimed/` — an executor has taken ownership (asserted by `git mv` + commit + **push**).
- `done/` — closed out (after the closeout handoff is written).

Transitions are `git mv` between these dirs, committed + pushed. **Git is the mutex:** if two executors claim the same file, the second's push is rejected (non-fast-forward) → it re-pulls and takes the next. First-push-wins; no locking code.

## Dispatch file format
`pending/<dispatch_id>.md`, where `<dispatch_id>` = `YYYY-MM-DD-<target>-<slug>` (stable, sortable). YAML frontmatter + the dispatch body:

```yaml
---
dispatch_id: 2026-05-29-cc-tcc-phase-e-tmt-emt-facets
target: CC            # CC | CODEX | COWORK   (single addressee; avoid ANY)
priority: 1           # lower = sooner; ordering is per-target
from: Desktop
created_at: 2026-05-29
authority: gated      # gated (operator "go" required) | autonomous-safe
predecessor: null     # <dispatch_id> this depends on, or null
closeout: ops/agents/handoffs/2026-05-29-<slug>-closeout.md
---
<dispatch body — the work instructions, i.e. what the operator pastes today>
```

`target` is the addressing primitive. Order within a target = `(priority asc, dispatch_id asc)` — deterministic, no clock dependence.

## Session-start self-serve protocol (every executor)
On session start, substitute your own `target` (CC | CODEX | COWORK) and run:
1. `git pull` this repo.
2. List `ops/agents/inbox/pending/*.md`; filter frontmatter `target == <me>`.
3. Sort by `(priority, dispatch_id)`; take the first. Respect `predecessor` — skip if its predecessor is not yet in `done/`.
4. Check visible prerequisites before claim. If the dispatch body requires an out-of-band dependency that is plainly absent on the current host or clone, do **not** claim it. Leave it in `pending/` and return a narrow status report to Desktop such as: `next dispatch is eligible by predecessor but not executable here because <prerequisite> is unmet`.
5. **Claim:** `git mv pending/<f> claimed/<f>`; commit `claim: <dispatch_id> by <me>`; **push**. If the push is rejected (someone claimed first) → `git pull`, drop that file, retry from step 2.
6. Execute the dispatch. Write the closeout to the `closeout:` path under `ops/agents/handoffs/`.
7. **Close:** `git mv claimed/<f> done/<f>`; commit `done: <dispatch_id>`; push.

**`authority: gated` is the default** — wait for the operator's explicit "go" before executing. Only `autonomous-safe` dispatches may run unattended (a later, not-yet-enabled phase).

## Unmet prerequisites
- If the blocker is visible **before claim**: leave the dispatch in `pending/`; do not create a claim commit just to discover the same blocker again.
- The expected response is a repo-truthful status note, not ad hoc replanning. Example: `E3 closed successfully. F is next in queue but remains pending because APEX_OLARES_LIVE_DSN is unset on this host.`
- This inbox currently has no `blocked/` state. Until one is explicitly added, avoid claiming work that is already known to be unexecutable from the current repo state or host environment.

## Per-executor notes
- **CC** (host-resident, Remote-SSH, this workspace): runs all 6 steps in its own clone — the inbox is inside the repo it already has open. No extra setup.
- **Codex Cloud** (origin-based): reads `pending/` from the workspace origin; claims by commit + push. (May be launch-seeded with the selected dispatch; the inbox semantics are identical.)
- **Cowork** (host SSH): runs against the host clone.

## Boundaries
- **This repo is PUBLIC.** Dispatch bodies must carry **no secrets/credentials** — redaction is the author's (Desktop's) job at author time. Any genuinely sensitive dispatch stays in the private `apex-ops-substrate` and reverts to manual relay (a known, bounded exception).
- Desktop authors/strategizes in the substrate; only the finished, addressed dispatch crosses into this inbox (Desktop holds both clones, so the boundary is crossed once at author time — not every time by the operator's clipboard).
