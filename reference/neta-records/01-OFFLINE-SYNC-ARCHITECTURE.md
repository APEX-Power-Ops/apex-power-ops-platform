# NETA Records — Offline-Sync Architecture (PowerDB Replacement)

> **The "how it works" record for the PowerDB-replacement lane.** Provisioning,
> offline field capture, and reconciliation — and the decisions that pin the data
> model. Read this before changing any `neta.*` table, sync rule, or the field PWA.

- **Status:** RULED — direction decided 2026-06-12 (operator: Jason Swenson)
- **Owner:** APEX NETA Records lane
- **Home:** `reference/neta-records/` (beside the migrations it governs)
- **Companion:** `00-MASTER-INDEX.md` (domain charter), `POWERDB-PARITY-PUNCHLIST.md` (forward tracker)

---

## 1. Why offline is the whole design

PowerDB exists the way it does because **techs work where there is no signal** —
medium-voltage vaults, switchgear rooms, substations behind concrete and steel.
A replacement that assumes connectivity is a replacement that fails on day one.
Therefore offline is not a feature bolted on later; it is the **load-bearing
constraint** that the data model and the write path are shaped around.

The real workflow is three phases with a sync boundary between each:

| Phase | Where | Network | What happens |
|---|---|---|---|
| **Provision** | Office | online | Build job → define equipment list (assets) → assign the right NETA data sheet per asset → set acceptance windows + PM cadence → push the job package down to the device |
| **Execute** | Field | **offline, hours–days** | Open the job on the device, fill data sheets, auto pass/fail vs the acceptance window, capture to a local store with zero network |
| **Reconcile** | Back online | online | Device drains its outbox to the server; server dedupes/merges; reports generate office-side |

---

## 2. Decisions of record (2026-06-12)

| # | Decision | Choice | Rationale |
|---|---|---|---|
| D1 | Field device/surface | **Installable PWA** | One codebase, cross-platform laptop/tablet, offline via local store, no app-store friction. Lands in `apps/field-surface` (existing seed lane) or an `operations-web` route group. |
| D2 | Offline scope for V1 | **Fully offline-capable** | A tech must run an entire job — open assets, fill sheets, auto pass/fail — with **zero** connectivity, then sync. Matches real vault/substation use. |
| D3 | Sync engine | **PowerSync** (turnkey Postgres↔local sync) | Offline-first with a local SQLite store and multi-hour offline sessions; documented Supabase partner; its `uploadData` write hook maps directly onto the existing `mutation-seam` + `pm.idempotency_keys` infra. ElectricSQL's current build is read/pull-strong but write-path BYO, and its older local-first product was sunset — riskier for a vault-grade offline requirement. |

These are revisitable, but a change to D2 or D3 is a **schema-affecting** change and
must amend this doc first (SSoT law inherited from the TCC lane).

---

## 3. The authority split (what makes conflicts rare)

Every `neta.*` table is classified into exactly one sync direction. This is the
single most important rule in the lane:

### Reference data — **server-authoritative, flows DOWN only**
`asset_classes`, `assets`, `datasheet_templates`, `pm_programs`, `pm_schedules`

- Authored office-side; pulled to the device as read-mostly reference.
- The device never originates edits to these in V1, so **they cannot conflict.**
- A future "field nameplate correction" is modeled as a *proposed change* record,
  not an in-place device edit — preserving the one-way flow.

### Field records — **device-authoritative, flow UP only**
`datasheets`, `test_results`, `pm_events`

- Originated/filled on the device during the offline session.
- **Single-writer:** the assigned tech owns that data sheet for the visit, so two
  devices never write the same row concurrently.
- Therefore **last-write-wins with a `client_rev` guard is sufficient** — no CRDT,
  no field-level merge engine.

Each device-authoritative table carries the sync contract columns (in migration `002`):

| Column | Meaning |
|---|---|
| `origin_device` | Install/device id that captured the row |
| `client_rev` | Bumped on each device edit; LWW guard on upload |
| `client_captured_at` | When filled on device (vs server `created_at`) |
| `synced_at` | When the upload landed server-side |

Row primary keys are **client-generated UUIDs** (`gen_random_uuid()` server-side,
generated locally on device), so a row created offline keeps its identity through
sync — no id remapping.

---

## 4. The write path (how a sync actually lands)

This is where the repo's existing infrastructure does the heavy lifting.

1. **Capture (offline):** the tech's edit writes to local SQLite and appends to the
   PowerSync upload queue (outbox). Each logical mutation is tagged with a
   **client-generated UUID idempotency key** at capture time.
2. **Drain (reconnect):** PowerSync calls our `uploadData` connector, which POSTs
   each queued mutation to the **`mutation-seam`** write API — the same governed
   13-stage pipeline used for PM/work mutations.
3. **Dedupe (server):** the seam registers the idempotency key in
   **`pm.idempotency_keys`** (`UNIQUE (route, idempotency_key)`). A replay of an
   already-applied mutation is a no-op that returns the stored response — so
   "did my sync land?" is never a question and retries are always safe.
4. **Confirm (downstream):** the applied row's `synced_at` is set; PowerSync's
   replication stream reflects the server state back to the device, closing the loop.

```
device SQLite ──outbox──▶ PowerSync uploadData ──POST(idempotency-key)──▶ mutation-seam
                                                                              │
                                                                  pm.idempotency_keys
                                                                   (UNIQUE dedupe)
                                                                              │
                                                                      neta.* rows
                                                                              │
device SQLite ◀────────── PowerSync replication (sync rules) ◀────────────────┘
```

**Why this is the right reuse:** the durable idempotency store and the mutation
pipeline were built *specifically* so a client could replay a write safely after a
network gap. An offline outbox is the exact consumer that machinery was waiting for.

---

## 5. Provisioning (how a job gets to the device)

PowerSync **sync rules** define which rows replicate to which device. A tech only
needs *their* job, not the whole catalog:

- Bucket the asset subtree (and its blank data sheets, acceptance windows, and PM
  cadence) by **assignment** — the project/work package the tech is staffed on.
- The device downloads that bucket while online (office or truck), then goes dark.
- Acceptance windows (`test_results.min_acceptable/max_acceptable/expected`) ride
  down with the templates so **auto pass/fail works entirely offline.**

This is why the acceptance window lives on the result/template, not in a server-side
calc call: the calc has to happen in the tech's hand with no network. (The TCC
calc-engine can still *seed* those windows office-side during provisioning.)

---

## 6. What this defers (named, not hidden)

- **Instrument import** — pulling readings directly off Megger/test sets
  (serial/USB/Bluetooth) is a major PowerDB differentiator and a later lane. The
  `test_results.value_kind` shape already leaves room for it.
- **Field nameplate correction** as a proposed-change flow (keeps reference data
  one-way for now).
- **Multi-tech concurrent capture** on the *same* data sheet — out of scope while
  the single-writer rule holds; would require field-level merge if ever needed.
- **Hard cross-schema FK activation** (`neta` → `org`/`work`) — currently soft UUID
  links; activation is a punch-list chip.

---

## 7. Open questions (honesty register)

- **PowerSync hosting** — self-host the sync service on the Olares stack vs. managed
  PowerSync Cloud. Affects the infra lane, not the schema.
- **Sync-rule granularity** — per-tech vs per-crew bucket; depends on whether a crew
  shares one device or each tech carries their own.
- **Attachment sync** — photos/thermal images attached to a data sheet need a blob
  channel (PowerSync attachments helper or Supabase Storage with its own outbox).
