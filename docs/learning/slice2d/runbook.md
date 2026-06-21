# Slice 2d Acquisition Pilot — Live Rehearsal Runbook

**Status:** operator-executed (Task 6) — NOT automated  
**Branch:** `learning/slice2d-acquisition-pilot`  
**Run ID convention:** `slice2d-rehearsal-01` (increment suffix for reruns)

---

## 0. Gate: `data_write` approval required

> **STOP. Do NOT proceed without explicit operator approval to write to `learning_dev`.**

All Tasks 1–5 ran exclusively against `learning_test`. This runbook is the first and only path that
writes to `learning_dev`. The helper hard-refuses any DSN containing `*.supabase.co` or the prod
project ref `fxoyniqnrlkxfligbxmg` — but the operator must confirm intent before sourcing
`LEARNING_DEV_DSN`.

Approval signal: operator explicitly says "run against learning_dev" or equivalent.

---

## 1. Prerequisites

- SSH access to the Olares host (`olares-mesh`).
- `infra/.env` present in the repo root with `DEV_PG_PASSWORD` and `LEARNING_DEV_DSN` set (unquoted,
  source-safe). Verify: `source infra/.env && echo $LEARNING_DEV_DSN`.
- The operator-held evidence map is populated: `.claude/PLATFORM/slice2d_evidence_map.md` (kept out of
  git; never committed). This file records the real person handle, observation channel, timestamp, and
  observer attestation for each event. See Section 4 for the per-event requirement.
- `uv` available: `export PATH="$HOME/.local/bin:$PATH"`.

---

## 2. Provision the rehearsal cohort

Source the env and run the provision script against `learning_dev`:

```bash
cd /home/olares/code/apex/apex-learning-lane
export PATH="$HOME/.local/bin:$PATH"
set -a && . infra/.env && set +a
export PGPASSWORD="$DEV_PG_PASSWORD"

psql "$LEARNING_DEV_DSN" -f scripts/learning/slice2d_provision_cohort.sql
```

The script inserts the rehearsal `user_profiles` row(s) and sets `is_active = true`. Confirm with:

```bash
psql "$LEARNING_DEV_DSN" -c \
  "SELECT id, display_name, employee_id, is_active FROM user_profiles WHERE display_name LIKE '%rehearsal%';"
```

---

## 3. Capture: event sequence

All four `learning-capture acquire` commands target SCADA content
`9c47a9ed-c46b-4d1d-a604-7c68647c913c`. The real person engages the content on their own device; the
observer records each event with the CLI immediately after witnessing the engagement.

Replace `<initials>` with the observer handle (e.g. `JLS`) and `<pointer>` with the opaque
`evidence_ref` key from `.claude/PLATFORM/slice2d_evidence_map.md`.

### 3a. Resource viewed

```bash
learning-capture acquire resource_viewed \
  --content-id 9c47a9ed-c46b-4d1d-a604-7c68647c913c \
  --user-id <rehearsal-user-uuid> \
  --run-id slice2d-rehearsal-01 \
  --observed-by <initials> \
  --evidence-ref <pointer> \
  --fidelity rehearsal
```

### 3b. Self-assessment (confidence 1–5)

```bash
learning-capture acquire self_assessment \
  --content-id 9c47a9ed-c46b-4d1d-a604-7c68647c913c \
  --user-id <rehearsal-user-uuid> \
  --run-id slice2d-rehearsal-01 \
  --observed-by <initials> \
  --evidence-ref <pointer> \
  --fidelity rehearsal \
  --confidence <1-5>
```

### 3c. Assessment completed (score 0–100)

```bash
learning-capture acquire assessment_completed \
  --content-id 9c47a9ed-c46b-4d1d-a604-7c68647c913c \
  --user-id <rehearsal-user-uuid> \
  --run-id slice2d-rehearsal-01 \
  --observed-by <initials> \
  --evidence-ref <pointer> \
  --fidelity rehearsal \
  --score <0-100>
```

The `--score` value comes from the real graded instrument (not estimated). The observer must have
line-of-sight to the instrument result or the attestation from the person themselves.

### 3d. KSA mapped

```bash
learning-capture acquire ksa_mapped \
  --content-id 9c47a9ed-c46b-4d1d-a604-7c68647c913c \
  --user-id <rehearsal-user-uuid> \
  --run-id slice2d-rehearsal-01 \
  --observed-by <initials> \
  --evidence-ref <pointer> \
  --fidelity rehearsal
```

---

