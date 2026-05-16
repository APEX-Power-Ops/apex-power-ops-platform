# PM Lane 091 Handoff - Local PM Intake Workflow Map Disclosure Controls

Date: 2026-05-16
Status: Local-current implemented
Scope: Browser-local default-open disclosure control for the existing `/pm-review/import-intake` Local PM Intake Workflow Map panel

## Executive Summary

PM Lane 091 wraps the existing `#pm-workflow-map` / `Local PM intake workflow map` panel in a native default-open disclosure control.

The affected workflow-map items are preserved:

1. Source intake,
2. Exception review,
3. Decision draft,
4. Field prep,
5. Executor closeout,
6. Approval persistence boundary,
7. Project import boundary.

This gives Jason a browser-native way to fold the AI/orchestration workflow map after reviewing it. It does not persist collapsed state.

It preserves the existing panel id, aria label, placement inside Workflow Review Panels, seven derived items, labels, hrefs, order, status pills, dynamic text, no-storage behavior, no-authority wording, read seam, and storage boundary.

It does not add a new route, link, target, output, export action, export artifact, export contract, local storage key, backend route, hosted proof, approval record, import mutation, task, issue, field record, or production write.

## Why This Lane

PM Lane 084 added default-open disclosure controls to the detail workbench.

PM Lane 085 applied the same pattern to the helper-panel stack.

PM Lane 086 applied the pattern to the top output action rail.

PM Lane 087 applied the pattern to the quick-jump rail.

PM Lane 088 applied the pattern to the conditional output status rail.

PM Lane 089 applied the pattern to the route-link rail.

PM Lane 090 applied the pattern to the handoff-guide panel.

PM Lane 091 applies the pattern to only the workflow-map panel so AI/orchestration workflow guidance remains available by default but can be folded after review.

## Sidecar Result

A read-only sidecar from PM Lane 090 recommended PM Lane 091 as the next local slice after the handoff-guide disclosure pattern landed. The recommendation was accepted with a narrow boundary:

1. wrap only the existing `#pm-workflow-map` / `Local PM intake workflow map` panel,
2. keep the disclosure control default-open,
3. do not persist collapsed/open state,
4. keep the map inside Workflow Review Panels,
5. preserve the seven derived map items, labels, hrefs, order, status pills, dynamic text, no-storage behavior, and no-authority wording,
6. preserve route links, quick-jump links, output actions, output statuses, output selector, handoff guide, open-items lens, helper/detail disclosures, reads, storage, hosted posture, and mutation behavior,
7. preserve PM Lane 083's no-implied-authority smoke guard,
8. leave PM Lane 084 detail, PM Lane 085 helper, PM Lane 086 output-action, PM Lane 087 quick-jump, PM Lane 088 output-status, PM Lane 089 route-link, and PM Lane 090 handoff-guide controls untouched.

A separate read-only sidecar completed a PM Lane 092 scout and has no write ownership in this tranche.

The returned recommendation is:

`Project Miner Local PM Intake Open Items Lens Disclosure Controls`

That next lane should wrap only the existing `#pm-open-items` / `Local PM Intake Open Items Lens` panel in `/pm-review/import-intake` as a default-open native disclosure. It should preserve the six derived open-items entries, labels, hrefs, order, status pills, dynamic text, no-storage behavior, no-authority wording, and placement inside Workflow Review Panels; prove default-open, collapse/reopen behavior, hidden/visible open-items rows, unchanged link counts and hrefs, and no collapse/disclosure/open-items localStorage key; and avoid PM Lane 091 workflow-map edits, handoff-guide behavior, helper group placement, route links, quick-jump changes, output-action changes, output-status changes, exports, storage, read, backend, approval, import, task, assignment, schedule, status, hosted, Supabase, Render, Vercel, SQL, schema, production, or AI business-state changes.

## What Changed

Operations-web:

1. converts the Local PM Intake Workflow Map panel wrapper to a native `details open` wrapper,
2. keeps the existing `pm-workflow-map` id and `Local PM intake workflow map` aria label on the wrapper,
3. keeps the existing heading and browser-local pill in the `summary`,
4. nests the existing workflow-map cards inside `Local PM intake workflow map items`,
5. leaves the existing workflow-map item labels, hrefs, order, status pills, dynamic text, no-storage/no-authority wording, storage keys, output actions, output statuses, route links, quick-jump links, handoff guide, helper disclosures, detail disclosures, and read seams unchanged,
6. adds no JavaScript state and no persisted collapsed state.

Focused smoke:

1. asserts the workflow-map disclosure is open by default,
2. verifies the existing seven child workflow-map links and hrefs,
3. collapses and reopens the map,
4. proves the workflow-map items hide and return with native disclosure behavior,
5. proves no `pm-import-intake-*` localStorage key containing collapse, disclosure, or workflow-map state is created,
6. preserves every existing workflow-map dynamic-text assertion,
7. preserves PM Lane 083's no-implied-authority control and wording guard,
8. preserves PM Lane 084 detail, PM Lane 085 helper, PM Lane 086 output-action, PM Lane 087 quick-jump, PM Lane 088 output-status, PM Lane 089 route-link, and PM Lane 090 handoff-guide disclosure coverage.

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-091-local-pm-intake-workflow-map-disclosure-controls.json', encoding='utf-8')); print('packet-json-ok')"
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
9. handoff-guide changes,
10. workflow-map item label changes,
11. workflow-map href changes,
12. workflow-map item count changes,
13. workflow-map order changes,
14. workflow-map status pill changes,
15. workflow-map dynamic text changes,
16. open-items lens changes,
17. helper panel relocation,
18. detail panel changes,
19. new localStorage keys,
20. persisted collapsed state,
21. new export actions,
22. new export artifacts,
23. export contract widening,
24. export filename changes,
25. export content changes,
26. new read seams,
27. mutation seam changes,
28. hosted parity claims,
29. SQL file creation,
30. SQL execution,
31. schema migration,
32. Supabase writes,
33. approval persistence,
34. import mutation,
35. live service calls,
36. Render redeploy,
37. Vercel promotion,
38. new service creation,
39. DNS, auth, ingress, or secret changes,
40. fixture replay,
41. workbook macro execution,
42. workbook writeback,
43. work authorization,
44. field release,
45. issue creation,
46. task creation,
47. live work order creation,
48. durable field records,
49. production tracking writes,
50. assignment mutation,
51. schedule mutation,
52. status mutation,
53. autonomous AI business-state mutation.

## Next Recommended Move

Keep the next PM lane focused on one of two bounded tracks:

1. accept returned hosted closeouts through PM Lane 076 if Vercel or Render executor evidence arrives,
2. otherwise authorize PM Lane 092 as Local PM Intake Open Items Lens Disclosure Controls, preserving Lane 084 through Lane 091 disclosure coverage while changing only the existing open-items lens panel ergonomics.

Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are explicitly accepted.
