# PowerDB Schema Comprehensive Audit
## Phoenix Region Database Analysis

**Created:** December 2, 2025  
**Database:** prod_rgn_Services-Phoenix.mdf  
**Source:** LocalDB\PowerDB instance  
**Purpose:** Complete field inventory and GUID mapping for Dataverse integration

---

## 📊 Database Statistics

| Metric | Count |
|--------|-------|
| **Total Tables** | 80 |
| **Total Columns** | 1,209 |
| **GUID Columns** | 163 |
| **Foreign Key Relationships** | 45 |

### Key Table Record Counts

| Table | Total Records | Active Records |
|-------|---------------|----------------|
| **PdbJob** (Projects) | 149 | 139 |
| **Results_Header** (Assets/Tests) | 9,690 | 7,572 |
| **Device_Type** (Forms) | 884 | 845 |
| **PdbAddrInfo** (Addresses) | 8,963 | 8,873 |
| **Relay** (Equipment Master) | 10,189 | 9,524 |

---

## 🗂️ Complete Table Inventory

### Core Business Tables

| # | Table Name | Purpose | Key GUID | Record Count |
|---|------------|---------|----------|--------------|
| 1 | **PdbJob** | Jobs/Projects | JobGUID | 139 active |
| 2 | **Results_Header** | Test Results/Assets | ResultsGUID | 7,572 active |
| 3 | **Device_Type** | Test Form Definitions | DeviceGUID | 845 active |
| 4 | **PdbAddrInfo** | Address Details | AddrGUID | 8,873 active |
| 5 | **PdbAddrHeader** | Company Headers | CompanyGUID | - |
| 6 | **Relay** | Equipment Master Records | RelayGUID | 9,524 active |
| 7 | **PdbUserAccount** | User Accounts | UserGUID | - |
| 8 | **Manufacturer** | Equipment Manufacturers | ManufGUID | - |

### Supporting Tables

| Table | Purpose |
|-------|---------|
| **JobAttribute** | Custom job attributes |
| **JobUserAccount** | Job-to-user assignments |
| **PdbJobEquipment** | Job-equipment links |
| **PdbJobInfo** | Extended job information |
| **PdbCategory** / **PdbSubCategory** | Equipment categorization |
| **PdbCompliance** | Compliance tracking |
| **PdbTestStatus** | Test status definitions |
| **PdbTemplate** | Report templates |
| **FormFamily** | Form category groupings |
| **FormTemplet** | Form template definitions |

### Results/Test Data Tables

| Table | Purpose |
|-------|---------|
| **Results_Header** | Main test result record |
| **Results_Sequence** | Test sequence/steps |
| **Results_Values** | Numeric test values |
| **Results_String** | String test values |
| **Results_Digital** | Digital/binary values |
| **Results_FP** | Floating point values |
| **Results_Graph** | Graph data |
| **Results_Info** | Result metadata |
| **Results_Labels** | Field labels |
| **Results_Settings** | Test settings |
| **Results_Print_Order** | Print ordering |
| **ResultsDelta** | Change tracking |

### Archive Tables (Historical Data)

| Table | Purpose |
|-------|---------|
| **PdbJobArchive** | Archived jobs |
| **PdbAddrInfoArchive** | Archived addresses |
| **PdbFormArchive** | Archived forms |
| **RelayArchive** | Archived equipment |
| **ResultsHdrBinary_HIST** | Historical binary data |

---

## 🔑 Master GUID Mapping Reference

### Primary Entity GUIDs (Primary Keys)

| Entity | GUID Column | Data Type | Length | Description |
|--------|-------------|-----------|--------|-------------|
| **Job** | `JobGUID` | nvarchar | 20 | Unique job identifier |
| **Result** | `ResultsGUID` | nvarchar | 20 | Unique test result identifier |
| **Device/Form** | `DeviceGUID` | nvarchar | 20 | Unique form/device type identifier |
| **Address** | `AddrGUID` | nvarchar | 20 | Unique address identifier |
| **Company** | `CompanyGUID` | nvarchar | 20 | Unique company identifier |
| **Equipment** | `RelayGUID` | nvarchar | 20 | Unique equipment master identifier |
| **User** | `UserGUID` | nvarchar | 20 | Unique user identifier |
| **Region** | `RegionGUID` | nvarchar | 20 | Regional database identifier |

### Foreign Key GUIDs (Relationships)

