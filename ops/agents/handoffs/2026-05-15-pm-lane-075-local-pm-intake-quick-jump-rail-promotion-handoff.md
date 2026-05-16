# PM Lane 075 Handoff - Local PM Intake Quick Jump Rail Promotion

Date: 2026-05-15
Status: Local-current implemented
Scope: Browser-local navigation placement for the Project Miner intake workbench

## Executive Summary

PM Lane 075 moves the existing `PM Intake Quick Jump Rail` near the top of `/pm-review/import-intake`.

The rail now appears immediately after the Project Miner intake summary cards and before the helper-panel stack:

1. command center,
2. meeting readout,
3. constraint radar,
4. daily review script,
5. start-here focus,
6. output selector,
7. handoff guide,
8. workflow map,
9. open-items lens.

The point is practical: the quick jump rail should be usable before Jason has to scroll through the entire helper stack. This tranche makes the existing navigation act like an entry point instead of another lower-page panel.

This is browser-local navigation placement only. It creates no new panel, export action, export artifact, handoff artifact, localStorage key, backend route, schema, approval record, task, issue, schedule, status, durable field record, production tracking row, hosted parity claim, or production write.

## What Changed

The workbench now includes:

1. `PM Intake Quick Jump Rail` immediately after the summary cards,
2. a stable `pm-quick-jump-rail` section id,
3. the same existing quick jump labels and links,
4. focused smoke coverage proving the rail appears once,
5. focused smoke coverage proving the rail is ordered before the command-center helper stack,
6. focused smoke coverage preserving exact read seams and zero mutation calls.

No quick jump target was removed. No new route, read seam, mutation seam, export button, export filename, storage key, or live service call was added.

## Sidecar Result

A read-only sidecar scout reviewed PM Lane 075 scope while implementation proceeded locally on the critical path.

The sidecar was instructed to:

1. review the current route and PM lane docs around Lanes 064 and 071-074,
2. compare quick-jump promotion against another export-context extension,
3. make no edits, stage no files, and access no external services,
4. return guardrails and smoke assertions for the recommended slice.

The sidecar independently recommended the same lane: promote the existing quick jump rail above the helper stack rather than adding another export-context extension. It also called out hosted parity as the stronger non-local alternative, but classified that as an authenticated executor lane rather than a small local PM workbench slice.

The sidecar made no edits, staged no files, committed nothing, pushed nothing, deployed nothing, ran no macros, and did not access Supabase, Render, Vercel, Olares, or live services.

## Validation

Commands are run from:

```text
C:/APEX Platform/apex-power-ops-platform
```

Operations-web typecheck:

```powershell
corepack pnpm --filter @apex/operations-web typecheck
```

Operations-web build:

```powershell
corepack pnpm --filter @apex/operations-web build
```

PM quick-jump promotion wording scan:

```powershell
rg -n "selected recipient|handoff created|assigned|scheduled|ready for execution|ready for field|field ready|field log of record|hosted parity proven|approval ready|packet admitted|daily report|tracking system|percent complete|released|cleared|approved|accepted|authorized|go/no-go passed|dispatch|dispatched|customer confirmed|JHA complete|LOTO approved|material released|issue created|task created|work order|production-ready" apps/operations-web/app/pm-review/import-intake/page.tsx apps/operations-web/tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Focused import-intake smoke:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Focused PM intake smoke suite:

```powershell
corepack pnpm --dir apps/operations-web exec playwright test tests/browser-shell.pm-import-candidate.smoke.spec.ts tests/browser-shell.pm-import-admission-plan.smoke.spec.ts tests/browser-shell.pm-import-approval-readiness.smoke.spec.ts tests/browser-shell.pm-import-intake.smoke.spec.ts
```

Packet JSON parse:

```powershell
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-15-pm-lane-075-local-pm-intake-quick-jump-rail-promotion.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. PM quick-jump promotion wording scan passed with no matches.
4. focused import-intake Playwright smoke passed with `1 passed`.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed with line-ending normalization warnings only.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. new localStorage keys,
3. new export actions,
4. new export artifacts,
5. new handoff artifacts,
6. new read seams,
7. mutation seam changes,
8. durable field records,
9. production tracking writes,
10. work authorization,
11. field release,
12. issue creation,
13. task creation,
14. live work order creation,
15. live task creation,
16. hosted parity claims,
17. SQL file creation,
18. SQL execution,
19. schema migration,
20. Supabase writes,
21. adapter implementation,
22. approval persistence,
23. import mutation,
24. live service calls,
25. Render redeploy,
26. Vercel promotion,
27. service creation,
28. DNS, auth, ingress, or secret changes,
29. fixture replay,
30. workbook macro execution,
31. workbook writeback,
32. assignment mutation,
33. schedule mutation,
34. status mutation,
35. autonomous AI business-state mutation.

## Next Recommended Move

After this navigation placement slice is validated, keep the next PM lane focused on either simplifying the visible workbench surface further or closing hosted parity through an authenticated executor. Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are explicitly accepted.
