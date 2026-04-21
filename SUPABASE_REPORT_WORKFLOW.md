# Apex Power Ops - Automated Report Generation Workflow

## Overview

This document outlines the proposed automated report generation system using Supabase as the backend infrastructure. The goal is to eliminate manual bottlenecks in report creation by allowing technicians to generate branded, professional reports directly from project data.

## Current Pain Points

- Report creation requires manual editing of PowerPoint/Visme templates
- Technicians struggle with formatting preservation
- Jason is a bottleneck in the current workflow
- Multiple tools involved (Adobe Express, Visme, Word, PDF)
- Risk of inconsistent branding and formatting errors

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TECH WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐    ┌──────────────┐    ┌───────────────────┐    │
│   │  Select  │───▶│ Auto-Fill    │───▶│  Review & Submit  │    │
│   │  Project │    │ Form Fields  │    │                   │    │
│   └──────────┘    └──────────────┘    └─────────┬─────────┘    │
│                                                 │               │
└─────────────────────────────────────────────────┼───────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SUPABASE BACKEND                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌────────────────┐   │
│   │   Database   │───▶│ Edge Function│───▶│    Storage     │   │
│   │  (Postgres)  │    │  (Generate)  │    │  (Final PDFs)  │   │
│   └──────────────┘    └──────┬───────┘    └────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│                     ┌────────────────┐                         │
│                     │ Document Gen   │                         │
│                     │ (Carbone.io)   │                         │
│                     └────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema Extension

### New Table: `reports`

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships to existing schema
    project_id UUID REFERENCES projects(id) NOT NULL,
    employee_id UUID REFERENCES employees(id) NOT NULL,  -- Uses existing employees table
    
    -- Report metadata
    report_type TEXT NOT NULL CHECK (report_type IN (
        'ATS',           -- Acceptance Testing
        'MTS',           -- Maintenance Testing  
        'ATS_MAINT',     -- ATS Maintenance
        'IR'             -- Infrared Thermography
    )),
    report_number TEXT,
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Content fields
    attn_name TEXT,
    re_line TEXT,
    project_description TEXT,
    results_summary TEXT,
    recommendations TEXT,
    
    -- Section toggles (which sections to include)
    include_scope BOOLEAN DEFAULT true,
    include_results BOOLEAN DEFAULT true,
    include_procedures BOOLEAN DEFAULT true,
    include_equipment_summary BOOLEAN DEFAULT true,
    
    -- Generated output
    pdf_storage_path TEXT,
    pdf_url TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN (
        'draft', 
        'generated', 
        'finalized'
    )),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    generated_at TIMESTAMPTZ,
    finalized_at TIMESTAMPTZ
);

-- Index for common queries
CREATE INDEX idx_reports_project ON reports(project_id);
CREATE INDEX idx_reports_employee ON reports(employee_id);
CREATE INDEX idx_reports_status ON reports(status);
```

### Extend Existing: `employees` Table

The existing `employees` table already has most required fields. Add these columns for report generation:

```sql
-- Add signature support to existing employees table
ALTER TABLE employees ADD COLUMN IF NOT EXISTS signature_storage_path TEXT;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS title TEXT DEFAULT 'Power Systems Technician';
ALTER TABLE employees ADD COLUMN IF NOT EXISTS office TEXT;

-- Note: employees table already has:
-- id, employee_name, email, phone, location_id, role, is_active, etc.
```

### New Table: `report_apparatus`

Links apparatus to specific reports (subset of project apparatus included in report):

```sql
CREATE TABLE report_apparatus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    apparatus_id UUID REFERENCES apparatus(id),
    
    -- Order in report
    sort_order INTEGER DEFAULT 0,
    
    -- Override fields (if different from apparatus record)
    designation_override TEXT,
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Report Types & Sections

