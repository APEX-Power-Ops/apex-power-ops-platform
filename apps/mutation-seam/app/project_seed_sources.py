from __future__ import annotations

import os
import re
from collections import Counter
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_PROJECT_MINER_PLANNING_ROOT = Path.home() / "Desktop" / "Project Miner PM Planning"
DEFAULT_ESTIMATOR_WORKBOOK_NAME = "Estimator R3 - Project Miner Temp Power Testing.xlsm"
DEFAULT_SLD_PDF_NAME = "Miner Temp SLD-AP-BCARRASCO.pdf"
LEGACY_ESTIMATOR_WORKBOOK_PATH = Path.home() / "Desktop" / DEFAULT_ESTIMATOR_WORKBOOK_NAME
LEGACY_SLD_PDF_PATH = Path.home() / "Desktop" / DEFAULT_SLD_PDF_NAME

TOPOLOGY_PATTERNS = [
    re.compile(r"PWR\s+SKID\s*-\s*[A-Z0-9]+", re.IGNORECASE),
    re.compile(r"MVTX\s*-\s*[A-Z0-9]+", re.IGNORECASE),
    re.compile(r"SWBD\s*-\s*[A-Z0-9]+", re.IGNORECASE),
    re.compile(r"MVS\s*-\s*[A-Z0-9]+", re.IGNORECASE),
    re.compile(r"LVPP\s*-\s*[A-Z0-9]+", re.IGNORECASE),
    re.compile(r"LVTX\s*-\s*[A-Z0-9]+", re.IGNORECASE),
]


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return value


def _normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip()).upper()


def _first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def _project_miner_planning_root() -> Path:
    return Path(
        os.getenv("APEX_PROJECT_MINER_PLANNING_ROOT", str(DEFAULT_PROJECT_MINER_PLANNING_ROOT)).strip()
    )


def _default_paths() -> tuple[str, str]:
    planning_root = _project_miner_planning_root()
    workbook_path = os.getenv("APEX_PROJECT_ESTIMATOR_WORKBOOK")
    sld_path = os.getenv("APEX_PROJECT_SLD_PDF")
    resolved_workbook_path = Path(workbook_path.strip()) if workbook_path else _first_existing_path(
        planning_root / DEFAULT_ESTIMATOR_WORKBOOK_NAME,
        LEGACY_ESTIMATOR_WORKBOOK_PATH,
    )
    resolved_sld_path = Path(sld_path.strip()) if sld_path else _first_existing_path(
        planning_root / DEFAULT_SLD_PDF_NAME,
        LEGACY_SLD_PDF_PATH,
    )
    return str(resolved_workbook_path), str(resolved_sld_path)


def clear_project_seed_cache() -> None:
    load_project_seed_sources.cache_clear()


def extract_topology_labels_from_text(text: str) -> List[str]:
    labels: List[str] = []
    seen = set()
    for pattern in TOPOLOGY_PATTERNS:
        for match in pattern.finditer(text or ""):
            normalized = _normalize_label(match.group(0))
            if normalized not in seen:
                seen.add(normalized)
                labels.append(normalized)
    return labels


def _load_pdf_topology_labels(pdf_path: Path) -> Dict[str, Any]:
    if not pdf_path.exists():
        return {
            "pdf_found": False,
            "topology_labels": [],
            "topology_counts": {},
            "pdf_pages_read": 0,
        }

    try:
        from pypdf import PdfReader
    except Exception:
        return {
            "pdf_found": True,
            "topology_labels": [],
            "topology_counts": {},
            "pdf_pages_read": 0,
        }

    reader = PdfReader(str(pdf_path))
    labels: List[str] = []
    seen = set()
    pages_read = 0
    for page in reader.pages[:8]:
        pages_read += 1
        text = page.extract_text() or ""
        for label in extract_topology_labels_from_text(text):
            if label not in seen:
                seen.add(label)
                labels.append(label)

    counts = Counter(label.split("-")[0].strip() for label in labels)
    return {
        "pdf_found": True,
        "topology_labels": labels,
        "topology_counts": dict(counts),
        "pdf_pages_read": pages_read,
    }


