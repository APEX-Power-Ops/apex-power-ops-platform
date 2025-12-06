import pdfplumber
import os

output_file = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\pdf_extraction_test.txt'
pdf_path = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\1F0-E602 _1F0EL-SS-A-01_ELECTRICAL ONE LINE DIAGRAM.pdf'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"Extracting from: {os.path.basename(pdf_path)}\n")
    f.write("=" * 60 + "\n\n")
    
    with pdfplumber.open(pdf_path) as pdf:
        f.write(f"Number of pages: {len(pdf.pages)}\n\n")
        
        for i, page in enumerate(pdf.pages):
            f.write(f"--- PAGE {i+1} ---\n")
            f.write(f"Page size: {page.width} x {page.height}\n\n")
            
            # Extract text
            text = page.extract_text()
            if text:
                f.write("EXTRACTED TEXT:\n")
                f.write(text)
                f.write("\n\n")
            else:
                f.write("No text extracted from this page\n\n")
            
            # Try to extract tables
            tables = page.extract_tables()
            if tables:
                f.write(f"TABLES FOUND: {len(tables)}\n")
                for j, table in enumerate(tables):
                    f.write(f"\nTable {j+1}:\n")
                    for row in table[:20]:  # First 20 rows
                        f.write(f"  {row}\n")
                f.write("\n")

print("Extraction complete")
