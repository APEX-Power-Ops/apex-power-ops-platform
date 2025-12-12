# Coordination System - Decision Document

**Created:** 2025-12-11
**Purpose:** Synthesize both Claude proposals, present options, decide together
**Stakeholders:** Jason, Desktop Claude, VS Code Claude

---

## What We Learned: Capability Reality Check

**Big Discovery:** Desktop Claude was wrong about its own limitations.

| Capability | Desktop Assumed | Desktop Actual | VS Code Actual |
|------------|-----------------|----------------|----------------|
| Supabase MCP | ✅ | ✅ | ✅ |
| File system | ✅ | ✅ | ✅ |
| Git (command line) | ⚠️ Uncertain | ✅ Works | ✅ Works |
| Memory MCP | ❌ "Don't have" | ✅ **Has it** (10 entities, project history since Nov) | ✅ Has it |
| GitHub MCP | ❌ | ❌ | ✅ (push, PRs) |
| Run localhost | ❌ | ❌ | ✅ (Simple Browser) |
| View browser | ❌ | ❌ | ⚠️ Limited (Simple Browser) |

**Key Insight:** The only real capability difference is VS Code can run the dev server and view localhost. Everything else is parity. Task split should be about **workflow context**, not capability limitations.

---

## The Core Problem We're Solving

1. **Documentation drift** - STATE.md claimed "28 NETA sections pending" when database had 100% complete (66 procedures, 956 test items)
2. **File sprawl** - 19 files in `.claude/` with overlapping/conflicting purposes
3. **No verification loop** - Claims weren't checked against reality
4. **Jason as bottleneck** - Manual relay between Claude instances
5. **Session context loss** - Each session starts confused

---

## Two Proposals: Side by Side

### Structure

| Aspect | Desktop Proposal | VS Code Proposal |
|--------|------------------|------------------|
| Primary state file | `STATE.md` (Markdown) | `SYNC_STATUS.yaml` (YAML) |
| Session history | Inline "Recent Activity" section | Separate `SESSION_LOG.md` |
| Handoffs | Inline "Pending Decisions" | Separate `HANDOFFS/TO_*.md` |
| Pending decisions | Inline section | Separate `DECISIONS/PENDING.md` |
| Schema tracking | Database verification | Auto-generated `SCHEMAS/current_schema.sql` |
| Archive strategy | Move to `_archive/` | Same |

### Change Management

| Level | Desktop Model | VS Code Model |
|-------|--------------|---------------|
| No coordination | "Non-breaking" | Level 0: Independent |
| Light coordination | (not distinguished) | Level 1: Notify (update after) |
| Medium coordination | (not distinguished) | Level 2: Announce (update before AND after) |
| Full coordination | "Blocking" | Level 3: Coordinate (handoff required) |

### Verification Philosophy

| | Desktop | VS Code |
|-|---------|---------|
| Core principle | Trust but verify | Query-first approach |
| Who owns truth | Claude with verification capability | Same |
| Stale threshold | Implicit | Explicit: >24 hours = re-verify |

---

## Key Decisions Needed

### Decision 1: File Format

**Option A: Markdown** (Desktop preference)
- Pros: Human-readable, easy to edit, no syntax errors, works in GitHub preview
- Cons: No machine parsing if we ever build tooling

**Option B: YAML** (VS Code preference)  
- Pros: Machine-parseable, structured, future tooling ready
- Cons: Syntax errors possible, less readable in chat

**Option C: Markdown with YAML frontmatter**
- Pros: Best of both - human-readable body, structured header
- Cons: More complex to maintain

**My recommendation:** Start with Markdown. We're not building tooling yet. Revisit if that changes.

---

### Decision 2: Separation vs. Consolidation

**Option A: One file does everything** (Desktop preference)
```
.claude/
├── STATE.md           # Everything in one place
├── PROTOCOL.md        # How we work (static)
└── _archive/          # Old stuff
```

**Option B: Specialized files** (VS Code preference)
```
.claude/
├── SYNC.md            # Current state only
├── SESSION_LOG.md     # Append-only history
├── HANDOFFS/
│   ├── TO_DESKTOP.md
│   └── TO_VSCODE.md
├── DECISIONS/
│   └── PENDING.md
└── _archive/
```

**Tradeoffs:**
- Option A: Simpler, everything in one place, but file grows forever
- Option B: Clear separation, can archive/delete handoffs after processing, but more files to check

**My recommendation:** Option B is better. The handoff inbox model (TO_DESKTOP.md, TO_VSCODE.md) is cleaner than inline sections. Each Claude reads their inbox, processes it, clears it.

---

### Decision 3: Change Level Granularity

