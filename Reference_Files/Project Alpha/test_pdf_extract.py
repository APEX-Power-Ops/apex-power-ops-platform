import pdfplumber
import os

output_file = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\pdf_extraction_test.txt'
test_pdf = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\1F0-E602 _1F0EL-SS-A-01_ELECTRICAL ONE LINE DIAGRAM.pdf'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 70 + "\n")
    f.write("PDF EXTRACTION TEST - 1F0EL-SS-A-01\n")
    f.write("=" * 70 + "\n\n")
    
    try:
        with pdfplumber.open(test_pdf) as pdf:
            f.write(f"Pages: {len(pdf.pages)}\n\n")
            
            for page_num, page in enumerate(pdf.pages):
                f.write(f"\n{'='*50}\n")
                f.write(f"PAGE {page_num + 1}\n")
                f.write(f"{'='*50}\n")
                f.write(f"Width: {page.width}, Height: {page.height}\n\n")
                
                # Extract text
                text = page.extract_text()
                if text:
                    f.write("RAW TEXT:\n")
                    f.write("-" * 40 + "\n")
                    f.write(text[:3000] + "\n")
                    if len(text) > 3000:
                        f.write(f"\n... (truncated, total {len(text)} chars)\n")
                else:
                    f.write("No text extracted\n")
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    f.write(f"\n\nTABLES FOUND: {len(tables)}\n")
                    f.write("-" * 40 + "\n")
                    for i, table in enumerate(tables):
                        f.write(f"\nTable {i+1} ({len(table)} rows):\n")
                        for row_num, row in enumerate(table[:15]):  # First 15 rows
                            cleaned = [str(cell)[:30] if cell else '' for cell in row]
                            f.write(f"  {row_num}: {' | '.join(cleaned)}\n")
                        if len(table) > 15:
                            f.write(f"  ... (+{len(table)-15} more rows)\n")
                else:
                    f.write("\nNo tables found\n")
                    
    except Exception as e:
        f.write(f"Error: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

print("Done - check pdf_extraction_test.txt")
