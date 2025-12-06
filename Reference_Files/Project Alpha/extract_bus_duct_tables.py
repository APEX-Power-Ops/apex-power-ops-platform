"""
Extract Bus Duct Equipment Tables from SLD PDFs
These tables show: Bus Duct Name, Equipment, Tag#, Volts, Amp Frame, Amp Trip

Uses pdfplumber's table detection to extract structured data
"""
import pdfplumber
import os
import re
import json
import csv
from datetime import datetime

# Paths
pdf_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha'
output_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\output'
os.makedirs(output_folder, exist_ok=True)

def clean_cell(cell):
    """Clean up cell values"""
    if cell is None:
        return ""
    cell = str(cell).strip()
    cell = re.sub(r'\s+', ' ', cell)  # Normalize whitespace
    return cell

def extract_bus_duct_name(text):
    """Extract bus duct name from PDF text (e.g., 1F0EL-BD-A-03b)"""
    patterns = [
        r'BUS DUCT NAME[:\s]*([A-Z0-9\-]+)',
        r'(1F0[A-Z]{2}-BD-[A-Z]-\d{2}[A-Za-z]?)',
        r'(1F0[A-Z]{2}-[A-Z]{2,5}-[A-Z0-9\-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None

def is_equipment_table(table):
    """Check if table looks like an equipment ratings table"""
    if not table or len(table) < 2:
        return False
    
    # Check header row for keywords
    header = ' '.join(str(cell or '').upper() for cell in table[0])
    keywords = ['EQUIPMENT', 'TAG', 'VOLT', 'AMP', 'FRAME', 'TRIP', 'RATING']
    
    matches = sum(1 for kw in keywords if kw in header)
    return matches >= 2

def parse_equipment_table(table, bus_duct_name):
    """Parse equipment table into structured records"""
    records = []
    
    if not table or len(table) < 2:
        return records
    
    # Find header row
    header_idx = 0
    for i, row in enumerate(table[:3]):  # Check first 3 rows for header
        row_text = ' '.join(str(cell or '').upper() for cell in row)
        if 'EQUIPMENT' in row_text or 'TAG' in row_text:
            header_idx = i
            break
    
    # Map columns
    header = [clean_cell(c).upper() for c in table[header_idx]]
    col_map = {}
    
    for i, h in enumerate(header):
        if 'EQUIPMENT' in h:
            col_map['equipment'] = i
        elif 'TAG' in h:
            col_map['tag'] = i
        elif 'VOLT' in h:
            col_map['volts'] = i
        elif 'FRAME' in h:
            col_map['amp_frame'] = i
        elif 'TRIP' in h:
            col_map['amp_trip'] = i
    
    # Parse data rows
    for row in table[header_idx + 1:]:
        if not row or all(cell is None or str(cell).strip() == '' for cell in row):
            continue
        
        record = {
            'bus_duct': bus_duct_name or 'UNKNOWN',
            'equipment': '',
            'tag_num': '',
            'volts': '',
            'amp_frame': '',
            'amp_trip': ''
        }
        
        for field, idx in col_map.items():
            if idx < len(row):
                value = clean_cell(row[idx])
                # Skip header-like values in data rows
                if value.upper() in ['EQUIPMENT', 'TAG', 'TAG #', 'VOLTS', 'AMP', 'FRAME', 'TRIP']:
                    continue
                record[field] = value
        
        # Only add if we have meaningful data
        if record['equipment'] or record['tag_num']:
            records.append(record)
    
    return records

def extract_tables_from_pdf(pdf_path):
    """Extract all equipment tables from a PDF"""
    all_records = []
    bus_duct_name = None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # First pass: get bus duct name from text
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            bus_duct_name = extract_bus_duct_name(full_text)
            
            # Second pass: extract tables
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                
                for table in tables:
                    if is_equipment_table(table):
                        records = parse_equipment_table(table, bus_duct_name)
                        for r in records:
                            r['source_page'] = page_num
                        all_records.extend(records)
    
    except Exception as e:
        print(f"  Error: {e}")
        return [], None, str(e)
    
    return all_records, bus_duct_name, None

def main():
    print("=" * 60)
    print("BUS DUCT EQUIPMENT TABLE EXTRACTION")
    print("=" * 60)
    
    all_records = []
    file_results = []
    
    # Get PDF files
    pdf_files = sorted([f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')])
    print(f"\nProcessing {len(pdf_files)} PDF files...\n")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        print(f"[{i}/{len(pdf_files)}] {pdf_file[:50]}...")
        
        records, bus_duct, error = extract_tables_from_pdf(pdf_path)
        
        file_result = {
            'filename': pdf_file,
            'bus_duct': bus_duct,
            'records_found': len(records),
            'error': error
        }
        file_results.append(file_result)
        
        if records:
            for r in records:
                r['source_file'] = pdf_file
            all_records.extend(records)
            print(f"    Found {len(records)} equipment records (Bus Duct: {bus_duct})")
    
    print(f"\n{'=' * 60}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total equipment records: {len(all_records)}")
    
    # Write CSV output
    csv_path = os.path.join(output_folder, 'bus_duct_equipment.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'bus_duct', 'equipment', 'tag_num', 'volts', 'amp_frame', 'amp_trip', 
            'source_file', 'source_page'
        ])
        writer.writeheader()
        writer.writerows(all_records)
    print(f"\nCSV output: {csv_path}")
    
    # Write JSON output
    json_path = os.path.join(output_folder, 'bus_duct_equipment.json')
    output_data = {
        'extraction_date': datetime.now().isoformat(),
        'total_files': len(pdf_files),
        'files_with_tables': sum(1 for f in file_results if f['records_found'] > 0),
        'total_records': len(all_records),
        'file_results': file_results,
        'records': all_records
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    print(f"JSON output: {json_path}")
    
    # Write summary TXT for Claude Desktop
    txt_path = os.path.join(output_folder, 'bus_duct_equipment_summary.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("BUS DUCT EQUIPMENT EXTRACTION SUMMARY\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total PDFs processed: {len(pdf_files)}\n")
        f.write(f"PDFs with equipment tables: {sum(1 for f in file_results if f['records_found'] > 0)}\n")
        f.write(f"Total equipment records: {len(all_records)}\n\n")
        
        # Group by bus duct
        by_bus_duct = {}
        for r in all_records:
            bd = r['bus_duct']
            if bd not in by_bus_duct:
                by_bus_duct[bd] = []
            by_bus_duct[bd].append(r)
        
        f.write("=" * 80 + "\n")
        f.write("EQUIPMENT BY BUS DUCT\n")
        f.write("=" * 80 + "\n")
        
        for bus_duct in sorted(by_bus_duct.keys()):
            records = by_bus_duct[bus_duct]
            f.write(f"\n{bus_duct} ({len(records)} items)\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'Tag':<6} {'Equipment':<40} {'V':<5} {'Frame':<6} {'Trip':<6}\n")
            f.write("-" * 60 + "\n")
            
            for r in records:
                f.write(f"{r['tag_num']:<6} {r['equipment'][:40]:<40} {r['volts']:<5} {r['amp_frame']:<6} {r['amp_trip']:<6}\n")
    
    print(f"TXT output: {txt_path}")
    print("\nDone!")

if __name__ == '__main__':
    main()
