"""
Extract Bus Duct Equipment Tables from Screenshot Images
Uses EasyOCR for text recognition, then parses tabular data

Images should be screenshots of the Bus Duct rating tables showing:
- Bus Duct Name (e.g., 1F0EL-BD-A-03b)
- Equipment names
- Tag numbers
- Voltage, Amp Frame, Amp Trip ratings
"""
import os
import re
import json
import csv
from datetime import datetime
from PIL import Image

# Try EasyOCR first, fall back to pytesseract
try:
    import easyocr
    OCR_ENGINE = 'easyocr'
    reader = easyocr.Reader(['en'], gpu=False)  # CPU mode
    print("Using EasyOCR")
except ImportError:
    try:
        import pytesseract
        OCR_ENGINE = 'pytesseract'
        print("Using pytesseract")
    except ImportError:
        print("ERROR: No OCR engine available. Install easyocr or pytesseract")
        exit(1)

# Paths
image_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\Images'
output_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\output'
os.makedirs(output_folder, exist_ok=True)

def ocr_image(image_path):
    """Extract text from image using available OCR engine"""
    if OCR_ENGINE == 'easyocr':
        results = reader.readtext(image_path, detail=0, paragraph=False)
        return '\n'.join(results)
    else:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)

def extract_bus_duct_name(text):
    """Find bus duct name in OCR text"""
    patterns = [
        r'(1F0[A-Z]{2}-BD-[A-Z]-\d{2}[A-Za-z]?)',
        r'BUS\s*DUCT\s*NAME[:\s]*([A-Z0-9\-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None

def parse_equipment_lines(text, bus_duct_name):
    """Parse OCR text to extract equipment records"""
    records = []
    lines = text.split('\n')
    
    # Pattern for equipment lines: EQUIPMENT_NAME TAG# VOLTS FRAME TRIP
    # Example: "ANODE(-) NO.1 CLEANER (TOP) 1 480 250 225"
    
    equipment_pattern = re.compile(
        r'(ANODE.*?|COATER.*?|TRANSFER.*?|FEED.*?|.*?PANEL.*?|.*?MIXER.*?|.*?DIST.*?|1F0[A-Z\-0-9]+)'
        r'[\s,]+(\d{1,3})[\s,]+'  # Tag number
        r'(\d{3})[\s,]+'          # Volts (480, etc)
        r'(\d{2,4})[\s,]+'        # Amp Frame
        r'(\d{2,4})',             # Amp Trip
        re.IGNORECASE
    )
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = equipment_pattern.search(line)
        if match:
            records.append({
                'bus_duct': bus_duct_name or 'UNKNOWN',
                'equipment': match.group(1).strip(),
                'tag_num': match.group(2),
                'volts': match.group(3),
                'amp_frame': match.group(4),
                'amp_trip': match.group(5)
            })
            continue
        
        # Try simpler pattern - just numbers at end
        simple_pattern = re.compile(
            r'(.+?)\s+(\d{1,3})\s+(\d{3})\s+(\d{2,4})\s+(\d{2,4})\s*$'
        )
        match = simple_pattern.search(line)
        if match:
            equipment = match.group(1).strip()
            # Skip header rows
            if any(h in equipment.upper() for h in ['EQUIPMENT', 'BUS PLUG', 'RATINGS']):
                continue
            records.append({
                'bus_duct': bus_duct_name or 'UNKNOWN',
                'equipment': equipment,
                'tag_num': match.group(2),
                'volts': match.group(3),
                'amp_frame': match.group(4),
                'amp_trip': match.group(5)
            })
    
    return records

def process_image(image_path):
    """Process single image and extract equipment data"""
    print(f"  OCR processing...")
    text = ocr_image(image_path)
    
    print(f"  Extracting bus duct name...")
    bus_duct = extract_bus_duct_name(text)
    
    print(f"  Parsing equipment records...")
    records = parse_equipment_lines(text, bus_duct)
    
    return {
        'raw_text': text,
        'bus_duct': bus_duct,
        'records': records
    }

def main():
    print("=" * 60)
    print("BUS DUCT TABLE EXTRACTION FROM IMAGES")
    print(f"OCR Engine: {OCR_ENGINE}")
    print("=" * 60)
    
    all_records = []
    all_results = []
    
    # Get image files
    image_files = sorted([
        f for f in os.listdir(image_folder) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))
    ])
    
    print(f"\nFound {len(image_files)} images\n")
    
    for i, image_file in enumerate(image_files, 1):
        image_path = os.path.join(image_folder, image_file)
        print(f"[{i}/{len(image_files)}] {image_file}")
        
        try:
            result = process_image(image_path)
            result['filename'] = image_file
            all_results.append(result)
            
            for r in result['records']:
                r['source_file'] = image_file
            all_records.extend(result['records'])
            
            print(f"    Bus Duct: {result['bus_duct']}")
            print(f"    Records: {len(result['records'])}")
            
        except Exception as e:
            print(f"    ERROR: {e}")
            all_results.append({
                'filename': image_file,
                'error': str(e),
                'records': []
            })
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total images: {len(image_files)}")
    print(f"Total records: {len(all_records)}")
    
    # Output CSV
    csv_path = os.path.join(output_folder, 'bus_duct_from_images.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if all_records:
            writer = csv.DictWriter(f, fieldnames=[
                'bus_duct', 'equipment', 'tag_num', 'volts', 'amp_frame', 'amp_trip', 'source_file'
            ])
            writer.writeheader()
            writer.writerows(all_records)
    print(f"\nCSV: {csv_path}")
    
    # Output JSON
    json_path = os.path.join(output_folder, 'bus_duct_from_images.json')
    output = {
        'extraction_date': datetime.now().isoformat(),
        'ocr_engine': OCR_ENGINE,
        'total_images': len(image_files),
        'total_records': len(all_records),
        'results': all_results,
        'records': all_records
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"JSON: {json_path}")
    
    # Output raw text (for debugging)
    txt_path = os.path.join(output_folder, 'bus_duct_ocr_raw.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for result in all_results:
            f.write(f"\n{'='*60}\n")
            f.write(f"FILE: {result.get('filename', 'unknown')}\n")
            f.write(f"BUS DUCT: {result.get('bus_duct', 'unknown')}\n")
            f.write(f"{'='*60}\n")
            f.write(result.get('raw_text', '') + "\n")
    print(f"RAW TEXT: {txt_path}")
    
    print("\nDone!")

if __name__ == '__main__':
    main()
