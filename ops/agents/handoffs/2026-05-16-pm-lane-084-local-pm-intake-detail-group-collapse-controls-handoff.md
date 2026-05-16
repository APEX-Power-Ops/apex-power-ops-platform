# PM Lane 084 Handoff - Local PM Intake Detail Group Collapse Controls

Date: 2026-05-16
Status: Local-current implemented
Scope: Browser-local default-open disclosure controls for existing `/pm-review/import-intake` detail groups

## Executive Summary

PM Lane 084 wraps the six existing PM Lane 082 detail-workbench groups in native default-open disclosure controls.

The affected groups are:

1. Review Snapshot Detail,
2. Source and Exception Detail,
3. Approval Prep Detail,
4. Executor Closeout Detail,
5. Field Prep Detail,
6. Authority Boundary Detail.

This gives Jason a browser-native way to fold long detail sections while reviewing. It does not persist collapsed state.

It preserves every existing child panel id, aria label, anchor target, route link, quick-jump link, export action, output status, generated filename, export content, read seam, and storage boundary.

It does not add a new route, output, export contract, local storage key, backend route, hosted proof, approval record, import mutation, task, issue, field record, or production write.

## Why This Lane

PM Lane 082 grouped the long detail workbench. PM Lane 083 locked down authority wording and zero-mutation posture in the focused smoke.

The next practical friction was scroll control: Jason can now fold large sections during a review without changing any data contract or relying on persisted UI state.

## Sidecar Result

A read-only sidecar from PM Lane 083 recommended PM Lane 084 as the next local slice after the authority wording guard landed. The recommendation was accepted with a narrow boundary:

1. wrap only the six existing PM Lane 082 detail groups,
2. keep all disclosure controls default-open,
3. do not persist collapsed/open state,
4. preserve route links, quick jumps, exports, statuses, storage, reads, hosted posture, and mutation behavior,
5. preserve PM Lane 083's no-implied-authority smoke guard.

A separate read-only sidecar completed the next-lane scout and recommended PM Lane 085 as Local PM Intake Helper Group Disclosure Controls. That sidecar made no file changes, staged nothing, ran no services, and did not access live Supabase, Render, or Vercel services.

## What Changed

Operations-web:

1. converts the six detail-workbench group wrappers to native `details open` wrappers,
2. moves each detail-group heading into a `summary`,
3. leaves the existing child panels, ids, aria labels, content, localStorage keys, exports, route links, quick-jump links, and read seams unchanged,
4. adds no JavaScript state and no persisted collapsed state.

Focused smoke:

1. asserts all six disclosure groups are open by default,
2. collapses and reopens Review Snapshot Detail,
3. proves the snapshot panel hides and returns with native disclosure behavior,
4. proves no `pm-import-intake-*` localStorage key containing collapse, detail, or disclosure state is created,
5. preserves PM Lane 083's no-implied-authority control and wording guard.

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
& "C:/APEX Platform/apex-power-ops-platform/.venv/Scripts/python.exe" -c "import json; json.load(open(r'C:/APEX Platform/apex-power-ops-platform/ops/agents/packets/draft/2026-05-16-pm-lane-084-local-pm-intake-detail-group-collapse-controls.json', encoding='utf-8')); print('packet-json-ok')"
```

Diff hygiene:

```powershell
git diff --check
git diff --cached --check
```

Current local validation result:

1. operations-web typecheck passed.
2. operations-web production build passed with `/pm-review/import-intake` in the route output.
3. PM authority wording scan passed with no matches.
4. focused import-intake Playwright smoke initially failed against stale built output before rebuild, then passed with `1 passed` after rebuilding.
5. focused PM intake Playwright smoke suite passed with `4 passed`.
6. packet JSON parse passed with `packet-json-ok`.
7. `git diff --check` passed.
8. `git diff --cached --check` passed.

## Guardrails Preserved

This tranche does not authorize:

1. backend endpoint changes,
2. new routes,
3. route target changes,
4. quick-jump link changes,
5. output action changes,
6. output status changes,
7. detail panel content changes,
8. detail panel id changes,
9. existing detail panel aria-label changes,
10. new localStorage keys,
11. persisted collapsed state,
12. new export actions,
13. new export artifacts,
14. export contract widening,
15. export filename changes,
16. export content changes,
17. new read seams,
18. mutation seam changes,
19. hosted parity claims,
20. SQL file creation,
21. SQL execution,
22. schema migration,
23. Supabase writes,
24. approval persistence,
25. import mutation,
26. live service calls,
27. Render redeploy,
28. Vercel promotion,
29. new service creation,
30. DNS, auth, ingress, or secret changes,
31. fixture replay,
32. workbook macro execution,
33. workbook writeback,
34. work authorization,
35. field release,
36. issue creation,
37. task creation,
38. live work order creation,
39. durable field records,
40. production tracking writes,
41. assignment mutation,
42. schedule mutation,
43. status mutation,
44. autonomous AI business-state mutation.

## Next Recommended Move

Keep the next PM lane focused on one of two bounded tracks:

1. accept returned hosted closeouts through PM Lane 076 if Vercel or Render executor evidence arrives,
2. continue PM Lane 085, Local PM Intake Helper Group Disclosure Controls, as a separate browser-local default-open disclosure-controls slice for the helper-panel stack.

Durable field records, approval persistence, import mutation, and production tracking remain blocked until later admitted packets exist and are explicitly accepted.