| Column | Found In Tables | References |
|--------|-----------------|------------|
| `JobGUID` | Results_Header, JobAttribute, JobUserAccount, PdbJobEquipment, PdbJobInfo, PdbJob_Print_Order | PdbJob.JobGUID |
| `ResultsGUID` | Results_Sequence, Results_Settings, Results_Print_Order, ResultsDelta, DeltaComment, DeltaDeficiency, DeltaCorrAct, DeltaRecommend, ResultAttribute, PdbResultCompliance | Results_Header.ResultsGUID |
| `DeviceGUID` | Results_Header, Device_Type_Settings, Device_Type_Print_Order, FormDataTypeTags, Test_Report, Relay | Device_Type.DeviceGUID |
| `RelayGUID` | Results_Header, Relay_Settings, RelayManufModel, PdbJobEquipment, PdbCompliance, AssetAttribute | Relay.RelayGUID |
| `UserGUID` | JobUserAccount, PdbSynchTrack, ModUser, FormUpdate, RelayManufModel | PdbUserAccount.UserGUID |
| `CompanyGUID` | PdbAddrInfo, PdbJob (Cust/User), Relay (Cust/User) | PdbAddrHeader.CompanyGUID |
| `AddrGUID` | PdbJob (Cust/Eqmt/User), Relay (Cust/Eqmt/User) | PdbAddrInfo.AddrGUID |

---

## 📋 Detailed Table Schemas

### PdbJob (Jobs/Projects) - 47 Columns

| Column | Type | Length | Purpose | Maps To Dataverse |
|--------|------|--------|---------|-------------------|
| `JobGUID` | nvarchar | 20 | **Primary Key** | `cr950_powerdb_job_guid` |
| `JobNumber` | nvarchar | 80 | **Human-readable ID** | `cr950_jobnumber` ✅ |
| `Description` | nvarchar | MAX | Job description | `cr950_description` |
| `DateCreated` | datetime | - | Creation timestamp | `createdon` |
| `DateModified` | datetime | - | Last modified | `modifiedon` |
| `TargetStartDate` | datetime | - | Target start | `cr950_startdate` |
| `DueDate` | datetime | - | Due date | `cr950_duedate` |
| `CompletedDate` | datetime | - | Completion date | `cr950_completeddate` |
| `bComplete` | tinyint | - | Completion flag | `cr950_iscomplete` |
| `bInvoiceComplete` | int | - | Invoice status | `cr950_invoiced` |
| `bReportsSent` | int | - | Reports sent flag | `cr950_reportssent` |
| `CustCompanyGUID` | nvarchar | 20 | Customer company FK | → Client lookup |
| `CustAddrGUID` | nvarchar | 20 | Customer address FK | → Client address |
| `EqmtAddrGUID` | nvarchar | 20 | Equipment/site address FK | → Site lookup |
| `UserCompanyGUID` | nvarchar | 20 | Testing company FK | - |
| `UserAddrGUID` | nvarchar | 20 | Testing address FK | - |
| `MgrUserGUID` | nvarchar | 20 | Manager user FK | `cr950_projectlead` |
| `CreatorUserGUID` | nvarchar | 20 | Creator user FK | `createdby` |
| `RegionGuid` | nvarchar | 20 | Region FK | `cr950_businessunit` |
| `Info1-10` | nvarchar | 40 | Custom fields 1-10 | Custom fields |
| `bIsDel` | int | - | Soft delete flag | - |
| `bLocked` | tinyint | - | Lock flag | - |

### Results_Header (Assets/Test Results) - 72 Columns

| Column | Type | Length | Purpose | Maps To Dataverse |
|--------|------|--------|---------|-------------------|
| `ResultsGUID` | nvarchar | 20 | **Primary Key** | `cr950_powerdb_results_guid` |
| `JobGUID` | nvarchar | 20 | **Job FK** | → Project lookup |
| `RelayGUID` | nvarchar | 20 | **Equipment FK** | → Equipment master |
| `DeviceGuid` | nvarchar | 20 | **Form/Device FK** | `cr950_powerdb_device_guid` |
| `EquipmentLocation` | nvarchar | 80 | **Asset location/name** | `cr950_designation` ✅ |
| `SerialNum` | nvarchar | MAX | Serial numbers | `cr950_serialnumber` |
| `Tester` | nvarchar | 80 | Technician name | `cr950_technician` |
| `TestDate` | datetime | - | Test date | `cr950_testdate` |
| `DateCreated` | datetime | - | Record created | `createdon` |
| `Comments` | nvarchar | MAX | Test comments | `cr950_comments` |
| `Deficiencies` | nvarchar | MAX | Found deficiencies | `cr950_deficiencies` |
| `Recommendations` | nvarchar | MAX | Recommendations | `cr950_recommendations` |
| `CorrectiveActions` | nvarchar | MAX | Corrective actions | `cr950_correctiveactions` |
| `Org1-8` | nvarchar | 80 | Organizational hierarchy | Site/Location hierarchy |
| `bComplete` | tinyint | - | Completion flag | `cr950_iscomplete` |
| `AsFoundAsLeft` | nvarchar | 6 | As Found/As Left | `cr950_testtype` |
| `TestStatusGUID` | nvarchar | 20 | Test status FK | `cr950_teststatus` |
| `UserStr0-9` | nvarchar | 80 | Custom string fields | Custom fields |
| `UserNum0-4` | int | - | Custom numeric fields | Custom fields |
| `UserDate0-2` | datetime | - | Custom date fields | Custom fields |
| `bIsDel` | int | - | Soft delete flag | - |

