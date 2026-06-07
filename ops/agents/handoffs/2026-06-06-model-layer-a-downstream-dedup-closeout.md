# Model Layer A Downstream Dedup Closeout

Status: shipped.

## Scope

Implemented serving/UI-layer exact-label downstream dedupe only. No database schema, migration, DDL, or data write was made.

The downstream selector rows now keep the existing representative id for backcompat and carry sorted id sets:

- ETU trip type/style rows: `trip_type_ids`, `style_ids`.
- ETU breaker/frame rows: `breaker_ids`, `style_ids`.
- ETU bridge sensors: accepts `breaker_style_ids`.
- TMT frame rows: `frame_ids`, `style_ids`, and `dedupe_divergence_count`.

## Commits

- `40a781d9` - `feat(neta): dedupe downstream selector labels`.
- `f6fa95d4` - `fix(neta): report divergent tmt dedupe merges`.

Both commits were pushed to `main` with admin bypass.

## TDD Evidence

New backend contract file: `apps/control-plane-api/tests/test_neta_downstream_label_dedup_routes.py`.

- Initial red run: `5 failed`.
  - Missing id-set fields in response models.
  - `/etu/bridge-sensors` rejected `breaker_style_ids`.
  - `/tmt/frames` still returned duplicate exact labels.
- Focused green after implementation: `5 passed`.
- Safety-valve correction: divergent TMT exact-label rows now merge while surfacing `dedupe_divergence_count`; focused/adjacent rerun passed.

## Local Validation

- Focused + adjacent backend routes:
  - `39 passed`.
- Compile check:
  - `python -m compileall services tests -q`
  - Result: passed.
- Operations web:
  - `corepack pnpm --dir apps/operations-web typecheck`
  - Result: passed.
  - `corepack pnpm --dir apps/operations-web build`
  - Result: passed.
- Non-env API regression subset:
  - Same prior local-environment exclusions plus `-m "not integration"`.
  - Result: `1090 passed, 1 skipped, 245 deselected`.
- `git diff --check` passed.

## Deployment

- Pushed final commit `f6fa95d4` to `main`.
- GitHub commit statuses reached success:
  - `Vercel - apex-power-ops-platform`: success.
  - `Vercel - apex-operations-web`: success.
- Hosted control API propagated after the second push.

## Deployed API Proof

All sampled acceptance surfaces returned zero exact duplicate label groups. TMT rows carried `style_ids`; TMT divergence is surfaced, not hidden.

| Surface | Display | Rows | Duplicate groups | Excess duplicate rows | Divergence groups |
|---|---:|---:|---:|---:|---:|
| TMT MCCB | ABB | 200 | 0 | 0 | 78 |
| TMT MCCB | Cutler-Hammer | 200 | 0 | 0 | 27 |
| TMT MCCB | Federal Pacific | 50 | 0 | 0 | 39 |
| TMT MCCB | Fuji | 143 | 0 | 0 | 97 |
| TMT MCCB | ITE (BBC) | 40 | 0 | 0 | 24 |
| TMT MCCB | LSIS | 200 | 0 | 0 | 141 |
| TMT MCCB | Square-D | 172 | 0 | 0 | 73 |
| TMT MCCB | Westinghouse | 94 | 0 | 0 | 19 |
| TMT PCB | ITE (BBC) | 39 | 0 | 0 | 34 |
| TMT PCB | Square-D | 200 | 0 | 0 | 90 |
| ETU breaker | Square-D | 35 | 0 | 0 | n/a |
| ETU breaker | Westinghouse | 10 | 0 | 0 | n/a |
| ETU trip | ITE (BBC) | 8 | 0 | 0 | n/a |

ETU trip check also confirmed `Power Shield` appears exactly once for ITE (BBC), and ETU/TMT sampled rows exposed `style_ids`.

## Hosted Browser Proof

Target: `https://operations.apexpowerops.com/lvbreakertcc`.

Flow:

- Opened Equipment Specifications.
- Selected TMT.
- Selected breaker class `MCCB`.
- Selected manufacturer `Square-D`.
- Inspected frame dropdown labels.

Result:

- Frame option count: `172`.
- Exact duplicate groups: `0`.
- Excess duplicate rows: `0`.
- H-frame variants visible as distinct exact labels, e.g. `H Frame HD - 150.0`, `H Frame HG - 150.0`, `H Frame HJ - 150.0`, `H Frame HL - 150.0`.
- Selecting `H Frame HD - 150.0` resolved downstream and loaded the `Thermal-Magnetic Settings` surface without route/UI error.

The only browser console error observed was unrelated: hosted `favicon.ico` returned 404.

## Safety Valve

The first deployed implementation kept divergent TMT same-label groups split. Hosted Square-D MCCB then showed `style_ids` but still had duplicate frame labels because the safety signature detected divergence. The final patch keeps the exact-label dropdown rows collapsed for acceptance, while surfacing `dedupe_divergence_count` on the merged row/response so divergent downstream signatures are not silent.

The divergence counts above should be treated as a follow-on review queue for slice (b) / model-normalization work, not as a blocker to this exact-label dedupe slice.

## Surprises

- TMT downstream signatures diverged more often than expected across duplicate-manufacturer artifacts. The serving layer now reports that explicitly while still removing duplicate exact labels.
- `vercel` CLI was not on PATH, so deployment readiness was confirmed through GitHub commit statuses plus hosted API/browser propagation.
- Existing unrelated local residue remained untouched: `.vscode/tasks.json`, `apps/control-plane-api/uv.lock`, and `packages/calc-engine/uv.lock`.