| Report Type | Cover | Summary Letter | Scope | Results | Procedures | Equipment Table | Test Data | Thermal Images |
|-------------|-------|----------------|-------|---------|------------|-----------------|-----------|----------------|
| ATS (Acceptance) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Optional |
| MTS (Maintenance) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Optional |
| ATS Maintenance | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Optional |
| IR (Thermography) | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |

## Document Generation

### Recommended: Carbone.io

Carbone is an open-source document generator that uses LibreOffice-compatible templates (.docx, .odt) with JSON data injection.

**Why Carbone:**
- Open source (self-hostable)
- Template format is familiar (Word/LibreOffice)
- Handles complex layouts, tables, images
- Outputs PDF directly
- Can run in Docker alongside Supabase

**Template Variables Example:**
```
{d.report_date}
{d.client.name}
{d.site.name}
{d.tech.full_name}
{d.tech.signature_url}

{#d.apparatus}
| {d.designation} | {d.location} | {d.manufacturer} | {d.model} |
{/d.apparatus}
```

### Alternative: Documint

Cloud-based visual template designer. Easier setup but recurring cost.

## Edge Function: Generate Report

```typescript
// supabase/functions/generate-report/index.ts

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const { report_id } = await req.json()
  
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )
  
  // 1. Fetch report with all related data
  const { data: report } = await supabase
    .from('reports')
    .select(`
      *,
      project:projects(
        *,
        client:clients(*),
        site:sites(*)
      ),
      employee:employees(*),
      apparatus:report_apparatus(
        *,
        apparatus:apparatus(*)
      )
    `)
    .eq('id', report_id)
    .single()
  
  // 2. Prepare data for template
  const templateData = {
    report_date: formatDate(report.report_date),
    report_number: report.report_number,
    attn_name: report.attn_name,
    re_line: report.re_line,
    project_description: report.project_description,
    
    client: {
      name: report.project.client.name,
    },
    site: {
      name: report.project.site.name,
      address: report.project.site.address,
    },
    employee: {
      full_name: report.employee.employee_name,
      title: report.employee.title || 'Power Systems Technician',
      office: report.employee.office || 'Apex Power Ops',
      phone: report.employee.phone,
      email: report.employee.email,
      signature_url: getSignatureUrl(report.employee.signature_storage_path),
    },
    apparatus: report.apparatus.map(a => ({
      designation: a.designation_override || a.apparatus.designation,
      location: a.apparatus.location,
      manufacturer: a.apparatus.manufacturer,
      model: a.apparatus.model,
      serial: a.apparatus.serial_number,
      volts: a.apparatus.voltage,
      amps: a.apparatus.amperage,
    })),
  }
  
  // 3. Call Carbone API or self-hosted instance
  const pdfBuffer = await generatePdfWithCarbone(
    report.report_type,  // Determines which template
    templateData
  )
  
  // 4. Upload to Supabase Storage
  const filename = `${report.report_number}_${Date.now()}.pdf`
  const { data: upload } = await supabase.storage
    .from('reports')
    .upload(filename, pdfBuffer, {
      contentType: 'application/pdf'
    })
  
  // 5. Update report record
  const { data: publicUrl } = supabase.storage
    .from('reports')
    .getPublicUrl(filename)
    
  await supabase
    .from('reports')
    .update({
      pdf_storage_path: upload.path,
      pdf_url: publicUrl.publicUrl,
      status: 'generated',
      generated_at: new Date().toISOString()
    })
    .eq('id', report_id)
  
  return new Response(
    JSON.stringify({ success: true, pdf_url: publicUrl.publicUrl }),
    { headers: { 'Content-Type': 'application/json' } }
  )
})
```

## User Interface Flow

### Step 1: Select Project
```
┌────────────────────────────────────────┐
│ Create New Report                      │
├────────────────────────────────────────┤
│                                        │
│  Project: [Search/Select dropdown]     │
│                                        │
│  ┌────────────────────────────────┐   │
│  │ Stellar Energy - Sundance TIAC │   │
│  │ ABC Corp - Main Campus         │   │
│  │ XYZ Inc - Data Center          │   │
│  └────────────────────────────────┘   │
│                                        │
└────────────────────────────────────────┘
```