## 4. Genuine-engagement evidence requirement

Every event recorded in step 3 MUST have a corresponding entry in the operator-held evidence map
(`.claude/PLATFORM/slice2d_evidence_map.md`). That entry records:

- **Who:** the real person (handle/initials — not full name in the committed file)
- **What:** what engagement occurred (viewed the PDF, completed the quiz, etc.)
- **When:** approximate timestamp (UTC)
- **Channel:** how the observation was made (in-person, screen-share, graded instrument export, etc.)
- **Observer attestation:** a line signed by the observer confirming the event was genuine

An event with no retrievable, attestable evidence entry in the operator-held map is excluded from
the committed evidence packet. Do not capture events that cannot be attested.

---

## 5. Verification

Capture the four read-model responses **before** Step 3 (baseline) and **after** (post-capture), and
paste them into the evidence packet template.

```bash
BASE_URL="http://localhost:3001"   # adjust to the running control-plane port
USER="<rehearsal-user-uuid>"
CONTENT="9c47a9ed-c46b-4d1d-a604-7c68647c913c"

# 1. Progress
curl -s "$BASE_URL/api/v1/learning/progress?user_id=$USER" | jq .

# 2. Assessments
curl -s "$BASE_URL/api/v1/learning/assessments?user_id=$USER" | jq .

# 3. Competency
curl -s "$BASE_URL/api/v1/learning/competency?user_id=$USER&level=III" | jq .

# 4. Cohort (level-scoped; the cohort route aggregates all active users at the level)
curl -s "$BASE_URL/api/v1/learning/cohort?level=III" | jq .
```

### Independent SQL manifest

Verify the exact KSA set surfaced by the resolver for this content:

```sql
SELECT DISTINCT k.ksa_code, k.certification_level
FROM   public.learning_events le
JOIN   public.content_concept_links ccl ON ccl.content_id = le.study_content_id
JOIN   public.edition_ksa_map ekm ON ekm.concept_id = ccl.concept_id AND ekm.is_active
JOIN   public.ksas k ON k.ksa_code = ekm.ksa_code AND k.certification_level::text = ekm.level
WHERE  le.user_id = '<rehearsal-user-uuid>'
  AND  le.study_content_id = '9c47a9ed-c46b-4d1d-a604-7c68647c913c'
  AND  le.event_type IN ('resource_completed','assessment_completed')
  AND  k.certification_level::text = 'III'
ORDER  BY k.ksa_code;
-- Expected for the SCADA content at Level III: KSA-III-SC-002, KSA-III-SC-003.
```

Paste the output into the manifest assertion table in the evidence packet.

### Backdating check

Confirm `occurred_at` is within a reasonable window of `created_at` (record insertion time). A large
gap indicates a manual or erroneous timestamp:

```sql
SELECT event_id, event_type, occurred_at, created_at,
       EXTRACT(EPOCH FROM (created_at - occurred_at)) AS lag_seconds
FROM   public.learning_events
WHERE  (payload->>'acquisition_run_id') = 'slice2d-rehearsal-01'
ORDER  BY occurred_at;
```

Lag of more than ~300 seconds warrants a note in the evidence packet.

---

## 6. Redaction check (REQUIRED before committing the evidence packet)

Run the guard over the completed evidence packet before staging it:

```bash
bash scripts/learning/redaction_check.sh docs/learning/slice2d/evidence_packet.template.md
```

The guard rejects any email-shaped PII (except `@learning.invalid` synthetic handles) and any term
in `$REDACTION_DENYLIST` (operator-held, not committed). The packet must pass before committing.

---

## 7. Reversal / retire

To retire the rehearsal cohort without deleting it (required — the append-only trigger forbids
deletes of events with FK referents):

```bash
psql "$LEARNING_DEV_DSN" -f scripts/learning/slice2d_retire_cohort.sql
```

This sets `is_active = false` on the provisioned `user_profiles` row(s). Events remain immutable in
`learning_events`. Destructive teardown (DELETE) is permitted only in `learning_test`, never in
`learning_dev`.

---

## 8. Commit the evidence packet

After the redaction check passes:

```bash
git add docs/learning/slice2d/evidence_packet.template.md
git commit -m "docs(learning): Slice 2d rehearsal evidence packet"
```

Ensure `.claude/PLATFORM/slice2d_evidence_map.md` is NOT staged (it is gitignored or operator-held).

---

*End of runbook — Task 6 is operator-executed. Automated infrastructure is Task 5.*
