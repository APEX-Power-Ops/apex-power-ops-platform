#!/usr/bin/env python3
"""
NETA Data Import Script
Parses NETA JSON files and generates SQL for Supabase import.

Usage: python import_neta_data.py

Output: Creates SQL files for importing into Supabase.
"""

import json
import os
import uuid
from pathlib import Path
from datetime import datetime

# Configuration
NETA_FILES = {
    'ATS': {'file': 'ANSI_NETA_ATS-2025_Final_v2.json', 'version': '2025'},
    'MTS': {'file': 'ANSI_NETA_MTS-2023_FINAL_v2.json', 'version': '2023'},
    'ECS': {'file': 'ANSI_NETA_ECS-2024_v2.json', 'version': '2024'},
    'ETT': {'file': 'ANSI_NETA_ETT-2022_FINAL_v2.json', 'version': '2022'}
}

NETA_DIR = Path(r'C:\RESA_Power_Build\Reference_Files\NETA\Extracted')
OUTPUT_DIR = Path(r'C:\RESA_Power_Build\Supabase\data')

def escape_sql(text):
    """Escape single quotes for SQL."""
    if text is None:
        return 'NULL'
    return "'" + text.replace("'", "''") + "'"

def generate_uuid():
    """Generate a new UUID."""
    return str(uuid.uuid4())


def parse_neta_file(filepath, standard_type, version):
    """Parse a NETA JSON file and return procedures and test items."""
    procedures = []
    test_items = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sections = data.get('sections', {})
    sort_order = 0
    
    for section_num, section_data in sections.items():
        sort_order += 1
        procedure_id = generate_uuid()
        
        # Count test types
        vm_tests = section_data.get('visual_mechanical_tests', [])
        elec_tests = section_data.get('electrical_tests', [])
        
        has_vm = len(vm_tests) > 0
        has_elec = len(elec_tests) > 0
        has_optional = any(t.get('optional', False) for t in vm_tests + elec_tests)
        
        # Create procedure record
        procedure = {
            'id': procedure_id,
            'standard_type': standard_type,
            'standard_version': version,
            'section_number': section_data.get('section_number', section_num),
            'equipment_category': section_data.get('equipment_category', ''),
            'title': section_data.get('title', ''),
            'has_visual_mechanical': has_vm,
            'has_electrical_tests': has_elec,
            'has_optional_tests': has_optional,
            'sort_order': sort_order
        }
        procedures.append(procedure)
        
        # Create test item records - Visual/Mechanical
        item_sort = 0
        for test in vm_tests:
            item_sort += 1
            test_items.append({
                'id': generate_uuid(),
                'procedure_id': procedure_id,
                'test_type': 'visual_mechanical',
                'test_number': test.get('number', str(item_sort)),
                'description': test.get('description', ''),
                'is_optional': test.get('optional', False),
                'sort_order': item_sort
            })
        
        # Create test item records - Electrical
        for test in elec_tests:
            item_sort += 1
            test_items.append({
                'id': generate_uuid(),
                'procedure_id': procedure_id,
                'test_type': 'electrical',
                'test_number': test.get('number', str(item_sort)),
                'description': test.get('description', ''),
                'is_optional': test.get('optional', False),
                'sort_order': item_sort
            })
    
    return procedures, test_items


def generate_procedures_sql(procedures):
    """Generate SQL INSERT statements for procedures."""
    lines = [
        "-- NETA Procedures Import",
        f"-- Generated: {datetime.now().isoformat()}",
        "-- Source: NETA ATS, MTS, ECS, ETT Standards",
        "",
        "BEGIN;",
        "",
        "INSERT INTO neta_procedures (",
        "  id, standard_type, standard_version, section_number,",
        "  equipment_category, title, has_visual_mechanical,",
        "  has_electrical_tests, has_optional_tests, sort_order",
        ") VALUES"
    ]
    
    values = []
    for p in procedures:
        val = f"""(
    '{p['id']}',
    '{p['standard_type']}'::neta_standard_type,
    '{p['standard_version']}',
    {escape_sql(p['section_number'])},
    {escape_sql(p['equipment_category'])},
    {escape_sql(p['title'])},
    {str(p['has_visual_mechanical']).lower()},
    {str(p['has_electrical_tests']).lower()},
    {str(p['has_optional_tests']).lower()},
    {p['sort_order']}
  )"""
        values.append(val)
    
    lines.append(',\n'.join(values) + ';')
    lines.append("")
    lines.append("COMMIT;")
    return '\n'.join(lines)


def generate_test_items_sql(test_items):
    """Generate SQL INSERT statements for test items."""
    lines = [
        "-- NETA Test Items Import",
        f"-- Generated: {datetime.now().isoformat()}",
        "",
        "BEGIN;",
        "",
        "INSERT INTO neta_test_items (",
        "  id, procedure_id, test_type, test_number,",
        "  description, is_optional, sort_order",
        ") VALUES"
    ]
    
    values = []
    for t in test_items:
        val = f"""(
    '{t['id']}',
    '{t['procedure_id']}',
    '{t['test_type']}'::neta_test_type,
    {escape_sql(t['test_number'])},
    {escape_sql(t['description'])},
    {str(t['is_optional']).lower()},
    {t['sort_order']}
  )"""
        values.append(val)
    
    lines.append(',\n'.join(values) + ';')
    lines.append("")
    lines.append("COMMIT;")
    return '\n'.join(lines)


def main():
    """Main entry point."""
    print("=" * 60)
    print("NETA Data Import Script")
    print("=" * 60)
    
    all_procedures = []
    all_test_items = []
    
    for standard_type, config in NETA_FILES.items():
        filepath = NETA_DIR / config['file']
        version = config['version']
        
        if not filepath.exists():
            print(f"WARNING: File not found: {filepath}")
            continue
        
        print(f"\nProcessing {standard_type} ({config['file']})...")
        procedures, test_items = parse_neta_file(filepath, standard_type, version)
        
        print(f"  - Found {len(procedures)} procedures")
        print(f"  - Found {len(test_items)} test items")
        
        all_procedures.extend(procedures)
        all_test_items.extend(test_items)
    
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {len(all_procedures)} procedures, {len(all_test_items)} test items")
    print(f"{'=' * 60}")
    
    # Generate SQL files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write procedures SQL
    proc_sql = generate_procedures_sql(all_procedures)
    proc_file = OUTPUT_DIR / '20_neta_procedures.sql'
    with open(proc_file, 'w', encoding='utf-8') as f:
        f.write(proc_sql)
    print(f"\nWrote: {proc_file}")
    
    # Write test items SQL
    items_sql = generate_test_items_sql(all_test_items)
    items_file = OUTPUT_DIR / '21_neta_test_items.sql'
    with open(items_file, 'w', encoding='utf-8') as f:
        f.write(items_sql)
    print(f"Wrote: {items_file}")
    
    print("\n✅ Import files generated successfully!")
    print("\nTo import into Supabase, run these SQL files in order:")
    print(f"  1. {proc_file}")
    print(f"  2. {items_file}")

if __name__ == '__main__':
    main()
