# How to Work with Desktop Claude - Session Protocol

## The Problem
- I have NO memory between sessions
- Long chats degrade my performance
- Reading many files wastes context window
- Hunting for information wastes your time

## The Solution
One file. Short sessions. Explicit handoffs.

---

## Starting a Session

### Option A: Fresh Chat (Recommended)
Copy-paste this into a new Claude.ai chat:

```
Read this file and confirm you understand the current state:
C:\RESA_Power_Build\.claude\STATE.md
```

I will:
1. Read the file
2. Summarize what I understand
3. Confirm the next action
4. Begin working

### Option B: Continue Existing Chat
If chat is under 40 messages, just say:
```
Let's continue. Current state is in .claude/STATE.md
```

---

## During a Session

### Optimal Session Length
| Messages | Status | Action |
|----------|--------|--------|
| 1-20 | 🟢 Optimal | Continue freely |
| 20-40 | 🟡 Good | Monitor, consider natural breakpoint |
| 40-50 | 🟠 Wrap up | Finish current task, update state |
| 50+ | 🔴 End | Save work, start fresh chat |

### Signs I'm Degrading
- I repeat something I said earlier
- I ask about something we already decided
- I forget a file I read earlier in the chat
- Responses become less focused

**If you see these:** End session, start fresh.

---

## Ending a Session

### Tell Me Explicitly
Say: "Let's wrap up this session"

### I Will:
1. Update `.claude/STATE.md` with:
   - What's complete
   - What's in progress
   - What's next
2. List all files I created/modified
3. Confirm ready for handoff

### You Verify:
- STATE.md looks correct
- Files exist where I said

---

## Handoff to VS Code Claude

### When Needed
- I complete a deliverable VS Code needs
- I'm blocked waiting for VS Code's work
- Natural phase boundary

### What I Provide
```markdown
## Handoff: Desktop → VS Code

**Completed:**
- file1.md - description
- file2.sql - description

**VS Code Should:**
1. Review [specific file]
2. Create [specific file]

**I'm Blocked On:**
- Nothing / [specific item]
```

### What You Do
1. Copy handoff summary to VS Code Claude
2. Or just tell them: "Check .claude/STATE.md"

---

## File Reading Rules

### Always Read First
`.claude/STATE.md` - 66 lines, has everything

### Only Read When Needed
| Doing This | Read These |
|------------|------------|
| Writing spec docs | Previous spec docs (for consistency) |
| Writing schema SQL | `spec/` folder docs |
| Writing test data | Schema SQL files + DATA_DICTIONARY |
| Reviewing | The specific file being reviewed |

### Never Read Unless Asked
- WORKSPACE_PROTOCOL.md (340 lines - too long)
- DECISIONS_LOG.md (historical reference only)
- Audit reports (already incorporated into specs)
- Old archived files

---

## Quick Commands

### "Resume"
```
Read .claude/STATE.md and continue where we left off.
```

### "Status"
```
Read .claude/STATE.md and summarize current state.
```

### "Wrap Up"
```
Update STATE.md and prepare for session end.
```

### "Handoff to VS Code"
```
Prepare handoff summary and update STATE.md.
```

---

## Anti-Patterns (Don't Do These)

❌ **Don't:** "Hey Claude, remember yesterday when we..."
→ I don't remember. Read the state file.

❌ **Don't:** Keep a chat going for 100+ messages
→ My quality degrades. Start fresh.

❌ **Don't:** Ask me to read 5 files before starting
→ Wastes context. STATE.md should be enough.

❌ **Don't:** Assume I know where files are
→ Give me paths. I can't guess.

❌ **Don't:** End session without updating state
→ Next session starts confused.

---

## Optimal Flow Example

```
SESSION 1 (Messages 1-35)
─────────────────────────
You: "Read .claude/STATE.md and begin spec creation"
Me: *reads file* "I see we're starting Phase 0. I'll create 
    spec/ folder and begin DATA_DICTIONARY.md"
... work happens ...
You: "Let's wrap up"
Me: *updates STATE.md* "Session complete. DATA_DICTIONARY 
    50% done. Next: finish tables and start ENUMS."

SESSION 2 (Fresh chat, Messages 1-30)
─────────────────────────
You: "Read .claude/STATE.md and continue"
Me: *reads file* "Continuing DATA_DICTIONARY from where 
    we left off. Tables remaining: pss_studies..."
... work happens ...
```

---

## Summary

| Rule | Why |
|------|-----|
| STATE.md first | One file = instant context |
| Under 50 messages | Quality degrades after |
| Explicit wrap-up | State saved properly |
| Fresh chats are good | Clean context = better work |
| Paths not names | I can't search, I need exact locations |

---

*This protocol optimizes for Claude's actual constraints.*
*Following it = faster, better results with less frustration.*
