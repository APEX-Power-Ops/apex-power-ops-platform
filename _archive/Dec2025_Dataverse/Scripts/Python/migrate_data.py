#!/usr/bin/env python3
"""
RESA Power - Excel to Dataverse Migration Script
================================================

This script extracts data from the RESA Power Excel workbook and prepares
CSV files that can be imported into Microsoft Dataverse.

Usage:
    python migrate_data.py

Requirements:
    pip install pandas openpyxl

Output:
    Creates CSV files in ./migration_output/ folder
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

# Configuration
INPUT_FILE = 'RESA_Power_-_Project_Data_Entry_MASTER.xlsm'
OUTPUT_DIR = 'migration_output'

def setup_output_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"✓ Created output directory: {OUTPUT_DIR}")
    else:
        print(f"✓ Using existing directory: {OUTPUT_DIR}")

def extract_projects(excel_file):
    """
    Extract project information from Project_Form sheet
    
    Note: This is a template - adjust cell references based on actual layout
    """
    print("\n📊 Extracting Projects...")
    
    try:
        df = pd.read_excel(excel_file, sheet_name='Project_Form', header=None)
        
        # Adjust these indices based on where data actually is in your form
        # Current template assumes specific cell locations
        projects = []
        
        # Example extraction (modify based on actual layout):
        project = {
            'Client': df.iloc[3, 2] if len(df) > 3 and len(df.columns) > 2 else None,
            'ProjectName': df.iloc[4, 2] if len(df) > 4 and len(df.columns) > 2 else None,
            'JobNumber': df.iloc[5, 2] if len(df) > 5 and len(df.columns) > 2 else None,
            'StartDate': df.iloc[6, 2] if len(df) > 6 and len(df.columns) > 2 else None,
            'SiteAddress': df.iloc[7, 2] if len(df) > 7 and len(df.columns) > 2 else None,
            'SiteCity': df.iloc[8, 2] if len(df) > 8 and len(df.columns) > 2 else None,
            'SiteState': df.iloc[9, 2] if len(df) > 9 and len(df.columns) > 2 else None,
            'SiteZip': df.iloc[10, 2] if len(df) > 10 and len(df.columns) > 2 else None,
            'SiteContact': df.iloc[11, 2] if len(df) > 11 and len(df.columns) > 2 else None,
            'ContactPhone': df.iloc[12, 2] if len(df) > 12 and len(df.columns) > 2 else None,
            'ContactEmail': df.iloc[13, 2] if len(df) > 13 and len(df.columns) > 2 else None,
            'ProjectLead': df.iloc[14, 2] if len(df) > 14 and len(df.columns) > 2 else None,
        }
        
        # Only add if there's actual data
        if any(project.values()):
            projects.append(project)
        
        # Extract scope names from column E (index 4)
        scopes = []
        for i in range(3, min(30, len(df))):  # Check rows 3-30
            scope_value = df.iloc[i, 4] if len(df.columns) > 4 else None
            if scope_value and str(scope_value).startswith('Scope_'):
                scopes.append({
                    'ScopeName': scope_value,
                    'ScopeNumber': i - 2,  # Relative position
                    'ProjectJobNumber': project.get('JobNumber')
                })
        
        # Save projects
        projects_df = pd.DataFrame(projects)
        if not projects_df.empty:
            projects_df.to_csv(f'{OUTPUT_DIR}/Projects_Import.csv', index=False)
            print(f"  ✓ Extracted {len(projects_df)} project(s)")
        else:
            print("  ⚠ No project data found in Project_Form")
        
        # Save scopes
        scopes_df = pd.DataFrame(scopes)
        if not scopes_df.empty:
            scopes_df.to_csv(f'{OUTPUT_DIR}/Scopes_Import.csv', index=False)
            print(f"  ✓ Extracted {len(scopes_df)} scope(s)")
        else:
            print("  ⚠ No scope data found")
            
        return projects_df, scopes_df
        
    except Exception as e:
        print(f"  ✗ Error extracting projects: {e}")
        return pd.DataFrame(), pd.DataFrame()

def extract_tasks(excel_file):
    """Extract task data from All_Tasks sheet"""
    print("\n📋 Extracting Tasks...")
    
    try:
        # Read the sheet - it might have headers in row 1 or need to skip rows
        df = pd.read_excel(excel_file, sheet_name='All_Tasks')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Map to Dataverse-friendly names
        column_mapping = {
            'Task': 'TaskName',
            'Task_ID': 'TaskID',
            'Scope': 'Scope',
            'NETA_Standard': 'NETAStandard',
            'Apparatus': 'Apparatus',
            'Designation': 'Designation',
            'Drawing': 'Drawing',
            'STATUS': 'Status',
            'PRIORITY': 'Priority',
            'AVAILABILITY': 'Availability',
            'Assessment': 'Assessment',
            'QUOTED_HOURS': 'QuotedHours',
            'ACTUAL_HOURS': 'ActualHours',
            'REMAINING_HOURS': 'RemainingHours',
            '% COMPLETION': 'PercentComplete',
            'Date Due': 'DateDue',
            'DATE COMPLETED': 'DateCompleted',
            'Notes': 'Notes',
            'TASK_DELAYS': 'TaskDelays',
        }
        
        # Select and rename columns
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        tasks_df = df[available_columns].copy()
        tasks_df.columns = [column_mapping[col] for col in available_columns]
        
        # Convert numeric columns
        numeric_cols = ['QuotedHours', 'ActualHours', 'RemainingHours', 'PercentComplete']
        for col in numeric_cols:
            if col in tasks_df.columns:
                tasks_df[col] = pd.to_numeric(tasks_df[col], errors='coerce')
        
        # Convert date columns
        date_cols = ['DateDue', 'DateCompleted']
        for col in date_cols:
            if col in tasks_df.columns:
                tasks_df[col] = pd.to_datetime(tasks_df[col], errors='coerce')
                # Format as ISO date string for Dataverse
                tasks_df[col] = tasks_df[col].dt.strftime('%Y-%m-%d')
        
        # Remove rows with no task name
        if 'TaskName' in tasks_df.columns:
            tasks_df = tasks_df[tasks_df['TaskName'].notna()]
        
        # Save to CSV
        if not tasks_df.empty:
            tasks_df.to_csv(f'{OUTPUT_DIR}/Tasks_Import.csv', index=False)
            print(f"  ✓ Extracted {len(tasks_df)} tasks")
            print(f"  ℹ Columns: {', '.join(tasks_df.columns)}")
        else:
            print("  ⚠ No task data found")
            
        return tasks_df
        
    except Exception as e:
        print(f"  ✗ Error extracting tasks: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def extract_reference_lists(excel_file):
    """Extract dropdown reference data from All_Lists sheet"""
    print("\n📚 Extracting Reference Lists...")
    
    try:
        df = pd.read_excel(excel_file, sheet_name='All_Lists')
        
        # Extract each reference list type
        reference_lists = {
            'AssessmentTypes': 'ASSESSMENT KEY',
            'StatusValues': 'STATUS KEY',
            'AvailabilityOptions': 'AVAILABILITY KEY',
            'PriorityLevels': 'PRIORITY KEY',
            'NETAStandards': 'NETA_Standard'
        }
        
        for list_name, column_name in reference_lists.items():
            if column_name in df.columns:
                values = df[column_name].dropna().unique()
                # Remove empty strings
                values = [v for v in values if str(v).strip()]
                
                if len(values) > 0:
                    list_df = pd.DataFrame({
                        'Value': values,
                        'DisplayOrder': range(1, len(values) + 1)
                    })
                    list_df.to_csv(f'{OUTPUT_DIR}/{list_name}_Import.csv', index=False)
                    print(f"  ✓ Extracted {len(values)} {list_name}")
                else:
                    print(f"  ⚠ No data found for {list_name}")
            else:
                print(f"  ⚠ Column '{column_name}' not found for {list_name}")
                
    except Exception as e:
        print(f"  ✗ Error extracting reference lists: {e}")

def extract_apparatus(excel_file):
    """Extract apparatus/equipment catalog from Apparatus_List_w_Hours sheet"""
    print("\n🔧 Extracting Apparatus Catalog...")
    
    try:
        df = pd.read_excel(excel_file, sheet_name='Apparatus_List_w_Hours')
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Map columns
        column_mapping = {
            'Apparatus': 'ApparatusName',
            'ATS_Hours': 'ATSHours',
            'MTS_Hours': 'MTSHours',
            'Apparatus_Type': 'ApparatusType',
            'Category': 'Category'
        }
        
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        if available_columns:
            apparatus_df = df[available_columns].copy()
            apparatus_df.columns = [column_mapping[col] for col in available_columns]
            
            # Convert numeric columns
            for col in ['ATSHours', 'MTSHours']:
                if col in apparatus_df.columns:
                    apparatus_df[col] = pd.to_numeric(apparatus_df[col], errors='coerce')
            
            # Remove rows with no apparatus name
            if 'ApparatusName' in apparatus_df.columns:
                apparatus_df = apparatus_df[apparatus_df['ApparatusName'].notna()]
            
            if not apparatus_df.empty:
                apparatus_df.to_csv(f'{OUTPUT_DIR}/Apparatus_Import.csv', index=False)
                print(f"  ✓ Extracted {len(apparatus_df)} apparatus items")
            else:
                print("  ⚠ No apparatus data found")
        else:
            print("  ⚠ Required columns not found in Apparatus sheet")
            
    except Exception as e:
        print(f"  ✗ Error extracting apparatus: {e}")
        import traceback
        traceback.print_exc()

def extract_billing_data(excel_file):
    """Extract billing data from All_Tasks_Billing sheet"""
    print("\n💰 Extracting Billing Data...")
    
    try:
        df = pd.read_excel(excel_file, sheet_name='All_Tasks_Billing')
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Map key billing columns
        column_mapping = {
            'Scope': 'Scope',
            'Task_ID': 'TaskID',
            'Task': 'TaskName',
            'Week_Ending': 'WeekEnding',
            'Billing_Period': 'BillingPeriod',
            'Base_Labor_$': 'BaseLaborAmount',
            'Commute_Hrs': 'CommuteHours',
            'Commute_$': 'CommuteAmount',
            'PM_Hrs': 'PMHours',
            'PM_$': 'PMAmount',
            'Report_Hrs': 'ReportHours',
            'Report_$': 'ReportAmount',
            'Travel_Hrs': 'TravelHours',
            'Travel_$': 'TravelAmount',
            'Travel_Fixed_$': 'TravelFixedAmount',
            'ME_Fixed_$': 'MEFixedAmount',
            'Total_Var_Hrs': 'TotalVariableHours',
            'Total_Var_$': 'TotalVariableAmount',
            'Total_Fixed_$': 'TotalFixedAmount',
            'Subtotal_$': 'SubtotalAmount',
            'Total_Billable_$': 'TotalBillableAmount'
        }
        
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        if available_columns:
            billing_df = df[available_columns].copy()
            billing_df.columns = [column_mapping[col] for col in available_columns]
            
            # Convert numeric/currency columns
            numeric_cols = [col for col in billing_df.columns if 'Hours' in col or 'Amount' in col]
            for col in numeric_cols:
                billing_df[col] = pd.to_numeric(billing_df[col], errors='coerce')
            
            # Convert date columns
            if 'WeekEnding' in billing_df.columns:
                billing_df['WeekEnding'] = pd.to_datetime(billing_df['WeekEnding'], errors='coerce')
                billing_df['WeekEnding'] = billing_df['WeekEnding'].dt.strftime('%Y-%m-%d')
            
            # Remove rows with no task
            if 'TaskName' in billing_df.columns:
                billing_df = billing_df[billing_df['TaskName'].notna()]
            
            if not billing_df.empty:
                billing_df.to_csv(f'{OUTPUT_DIR}/BillingLines_Import.csv', index=False)
                print(f"  ✓ Extracted {len(billing_df)} billing records")
            else:
                print("  ⚠ No billing data found")
        else:
            print("  ⚠ Required billing columns not found")
            
    except Exception as e:
        print(f"  ✗ Error extracting billing data: {e}")
        import traceback
        traceback.print_exc()

def extract_labor_rates(excel_file):
    """Extract labor rate configuration from Scope_Labor_Rates sheet"""
    print("\n⚙️  Extracting Labor Rate Configuration...")
    
    try:
        df = pd.read_excel(excel_file, sheet_name='Scope_Labor_Rates')
        
        # Remove empty rows
        df = df.dropna(how='all')
        
        # This sheet structure varies - adapt as needed
        # Typically might have scope names and associated rates
        
        if not df.empty:
            # Save raw for manual review and mapping
            df.to_csv(f'{OUTPUT_DIR}/LaborRates_Raw.csv', index=False)
            print(f"  ✓ Extracted labor rate data (review LaborRates_Raw.csv for structure)")
            print(f"  ℹ This may require manual mapping based on your specific layout")
        else:
            print("  ⚠ No labor rate data found")
            
    except Exception as e:
        print(f"  ✗ Error extracting labor rates: {e}")

def generate_migration_report(output_dir):
    """Generate a summary report of extracted data"""
    print("\n" + "="*60)
    print("📊 MIGRATION SUMMARY REPORT")
    print("="*60)
    
    files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    
    if not files:
        print("⚠ No CSV files generated")
        return
    
    print(f"\n✓ Generated {len(files)} CSV files:\n")
    
    total_records = 0
    for file in sorted(files):
        try:
            df = pd.read_csv(f'{output_dir}/{file}')
            records = len(df)
            total_records += records
            print(f"  • {file:<35} {records:>6} records")
        except Exception as e:
            print(f"  • {file:<35} ERROR reading file")
    
    print(f"\n{'='*60}")
    print(f"  TOTAL RECORDS: {total_records}")
    print(f"{'='*60}")
    
    print(f"\n📁 All files saved to: {os.path.abspath(output_dir)}/")
    
    print("\n📝 NEXT STEPS:")
    print("  1. Review generated CSV files for data quality")
    print("  2. Create corresponding tables in Dataverse")
    print("  3. Use Dataverse Data Import wizard to import CSVs")
    print("  4. Verify data integrity after import")
    print("  5. Set up relationships between imported tables")

def main():
    """Main execution function"""
    print("="*60)
    print("RESA POWER - DATA MIGRATION SCRIPT")
    print("="*60)
    print(f"Source: {INPUT_FILE}")
    print(f"Output: {OUTPUT_DIR}/")
    print("="*60)
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"\n✗ ERROR: File not found: {INPUT_FILE}")
        print(f"  Please ensure the Excel file is in the same directory as this script.")
        sys.exit(1)
    
    # Create output directory
    setup_output_directory()
    
    # Extract data from each sheet
    try:
        extract_projects(INPUT_FILE)
        extract_tasks(INPUT_FILE)
        extract_reference_lists(INPUT_FILE)
        extract_apparatus(INPUT_FILE)
        extract_billing_data(INPUT_FILE)
        extract_labor_rates(INPUT_FILE)
        
        # Generate summary report
        generate_migration_report(OUTPUT_DIR)
        
        print("\n✓ Migration data preparation complete!")
        print(f"\n📧 If you encounter any issues, please review the CSV files")
        print(f"   and adjust the script based on your actual Excel layout.\n")
        
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
