# Source Citation Guide (v2)
## Authoritative Source Formats for NETA Templates

---

## Purpose
Standardize citation text for study guides, practice tests, and feedback panels. Use real sections and table numbers; avoid placeholders.

## Source Types (6)
| Tag Class | Use For | Format | Example (real) |
|-----------|---------|--------|-----------------|
| `source-gill` | Paul Gill EPEMT | `Paul Gill EPEMT § [chapter].[section]` | Paul Gill EPEMT § 6.4.2 - VLF tan delta
| `source-neta` | NETA ATS/MTS/ETT | `NETA [ATS/MTS]-[year] § [section]` or `Table [number]` | NETA ATS-2025 Table 100.12 - Cable acceptance; NETA MTS-2023 § 7.3.2 - Maintenance criteria |
| `source-ieee` | IEEE Standards | `IEEE [number]-[year] § [section]` or `IEEE C57.104-2019 § [section]` | IEEE 400.2-2013 § 6.3 - VLF-TD criteria; IEEE C57.104-2019 § 5.1 - DGA condition levels |
| `source-nfpa` | NFPA 70E/70B | `NFPA [number]-[year] § [article].[section]` | NFPA 70E-2024 § 130.5(C) - Arc flash risk assessment |
| `source-nec` | NEC (NFPA 70) | `NFPA 70-[year] Article [article]` | NFPA 70-2023 Article 250 - Grounding and bonding |
| `source-osha` | OSHA CFR | `29 CFR 1910.[section]` | 29 CFR 1910.333(b) - Hazardous energy control |

## Common IEEE Standards (reference list)
- IEEE 43-2013 § 12.2 – Motor insulation resistance
- IEEE 81-2012 § 10 – Ground testing
- IEEE 142-2007 § 3 – Grounding (Green Book)
- IEEE 399-1997 § 4 – Power system analysis (Brown Book)
- IEEE 400.2-2013 § 6.3 – VLF tan delta criteria
- IEEE 519-2022 § 5 – Harmonics limits
- IEEE 1584-2018 § 4 – Arc flash calculations
- IEEE C37.09-2018 § 5 – Breaker testing
- IEEE C57.12.90-2021 § 10 – Transformer insulation power factor
- IEEE C57.104-2019 § 5 – DGA interpretation

## Usage Rules
1. **Authoritative Only:** Cite standards or Paul Gill; manufacturer docs only when required for equipment-specific values.
2. **Precision:** Include section/table numbers; avoid vague references.
3. **Consistency:** Use the tag class that matches the source type for chips and panels.
4. **Placement:**
   - Study guides: Source panel list items (`source-tag` + detail text).
   - Practice tests: `sourceRef` array rendered as chips in feedback.
5. **Verification:** Cross-check values against the cited section before publishing.

## Example Panel (HTML)
```html
<aside class="sources-panel">
  <h4>📚 Authoritative Sources</h4>
  <ul class="source-list">
    <li><span class="source-tag source-gill">Paul Gill</span><span class="source-detail">EPEMT § 4.3 - Transformer IR</span></li>
    <li><span class="source-tag source-neta">NETA</span><span class="source-detail">ATS-2025 Table 100.1 - Transformer tests</span></li>
    <li><span class="source-tag source-ieee">IEEE</span><span class="source-detail">C57.104-2019 § 5 - DGA condition levels</span></li>
  </ul>
</aside>
```

## Example Chips (Feedback)
```html
<div class="source-chips">
  <span class="source-chip chip-gill">Paul Gill EPEMT § 6.4.2</span>
  <span class="source-chip chip-ieee">IEEE 400.2-2013 § 6.3</span>
  <span class="source-chip chip-neta">NETA ATS-2025 Table 100.12</span>
</div>
```

## Anti-Patterns
- ❌ "Manufacturer manual" without citing section/page
- ❌ "IEEE spec" with no number/year
- ❌ Placeholder text like "TBD" or "Ref needed"
- ❌ Fake sections that do not exist

## Quality Check
- [ ] Source type matches tag class
- [ ] Section/table numbers present
- [ ] Year/version correct
- [ ] Content in guide/test aligns with cited values
