# APEX PM Lane 314 - Project Miner Temp Power Actuals Route Publication Gate After Authenticated Redeploy

Date: 2026-05-18

Status: Executed and accepted closed after hosted promotion

Decision label:

`PROJECT_MINER_TEMP_POWER_ACTUALS_ROUTE_PUBLICATION_GATE_AFTER_AUTHENTICATED_REDEPLOY`

## Purpose

PM Lane 314 closed the publication gap that remained after authenticated Render execution proved the earlier blocker was no longer auth.

The admitted Temp Power actuals route slice has now been published to `clean-main`, auto-deployed on the existing mutation-seam service, and verified on both hosted seam URLs.

## Selected Outcome

Selected outcome:

`ACTUALS_ROUTE_PUBLICATION_GATE_CLOSED_HOSTED_GREEN`

## Proven Facts

1. existing service `apex-platform-mutation-seam` is bound to repo `jasonlswenson-sys/apex-power-ops`, branch `clean-main`, root directory `apps/mutation-seam`
2. the admitted Temp Power actuals slice was published to `clean-main` as commit `3d47834eb32aa29b80152df3973f91d7c62a2e30`
3. Render auto-deploy created deployment `dep-d85j0a37uimc738l7060`
4. that deployment reached `live`
5. bounded hosted smoke now passes on both `https://mutation-seam.apexpowerops.com` and `https://apex-platform-mutation-seam.onrender.com`
6. the Temp Power actuals routes are now present in hosted OpenAPI and the actuals readback route returns `200`

## Resolution

The publication blocker is closed.

There is no remaining blocker inside the admitted Temp Power actuals capture-review slice. Any later work beyond this slice requires a new explicit admission lane rather than reopening publication or hosted-parity work for this branch.