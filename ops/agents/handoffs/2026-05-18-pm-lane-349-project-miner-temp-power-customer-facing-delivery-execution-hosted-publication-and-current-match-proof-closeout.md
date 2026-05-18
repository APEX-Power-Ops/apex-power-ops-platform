# PM Lane 349 - Customer-Facing Delivery Execution Hosted Publication And Current-Match Proof Closeout

## Outcome

PM Lane 349 is complete.

The public Temp Power customer-facing delivery execution route is now published on operations-web production, and the canonical hosted customer delivery event row is current across the operations-web alias plus both public mutation-seam hosts.

Final outcome:

`HOSTED_CUSTOMER_FACING_DELIVERY_EXECUTION_PUBLISHED_AND_CURRENT_MATCH_PROVEN`

## Governing Facts

1. PM Lane 347 implemented the admitted local customer-facing delivery execution route, mutation route, and readback.
2. PM Lane 348 added the hosted seam and hosted route smoke surfaces for this slice.
3. The repo-owned deployed mutation-seam smoke now passes on both `https://mutation-seam.apexpowerops.com` and `https://apex-platform-mutation-seam.onrender.com` with both `--include-temp-power-customer-delivery-proof-review` and `--include-temp-power-customer-delivery-execution` enabled.
4. The public operations-web hosted smoke now returns `SMOKE_SUMMARY failed=0 passed=13` on `https://operations.apexpowerops.com`, including `/pm-review/customer-delivery-execution`.
5. The canonical hosted lineage remains preview review `temp-power-customer-preview-review-1085e8e5fad27553463479f7`, delivery/proof review `temp-power-customer-delivery-proof-review-2ec74d71b109cfb3f8b1fb60`, and customer delivery event `pm-lane-337-temp-power-delivery-event-2026-05-18`.
6. A malformed hosted POST was rejected until `payload.idempotency_key` matched the envelope `idempotency_key`, proving the live seam still enforces packet-shape parity.
7. The later clean hosted replay returned `idempotent_hit` for entity `pm-lane-337-temp-power-delivery-event-2026-05-18`, preserving mutation `mut-b2ea9ced-aae1-49ed-9180-72426fff1564` and audit `audit-755d4643-4320-4098-84d4-be7cb9939e32`.
8. Public readbacks from the operations-web alias, the apex seam host, and the Render seam host all returned `customer_delivery_event_recorded_current_match` with `record_count=1` and lineage booleans true.

## Boundary

Still not admitted:

1. any claim that the clean replay in this closeout window created the first hosted delivery-event row
2. finance output
3. source writeback
4. customer billing delivery

## Next Truth

The previous hosted blocker is closed.

If PM work continues from this point, the next truthful move is a separate downstream authority packet rather than another customer-facing delivery execution publication or current-match proof packet.