def _workbook_line_items(workbook_path: Path) -> Dict[str, Any]:
    if not workbook_path.exists():
        return {
            "workbook_found": False,
            "sheet_name": None,
            "project_name": None,
            "location": None,
            "drawing_package": None,
            "issue_date": None,
            "line_items": [],
            "expanded_apparatus_candidates": [],
        }

    from openpyxl import load_workbook

    workbook = load_workbook(BytesIO(workbook_path.read_bytes()), data_only=True, read_only=True)
    try:
        sheet_name = "Updated" if "Updated" in workbook.sheetnames else "Quote Tab"
        sheet = workbook[sheet_name]

        row3 = [_clean(value) for value in next(sheet.iter_rows(min_row=3, max_row=3, values_only=True))]
        row4 = [_clean(value) for value in next(sheet.iter_rows(min_row=4, max_row=4, values_only=True))]

        line_items: List[Dict[str, Any]] = []
        expanded_candidates: List[Dict[str, Any]] = []
        line_index = 0
        apparatus_counter = 0

        for row in sheet.iter_rows(min_row=6, values_only=True):
            values = [_clean(value) for value in row]
            qty = values[2] if len(values) > 2 else None
            section = values[3] if len(values) > 3 else None
            apparatus_type = values[4] if len(values) > 4 else None
            designation = values[5] if len(values) > 5 else None
            notes = values[6] if len(values) > 6 else None
            hrs_per_unit = values[8] if len(values) > 8 else None
            hrs_line = values[9] if len(values) > 9 else None

            if apparatus_type is None:
                continue

            try:
                quantity = int(qty)
            except Exception:
                quantity = 1

            line_index += 1
            line_item = {
                "line_id": f"miner-line-{line_index:03d}",
                "qty": quantity,
                "section": section,
                "apparatus_type": apparatus_type,
                "designation": designation,
                "drawing_ref": notes,
                "hrs_per_unit": hrs_per_unit,
                "hrs_line": hrs_line,
            }
            line_items.append(line_item)

            for item_index in range(1, quantity + 1):
                apparatus_counter += 1
                suffix = f"{item_index:02d}" if quantity > 1 else "01"
                display_name = designation or apparatus_type
                expanded_candidates.append(
                    {
                        "candidate_id": f"miner-app-{apparatus_counter:04d}",
                        "line_id": line_item["line_id"],
                        "section": section,
                        "apparatus_type": apparatus_type,
                        "designation": designation,
                        "drawing_ref": notes,
                        "display_name": f"{display_name} {suffix}" if quantity > 1 else str(display_name),
                        "planned_hours": hrs_per_unit,
                    }
                )
    finally:
        workbook.close()

    return {
        "workbook_found": True,
        "sheet_name": sheet_name,
        "project_name": row3[4] if len(row3) > 4 else None,
        "location": row4[4] if len(row4) > 4 else None,
        "drawing_package": row3[5] if len(row3) > 5 else None,
        "issue_date": row4[5] if len(row4) > 5 else None,
        "line_items": line_items,
        "expanded_apparatus_candidates": expanded_candidates,
    }


@lru_cache(maxsize=4)
def load_project_seed_sources(
    estimator_workbook_path: Optional[str] = None,
    sld_pdf_path: Optional[str] = None,
) -> Dict[str, Any]:
    workbook_path = Path(estimator_workbook_path or _default_paths()[0])
    pdf_path = Path(sld_pdf_path or _default_paths()[1])

    workbook_data = _workbook_line_items(workbook_path)
    pdf_data = _load_pdf_topology_labels(pdf_path)

    return {
        "metadata": {
            "estimator_workbook_path": str(workbook_path),
            "estimator_workbook_found": workbook_data["workbook_found"],
            "sld_pdf_path": str(pdf_path),
            "sld_pdf_found": pdf_data["pdf_found"],
        },
        "project_name": workbook_data["project_name"],
        "location": workbook_data["location"],
        "drawing_package": workbook_data["drawing_package"],
        "issue_date": workbook_data["issue_date"],
        "source_sheet": workbook_data["sheet_name"],
        "line_items": workbook_data["line_items"],
        "expanded_apparatus_candidates": workbook_data["expanded_apparatus_candidates"],
        "topology_labels": pdf_data["topology_labels"],
        "topology_counts": pdf_data["topology_counts"],
        "pdf_pages_read": pdf_data["pdf_pages_read"],
    }
