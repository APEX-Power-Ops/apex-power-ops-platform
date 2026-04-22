# Question Schema v2
## Practice Test Object Specification (Level II/III/IV)

---

## Purpose
Defines the JSON structure for practice test questions with explicit source citations and Level IV readiness. Null-safe by design; all optional fields must be handled gracefully in rendering.

## Field Definitions
| Field | Required | Type | Validation | Notes |
|-------|----------|------|------------|-------|
| `id` | ✅ | Number | Sequential, no gaps | 1, 2, 3... |
| `question` | ✅ | String | Non-empty | May include inline HTML |
| `options` | ✅ | Array | Exactly 4 strings | Order = A/B/C/D |
| `correct` | ✅ | Number | 0,1,2,3 | 0-indexed |
| `explanation` | ✅ | String | ≥ 50 chars | Technical reasoning |
| `whyMatters` | ✅ | String | ≥ 30 chars | Real-world impact |
| `commonMistake` | ✅ | String | ≥ 30 chars | Frequent error and why |
| `guideRef` | ✅ | Object | `file` and `title` non-empty | Links to study guide |
| `sourceRef` | ⚪ | Array | If present: `{ source, section, topic }` strings | Authoritative citations |
| `levelTag` | ⚪ | String | One of "II","III","IV" | Drives badge styling |
| `ksa` | ⚪ | String | Format `XX-###` | Domain prefixes: ET, SF, CT, SC, TE |
| `difficulty` | ⚪ | String | `foundation`/`core`/`advanced`/`challenge` | Explicit difficulty |

## Example Object (real citations)
```javascript
{
  id: 14,
  question: "During VLF testing of a 15kV XLPE feeder, tan delta at 1.5 U₀ is 25% higher than at 1.0 U₀. This indicates:",
  options: [
    "A) Normal condition within IEEE 400.2 limits",
    "B) Water treeing that warrants investigation",
    "C) Test set leakage causing error",
    "D) Overheating during test"
  ],
  correct: 1,
  explanation: "Tip-up (increase in dissipation factor with voltage) is a water-tree indicator in XLPE. IEEE 400.2-2013 § 6.3 notes that >25% increase from 1.0 U₀ to 1.5 U₀ should trigger further investigation.",
  whyMatters: "Early detection avoids in-service failure, unplanned outages, and safety hazards during switching.",
  commonMistake: "Confusing low absolute tan delta with healthy insulation while ignoring voltage-dependent increase.",
  guideRef: { file: "25-Cable-Testing-Modern.html", title: "Modern Cable Testing Methods" },
  sourceRef: [
    { source: "Paul Gill EPEMT", section: "§ 6.4.2", topic: "VLF Tan Delta" },
    { source: "IEEE 400.2-2013", section: "§ 6.3", topic: "VLF-TD Criteria" },
    { source: "NETA ATS-2025", section: "Table 100.12", topic: "Cable Acceptance" }
  ],
  levelTag: "IV",
  ksa: "CT-042",
  difficulty: "advanced"
}
```

## Validation Rules
- `options.length === 4`
- `correct` in `[0,1,2,3]`
- `sourceRef`: optional; if absent or empty, render no chips/panel
- `levelTag`: optional; if set, must be `II|III|IV`
- `ksa`: optional; matches `/^[A-Z]{2}-\d{3}$/`
- `difficulty`: one of `foundation|core|advanced|challenge`

## Rendering: Source Chips (feedback panel)
```javascript
function renderSourceChips(sourceRef) {
  if (!sourceRef || !Array.isArray(sourceRef) || sourceRef.length === 0) return '';
  const getChipClass = (source) => {
    const s = source.toLowerCase();
    if (s.includes('gill')) return 'chip-gill';
    if (s.includes('neta')) return 'chip-neta';
    if (s.includes('ieee')) return 'chip-ieee';
    if (s.includes('nfpa') || s.includes('70e')) return 'chip-nfpa';
    return 'chip-default';
  };
  const chips = sourceRef.map(ref => `<span class="source-chip ${getChipClass(ref.source)}">${ref.source} ${ref.section}</span>`).join('');
  return `
    <div class="feedback-sources">
      <strong>📚 Sources:</strong>
      <div class="source-chips">${chips}</div>
    </div>
  `;
}
```

## Chip Styles (inline CSS fragment)
```css
.feedback-sources { margin-top: 15px; padding-top: 15px; border-top: 1px dashed rgba(0,0,0,0.15); }
.source-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.source-chip { display: inline-block; padding: 5px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: 500; }
.chip-gill { background: #fef3c7; color: #92400e; }
.chip-neta { background: #dcfce7; color: #166534; }
.chip-ieee { background: #dbeafe; color: #1e40af; }
.chip-nfpa { background: #fee2e2; color: #991b1b; }
.chip-default { background: #f1f5f9; color: #64748b; }
```

## Null Handling
- If `sourceRef` is missing/empty, render nothing (no errors).
- Front-end should tolerate missing optional fields without breaking layout.

## Mapping to Level Badges
- `levelTag` drives active badge styling in study guides/tests. Example: `levelTag: "IV"` → highlight Level IV badge.

## Storage / Future Platform
- Keep `ksa` aligned with `KSA-MASTER-INDEX.md` for migration.
- Maintain `guideRef.file` naming per MASTER-STANDARDS (HTML in NETA-X folders).
