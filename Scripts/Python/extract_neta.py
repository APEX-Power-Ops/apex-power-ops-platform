#!/usr/bin/env python3
"""
NETA Standards PDF Extractor
============================
Extracts structured test checklists from NETA ATS/MTS PDF documents.

Usage:
    python extract_neta.py                    # Process all PDFs in NETA folder
    python extract_neta.py --file "ATS-2025"  # Process specific file
    python extract_neta.py --section "7.6"    # Extract specific section
    python extract_neta.py --format json      # Output as JSON (default: markdown)

Output:
    Creates structured files in Reference_Files/NETA/Extracted/
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

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
    category: str = ""  # Visual/Mechanical or Electrical


@dataclass
class EquipmentSection:
    """A NETA equipment section (e.g., 7.6 Circuit Breakers)"""
    section_number: str
    title: str
    subsection: str = ""
    equipment_type: str = ""
    visual_mechanical_tests: list = field(default_factory=list)
    electrical_tests: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    page_start: int = 0
    page_end: int = 0


class NETAExtractor:
    """Extracts and structures NETA test specifications from PDFs"""
    
    # Section patterns for NETA documents
    SECTION_PATTERN = re.compile(
        r'^(\d+\.\d+(?:\.\d+)?)\s+(.+?)(?:\s*\n|$)',
        re.MULTILINE
    )
    
    # Test item patterns
    TEST_ITEM_PATTERN = re.compile(
        r'^\s*(\d+)\.\s*(.+?)(?:\n|$)',
        re.MULTILINE
    )
    
    # Equipment categories we care about
    EQUIPMENT_SECTIONS = {
        "7.1": "Switchgear and Switchboard Assemblies",
        "7.2": "Switches",
        "7.3": "Metal-Enclosed Busways",
        "7.4": "Motor Control Devices and Motor Control Centers",
        "7.5": "Adjustable Frequency Drives (AFD)",
        "7.6": "Circuit Breakers",
        "7.7": "Protective Relays",
        "7.8": "Instrument Transformers",
        "7.9": "Metering",
        "7.10": "Grounding Systems",
        "7.11": "Ground-Fault Systems",
        "7.12": "Power Transformers",
        "7.13": "Cables",
        "7.14": "Surge Arresters and Surge Protective Devices",
        "7.15": "Automatic Transfer Switches",
        "7.16": "Generators",
        "7.17": "Uninterruptible Power Supply Systems",
        "7.18": "DC Storage Batteries",
        "7.19": "Emergency Systems",
        "7.20": "Motor and Generator Rotating Machinery",
        "7.21": "Capacitors",
        "7.22": "Photovoltaic Systems",
        "7.23": "Wind Turbine Generators",
        "7.24": "Energy Storage Systems",
        "7.25": "High-Voltage Direct Current",
        "7.26": "Electric Vehicle Charging"
    }
    
    def __init__(self, pdf_path: Path, verbose: bool = False):
        self.pdf_path = Path(pdf_path)
        self.verbose = verbose
        self.sections: list[EquipmentSection] = []
        self.doc_type = self._detect_doc_type()
        
    def _detect_doc_type(self) -> str:
        """Detect if this is ATS or MTS"""
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
        """Verbose logging"""
        if self.verbose:
            print(f"  {msg}")
    
    def extract(self) -> list[EquipmentSection]:
        """Main extraction method"""
        print(f"\n📄 Processing: {self.pdf_path.name}")
        print(f"   Document type: {self.doc_type}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"   Total pages: {len(pdf.pages)}")
            
            # First pass: find all section 7.x headers
            self._find_sections(pdf)
            
            # Second pass: extract test items for each section
            self._extract_tests(pdf)
        
        print(f"   ✅ Extracted {len(self.sections)} equipment sections")
        return self.sections
    
    def _find_sections(self, pdf):
        """Find all section 7.x.x headers in the document"""
        current_section = None
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            # Look for section headers like "7.6.1 Circuit Breakers, Vacuum, Medium-Voltage"
            for match in re.finditer(r'^(7\.\d+(?:\.\d+)?)\s+(.+?)$', text, re.MULTILINE):
                section_num = match.group(1)
                title = match.group(2).strip()
                
                # Skip table of contents entries (usually have page numbers at end)
                if re.search(r'\.\s*\d+$', title):
                    continue
                
                # Skip if title is too short (probably not a real header)
                if len(title) < 5:
                    continue
                
                self._log(f"Found section {section_num}: {title[:50]}...")
                
                # Close previous section
                if current_section:
                    current_section.page_end = page_num
                
                # Create new section
                section = EquipmentSection(
                    section_number=section_num,
                    title=title,
                    page_start=page_num
                )
                
                # Determine parent section and equipment type
                parts = section_num.split('.')
                if len(parts) >= 2:
                    parent = f"{parts[0]}.{parts[1]}"
                    section.equipment_type = self.EQUIPMENT_SECTIONS.get(parent, "")
                
                self.sections.append(section)
                current_section = section
        
        # Close last section
        if current_section:
            current_section.page_end = len(pdf.pages) - 1
    
    def _extract_tests(self, pdf):
        """Extract test items for each section"""
        for section in self.sections:
            self._log(f"Extracting tests for {section.section_number}...")
            
            # Get text from section's pages
            section_text = ""
            for page_num in range(section.page_start, min(section.page_end + 1, len(pdf.pages))):
                page = pdf.pages[page_num]
                section_text += (page.extract_text() or "") + "\n"
            
            # Find the section content
            self._parse_section_content(section, section_text)
    
    def _parse_section_content(self, section: EquipmentSection, text: str):
        """Parse the section text to extract test items"""
        
        # Split into Visual/Mechanical and Electrical sections
        vm_match = re.search(
            r'(?:Visual\s+and\s+Mechanical\s+(?:Inspection|Tests?)|A\.\s*Visual\s+and\s+Mechanical)',
            text, re.IGNORECASE
        )
        elec_match = re.search(
            r'(?:Electrical\s+Tests?|B\.\s*Electrical\s+Tests?)',
            text, re.IGNORECASE
        )
        
        # Extract Visual/Mechanical tests
        if vm_match:
            vm_start = vm_match.end()
            vm_end = elec_match.start() if elec_match else len(text)
            vm_text = text[vm_start:vm_end]
            section.visual_mechanical_tests = self._extract_test_items(vm_text, "Visual/Mechanical")
        
        # Extract Electrical tests
        if elec_match:
            elec_text = text[elec_match.end():]
            # Stop at next major section or end
            next_section = re.search(r'\n\d+\.\d+\s+[A-Z]', elec_text)
            if next_section:
                elec_text = elec_text[:next_section.start()]
            section.electrical_tests = self._extract_test_items(elec_text, "Electrical")
    
    def _extract_test_items(self, text: str, category: str) -> list[TestItem]:
        """Extract numbered test items from text"""
        items = []
        
        # Pattern for numbered items like "1. Inspect for physical damage..."
        # Handle multi-line items
        pattern = r'^\s*(\d+)\.\s+(.+?)(?=\n\s*\d+\.\s+|\n\s*[A-Z]\.\s+|\Z)'
        
        for match in re.finditer(pattern, text, re.MULTILINE | re.DOTALL):
            number = match.group(1)
            description = match.group(2).strip()
            
            # Clean up the description
            description = re.sub(r'\s+', ' ', description)  # Normalize whitespace
            description = description.strip()
            
            # Skip if too short or looks like page number
            if len(description) < 10:
                continue
            
            # Extract acceptance criteria if present (often after "shall" or in parentheses)
            criteria = ""
            criteria_match = re.search(r'\(([^)]+)\)$', description)
            if criteria_match:
                criteria = criteria_match.group(1)
            
            items.append(TestItem(
                number=number,
                description=description,
                acceptance_criteria=criteria,
                category=category
            ))
        
        return items
    
    def to_markdown(self) -> str:
        """Convert extracted data to Markdown format"""
        lines = [
            f"# NETA {self.doc_type} Test Specifications",
            f"",
            f"*Extracted from: {self.pdf_path.name}*",
            f"",
            "---",
            ""
        ]
        
        # Group by parent section
        current_parent = ""
        
        for section in self.sections:
            parts = section.section_number.split('.')
            parent = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else section.section_number
            
            # Add parent header if new
            if parent != current_parent:
                current_parent = parent
                parent_title = self.EQUIPMENT_SECTIONS.get(parent, "")
                lines.extend([
                    f"## {parent} {parent_title}",
                    ""
                ])
            
            # Add subsection
            lines.extend([
                f"### {section.section_number} {section.title}",
                ""
            ])
            
            # Visual/Mechanical Tests
            if section.visual_mechanical_tests:
                lines.extend([
                    "#### A. Visual and Mechanical Inspection",
                    ""
                ])
                for item in section.visual_mechanical_tests:
                    lines.append(f"- [ ] **{item.number}.** {item.description}")
                lines.append("")
            
            # Electrical Tests
            if section.electrical_tests:
                lines.extend([
                    "#### B. Electrical Tests",
                    ""
                ])
                for item in section.electrical_tests:
                    lines.append(f"- [ ] **{item.number}.** {item.description}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def to_json(self) -> dict:
        """Convert extracted data to JSON-serializable dict"""
        return {
            "source_file": self.pdf_path.name,
            "document_type": self.doc_type,
            "extraction_version": "1.0",
            "sections": [
                {
                    "section_number": s.section_number,
                    "title": s.title,
                    "equipment_type": s.equipment_type,
                    "visual_mechanical_tests": [asdict(t) for t in s.visual_mechanical_tests],
                    "electrical_tests": [asdict(t) for t in s.electrical_tests],
                }
                for s in self.sections
            ]
        }


def main():
    parser = argparse.ArgumentParser(
        description="Extract NETA test checklists from PDF documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python extract_neta.py                    # Process all PDFs
    python extract_neta.py --file ATS         # Process ATS only  
    python extract_neta.py --format json      # Output as JSON
    python extract_neta.py -v                 # Verbose output
        """
    )
    parser.add_argument(
        "--file", "-f",
        help="Filter to specific file (partial match, e.g., 'ATS' or 'MTS')"
    )
    parser.add_argument(
        "--format", "-o",
        choices=["markdown", "json", "both"],
        default="both",
        help="Output format (default: both)"
    )
    parser.add_argument(
        "--section", "-s",
        help="Extract only specific section (e.g., '7.6' for circuit breakers)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Find NETA folder
    script_dir = Path(__file__).parent.parent.parent  # Go up to RESA_Power_Build
    neta_dir = script_dir / "Reference_Files" / "NETA"
    
    if not neta_dir.exists():
        print(f"❌ NETA folder not found at: {neta_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir = neta_dir / "Extracted"
    output_dir.mkdir(exist_ok=True)
    
    # Find PDF files
    pdf_files = list(neta_dir.glob("*.pdf"))
    
    if args.file:
        pdf_files = [p for p in pdf_files if args.file.upper() in p.name.upper()]
    
    if not pdf_files:
        print(f"❌ No PDF files found in {neta_dir}")
        sys.exit(1)
    
    print(f"\n🔍 NETA Standards Extractor")
    print(f"   Source: {neta_dir}")
    print(f"   Output: {output_dir}")
    print(f"   Files to process: {len(pdf_files)}")
    
    all_sections = []
    
    for pdf_path in pdf_files:
        extractor = NETAExtractor(pdf_path, verbose=args.verbose)
        sections = extractor.extract()
        
        # Filter by section if specified
        if args.section:
            sections = [s for s in sections if s.section_number.startswith(args.section)]
            extractor.sections = sections
        
        all_sections.extend(sections)
        
        # Output files
        base_name = pdf_path.stem.replace(" ", "_")
        
        if args.format in ("markdown", "both"):
            md_path = output_dir / f"{base_name}.md"
            md_path.write_text(extractor.to_markdown(), encoding="utf-8")
            print(f"   📝 Wrote: {md_path.name}")
        
        if args.format in ("json", "both"):
            json_path = output_dir / f"{base_name}.json"
            json_path.write_text(
                json.dumps(extractor.to_json(), indent=2),
                encoding="utf-8"
            )
            print(f"   📋 Wrote: {json_path.name}")
    
    # Summary
    print(f"\n✅ Extraction complete!")
    print(f"   Total sections extracted: {len(all_sections)}")
    
    # Show section summary
    section_counts = {}
    for s in all_sections:
        parts = s.section_number.split('.')
        parent = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else s.section_number
        section_counts[parent] = section_counts.get(parent, 0) + 1
    
    print(f"\n   Section breakdown:")
    for sec, count in sorted(section_counts.items()):
        title = NETAExtractor.EQUIPMENT_SECTIONS.get(sec, "")
        print(f"   • {sec} {title}: {count} subsections")


if __name__ == "__main__":
    main()
