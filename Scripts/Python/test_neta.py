"""Quick test of NETA extraction"""
import pdfplumber
from pathlib import Path

neta_dir = Path(r"c:\RESA_Power_Build\Reference_Files\NETA")
output_dir = neta_dir / "Extracted"
output_dir.mkdir(exist_ok=True)

print(f"NETA dir exists: {neta_dir.exists()}")
print(f"Output dir: {output_dir}")

pdfs = list(neta_dir.glob("*.pdf"))
print(f"Found {len(pdfs)} PDFs:")
for p in pdfs:
    print(f"  - {p.name}")

# Test reading first PDF
if pdfs:
    pdf_path = pdfs[0]
    print(f"\nReading: {pdf_path.name}")
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        # Get page 50 (should be in section 7)
        text = pdf.pages[50].extract_text() or ""
        print(f"\nSample text from page 50:\n{text[:800]}")
        
    # Write a test file
    test_file = output_dir / "test_output.txt"
    test_file.write_text("Test write successful!", encoding="utf-8")
    print(f"\nWrote test file: {test_file}")
