# RESA Power Build - Solution Version History
**Current Version**: v1.4.0.0  
**Last Updated**: November 23, 2025

---

## 📦 Active Versions

### **v1.4.0.0** (CURRENT - Nov 22, 2025)
**Status**: ✅ Deployed to org99cd6c6e.crm.dynamics.com

**Major Changes**:
- 16 Tables (added 6 new tables from v1.3.0.5)
- 291+ Fields total
- 10 Lookup relationships (operational)
- 30 Formula fields
- Added financial summary tables:
  - ProjectFinancialSummary
  - ScopeFinancialSummary

**New Tables Added**:
1. Client
2. Site
3. Employee
4. Quote
5. ResourceAssignment
6. Equipment

**Technical Details**:
- Date tracking fields: 8 per table (Created, Modified, Completed, etc.)
- Financial rollups: Ready for implementation
- KPI fields: Prepared structures
- Export files: Both managed and unmanaged

### **v1.3.0.5** (ROLLBACK - Nov 14, 2025)
**Status**: 🔄 Kept for rollback safety

**Configuration**:
- 14 Tables (8 core + 6 new)
- Stable baseline before financial tables
- Last v1.3.x release

**Purpose**: Safety net if v1.4.0.0 rollback needed

---

## 🗄️ Archived Versions (Archive/)

### **v1.3.0.1 - v1.3.0.4**
**Status**: Archived (historical reference only)
**Location**: Solution_Exports/Archive/
**Reason**: Superseded by v1.3.0.5 and v1.4.0.0

---

## 📋 Export Process

### **Standard Export Procedure**
1. Open Power Apps (make.powerapps.com)
2. Select environment: org99cd6c6e.crm.dynamics.com
3. Navigate to Solutions → RESA Power Project Tracker
4. Click "Export"
5. Choose version type:
   - **Unmanaged**: For development/customization
   - **Managed**: For production deployment
6. Save to \Solution_Exports/v{VERSION}/\
7. Also create ZIP archive: \RESAPowerProjectTracker_{VERSION}.zip\

### **Version Numbering**
- Format: \{MAJOR}.{MINOR}.{PATCH}.{BUILD}\
- Example: v1.4.0.0
- Increment:
  - MAJOR: Breaking changes, complete redesign
  - MINOR: New features, new tables
  - PATCH: Bug fixes, field updates
  - BUILD: Small tweaks, documentation

### **What to Export**
- **Include**:
  - All custom tables and fields
  - Relationships and lookups
  - Forms and views
  - Business rules
  - Workflows
- **Exclude**:
  - System tables
  - Default Dataverse components
  - Test data

---

## 🗂️ Folder Organization

\\\
Solution_Exports/
├── v1.4.0.0/                    (CURRENT - Nov 22, 2025)
│   ├── [Content_Types].xml
│   ├── customizations.xml       (16 tables definition)
│   ├── solution.xml
│   └── ... other export files
│
├── v1.3.0.5/                    (ROLLBACK - Nov 14, 2025)
│   └── ... export files
│
├── Archive/                     (OLD VERSIONS)
│   ├── v1.3.0.1/
│   ├── v1.3.0.2/
│   ├── v1.3.0.3/
│   └── v1.3.0.4/
│
├── RESAPowerProjectTracker_1_4_0_0.zip    (Current ZIP)
├── RESAPowerProjectTracker_1_3_0_5.zip    (Rollback ZIP)
├── VERSION_HISTORY.md           (This file)
└── README.md                    (Quick reference)
\\\

---

## 🔄 Retention Policy

### **Keep Active**
- Current version (v1.4.0.0)
- Last stable version (v1.3.0.5) for rollback

### **Move to Archive**
- Versions older than last 2 releases
- Superseded by newer implementations

### **Delete (Optional)**
- Archive versions >6 months old
- Versions with known critical bugs
- Pre-production experimental versions

---

## 🚀 Deployment History

| Version | Date | Environment | Status | Notes |
|---------|------|-------------|--------|-------|
| v1.4.0.0 | Nov 22, 2025 | org99cd6c6e | ✅ Active | 16 tables, financial summaries |
| v1.3.0.5 | Nov 14, 2025 | org04ad071f | 🔄 Rollback | Last v1.3.x release |
| v1.3.0.4 | Nov 12, 2025 | org04ad071f | 🗄️ Archived | |
| v1.3.0.3 | Nov 10, 2025 | org04ad071f | 🗄️ Archived | |
| v1.3.0.2 | Nov 8, 2025 | org04ad071f | 🗄️ Archived | |
| v1.3.0.1 | Nov 5, 2025 | org04ad071f | 🗄️ Archived | |

---

## 🎯 Next Version (Planned)

### **v1.5.0.0** (Target: Early December 2025)
**Focus**: Rollup fields and KPI implementation

**Planned Additions**:
- 32 Rollup fields (18 date tracking + 14 revenue)
- 6 KPI views
- Enhanced financial calculations
- Improved forms for new tables

**Prerequisites**:
- ✅ v1.4.0.0 stable in production
- ⏳ MCP testing server operational
- ⏳ Rollup field implementation complete
- ⏳ Comprehensive testing

---

**Created**: November 23, 2025  
**Next Review**: v1.5.0.0 release
