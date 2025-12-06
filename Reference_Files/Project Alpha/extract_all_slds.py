import pdfplumber
import os
import re
from collections import defaultdict

output_file = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\sld_equipment_extraction.txt'
pdf_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha'

# Equipment designation patterns
# Format: 1F0XX-YYY-N NN or 1F0XX-YYY-A-NN
patterns = [
    r'1F0[A-Z]{2}-[A-Z]{2,5}-[A-Z0-9]-?\d{1,2}[A-Z]?',  # 1F0EL-BD-A-01, 1F0EL-SS-A-01
    r'1F0[A-Z]{2}-[A-Z]{2,5}-\d\s*\d{1,2}[A-Z]?',       # 1F0EL-LP-1 01
]

combined_pattern = '|'.join(f'({p})' for p in patterns)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("SLD EQUIPMENT EXTRACTION - ALL PDFs\n")
    f.write("=" * 80 + "\n\n")
    
    # Get all PDF files
    pdf_files = sorted([fn for fn in os.listdir(pdf_folder) if fn.endswith('.pdf')])
    f.write(f"Total PDFs found: {len(pdf_files)}\n\n")
    
    all_equipment = defaultdict(set)  # SLD -> set of equipment
    all_designations = set()
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        
        # Extract SLD designation from filename
        # Pattern: 1F0-E6XX _1F0XX-SS-X-XX_...
        sld_match = re.search(r'(1F0[A-Z]{2}-SS-[A-Z]-\d{2})', pdf_file)
        if sld_match:
            sld_name = sld_match.group(1)
        else:
            # Try alternate patterns
            sld_match2 = re.search(r'(EMERGENCY|DATA CENTER|GENERATOR)', pdf_file, re.I)
            sld_name = pdf_file.split('_')[0] if not sld_match2 else pdf_file[:30]
        
        f.write(f"\n{'='*60}\n")
        f.write(f"FILE: {pdf_file}\n")
        f.write(f"SLD: {sld_name}\n")
        f.write(f"{'='*60}\n")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                # Find all equipment designations
                found = set()
                for match in re.finditer(combined_pattern, full_text):
                    designation = match.group(0).strip()
                    # Clean up spacing
                    designation = re.sub(r'\s+', ' ', designation)
                    found.add(designation)
                    all_designations.add(designation)
                    all_equipment[sld_name].add(designation)
                
                if found:
                    f.write(f"Equipment found ({len(found)}):\n")
                    for eq in sorted(found):
                        f.write(f"  - {eq}\n")
                else:
                    f.write("No equipment designations found\n")
                    # Show sample of text for debugging
                    f.write(f"Sample text (first 500 chars): {full_text[:500]}\n")
                    
        except Exception as e:
            f.write(f"Error: {str(e)}\n")
    
    # Summary
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("EXTRACTION SUMMARY\n")
    f.write("=" * 80 + "\n\n")
    
    f.write(f"Total unique equipment designations: {len(all_designations)}\n\n")
    
    f.write("ALL UNIQUE DESIGNATIONS:\n")
    f.write("-" * 40 + "\n")
    for eq in sorted(all_designations):
        f.write(f"  {eq}\n")
    
    f.write(f"\n\nEQUIPMENT BY SLD:\n")
    f.write("-" * 40 + "\n")
    for sld in sorted(all_equipment.keys()):
        equip_list = all_equipment[sld]
        f.write(f"\n{sld} ({len(equip_list)} items):\n")
        for eq in sorted(equip_list):
            f.write(f"    {eq}\n")

print("Done - check sld_equipment_extraction.txt")
