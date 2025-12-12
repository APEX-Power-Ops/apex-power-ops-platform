# RESA Power Build V2 - Solution Version History

**Current Version**: v1.0.0.4  
**Solution Name**: RESA_Power_Build_V2  
**Environment**: org7bdbc942.crm.dynamics.com (Developer)  
**Last Updated**: December 2, 2025

---

## Current Environment

| Property | Value |
|----------|-------|
| **Org URL** | https://org7bdbc942.crm.dynamics.com |
| **Environment Type** | Developer |
| **Created** | December 2, 2025 |
| **Solution** | RESA_Power_Build_V2 |
| **Publisher Prefix** | cr950 |

---

## Active Version

### **v1.0.0.4** (CURRENT - December 2, 2025)

**Location**: `Solution_Exports/v1.0.0.4/`

**Contents**:
- `RESA_Power_Build_V2_1_0_0_4.zip` - Original export
- `customizations.xml` - Table/field definitions
- `solution.xml` - Solution metadata
- `Workflows/` - Power Automate flows
  - EstimatorImport flow (verified working)

**Changes in v1.0.0.4**:
- Verified Estimator Import flow for new and existing records
- Clean export from new Developer environment
- All connections configured for org7bdbc942

---

## Deprecated Environments (ARCHIVED)

All versions from previous environments are in `Solution_Exports/Archive/`:

| Environment | Versions | Status |
|-------------|----------|--------|
| org99cd6c6e | v1.3.x - v1.5.x | DEPRECATED (was NOT developer env) |
| org284447bd | Various | DEPRECATED (replaced) |

**Do not use archived versions** - they reference wrong environments.

---

## Version Naming Convention

`RESA_Power_Build_V2_Major_Minor_Patch_Build.zip`

- **Major**: Breaking schema changes
- **Minor**: New tables/fields
- **Patch**: Flow/form updates
- **Build**: Incremental exports
