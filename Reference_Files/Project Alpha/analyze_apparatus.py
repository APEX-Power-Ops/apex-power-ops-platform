import pandas as pd

output_file = r'C:\RESA_Power_Build\Reference_Files\Project Alpha\apparatus_analysis.txt'

df = pd.read_excel(r'C:\RESA_Power_Build\Reference_Files\Project Alpha\Master Apparatus List.xlsx')

with open(output_file, 'w') as f:
    f.write("=" * 60 + "\n")
    f.write("PROJECT ALPHA - MASTER APPARATUS LIST ANALYSIS\n")
    f.write("=" * 60 + "\n\n")
    
    f.write(f"Total Equipment Items: {len(df)}\n\n")
    
    f.write("--- UNIQUE SCOPES (Areas/Systems) ---\n")
    for scope in df['Scope'].unique():
        count = len(df[df['Scope'] == scope])
        f.write(f"  {scope}: {count} items\n")
    
    f.write("\n--- UNIQUE APPARATUS CATEGORIES ---\n")
    for cat in df['Apparatus Category'].dropna().unique():
        count = len(df[df['Apparatus Category'] == cat])
        f.write(f"  {cat}: {count} items\n")
    
    f.write("\n--- DESIGNATION FIELD STATUS ---\n")
    designated = df['Designation'].notna().sum()
    missing = df['Designation'].isna().sum()
    f.write(f"  With Designation: {designated}\n")
    f.write(f"  Missing Designation: {missing}\n")
    f.write(f"  Completion: {designated/len(df)*100:.1f}%\n")
    
    f.write("\n--- DRAWING FIELD STATUS ---\n")
    has_drawing = df['Drawing'].notna().sum()
    no_drawing = df['Drawing'].isna().sum()
    f.write(f"  With Drawing Reference: {has_drawing}\n")
    f.write(f"  Missing Drawing: {no_drawing}\n")
    f.write(f"  Completion: {has_drawing/len(df)*100:.1f}%\n")
    
    f.write("\n--- UNIQUE TASKS (Test Types) ---\n")
    for task in df['Task'].unique()[:30]:
        count = len(df[df['Task'] == task])
        f.write(f"  {task}: {count} items\n")
    
    f.write("\n--- SAMPLE: ITEMS WITH DESIGNATIONS ---\n")
    designated_items = df[df['Designation'].notna()][['Task_ID', 'Apparatus', 'Designation', 'Scope']].head(20)
    f.write(designated_items.to_string())
    
print("Analysis complete - written to", output_file)
