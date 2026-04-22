# Forms Studio

Status: Deferred placeholder lane

Purpose:
- reserved platform home for the future forms authoring and generation app
- primary bounded landing lane for approved active slices from `C:/APEX Platform/source-domains/neta-forms`

Current decision:
- defer app-shell activation in this cycle
- use `packages/forms-engine` as the bounded active implementation lane until real browser-app work is ready

Current rules:
1. do not import the source-domain repo wholesale
2. move only approved active slices into this lane
3. do not treat this lane as an active deployable until a real app shell, env contract, tests, and deployment notes exist
4. activate this lane when a forms browser surface is ready to own promoted UI slices rather than only shared generation logic

Activation trigger:
1. activate this lane only when a bounded forms browser app-shell packet is approved
2. require an explicit env contract, validation path, and deployment notes before treating the lane as active
3. until then, keep active reusable forms logic landing in `packages/forms-engine`

Authority order:
1. `C:/APEX Platform/Platform-Authority/`
2. `docs/authority/`
3. root `README.md`
4. `docs/OPERATOR-BOOTSTRAP-RUNBOOK.md`

This folder existed as an approved target lane at audit time but was empty. This README marks it as intentional rather than accidental.
