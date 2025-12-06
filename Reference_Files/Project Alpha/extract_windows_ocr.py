"""
Simple image-to-text extraction using Windows OCR (built into Windows 10/11)
No external dependencies needed beyond Pillow
"""
import os
import subprocess
import json
import csv
import re
from datetime import datetime

# Check if we can use Windows OCR via PowerShell
def windows_ocr(image_path):
    """Use Windows.Media.Ocr via PowerShell"""
    ps_script = f'''
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Foundation.IAsyncOperation`1,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.RandomAccessStream,Windows.Foundation,ContentType=WindowsRuntime]

Function Await($WinRtTask, $ResultType) {{
    $asTask = $WinRtTask.GetAwaiter()
    while (-not $asTask.IsCompleted) {{
        Start-Sleep -Milliseconds 50
    }}
    $asTask.GetResult()
}}

$file = [System.IO.File]::OpenRead("{image_path.replace(chr(92), chr(92)+chr(92))}")
$randomAccessStream = [Windows.Storage.Streams.RandomAccessStream]::FromStream($file)
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($randomAccessStream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

$ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$ocrResult = Await ($ocrEngine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
$ocrResult.Text
$file.Close()
'''
    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

# Paths
image_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\Images'
output_folder = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\output'
os.makedirs(output_folder, exist_ok=True)

def extract_bus_duct_name(text):
    """Find bus duct name in OCR text"""
    patterns = [
        r'(1F0[A-Z]{2}-BD-[A-Z]-\d{2}[A-Za-z]?)',
        r'(1FOEL-BD-[A-Z]-O?\d[A-Za-z]?)',  # Handle O vs 0
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).upper()
            # Fix common OCR errors
            name = name.replace('FOEL', 'F0EL').replace('-O', '-0')
            return name
    return None

def parse_table_lines(text, bus_duct):
    """Parse equipment from OCR text"""
    records = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        
        # Skip headers
        if any(h in line.upper() for h in ['EQUIPMENT', 'RATINGS', 'BUS PLUG', 'TAG #', 'VOLTS']):
            continue
        
        # Pattern: Equipment name followed by numbers
        # "ANODE(-) NO.1 CLEANER (TOP) 1 480 250 225"
        match = re.search(r'(.+?)\s+(\d{1,3})\s+(\d{3})\s+(\d{2,4})\s+(\d{2,4})\s*$', line)
        if match:
            equipment = match.group(1).strip()
            if len(equipment) > 5:  # Skip noise
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
    print("BUS DUCT TABLE EXTRACTION (Windows OCR)")
    print("=" * 60)
    
    all_records = []
    all_raw_text = []
    
    image_files = sorted([
        f for f in os.listdir(image_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])
    
    print(f"\nProcessing {len(image_files)} images...\n")
    
    for i, img_file in enumerate(image_files, 1):
        img_path = os.path.join(image_folder, img_file)
        print(f"[{i}/{len(image_files)}] {img_file}...", end=" ", flush=True)
        
        text = windows_ocr(img_path)
        bus_duct = extract_bus_duct_name(text)
        records = parse_table_lines(text, bus_duct)
        
        for r in records:
            r['source_file'] = img_file
        all_records.extend(records)
        
        all_raw_text.append({
            'file': img_file,
            'bus_duct': bus_duct,
            'text': text,
            'records_found': len(records)
        })
        
        print(f"Bus Duct: {bus_duct}, Records: {len(records)}")
    
    # Output
    print(f"\n{'=' * 60}")
    print(f"Total records extracted: {len(all_records)}")
    
    # CSV
    csv_path = os.path.join(output_folder, 'bus_duct_from_images.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        if all_records:
            writer = csv.DictWriter(f, fieldnames=[
                'bus_duct', 'equipment', 'tag_num', 'volts', 'amp_frame', 'amp_trip', 'source_file'
            ])
            writer.writeheader()
            writer.writerows(all_records)
    print(f"CSV: {csv_path}")
    
    # JSON
    json_path = os.path.join(output_folder, 'bus_duct_from_images.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': datetime.now().isoformat(),
            'total_records': len(all_records),
            'files_processed': len(image_files),
            'records': all_records,
            'raw_ocr': all_raw_text
        }, f, indent=2)
    print(f"JSON: {json_path}")
    
    # Raw text for debugging
    txt_path = os.path.join(output_folder, 'ocr_raw_text.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for item in all_raw_text:
            f.write(f"\n{'='*60}\n")
            f.write(f"FILE: {item['file']}\n")
            f.write(f"BUS DUCT: {item['bus_duct']}\n")
            f.write(f"RECORDS: {item['records_found']}\n")
            f.write(f"{'='*60}\n")
            f.write(item['text'] + "\n")
    print(f"RAW: {txt_path}")
    
    print("\nDone!")

if __name__ == '__main__':
    main()
