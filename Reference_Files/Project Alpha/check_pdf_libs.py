import os
import subprocess

output_file = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\pdf_libs_check.txt'

with open(output_file, 'w') as f:
    # Try to import PDF library
    try:
        import pdfplumber
        f.write("pdfplumber: AVAILABLE\n")
    except ImportError as e:
        f.write(f"pdfplumber: NOT INSTALLED - {e}\n")
        
    try:
        import fitz  # PyMuPDF
        f.write("PyMuPDF (fitz): AVAILABLE\n")
    except ImportError as e:
        f.write(f"PyMuPDF (fitz): NOT INSTALLED - {e}\n")

    try:
        from pdf2image import convert_from_path
        f.write("pdf2image: AVAILABLE\n")
    except ImportError as e:
        f.write(f"pdf2image: NOT INSTALLED - {e}\n")
        
    try:
        import PyPDF2
        f.write("PyPDF2: AVAILABLE\n")
    except ImportError as e:
        f.write(f"PyPDF2: NOT INSTALLED - {e}\n")

    # Check what's available
    result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
    f.write("\nInstalled packages with 'pdf' in name:\n")
    for line in result.stdout.split('\n'):
        if 'pdf' in line.lower():
            f.write(f"  {line}\n")

print("Check complete")
