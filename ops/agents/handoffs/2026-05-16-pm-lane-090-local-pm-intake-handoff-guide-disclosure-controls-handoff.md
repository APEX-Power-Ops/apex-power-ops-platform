# PM Lane 090 Handoff - Local PM Intake Handoff Guide Disclosure Controls

Date: 2026-05-16
Status: Local-current implemented
Scope: Browser-local default-open disclosure control for the existing `/pm-review/import-intake` Local PM Intake Handoff Guide panel

## Executive Summary

PM Lane 090 wraps the existing `#pm-handoff-guide` / `Local PM intake handoff guide` panel in a native default-open disclosure control.

The affected guide items are preserved:

1. Jason local review,
2. Field conversation prep,
3. Bounded executor context,
4. Hosted parity executor boundary,
5. Future approval-persistence packet boundary.

This gives Jason a browser-native way to fold the next-context AI/orchestration guide after reviewing it. It does not persist collapsed state.

It preserves the existing panel id, aria label, placement inside Daily Action Panels, five derived items, labels, hrefs, order, status pills, dynamic text, no-storage behavior, no-authority wording, read seam, and storage boundary.

It does not add a new route, link, target, output, export action, export artifact, export contract, local storage key, backend route, hosted proof, approval record, import mutation, task, issue, field record, or production write.

## Why This Lane

PM Lane 084 added default-open disclosure controls to the detail workbench.

PM Lane 085 applied the same pattern to the helper-panel stack.

PM Lane 086 applied the pattern to the top output action rail.

PM Lane 087 applied the pattern to the quick-jump rail.

PM Lane 088 applied the pattern to the conditional output status rail.

PM Lane 089 applied the pattern to the route-link rail.

PM Lane 090 applies the pattern to only the handoff-guide panel so next-context AI/orchestration guidance remains available by default but can be folded after review.

## Sidecar Result

A read-only sidecar from PM Lane 089 recommended PM Lane 090 as the next local slice after the route-link disclosure pattern landed. The recommendation was accepted with a narrow boundary:

1. wrap only the existing `#pm-handoff-guide` / `Local PM intake handoff guide` panel,
2. keep the disclosure control default-open,
3. do not persist collapsed/open state,
4. keep the guide inside Daily Action Panels,
5. preserve the five derived guide items, labels, hrefs, order, status pills, dynamic text, no-storage behavior, and no-authority wording,
6. preserve route links, quick-jump links, output actions, output statuses, output selector, helper/detail disclosures, reads, storage, hosted posture, and mutation behavior,
7. preserve PM Lane 083's no-implied-authority smoke guard,
8. leave PM Lane 084 detail, PM Lane 085 helper, PM Lane 086 output-action, PM Lane 087 quick-jump, PM Lane 088 output-status, and PM Lane 089 route-link controls untouched.

A separate read-only sidecar completed a PM Lane 091 scout and has no write ownership in this tranche.

The returned recommendation is:

`Project Miner Local PM Intake Workflow Map Disclosure Controls`

That next lane should wrap only the existing `#pm-workflow-map` / `Local PM Intake Workflow Map` panel in `/pm-review/import-intake` as a default-open native disclosure. It should preserve the seven derived workflow-map items, labels, hrefs, order, status pills, dynamic text, no-storage behavior, no-authority wording, and placement inside Workflow Review Panels; prove default-open, collapse/reopen behavior, hidden/visible workflow-map rows, unchanged link counts and hrefs, and no collapse/disclosure/workflow-map localStorage key; and avoid PM Lane 090 handoff-guide edits, Daily Action Panels grouping changes, open-items lens changes, route links, quick-jump changes, output-action changes, output-status changes, exports, storage, read, backend, approval, import, task, assignment, schedule, status, hosted, Supabase, Render, Vercel, SQL, schema, production, or AI business-state changes.

## What Changed

Operations-web:

1. converts the Local PM Intake Handoff Guide panel wrapper to a native `details open` wrapper,
2. keeps the existing `pm-handoff-guide` id and `Local PM intake handoff guide` aria label on the wrapper,
3. keeps the existing heading and browser-local pill in the `summary`,
4. nests the existing guide cards inside `Local PM intake handoff guide items`,
5. leaves the existing guide item labels, hrefs, order, status pills, dynamic text, no-storage/no-authority wording, storage keys, output actions, output statuses, route links, quick-jump links, helper disclosures, detail disclosures, and read seams unchanged,
6. adds no JavaScript state and no persisted collapsed state.

Focused smoke:

1. asserts the handoff-guide disclosure is open by default,
2. verifies the existing five child guide links and hrefs,
3. collapses and reopens the guide,
4. proves the guide items hide and return with native disclosure behavior,
5. proves no `pm-import-intake-*` localStorage key containing collapse, disclosure, or handoff-guide state is created,
6. preserves every existing guide dynamic-text assertion,
7. preserves PM Lane 083's no-implied-authority control and wording guard,
8. preserves PM Lane 084 detail, PM Lane 085 helper, PM Lane 086 output-action, PM Lane 087 quick-jump, PM Lane 088 output-status, and PM Lane 089 route-link disclosure coverage.

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

Authority wording scan:

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-090-local-pm-intake-handoff-guide-disclosure-controls.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. authority wording scan returned no matches.
4. focused import-intake Playwright smoke passed with `1 passed` after the fresh build.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse returned `packet-json-ok`.
7. `git diff --check` passed with line-ending warnings only.
8. `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. new routes,
3. route target changes,
4. route link changes,
5. quick-jump changes,
6. output action changes,
7. output status changes,
8. output selector changes,
9. handoff-guide item label changes,
10. handoff-guide href changes,
11. handoff-guide item count changes,
12. handoff-guide order changes,
13. handoff-guide status pill changes,
14. handoff-guide dynamic text changes,
15. helper panel relocation,
16. detail panel changes,
17. new localStorage keys,
18. persisted collapsed state,
19. new export actions,
20. new export artifacts,
21. export contract widening,
22. export filename changes,
23. export content changes,
24. new read seams,
25. mutation seam changes,
26. hosted parity claims,
27. SQL file creation,
28. SQL execution,
29. schema migration,
30. Supabase writes,
31. approval persistence,
32. import mutation,
33. live service calls,
34. Render redeploy,
35. Vercel promotion,
36. new service creation,
37. DNS, auth, ingress, or secret changes,
38. fixture replay,
39. workbook macro execution,
40. workbook writeback,
41. work authorization,
42. field release,
43. issue creation,
44. task creation,
45. live work order creation,
46. durable field records,
47. production tracking writes,
48. assignment mutation,
49. schedule mutation,
50. status mutation,
51. autonomous AI business-state mutation.

## Next Recommended Move

Keep the next PM lane focused on one of two bounded tracks:

1. accept returned hosted closeouts through PM Lane 076 if Vercel or Render executor evidence arrives,
2. otherwise authorize PM Lane 091 as Local PM Intake Workflow Map Disclosure Controls, preserving Lane 084 through Lane 090 disclosure coverage while changing only the existing workflow-map panel ergonomics.

Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are explicitly accepted.
