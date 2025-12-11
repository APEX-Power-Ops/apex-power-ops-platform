from PyPDF2 import PdfReader

pdf_path = r'C:\RESA_Power_Build\Reference_Files\PDFs\Stellar Energy - Sundance TIAC Acceptance Testing Report 093024.pdf'
reader = PdfReader(pdf_path)

print(f"Total Pages: {len(reader.pages)}")
print("\n--- Page Content Samples ---\n")

for i in range(min(15, len(reader.pages))):
    text = reader.pages[i].extract_text()
    preview = text[:300].replace('\n', ' ') if text else "(No extractable text - likely image/scan)"
    print(f"Page {i+1}: {preview}...")
    print("-" * 50)