### Device_Type (Test Forms) - 36 Columns

| Column | Type | Length | Purpose | Maps To Dataverse |
|--------|------|--------|---------|-------------------|
| `DeviceGUID` | nvarchar | 20 | **Primary Key** | `cr950_powerdb_device_guid` |
| `DeviceName` | nvarchar | 75 | **Form name** | `cr950_formname` ✅ |
| `Family` | nvarchar | 40 | **Equipment family** | `cr950_equipmentfamily` ✅ |
| `Manufacturer` | nvarchar | 40 | Default manufacturer | `cr950_manufacturer` |
| `FormNumber` | int | - | Form number ID | `cr950_formnumber` |
| `IEEEDevice` | nvarchar | 60 | IEEE device type | `cr950_ieeedevice` |
| `MaintPeriod` | int | - | Maintenance period | `cr950_maintenanceperiod` |
| `Notes` | nvarchar | MAX | Form notes | `cr950_notes` |
| `bIsRetired` | tinyint | - | Retired flag | - |
| `InstFamily` | nvarchar | 40 | Instrument family | - |

### PdbAddrInfo (Addresses) - 39 Columns

| Column | Type | Length | Purpose | Maps To Dataverse |
|--------|------|--------|---------|-------------------|
| `AddrGUID` | nvarchar | 20 | **Primary Key** | `cr950_powerdb_addr_guid` |
| `CompanyGUID` | nvarchar | 20 | **Company FK** | → Client lookup |
| `AddrLn1` | nvarchar | 100 | **Address line 1** | `cr950_address` ✅ |
| `AddrLn2` | nvarchar | 80 | Address line 2 | `cr950_address2` |
| `City` | nvarchar | 40 | **City** | `cr950_city` ✅ |
| `State` | nvarchar | 40 | **State** | `cr950_state` ✅ |
| `Zip` | nvarchar | 10 | ZIP code | `cr950_zipcode` |
| `Country` | nvarchar | 20 | Country | `cr950_country` |
| `FirstName` | nvarchar | 20 | Contact first name | `cr950_contactfirstname` |
| `LastName` | nvarchar | 20 | Contact last name | `cr950_contactlastname` |
| `Phone` | nvarchar | 20 | Phone | `cr950_phone` |
| `Mobile` | nvarchar | 20 | Mobile | `cr950_mobile` |
| `Fax` | nvarchar | 20 | Fax | - |
| `Email` | nvarchar | 40 | Email | `cr950_email` |
| `Type` | int | - | Address type (Cust/Site/User) | - |
| `bIsDel` | int | - | Soft delete flag | - |

---

## 🔗 Foreign Key Relationships (45 Total)

### Job-Related Relationships

```
PdbJob (JobGUID) ←──────┬── JobAttribute.JobGUID
                        ├── JobUserAccount.JobGUID
                        ├── PdbJobEquipment.JobGUID
                        ├── PdbJobInfo.JobGUID
                        ├── PdbJob_Print_Order.JobGUID
                        └── Results_Header.JobGUID
```

### Results-Related Relationships

```
Results_Header (ResultsGUID) ←──────┬── Results_Sequence.ResultsGUID
                                    ├── Results_Settings.ResultsGUID
                                    ├── Results_Print_Order.ResultsGUID
                                    ├── ResultsDelta.ResultsGUID
                                    ├── ResultAttribute.ResultsGUID
                                    ├── DeltaComment.ResultsGUID
                                    ├── DeltaDeficiency.ResultsGUID
                                    ├── DeltaCorrAct.ResultsGUID
                                    ├── DeltaRecommend.ResultsGUID
                                    ├── PdbResultCompliance.ResultsGUID
                                    └── ResultsHdrBinary_HIST.ResultsGUID
```

### Device/Form Relationships

```
Device_Type (DeviceGUID) ←──────┬── Device_Type_Settings.DeviceGUID
                                ├── Device_Type_Print_Order.DeviceGUID
                                ├── FormDataTypeTags.DeviceGUID
                                ├── Test_Report.DeviceGUID
                                ├── Results_Header.DeviceGuid
                                └── Relay.DeviceGUID
```

