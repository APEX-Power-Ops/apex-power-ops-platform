# Slice 2d Acquisition Pilot — Evidence Packet

```yaml
data_fidelity: rehearsal
run_id: slice2d-rehearsal-01
content_id: 9c47a9ed-c46b-4d1d-a604-7c68647c913c
date_executed: YYYY-MM-DD
operator: <initials>
```

> **ANNOTATION — coverage_percent is mapping breadth, NOT competence.**
> `coverage_percent` in the read models measures the fraction of KSAs for this content that have
> at least one captured event. It does NOT imply that any KSA has been demonstrated or mastered.
> Do NOT interpret any field in this packet as a competence certification.

---

## 1. Before / After — Four Read Models

Replace each `<PASTE JSON HERE>` block with the raw `jq .` output from the verification commands
in runbook Section 5. Capture baseline BEFORE the event sequence and post-capture AFTER.

### 1a. Progress (`/api/v1/learning/progress`)

**Before:**
```json
<PASTE JSON HERE>
```

**After:**
```json
<PASTE JSON HERE>
```

### 1b. Assessments (`/api/v1/learning/assessments`)

**Before:**
```json
<PASTE JSON HERE>
```

**After:**
```json
<PASTE JSON HERE>
```

### 1c. Competency (`/api/v1/learning/competency`)

**Before:**
```json
<PASTE JSON HERE>
```

**After:**
```json
<PASTE JSON HERE>
```

### 1d. Cohort (`/api/v1/learning/cohort`)

**Before:**
```json
<PASTE JSON HERE>
```

**After:**
```json
<PASTE JSON HERE>
```

---

## 2. KSA Manifest Assertion Table

From the independent SQL manifest (runbook Section 5). Populate `observed` column from the
after-state of the Competency and Progress read models.

| ksa_code | ksa_label | mapping_strength | expected_in_resolver | observed_in_after_state |
|----------|-----------|-----------------|----------------------|------------------------|
| <!-- run the manifest SQL and paste each row here --> | | | yes | yes / no / partial |

**Assertion:** Every `ksa_code` returned by the manifest SQL must appear in the after-state read
models. Any row where `observed_in_after_state` is `no` or `partial` is a gap requiring
investigation before promoting fidelity beyond `rehearsal`.

---

## 3. Per-Fidelity Breakdown

All events in this run carry `data_fidelity: rehearsal`. The breakdown below records event counts
by type. Fill from the SQL backdating query (runbook Section 5) or direct count.

| event_type            | count | fidelity    | notes                                      |
|-----------------------|-------|-------------|--------------------------------------------|
| resource_viewed       |       | rehearsal   |                                            |
| self_assessment       |       | rehearsal   | confidence value: <1-5>                    |
| assessment_completed  |       | rehearsal   | score from graded instrument: <0-100>%     |
| ksa_mapped            |       | rehearsal   |                                            |
| **TOTAL**             |       | rehearsal   |                                            |

No events of fidelity `synthetic` or `authentic` should appear in this run. Any unexpected fidelity
value is a defect.

---

## 4. Occurred_at vs Created_at Backdating Check

Paste the output of the lag query from runbook Section 5:

```
id | event_type | occurred_at | created_at | lag_seconds
---+------------+-------------+------------+------------
<PASTE SQL OUTPUT HERE>
```

**Acceptance criterion:** `lag_seconds` for all rows is less than 300 (5 minutes). Values exceeding
this threshold must be explained in a note below.

Notes: _(none / describe any anomalies here)_

---

## 5. Negative Control

The helper hard-refuses writes to any DSN containing `*.supabase.co` or the prod project ref
`fxoyniqnrlkxfligbxmg`. Record the result of the negative control attempt:

**Test command (do NOT actually execute against prod):**
```bash
LEARNING_DEV_DSN="postgresql://user:pw@db.fxoyniqnrlkxfligbxmg.supabase.co/postgres" \
  learning-capture acquire resource_viewed \
  --content-id 9c47a9ed-c46b-4d1d-a604-7c68647c913c \
  --user-id 00000000-0000-0000-0000-000000000001 \
  --run-id negative-control \
  --observed-by test \
  --evidence-ref nc-01 \
  --fidelity rehearsal
```

**Expected result:** Non-zero exit with error message containing "prod" or "refused" or similar
guard output. The prod database must NOT receive any event.

**Observed result:** _(paste actual output here — run in `learning_test` environment only)_

---

## 6. Redaction Check Result

```
bash scripts/learning/redaction_check.sh docs/learning/slice2d/evidence_packet.template.md
```

**Result:** PASS / FAIL  
**Output:** _(paste one-line output or "no output" if clean)_

The packet MUST pass before it is committed.

---

## 7. Observer Attestation Summary

Each event captured in Section 3 of the runbook has a corresponding entry in the operator-held
evidence map (`.claude/PLATFORM/slice2d_evidence_map.md`, not committed). This section confirms
that all events are attested.

| event_type            | evidence_ref  | attested (Y/N) |
|-----------------------|---------------|----------------|
| resource_viewed       | <pointer>     |                |
| self_assessment       | <pointer>     |                |
| assessment_completed  | <pointer>     |                |
| ksa_mapped            | <pointer>     |                |

All rows must show `Y` before the packet is finalized. An unattested event must be excluded from
the committed packet and the corresponding `learning_events` row flagged for review.

---

*Use only synthetic handles and `@learning.invalid` example addresses in this file.*  
*The real person-to-handle map lives exclusively in `.claude/PLATFORM/slice2d_evidence_map.md`.*
