# TCC Relay StdLib Snapshot 001 Source Lineage

This directory preserves the immutable relay snapshot admitted for Packet
`2026-04-30-tcc-relay-tranche-2`.

Status:

- Shared-infra source-lineage input for Tranche 2 replay
- Immutable after admission
- Not runtime authority by itself
- Not a replacement for the governed `work.tcc_relay*` substrate

Snapshot identity:

- Snapshot id: `stdlib-relay-snapshot-001`
- Captured: 2026-04-30
- Source root: `D:\Access DB\tables\`
- Extraction method: byte-for-byte copy of the admitted relay CSV export set

Governing packets and handoffs:

1. `Platform-Authority/TCC-RELAY-EXTRACTION-MAPPING-AND-PROVENANCE-STAGING-PACKET-2026-04-30.md`
2. `Platform-Authority/TCC-RELAY-TRANCHE-2-STAGED-POPULATION-AND-PROVENANCE-REPLAY-EXECUTION-PACKET-2026-04-30.md`
3. `apex-power-ops-platform/ops/agents/handoffs/2026-04-30-tcc-relay-tranche-2-staged-population-and-provenance-replay-execution-completion-handoff.md`

Included slices:

1. `data/Manufacturers.csv`
2. `data/Relays.csv`
3. `data/RelayDevices.csv`
4. `data/RelayLineSection.csv`
5. `data/RelayTDSection.csv`
6. `data/RelayRanges.csv`
7. `data/RelayDiscreteValues.csv`
8. `data/RelaySec2IEC.csv`
9. `data/RelaySec2IECCurves.csv`
10. `data/RelaySec2SWZ.csv`
11. `data/RelaySec2SWZCurves.csv`
12. `data/RelaySec2BSL.csv`
13. `data/RelaySec2BSLCurves.csv`
14. `data/RelaySec2MEQ.csv`
15. `data/RelaySec2MEQCurves.csv`
16. `data/RelaySec2PCD.csv`
17. `data/RelaySec2PCDCurves.csv`
18. `data/RelaySec2LRM.csv`
19. `data/RelaySec2RXD.csv`
20. `data/RelaySec2EGC.csv`
21. `data/RelaySec2TCP.csv`
22. `data/RelaySec2TCPCurves.csv`

Explicit exclusions:

1. `RelayID.csv`
2. all unadmitted StdLib tables outside the Packet 004 relay boundary
3. live MDB/ACCDB reads at replay time
4. calc-engine, API, and browser artifacts
5. deferred relay enrichment surfaces

Validation pointers:

1. `manifest/00_snapshot_manifest.md`
2. `manifest/01_validation_checklist.md`

The next truthful relay move after this snapshot and replay boundary is not more
source-lineage authoring. It is a separately authored Tranche 3 shared calc
substrate enablement execution packet.