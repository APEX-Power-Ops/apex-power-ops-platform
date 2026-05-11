# Field Surface

Status: Seed lane

Purpose:
- reserved platform lane for the future field execution surface
- current folder is a seed shell, not yet a fully governed deployable

Naming note:
- Platform-Authority target topology uses `field-app` language
- the current workspace decision is to retain this lane as `field-surface` until field-runtime work justifies a rename or cutover

Current rules:
1. do not assume this lane is production-ready
2. any new work here should add an explicit env contract, test lane, and deployment notes
3. prefer bounded platform-root implementation rather than direct imports from legacy repos

Graduation gate:
1. keep this lane classified as a seed until field-runtime work proves a real deployable boundary
2. do not force a rename or cutover while the runtime, operator flow, and deployment posture are still unproven
3. revisit graduation or rename only after the lane has a concrete env contract, validation path, and runtime ownership model

Authority order:
1. `C:/APEX Platform/apex-power-ops-platform/docs/authority/README.md`
2. `C:/APEX Platform/apex-power-ops-platform/docs/architecture/APEX-REPO-FOUNDATION-AND-CUTOVER-PLAN-2026-05-07.md`
3. `C:/APEX Platform/apex-power-ops-platform/README.md`
