import pandas as pd

output_file = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\tracker_analysis.txt'
tracker_path = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\Delta Diversified - Alpha LV Tracker.xlsm'

with open(output_file, 'w', encoding='utf-8') as f:
    xl = pd.ExcelFile(tracker_path)
    
    f.write("=" * 70 + "\n")
    f.write("DELTA DIVERSIFIED - ALPHA LV TRACKER ANALYSIS\n")
    f.write("=" * 70 + "\n\n")
    
    f.write(f"Sheet Names: {xl.sheet_names}\n\n")
    
    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(xl, sheet_name=sheet)
            f.write(f"\n{'='*60}\n")
            f.write(f"SHEET: {sheet}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Rows: {len(df)}, Columns: {len(df.columns)}\n")
            f.write(f"Columns: {list(df.columns)}\n\n")
            
            # Show first 25 rows
            f.write("First 25 rows:\n")
            f.write(df.head(25).to_string())
            f.write("\n\n")
            
            # If there's a Designation or Equipment column, show unique values
            for col in ['Designation', 'Equipment', 'Apparatus', 'Task', 'Drawing']:
                if col in df.columns:
                    unique_vals = df[col].dropna().unique()
                    f.write(f"\nUnique {col} values ({len(unique_vals)} total):\n")
                    for val in unique_vals[:30]:
                        f.write(f"  - {val}\n")
                    if len(unique_vals) > 30:
                        f.write(f"  ... and {len(unique_vals)-30} more\n")
        except Exception as e:
            f.write(f"\nError reading sheet {sheet}: {e}\n")

print("Analysis complete - written to", output_file)