**Option A: Binary** (Desktop original)
- Blocking (requires coordination)
- Non-blocking (proceed freely)

**Option B: Four Tiers** (VS Code proposal, Desktop conceded this is better)
- Level 0: Independent - no coordination needed
- Level 1: Notify - update SYNC after
- Level 2: Announce - update SYNC before AND after  
- Level 3: Coordinate - explicit handoff required

**My recommendation:** Four tiers. The distinction between "update after" and "update before AND after" prevents surprises without requiring full coordination for everything.

---

### Decision 4: Ownership Model

**Option A: By Capability**
- Desktop owns: Database, schema, migrations
- VS Code owns: Application code, UI, testing

**Option B: By Workflow Context**
- Desktop owns: Strategic/exploratory, documentation, Jason-facing discussions
- VS Code owns: Code implementation, IDE work, localhost verification

**Option C: Hybrid**
- Desktop: Schema design, architecture docs, specs, Jason strategy sessions
- VS Code: Application code, UI, integration testing, GitHub pushes
- Shared: Test data, coordination files

**Reality check:** Both have Supabase MCP. Both can write SQL. Both can edit files. Ownership isn't about who CAN do something—it's about who SHOULD to avoid duplication.

**My recommendation:** Option C (Hybrid) with this principle: **"If you're working in the IDE, you own it. If you're in a strategy conversation with Jason, you own it."**

---

### Decision 5: What to Archive

Current `.claude/` contents (19 files) need triage:

**Definitely Archive:**
- `COORDINATION.md` - severely stale (claims 0 NETA rows)
- `OPEN_DECISIONS.md` - if stale
- `SUPABASE_SWAP_GUIDE.md` - if swap is complete
- Old session summaries
- Duplicate/overlapping docs

**Keep (restructured):**
- State information → new `SYNC.md`
- Protocol information → `PROTOCOL.md`
- Current handoffs → `HANDOFFS/`

**Delete (don't even archive):**
- Files that are 100% superseded with no historical value

**My recommendation:** Do the archive now. Move everything except the new structure to `_archive/Dec2025_coordination_cleanup/`. Start clean.

---

## Proposed Final Structure

Based on synthesizing both proposals:

```
.claude/
├── SYNC.md                  # Primary state (who reads: EVERYONE, FIRST)
├── SESSION_LOG.md           # Append-only history (who maintains: BOTH)
├── PROTOCOL.md              # How we work (who maintains: rarely changes)
├── HANDOFFS/
│   ├── TO_DESKTOP.md        # Desktop's inbox (who maintains: VS Code writes, Desktop reads)
│   └── TO_VSCODE.md         # VS Code's inbox (who maintains: Desktop writes, VS Code reads)
├── DECISIONS/
│   └── PENDING.md           # Questions needing resolution (who maintains: BOTH)
└── _archive/                # Historical files
```

---

## Proposed Session Protocol

### Session Start (Both Claudes)
1. Read `SYNC.md`
2. Read your `HANDOFFS/TO_[YOU].md` inbox
3. Check `DECISIONS/PENDING.md` for items needing your input
4. Verify one database fact to confirm SYNC accuracy
5. Proceed with work

### Session End (Both Claudes)
1. Update `SYNC.md` with any state changes
2. Write to other Claude's inbox if handing off work
3. Append to `SESSION_LOG.md` with session summary
4. Clear your processed inbox items
5. Respond to any `DECISIONS/PENDING.md` items you can address

### Change Levels

| Level | When | Action Required |
|-------|------|-----------------|
| 0 - Independent | Reading, isolated new files | None |
| 1 - Notify | New components, test data, docs | Update SYNC.md after |
| 2 - Announce | API changes, reference data | Update SYNC.md before AND after |
| 3 - Coordinate | Schema DDL, breaking changes, deletes | Handoff + wait for confirmation |

---

## Questions for Jason

1. **File format:** Markdown (simple) or YAML (structured)? I recommend Markdown.

2. **Structure:** One mega-file or specialized files with handoff inboxes? I recommend specialized.

3. **Archive now?** Should I clean up the 19 existing files immediately? I recommend yes.

4. **Change levels:** Accept the four-tier model or simplify to two?

5. **Anything missing?** What coordination problems have we not addressed?

---

## Next Steps (After Your Input)

1. Archive old `.claude/` files to `_archive/Dec2025_coordination_cleanup/`
2. Create new file structure (SYNC.md, SESSION_LOG.md, PROTOCOL.md, HANDOFFS/)
3. Populate SYNC.md with verified current state (I'll query database)
4. Write PROTOCOL.md documenting the agreed system
5. Update Memory MCP with coordination system decision
6. Start using it

---

**Ready for your input, Jason.**
