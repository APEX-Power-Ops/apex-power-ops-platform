"""
Extract Bus Duct Equipment Tables from Images using Tesseract OCR
"""
import os
import re
import json
import csv
from datetime import datetime
from PIL import Image
import pytesseract

# Set Tesseract path (adjust if needed)
tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Users\jjswe\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
]
for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        print(f"Using Tesseract: {path}")
        break

# Paths  
image_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\Images'
output_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\output'
os.makedirs(output_folder, exist_ok=True)

def ocr_image(image_path):
    """OCR an image with Tesseract"""
    img = Image.open(image_path)
    # Use PSM 6 for uniform block of text (good for tables)
    text = pytesseract.image_to_string(img, config='--psm 6')
    return text

def extract_bus_duct_name(text):
    """Find bus duct name"""
    patterns = [
        r'(1F0[A-Z]{2}-BD-[A-Z]-\d{2}[A-Za-z]?)',
        r'(1FOEL-BD-[A-Z]-O?\d+[A-Za-z]?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).upper()
            return name
    return None

def parse_equipment(text, bus_duct):
    """Parse equipment records from OCR text"""
    records = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 15:
            continue
        
        # Skip headers
        if any(h in line.upper() for h in ['EQUIPMENT', 'RATINGS', 'BUS PLUG', 'AMP FRAME', 'VOLTS']):
            continue
        
        # Try to match: EQUIPMENT TAG VOLTS FRAME TRIP
        # Handle various spacing patterns
        match = re.search(
            r'([A-Z].*?)\s+(\d{1,3})\s+(\d{3})\s+(\d{2,4})\s+(\d{2,4})',
            line, re.IGNORECASE
        )
        if match:
            equipment = match.group(1).strip()
            # Filter out noise
            if len(equipment) > 5 and not equipment.startswith(('BUS', 'TAG', 'AMP')):
                records.append({
                    'bus_duct': bus_duct or 'UNKNOWN',
                    'equipment': equipment,
                    'tag_num': match.group(2),
                    'volts': match.group(3),
                    'amp_frame': match.group(4),
                    'amp_trip': match.group(5)
                })
    
    return records

def main():
    print("=" * 60)
    print("BUS DUCT TABLE EXTRACTION (Tesseract OCR)")
    print("=" * 60)
    
    all_records = []
    all_raw = []
    
    image_files = sorted([
        f for f in os.listdir(image_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])
    
    print(f"\nProcessing {len(image_files)} images...\n")
    
    for i, img_file in enumerate(image_files, 1):
        img_path = os.path.join(image_folder, img_file)
        print(f"[{i}/{len(image_files)}] {img_file}...", end=" ", flush=True)
        
        try:
            text = ocr_image(img_path)
            bus_duct = extract_bus_duct_name(text)
            records = parse_equipment(text, bus_duct)
            
            for r in records:
                r['source_file'] = img_file
            all_records.extend(records)
            
            all_raw.append({
                'file': img_file,
                'bus_duct': bus_duct,
                'records': len(records),
                'text': text
            })
            
            print(f"Bus: {bus_duct}, Records: {len(records)}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            all_raw.append({
                'file': img_file,
                'error': str(e)
            })
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"TOTAL RECORDS: {len(all_records)}")
    print(f"{'=' * 60}")
    
    # CSV output
    csv_path = os.path.join(output_folder, 'bus_duct_from_images.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if all_records:
            writer = csv.DictWriter(f, fieldnames=[
                'bus_duct', 'equipment', 'tag_num', 'volts', 'amp_frame', 'amp_trip', 'source_file'
            ])
            writer.writeheader()
            writer.writerows(all_records)
    print(f"\nCSV: {csv_path}")
    
    # JSON output
    json_path = os.path.join(output_folder, 'bus_duct_from_images.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'engine': 'tesseract',
            'total_records': len(all_records),
            'records': all_records,
            'raw': all_raw
        }, f, indent=2)
    print(f"JSON: {json_path}")
    
    # Raw text for review
    txt_path = os.path.join(output_folder, 'ocr_raw_tesseract.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for item in all_raw:
            f.write(f"\n{'='*60}\n")
            f.write(f"FILE: {item.get('file')}\n")
            f.write(f"BUS DUCT: {item.get('bus_duct')}\n")
            f.write(f"RECORDS: {item.get('records', 0)}\n")
            f.write(f"{'='*60}\n")
            f.write(item.get('text', item.get('error', '')) + "\n")
    print(f"RAW: {txt_path}")
    
    print("\nDone!")

if __name__ == '__main__':
    main()
