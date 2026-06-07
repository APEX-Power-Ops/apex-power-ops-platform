# Manufacturer Duplicate Consolidation Closeout

Status: shipped.

## Scope

Implemented serving/UI-layer consolidation only. No database schema/data change was made. EP manufacturer ids remain immutable; dropdown rows now group dynamically by `manufacturer_display` and carry `manufacturer_ids` for downstream union filters.

## Commits

- Implementation: `2fead9913616b58c4da184a6429a31f8f9d07641` (`feat(neta): consolidate manufacturer display ids`).
- Closeout/packet move: follow-on docs commit containing this file and the inbox pending-to-done move.

## TDD Evidence

Tests were added first in `apps/control-plane-api/tests/test_neta_manufacturer_dup_consolidation_routes.py`.

- Initial red run: `5 failed`.
  - Failures showed `manufacturer_ids` absent, list query params ignored, and id-set cross-filter params absent.
- Focused green run: `5 passed`.

## Local Validation

- Focused adjacent backend routes:
  - `43 passed`.
- Compile check:
  - `python -m compileall apps/control-plane-api/services/neta apps/control-plane-api/tests/test_neta_manufacturer_dup_consolidation_routes.py`
  - Result: passed.
- Operations web:
  - `pnpm --filter @apex/operations-web typecheck`
  - Result: passed.
  - `pnpm --filter @apex/operations-web build`
  - Result: passed.
- Non-env API regression subset:
  - Prior exact command without the integration marker hit this workstation's localhost Postgres SSL mismatch in `_integration.py` fixtures.
  - Rerun with the same exclusion set plus `-m "not integration"` passed: `1085 passed, 1 skipped, 245 deselected`.
- `git diff --check` passed.

## Deployment

- Pushed implementation commit `2fead991` to `main` with admin bypass.
- Vercel production deployment for operations-web is READY:
  - deployment id `dpl_DLch28crdmiCSsSsL6CVgY5GtYzx`
  - URL `https://apex-operations-ladsz5kp8-jasonlswenson-sys-projects.vercel.app`
  - alias `https://operations.apexpowerops.com`
- Public control-plane API propagated after the push; hosted NETA family smoke passed against `https://control.apexpowerops.com`.

## Dropdown Counts

| Family endpoint | Before rows / duplicate display labels | After rows / duplicate display labels |
|---|---:|---:|
| ETU trip `/cascade` | 63 / ABB, ITE (BBC), LSIS each x2 | 60 / none |
| ETU breaker `/etu/breaker-cascade?bridge_only=true` | 44 / Cutler-Hammer, LSIS, Square-D, Westinghouse each x2 | 40 / none |
| ETU breaker `/etu/breaker-cascade` | not sampled before | 110 / none; Square-D ids `[17,35,235]` |
| TMT ICCB | 0 / none | 0 / none |
| TMT MCCB | 101 / ABB, Cutler-Hammer, Federal Pacific, Fuji, ITE (BBC), LSIS, Square-D, Westinghouse each x2 | 93 / none |
| TMT PCB | 44 / ITE (BBC), Square-D each x2 | 42 / none |
| EMT | 14 / none | 14 / none |

Bridge-only Square-D correctly intersects to `[17,35]`; the full no-bridge-lens breaker endpoint returns `[17,35,235]` as requested.

## Hosted Proof

API:

- `/api/v1/neta/etu/breaker-cascade` returns one Square-D row with `manufacturer_ids:[17,35,235]`.
- All sampled dropdown endpoints above returned zero duplicate display labels after deployment.

Browser:

- `https://operations.apexpowerops.com/lvbreakertcc`
- ETU Breaker Manufacturer dropdown: Square-D, ITE (BBC), ABB, Cutler-Hammer each appeared once.
- ETU Trip Manufacturer dropdown: Square-D, ITE (BBC), ABB, Cutler-Hammer each appeared once.
- Selecting Square-D on the breaker axis sent:
  - `https://control.apexpowerops.com/api/v1/neta/etu/breaker-cascade?manufacturer_ids=17&manufacturer_ids=35&bridge_only=true&bridge_xfilter=true`
- The Breaker dropdown then rendered 36 downstream options from the unioned id set.

## Model-Dup Measurements

Model de-duplication remains out of scope, but duplicate downstream labels were measured after union filtering:

| Downstream surface | Display | Ids | Duplicate label groups | Excess duplicate rows | Examples |
|---|---|---:|---:|---:|---|
| ETU trip type | ITE (BBC) | `[11,125]` | 1 | 1 | Power Shield x2 |
| ETU breaker name | Square-D | `[17,35]` | 2 | 2 | `(Std)` x2, MP NW UL489 x2 |
| ETU breaker name | Westinghouse | `[18,36]` | 1 | 1 | Series C x2 |
| TMT MCCB frame label | ABB | `[1,43]` | 18 | 146 | Tmax Ts3* labels |
| TMT MCCB frame label | Cutler-Hammer | `[28,41]` | 11 | 55 | WMZ, Series G, Navy AQB |
| TMT MCCB frame label | Federal Pacific | `[8,118]` | 20 | 169 | NJL/NF/Fusematic/FPower labels |
| TMT MCCB frame label | Fuji | `[46,102]` | 33 | 137 | G-TWIN/BU Series labels |
| TMT MCCB frame label | ITE (BBC) | `[11,173]` | 25 | 88 | EQ/ET/MCP labels |
| TMT MCCB frame label | LSIS | `[192,304]` | 43 | 135 | ABE/ABH/EBE/EBH labels |
| TMT MCCB frame label | Square-D | `[17,235]` | 18 | 177 | H Frame, M Frame, F Frame labels |
| TMT MCCB frame label | Westinghouse | `[18,36]` | 15 | 113 | MCP/AB DE-ION/Series C labels |
| TMT PCB frame label | ITE (BBC) | `[4,11]` | 34 | 134 | LK/LKE/K-series labels |
| TMT PCB frame label | Square-D | `[17,35]` | 30 | 146 | Masterpact/MP MT/MP NT labels |

## Surprises

- The user-supplied inbox path under `C:\Users\jjswe\ops\...` was stale; the packet existed at repo-local `ops/agents/inbox/pending/...`.
- WSL `bash` was installed but unavailable; Git Bash was available and used for commit heredocs.
- The prior exact non-env command now enters DB-backed integration fixtures on this workstation and fails on local Postgres SSL mode. Adding `-m "not integration"` produced the intended non-env slice.
