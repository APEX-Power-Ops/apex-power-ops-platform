#!/usr/bin/env python3
"""
NETA Standards PDF Extractor v2.0
=================================
Improved extraction with better section detection and noise filtering.

Outputs clean, structured test checklists ready for:
- Tech mobile app checklists
- Report generation
- Dataverse template population
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from collections import OrderedDict

try:
    import pdfplumber
except ImportError:
    print("Installing required package: pdfplumber")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
    import pdfplumber


@dataclass
class TestItem:
    """Individual test item from NETA checklist"""
    number: str
    description: str
    acceptance_criteria: str = ""
    notes: str = ""
    is_optional: bool = False  # Items marked with *


@dataclass 
class EquipmentSection:
    """A NETA equipment section (e.g., 7.6.1 Circuit Breakers, Vacuum, MV)"""
    section_number: str
    title: str
    parent_section: str = ""
    equipment_category: str = ""
    visual_mechanical_tests: list = field(default_factory=list)
    electrical_tests: list = field(default_factory=list)
    test_values: list = field(default_factory=list)


# Master equipment categories
EQUIPMENT_CATEGORIES = {
    "7.1": "Switchgear and Switchboard Assemblies",
    "7.2": "Switches",
    "7.3": "Metal-Enclosed Busways",
    "7.4": "Motor Control",
    "7.5": "Adjustable Frequency Drives",
    "7.6": "Circuit Breakers",
    "7.7": "Protective Relays",
    "7.8": "Instrument Transformers",
    "7.9": "Metering",
    "7.10": "Grounding Systems",
    "7.11": "Ground-Fault Systems",
    "7.12": "Power Transformers",
    "7.13": "Cables",
    "7.14": "Surge Protection",
    "7.15": "Automatic Transfer Switches",
    "7.16": "Generators",
    "7.17": "UPS Systems",
    "7.18": "DC Batteries",
    "7.19": "Emergency Systems",
    "7.20": "Rotating Machinery",
    "7.21": "Capacitors",
    "7.22": "Photovoltaic Systems",
    "7.23": "Wind Turbines",
    "7.24": "Energy Storage",
    "7.25": "HVDC",
    "7.26": "EV Charging"
}


class NETAExtractorV2:
    """Improved NETA PDF extraction with better parsing"""
    
    def __init__(self, pdf_path: Path, verbose: bool = False):
        self.pdf_path = Path(pdf_path)
        self.verbose = verbose
        self.sections = OrderedDict()
        self.doc_type = self._detect_doc_type()
        self.raw_text = ""
        
    def _detect_doc_type(self) -> str:
        name = self.pdf_path.name.upper()
        if "ATS" in name:
            return "ATS"
        elif "MTS" in name:
            return "MTS"
        elif "ECS" in name:
            return "ECS"
        elif "ETT" in name:
            return "ETT"
        return "UNKNOWN"
    
    def _log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")
    
    def _clean_text(self, text: str) -> str:
        """Remove PDF artifacts and clean text"""
        # Remove page headers/footers
        text = re.sub(r'Page \d+ ANSI/NETA [A-Z]+-\d+', '', text)
        text = re.sub(r'ANSI/NETA [A-Z]+-\d+', '', text)
        # Remove section numbers appearing as headers
        text = re.sub(r'^\d+\.\s+INSPECTION AND TEST PROCEDURES.*$', '', text, flags=re.MULTILINE)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _is_valid_test_item(self, description: str) -> bool:
        """Filter out noise - keep only real test items"""
        if len(description) < 15:
            return False
        # Skip if looks like page number or header
        if re.match(r'^Page \d+', description):
            return False
        if 'INSPECTION AND TEST PROCEDURES' in description:
            return False
        if 'GENERAL SCOPE' in description:
            return False
        if 'APPLICABLE REFERENCES' in description:
            return False
        # Skip acceptance criteria (these go in a different section)
        if description.startswith('Bolt-torque levels shall be'):
            return False
        if description.startswith('Insulation-resistance values'):
            return False
        if description.startswith('Results of'):
            return False
        return True
    
    def extract(self) -> dict:
        """Main extraction - returns organized equipment sections"""
        print(f"\n📄 Processing: {self.pdf_path.name}")
        print(f"   Document type: NETA {self.doc_type}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"   Total pages: {len(pdf.pages)}")
            
            # Extract all text first
            all_text = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                all_text.append(text)
            self.raw_text = "\n\n".join(all_text)
            
            # Find and parse each Section 7.x.x
            self._parse_sections()
        
        print(f"   ✅ Extracted {len(self.sections)} equipment types")
        return self.sections
    
    def _parse_sections(self):
        """Parse all 7.x.x sections from the document"""
        
        # Pattern to find section headers: "7.6.1 Circuit Breakers, Vacuum, Medium-Voltage"
        section_pattern = re.compile(
            r'^(7\.\d+\.\d+)\s+([A-Z][^0-9\n]+?)(?:\n|$)',
            re.MULTILINE
        )
        
        matches = list(section_pattern.finditer(self.raw_text))
        self._log(f"Found {len(matches)} section headers")
        
        for i, match in enumerate(matches):
            section_num = match.group(1)
            title = match.group(2).strip()
            
            # Clean up title
            title = re.sub(r'\s+', ' ', title)
            title = title.rstrip(',.')
            
            # Skip TOC entries (usually short or have page numbers)
            if len(title) < 5 or re.search(r'\d+$', title):
                continue
                
            # Get parent section (7.6 from 7.6.1)
            parts = section_num.split('.')
            parent = f"{parts[0]}.{parts[1]}"
            category = EQUIPMENT_CATEGORIES.get(parent, "")
            
            # Get content until next section
            start_pos = match.end()
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(self.raw_text)
            
            section_content = self.raw_text[start_pos:end_pos]
            
            # Parse the section content
            section = self._parse_section_content(section_num, title, parent, category, section_content)
            
            # Only add if we found actual tests
            if section.visual_mechanical_tests or section.electrical_tests:
                # Use section_num as key to dedupe
                key = section_num
                if key not in self.sections:
                    self.sections[key] = section
                    self._log(f"  {section_num}: {len(section.visual_mechanical_tests)} V/M, {len(section.electrical_tests)} Elec tests")
    
    def _parse_section_content(self, section_num: str, title: str, parent: str, 
                                category: str, content: str) -> EquipmentSection:
        """Parse a section's content to extract test items"""
        
        section = EquipmentSection(
            section_number=section_num,
            title=title,
            parent_section=parent,
            equipment_category=category
        )
        
        # Find Visual and Mechanical section
        vm_match = re.search(
            r'A\.\s*Visual\s+and\s+Mechanical\s+Inspection',
            content, re.IGNORECASE
        )
        
        # Find Electrical Tests section
        elec_match = re.search(
            r'B\.\s*Electrical\s+Tests?',
            content, re.IGNORECASE
        )
        
        # Find Test Values section (C.)
        values_match = re.search(
            r'C\.\s*Test\s+Values',
            content, re.IGNORECASE
        )
        
        # Extract Visual/Mechanical tests
        if vm_match:
            vm_start = vm_match.end()
            vm_end = elec_match.start() if elec_match else (values_match.start() if values_match else len(content))
            vm_text = content[vm_start:vm_end]
            section.visual_mechanical_tests = self._extract_numbered_items(vm_text)
        
        # Extract Electrical tests
        if elec_match:
            elec_start = elec_match.end()
            elec_end = values_match.start() if values_match else len(content)
            elec_text = content[elec_start:elec_end]
            section.electrical_tests = self._extract_numbered_items(elec_text)
        
        return section
    
    def _extract_numbered_items(self, text: str) -> list:
        """Extract numbered test items from a section"""
        items = []
        
        # Pattern: starts with number and period, captures until next number or section marker
        # Handle both "1. Test description" and sub-items like "1. Test\n  a. Sub-test"
        pattern = re.compile(
            r'^\s*(\d+)\.\s+(.+?)(?=\n\s*\d+\.\s+|\n\s*[A-Z]\.\s+|\Z)',
            re.MULTILINE | re.DOTALL
        )
        
        for match in pattern.finditer(text):
            number = match.group(1)
            description = match.group(2).strip()
            
            # Clean the description
            description = self._clean_text(description)
            
            # Check if valid test item
            if not self._is_valid_test_item(description):
                continue
            
            # Check if optional (marked with *)
            is_optional = description.startswith('*')
            if is_optional:
                description = description[1:].strip()
            
            items.append(TestItem(
                number=number,
                description=description,
                is_optional=is_optional
            ))
        
        return items
    
    def to_markdown(self) -> str:
        """Generate clean Markdown output"""
        lines = [
            f"# NETA {self.doc_type} Test Specifications",
            "",
            f"*Source: {self.pdf_path.name}*",
            "",
            "---",
            ""
        ]
        
        current_parent = ""
        
        for section_num, section in self.sections.items():
            # Add category header
            if section.parent_section != current_parent:
                current_parent = section.parent_section
                cat_name = EQUIPMENT_CATEGORIES.get(current_parent, "")
                lines.extend([
                    f"## {current_parent} {cat_name}",
                    ""
                ])
            
            # Section header
            lines.extend([
                f"### {section.section_number} {section.title}",
                ""
            ])
            
            # Visual/Mechanical Tests
            if section.visual_mechanical_tests:
                lines.append("**A. Visual and Mechanical Inspection**")
                lines.append("")
                for item in section.visual_mechanical_tests:
                    opt = " *(optional)*" if item.is_optional else ""
                    lines.append(f"- [ ] {item.number}. {item.description}{opt}")
                lines.append("")
            
            # Electrical Tests
            if section.electrical_tests:
                lines.append("**B. Electrical Tests**")
                lines.append("")
                for item in section.electrical_tests:
                    opt = " *(optional)*" if item.is_optional else ""
                    lines.append(f"- [ ] {item.number}. {item.description}{opt}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_json(self) -> dict:
        """Generate JSON output for programmatic use"""
        return {
            "source_file": self.pdf_path.name,
            "document_type": self.doc_type,
            "extraction_version": "2.0",
            "equipment_categories": EQUIPMENT_CATEGORIES,
            "sections": {
                num: {
                    "section_number": s.section_number,
                    "title": s.title,
                    "parent_section": s.parent_section,
                    "equipment_category": s.equipment_category,
                    "visual_mechanical_tests": [
                        {"number": t.number, "description": t.description, "optional": t.is_optional}
                        for t in s.visual_mechanical_tests
                    ],
                    "electrical_tests": [
                        {"number": t.number, "description": t.description, "optional": t.is_optional}
                        for t in s.electrical_tests
                    ]
                }
                for num, s in self.sections.items()
            }
        }
    
    def to_dataverse_templates(self) -> list:
        """Generate templates ready for Dataverse import"""
        templates = []
        
        for section_num, section in self.sections.items():
            template = {
                "neta_section": section.section_number,
                "equipment_type": section.title,
                "category": section.equipment_category,
                "test_items": []
            }
            
            # Add V/M tests
            for item in section.visual_mechanical_tests:
                template["test_items"].append({
                    "test_type": "Visual/Mechanical",
                    "test_number": f"A.{item.number}",
                    "description": item.description,
                    "is_optional": item.is_optional,
                    "requires_value": False
                })
            
            # Add Electrical tests
            for item in section.electrical_tests:
                # Check if this test requires a recorded value
                requires_value = any(kw in item.description.lower() for kw in [
                    'measure', 'record', 'test', 'perform insulation', 'perform resistance'
                ])
                template["test_items"].append({
                    "test_type": "Electrical",
                    "test_number": f"B.{item.number}",
                    "description": item.description,
                    "is_optional": item.is_optional,
                    "requires_value": requires_value
                })
            
            templates.append(template)
        
        return templates


def main():
    parser = argparse.ArgumentParser(description="NETA PDF Extractor v2.0")
    parser.add_argument("--file", "-f", help="Filter to specific file (e.g., 'ATS')")
    parser.add_argument("--format", "-o", choices=["markdown", "json", "dataverse", "all"], 
                        default="all", help="Output format")
    parser.add_argument("--section", "-s", help="Extract specific section (e.g., '7.6')")
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    # Find NETA folder
    script_dir = Path(__file__).parent.parent.parent
    neta_dir = script_dir / "Reference_Files" / "NETA"
    
    if not neta_dir.exists():
        print(f"❌ NETA folder not found: {neta_dir}")
        sys.exit(1)
    
    output_dir = neta_dir / "Extracted"
    output_dir.mkdir(exist_ok=True)
    
    # Find PDFs
    pdf_files = list(neta_dir.glob("*.pdf"))
    if args.file:
        pdf_files = [p for p in pdf_files if args.file.upper() in p.name.upper()]
    
    if not pdf_files:
        print("❌ No PDF files found")
        sys.exit(1)
    
    print(f"\n🔍 NETA Extractor v2.0")
    print(f"   Source: {neta_dir}")
    print(f"   Output: {output_dir}")
    
    all_templates = []
    
    for pdf_path in sorted(pdf_files):
        extractor = NETAExtractorV2(pdf_path, verbose=args.verbose)
        sections = extractor.extract()
        
        # Filter by section if specified
        if args.section:
            sections = {k: v for k, v in sections.items() if k.startswith(args.section)}
            extractor.sections = sections
        
        base_name = pdf_path.stem.replace(" ", "_")
        
        # Output Markdown
        if args.format in ("markdown", "all"):
            md_path = output_dir / f"{base_name}_v2.md"
            md_path.write_text(extractor.to_markdown(), encoding="utf-8")
            print(f"   📝 {md_path.name}")
        
        # Output JSON
        if args.format in ("json", "all"):
            json_path = output_dir / f"{base_name}_v2.json"
            json_path.write_text(json.dumps(extractor.to_json(), indent=2), encoding="utf-8")
            print(f"   📋 {json_path.name}")
        
        # Output Dataverse templates
        if args.format in ("dataverse", "all"):
            templates = extractor.to_dataverse_templates()
            all_templates.extend(templates)
    
    # Write combined Dataverse templates
    if args.format in ("dataverse", "all") and all_templates:
        dv_path = output_dir / "neta_dataverse_templates.json"
        dv_path.write_text(json.dumps(all_templates, indent=2), encoding="utf-8")
        print(f"   🗄️  {dv_path.name} ({len(all_templates)} equipment types)")
    
    print(f"\n✅ Complete!")


if __name__ == "__main__":
    main()
