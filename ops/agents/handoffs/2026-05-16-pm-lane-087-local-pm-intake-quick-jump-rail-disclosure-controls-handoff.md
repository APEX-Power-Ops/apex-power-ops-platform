# PM Lane 087 Handoff - Local PM Intake Quick Jump Rail Disclosure Controls

Date: 2026-05-16
Status: Local-current implemented
Scope: Browser-local default-open disclosure control for the existing `/pm-review/import-intake` quick-jump rail

## Executive Summary

PM Lane 087 wraps the existing `#pm-quick-jump-rail` in a native default-open disclosure control.

The affected child groups are preserved:

1. Daily Review,
2. Outputs and Handoff,
3. Review Flow,
4. Source, Field, and Guardrails.

This gives Jason a browser-native way to fold the dense local navigator after orienting. It does not persist collapsed state.

It preserves the existing quick-jump rail id, aria label, group headings, link labels, href targets, link counts, order, target sections, read seam, and storage boundary.

It does not add a new route, link, target, output, export action, export artifact, export contract, local storage key, backend route, hosted proof, approval record, import mutation, task, issue, field record, or production write.

## Why This Lane

PM Lane 084 added default-open disclosure controls to the detail workbench.

PM Lane 085 applied the same pattern to the helper-panel stack.

PM Lane 086 applied the pattern to the top output action rail.

PM Lane 087 applies the pattern to only the quick-jump rail so the navigator remains available by default but can be folded after orientation.

## Sidecar Result

A read-only sidecar from PM Lane 086 recommended PM Lane 087 as the next local slice after the output-action disclosure pattern landed. The recommendation was accepted with a narrow boundary:

1. wrap only the existing `#pm-quick-jump-rail`,
2. keep the disclosure control default-open,
3. do not persist collapsed/open state,
4. preserve the rail id, aria label, group headings, link labels, href targets, link counts, order, and target sections,
5. preserve route links, output actions, output statuses, helper/detail disclosures, reads, storage, hosted posture, and mutation behavior,
6. preserve PM Lane 083's no-implied-authority smoke guard,
7. leave PM Lane 084 detail, PM Lane 085 helper, and PM Lane 086 output-action controls untouched.

A separate read-only sidecar completed a PM Lane 088 scout and has no write ownership in this tranche.

The returned recommendation is:

`Project Miner Local PM Intake Output Status Rail Disclosure Controls`

That next lane should wrap only the existing conditional `PM intake output status rail` on `/pm-review/import-intake` in a default-open native disclosure control. It should preserve the current absent-before-export-status behavior, Review/Executor/Field Prep status labels, message text, ordering, counts, and export behavior; prove default-open, collapse/reopen behavior, hidden/visible status groups, and no collapse/disclosure/output-status localStorage key; and avoid quick-jump, route, output action, export, storage, read, backend, approval, import, task, assignment, schedule, status, hosted, Supabase, Render, Vercel, SQL, schema, production, or AI business-state changes.

## What Changed

Operations-web:

1. converts the quick-jump rail wrapper to a native `details open` wrapper,
2. keeps the existing `pm-quick-jump-rail` id and `PM intake quick jump rail` aria label on the wrapper,
3. moves the existing heading and browser-local pill into the `summary`,
4. leaves the existing nav, group headings, link labels, href targets, link counts, order, target sections, storage keys, output actions, output statuses, and read seams unchanged,
5. adds no JavaScript state and no persisted collapsed state.

Focused smoke:

1. asserts the quick-jump disclosure is open by default,
2. verifies the existing four child link groups and link counts,
3. collapses and reopens the rail,
4. proves the child section links hide and return with native disclosure behavior,
5. proves no `pm-import-intake-*` localStorage key containing collapse, disclosure, or quick-jump state is created,
6. preserves every existing quick-jump href target assertion,
7. preserves PM Lane 083's no-implied-authority control and wording guard,
8. preserves PM Lane 084 detail, PM Lane 085 helper, and PM Lane 086 output-action disclosure coverage.

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-087-local-pm-intake-quick-jump-rail-disclosure-controls.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. focused import-intake Playwright smoke passed with `1 passed` after the fresh build.
4. authority wording scan returned no matches.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse returned `packet-json-ok`.
7. `git diff --check` passed with line-ending warnings only.
8. `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. new routes,
3. route target changes,
4. quick-jump link label changes,
5. quick-jump href changes,
6. quick-jump link count changes,
7. quick-jump order changes,
8. quick-jump target section changes,
9. output action changes,
10. output status changes,
11. helper panel changes,
12. detail panel changes,
13. new localStorage keys,
14. persisted collapsed state,
15. new export actions,
16. new export artifacts,
17. export contract widening,
18. export filename changes,
19. export content changes,
20. new read seams,
21. mutation seam changes,
22. hosted parity claims,
23. SQL file creation,
24. SQL execution,
25. schema migration,
26. Supabase writes,
27. approval persistence,
28. import mutation,
29. live service calls,
30. Render redeploy,
31. Vercel promotion,
32. new service creation,
33. DNS, auth, ingress, or secret changes,
34. fixture replay,
35. workbook macro execution,
36. workbook writeback,
37. work authorization,
38. field release,
39. issue creation,
40. task creation,
41. live work order creation,
42. durable field records,
43. production tracking writes,
44. assignment mutation,
45. schedule mutation,
46. status mutation,
47. autonomous AI business-state mutation.

## Next Recommended Move

Keep the next PM lane focused on one of two bounded tracks:

1. accept returned hosted closeouts through PM Lane 076 if Vercel or Render executor evidence arrives,
2. otherwise authorize PM Lane 088 as Local PM Intake Output Status Rail Disclosure Controls, preserving Lane 084 through Lane 087 disclosure coverage while changing only the conditional output-status rail ergonomics.

Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are explicitly accepted.
