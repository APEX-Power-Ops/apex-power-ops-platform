"""Coverage runner for the relay Note-tolerance parser (Chip 3 tier-0).

Reads a JSON array of relay records ``[{"mfr","type","note"}, ...]`` (pulled read-only
from `tcc.relays`; kept OUT of the repo since notes carry incidental names) and reports
what the parser extracts + aggregate coverage. The parser itself
(`services/neta/relay_note_tolerance.py`) + its tests are the committed artifacts; this
script is the one-shot assessment tool.

    python scripts/relay_note_tolerance_coverage.py <notes.json>
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from services.neta.relay_note_tolerance import has_tolerance_signal, parse_note_tolerances


def main(path: str) -> None:
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    gated = 0
    extracted = 0
    by_element: Counter = Counter()
    by_facet: Counter = Counter()
    by_conf: Counter = Counter()

    print(f"=== relay Note-tolerance extraction ({len(records)} records) ===\n")
    for rec in records:
        note = rec.get("note") or ""
        tols = parse_note_tolerances(note)
        if has_tolerance_signal(note):
            gated += 1
        if tols:
            extracted += 1
            print(f"[{rec.get('mfr')} / {rec.get('type')}]")
            for t in tols:
                if t.unit == "pct":
                    band = f"{t.low:+g}% / {t.high:+g}%"
                else:
                    band = f"{t.low:+g} / {t.high:+g} {t.unit}"
                print(f"    {t.element:11s} {t.facet:7s} {band:20s} [{t.confidence}]  «{t.raw[:60]}»")
                by_element[t.element] += 1
                by_facet[t.facet] += 1
                by_conf[t.confidence] += 1
            print()
        elif has_tolerance_signal(note):
            print(f"[{rec.get('mfr')} / {rec.get('type')}]  GATE-PASS but NO extraction (review)\n")

    print("=== coverage summary ===")
    print(f"records:            {len(records)}")
    print(f"tolerance-gated:    {gated}")
    print(f"yielded extraction: {extracted}")
    print(f"by element: {dict(by_element)}")
    print(f"by facet:   {dict(by_facet)}")
    print(f"by conf:    {dict(by_conf)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "relay_tol_notes.json")