### Equipment Master Relationships

```
Relay (RelayGUID) ←──────┬── Relay_Settings.RelayGUID
                         ├── RelayManufModel.RelayGUID
                         ├── PdbJobEquipment.RelayGUID
                         ├── PdbCompliance.RelayGUID
                         ├── AssetAttribute.RelayGUID
                         └── Results_Header.RelayGUID
```

---

## 📈 Form Families (Equipment Categories)

| Family | Form Count | Maps To NETA |
|--------|------------|--------------|
| CIRCUIT BREAKER | 217 | 7.x Series |
| RELAYS | 77 | 7.9.x Series |
| CABLES | 70 | 7.3.x Series |
| TRANSFORMERS | 52 | 7.2.x Series |
| MISCELLANEOUS | 37 | Various |
| INSTRUMENT TRANSFORMERS | 36 | 7.10.x Series |
| BATTERIES | 31 | 7.17.x Series |
| MOTOR CONTROL CENTERS | 24 | 7.16.x Series |
| SWITCHBOARDS | 24 | 7.1.x Series |
| GROUND MAT GROUNDING TESTS | 19 | 7.13.x Series |
| LOADBREAK SWITCHES | 16 | 7.5.x Series |
| TRANSFER SWITCHES | 14 | 7.11.x Series |
| GENERATORS | 13 | 7.15.x Series |
| POWER FACTOR TESTS | 13 | Specialized |
| INFRARED | 12 | Thermography |
| INSULATION FLUID | 10 | 7.2.x Series |

---

## 🗺️ Dataverse Integration Mapping

### Proposed Field Additions to Dataverse

| Dataverse Table | New Field | Type | PowerDB Source |
|-----------------|-----------|------|----------------|
| **cr950_projects** | `cr950_powerdb_job_guid` | String(20) | PdbJob.JobGUID |
| **cr950_apparatus** | `cr950_powerdb_results_guid` | String(20) | Results_Header.ResultsGUID |
| **cr950_apparatus** | `cr950_powerdb_device_guid` | String(20) | Results_Header.DeviceGuid |
| **cr950_apparatus** | `cr950_powerdb_relay_guid` | String(20) | Results_Header.RelayGUID |
| **cr950_clients** | `cr950_powerdb_company_guid` | String(20) | PdbAddrHeader.CompanyGUID |
| **cr950_sites** | `cr950_powerdb_addr_guid` | String(20) | PdbAddrInfo.AddrGUID |

### Natural Key Mappings (No GUID Required)

| Dataverse Field | PowerDB Field | Notes |
|-----------------|---------------|-------|
| `cr950_jobnumber` | `PdbJob.JobNumber` | **Universal link - use this!** |
| `cr950_designation` | `Results_Header.EquipmentLocation` | Asset identifier |
| `cr950_serialnumber` | `Results_Header.SerialNum` | Equipment serial |
| `cr950_testformname` | `Device_Type.DeviceName` | Form identification |

---

## 📁 Exported Files

| File | Contents | Records |
|------|----------|---------|
| `PowerDB_Schema_Audit.csv` | All tables and columns | 1,209 rows |
| `PowerDB_GUID_Columns.csv` | GUID column reference | 163 rows |
| `PowerDB_ForeignKeys.csv` | Foreign key relationships | 45 rows |

---

## 🔐 Data Access Notes

1. **Soft Deletes**: All major tables use `bIsDel` flag (0 = active, 1 = deleted)
2. **Region Filtering**: Use `RegionGuid` to filter by region
3. **Locking**: `bLocked` flag indicates record is in use
4. **Timestamps**: `DateSynch` tracks last sync, `SynchWriteDate` tracks write time
5. **Creator Tracking**: `CreatorGuid` / `LastModBy` track user activity

---

## 🚀 Integration Recommendations

### Phase 1: Read-Only Integration
1. Add GUID fields to Dataverse tables
2. Query PowerDB by `JobNumber` to find matching job
3. Pull test completion status and deficiencies
4. Display in Dataverse/Power Apps dashboards

### Phase 2: Asset Synchronization  
1. Match assets by `JobNumber` + `EquipmentLocation`
2. Pull `Device_Type.DeviceName` to identify test form
3. Sync `Comments`, `Deficiencies`, `Recommendations`
4. Update Dataverse apparatus status based on `bComplete`

### Phase 3: Bi-directional Sync (Future)
1. Create jobs in PowerDB from Dataverse projects
2. Pre-populate equipment from apparatus records
3. Sync test results back to Dataverse for reporting

---

*Audit completed: December 2, 2025*  
*Connection: LocalDB\PowerDB - prod_rgn_Services-Phoenix.mdf*
