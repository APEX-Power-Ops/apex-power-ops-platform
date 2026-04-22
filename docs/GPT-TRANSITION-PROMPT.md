# GPT Transition Prompt

Use this as a copy/paste session starter for a GPT instance working in the Apex Power Ops platform repo.

```text
You are working in the Apex Power Ops platform bootstrap repository.

Operating rules:
- Treat C:/APEX Platform/apex-power-ops-platform as the primary implementation root.
- Treat C:/APEX Platform/Platform-Authority as the strategic authority lane above the repo.
- Treat sibling source-domain repos under C:/APEX Platform/source-domains/ as bounded lineage and extraction lanes, not equal primary workspaces.

Current sibling source-domain paths:
- C:/APEX Platform/source-domains/tcc_v5_backend
- C:/APEX Platform/source-domains/neta-ett-study-material
- C:/APEX Platform/source-domains/neta-forms

When starting work:
1. Read AGENTS.md in the repo root.
2. Read README.md.
3. Read docs/OPERATOR-BOOTSTRAP-RUNBOOK.md.
4. Read docs/authority/ for current in-repo authority.
5. If the task depends on unre-homed source material, inspect the matching sibling source-domain repo under ../source-domains/.

Execution rules:
- Default to making changes in the platform repo when a target lane already exists here.
- Do not treat older source repos as equal peers unless the slice has not been re-homed yet.
- Do not import whole repos wholesale; move only bounded approved slices.
- Keep archive-heavy, binary-heavy, and lineage-only material out of active paths unless explicitly needed.
- Prefer the platform-local environment at C:/APEX Platform/apex-power-ops-platform/.venv.

When reporting status:
- Distinguish clearly between active platform paths and source-domain paths.
- Call out any stale path assumptions or older workspace conventions if they appear.

If there is ambiguity about where work belongs, prefer the platform repo first, then confirm against Platform-Authority before editing sibling source repos.
```

## Intended Use

This prompt is for session transition and fast orientation.

It is not a replacement for:
- `AGENTS.md`
- `README.md`
- `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`
- strategic authority in `C:/APEX Platform/Platform-Authority/`