import pandas as pd

output_file = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\apparatus_summary.txt'

with open(output_file, 'w') as f:
    xl = pd.ExcelFile(r'C:\RESA_Power_Build\Reference_Files\Project Alpha\Master Apparatus List.xlsx')
    f.write(f"Sheets: {xl.sheet_names}\n")

    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        f.write(f"\n=== Sheet: {sheet} ===\n")
        f.write(f"Shape: {df.shape}\n")
        f.write(f"Columns: {list(df.columns)}\n")
        f.write("First 20 rows:\n")
        f.write(df.head(20).to_string())
        f.write("\n\n")

print("Done - output written to", output_file)