### Step 2: Auto-Populated Form
```
┌────────────────────────────────────────┐
│ Report Details                         │
├────────────────────────────────────────┤
│                                        │
│  Report Type: [ATS ▼]                  │
│                                        │
│  Client: Stellar Energy    (auto)      │
│  Site: Sundance TIAC       (auto)      │
│  Date: [12/11/2025]                    │
│                                        │
│  Attn: [                    ]          │
│  RE: [                      ]          │
│                                        │
│  Description:                          │
│  ┌────────────────────────────────┐   │
│  │                                │   │
│  │                                │   │
│  └────────────────────────────────┘   │
│                                        │
│  Equipment: (from project)             │
│  ☑ ATS-1 - Main Switchgear            │
│  ☑ ATS-2 - Generator Transfer         │
│  ☐ ATS-3 - Emergency Panel            │
│                                        │
│  Employee: [Kole Ellertson ▼]          │
│                                        │
│  [Generate Report]                     │
│                                        │
└────────────────────────────────────────┘
```

### Step 3: Review & Download
```
┌────────────────────────────────────────┐
│ Report Generated                       │
├────────────────────────────────────────┤
│                                        │
│  ✓ Report successfully generated       │
│                                        │
│  [Preview PDF]  [Download]  [Email]    │
│                                        │
│  Status: Generated                     │
│  [Mark as Finalized]                   │
│                                        │
└────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Foundation (Current)
- [x] Design database schema
- [x] Migrate to Supabase ✅
- [ ] Add signature/title/office columns to employees table
- [ ] Set up Supabase Storage buckets

### Phase 2: Templates
- [ ] Create Carbone-compatible templates (.docx)
  - [ ] Summary Letter template
  - [ ] Scope of Work template
  - [ ] Results & Recommendations template
  - [ ] Cover pages (4 types)
- [ ] Test template variable injection
- [ ] Verify PDF output quality

### Phase 3: Edge Functions
- [ ] Deploy Carbone (self-hosted or cloud)
- [ ] Create generate-report Edge Function
- [ ] Implement PDF storage workflow
- [ ] Add error handling and logging

### Phase 4: User Interface
- [ ] Build report creation form
- [ ] Implement project search/select
- [ ] Add equipment selection UI
- [ ] Create report preview/download

### Phase 5: Refinement
- [ ] Add email delivery option
- [ ] Implement report versioning
- [ ] Create report history/archive view
- [ ] Add batch report generation

## File Storage Structure

```
supabase-storage/
├── templates/
│   ├── ATS_Summary_Letter.docx
│   ├── MTS_Summary_Letter.docx
│   ├── Scope_of_Work.docx
│   └── ...
├── signatures/
│   ├── employee_[uuid].png
│   └── ...
├── covers/
│   ├── ATS_Cover.pdf
│   ├── MTS_Cover.pdf
│   ├── IR_Cover.pdf
│   └── Maintenance_Cover.pdf
└── reports/
    └── [generated reports stored here]
```

## Security Considerations

- Row Level Security (RLS) on reports table
- Employees can only view/edit their own reports
- Managers can view all reports
- Generated PDFs in private bucket with signed URLs
- Service role key only used in Edge Functions

## Dependencies

| Component | Purpose | License/Cost |
|-----------|---------|--------------|
| Supabase | Database, Auth, Storage, Edge Functions | Free tier available |
| Carbone | Document generation | Open source (MIT) |
| LibreOffice | PDF conversion (used by Carbone) | Open source |

## References

- [Carbone Documentation](https://carbone.io/documentation.html)
- [Supabase Edge Functions](https://supabase.com/docs/guides/functions)
- [Supabase Storage](https://supabase.com/docs/guides/storage)

---

*Document Version: 1.0*  
*Last Updated: December 2024*  
*Status: Planning*
