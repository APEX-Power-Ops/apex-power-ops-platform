"""
Enhanced SLD Equipment Extraction
Uses pdfplumber (primary) with PyMuPDF fallback
Outputs both TXT and JSON for Claude Desktop compatibility
"""
import pdfplumber
import os
import re
import json
from collections import defaultdict
from datetime import datetime

# Try to import PyMuPDF as fallback
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Note: PyMuPDF not available, using pdfplumber only")

# Paths
pdf_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha'
output_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\output'
os.makedirs(output_folder, exist_ok=True)

# Equipment designation patterns - expanded
patterns = [
    r'1F0[A-Z]{2}-[A-Z]{2,5}-[A-Z]-\d{1,2}[A-Z]?',      # 1F0EL-SS-A-01, 1F0EL-BD-A-01
    r'1F0[A-Z]{2}-[A-Z]{2,5}-\d\s*\d{1,2}[A-Z]?',       # 1F0EL-LP-1 01
    r'1F0[A-Z]{2}-[A-Z]{2,5}-\d{1,2}[A-Z]?',            # 1F0AS-ESWB-02
    r'1F0[A-Z]{2}-[A-Z]{2,5}-[A-Z]\d?-\d{1,2}[A-Z]?',   # Catch variations
]
combined_pattern = '|'.join(f'({p})' for p in patterns)

# Equipment type mapping
EQUIPMENT_TYPES = {
    'SS': 'Switchgear/Substation',
    'BD': 'Breaker/Distribution',
    'ATS': 'Automatic Transfer Switch',
    'UPS': 'Uninterruptible Power Supply',
    'ESWB': 'Emergency Switchboard',
    'DS': 'Disconnect Switch',
    'LP': 'Lighting Panel',
    'LPDP': 'Low Power Distribution Panel',
    'HPDP': 'High Power Distribution Panel',
    'HPP': 'High Power Panel',
    'EHDP': 'Emergency High Distribution Panel',
    'GEN': 'Generator',
}

def get_equipment_type(designation):
    """Extract equipment type from designation"""
    for code, name in EQUIPMENT_TYPES.items():
        if f'-{code}-' in designation or f'-{code}' in designation:
            return {'code': code, 'name': name}
    return {'code': 'UNK', 'name': 'Unknown'}

def extract_with_pdfplumber(pdf_path):
    """Primary extraction method"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return None, str(e)
    return text, None

def extract_with_pymupdf(pdf_path):
    """Fallback extraction method"""
    if not PYMUPDF_AVAILABLE:
        return None, "PyMuPDF not installed"
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        return None, str(e)
    return text, None

def extract_equipment(text):
    """Find all equipment designations in text"""
    found = set()
    for match in re.finditer(combined_pattern, text, re.IGNORECASE):
        designation = match.group(0).strip().upper()
        designation = re.sub(r'\s+', ' ', designation)  # Normalize spaces
        found.add(designation)
    return found

def main():
    results = {
        'extraction_date': datetime.now().isoformat(),
        'total_pdfs': 0,
        'successful_extractions': 0,
        'total_equipment': 0,
        'files': [],
        'all_equipment': [],
        'equipment_by_type': defaultdict(list),
        'equipment_by_sld': defaultdict(list),
    }
    
    all_designations = set()
    
    # Get PDF files
    pdf_files = sorted([f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')])
    results['total_pdfs'] = len(pdf_files)
    
    print(f"Processing {len(pdf_files)} PDF files...")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        
        # Extract SLD name from filename
        sld_match = re.search(r'(1F0[A-Z]{2}-SS-[A-Z]-\d{2})', pdf_file)
        sld_name = sld_match.group(1) if sld_match else pdf_file.split('_')[0]
        
        # Try pdfplumber first
        text, error = extract_with_pdfplumber(pdf_path)
        extraction_method = 'pdfplumber'
        
        # Fallback to PyMuPDF if needed
        if not text and PYMUPDF_AVAILABLE:
            text, error = extract_with_pymupdf(pdf_path)
            extraction_method = 'pymupdf'
        
        file_result = {
            'filename': pdf_file,
            'sld_name': sld_name,
            'method': extraction_method,
            'equipment': [],
            'error': error
        }
        
        if text:
            equipment = extract_equipment(text)
            file_result['equipment'] = sorted(list(equipment))
            all_designations.update(equipment)
            
            for eq in equipment:
                eq_type = get_equipment_type(eq)
                results['equipment_by_type'][eq_type['name']].append(eq)
                results['equipment_by_sld'][sld_name].append(eq)
            
            if equipment:
                results['successful_extractions'] += 1
        
        results['files'].append(file_result)
        
        # Progress
        if i % 10 == 0:
            print(f"  Processed {i}/{len(pdf_files)}...")
    
    # Finalize results
    results['all_equipment'] = sorted(list(all_designations))
    results['total_equipment'] = len(all_designations)
    
    # Convert defaultdicts for JSON
    results['equipment_by_type'] = {k: sorted(list(set(v))) for k, v in results['equipment_by_type'].items()}
    results['equipment_by_sld'] = {k: sorted(list(set(v))) for k, v in results['equipment_by_sld'].items()}
    
    # Write JSON output (for programmatic use)
    json_path = os.path.join(output_folder, 'sld_equipment.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"JSON output: {json_path}")
    
    # Write TXT output (for Claude Desktop readability)
    txt_path = os.path.join(output_folder, 'sld_equipment_summary.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("SLD EQUIPMENT EXTRACTION SUMMARY\n")
        f.write(f"Generated: {results['extraction_date']}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total PDFs processed: {results['total_pdfs']}\n")
        f.write(f"Successful extractions: {results['successful_extractions']}\n")
        f.write(f"Total unique equipment: {results['total_equipment']}\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("EQUIPMENT BY TYPE\n")
        f.write("=" * 80 + "\n\n")
        
        for eq_type, items in sorted(results['equipment_by_type'].items()):
            f.write(f"\n{eq_type} ({len(items)} items):\n")
            f.write("-" * 40 + "\n")
            for item in items:
                f.write(f"  {item}\n")
        
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("ALL EQUIPMENT (ALPHABETICAL)\n")
        f.write("=" * 80 + "\n\n")
        
        for eq in results['all_equipment']:
            eq_type = get_equipment_type(eq)
            f.write(f"  {eq:<25} [{eq_type['code']}]\n")
    
    print(f"TXT output: {txt_path}")
    
    # Write CSV for Excel import
    csv_path = os.path.join(output_folder, 'sld_equipment.csv')
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("Designation,Type_Code,Type_Name,Source_SLD\n")
        for sld, equipment_list in results['equipment_by_sld'].items():
            for eq in equipment_list:
                eq_type = get_equipment_type(eq)
                f.write(f'"{eq}","{eq_type["code"]}","{eq_type["name"]}","{sld}"\n')
    print(f"CSV output: {csv_path}")
    
    print(f"\nDone! Found {results['total_equipment']} unique equipment designations.")

if __name__ == '__main__':
    main()
