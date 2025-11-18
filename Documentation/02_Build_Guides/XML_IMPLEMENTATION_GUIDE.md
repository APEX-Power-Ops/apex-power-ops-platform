# XML-Based Implementation Guide
## RESA Power Project Tracker Advanced Features

**Version:** 1.0  
**Created:** November 10, 2025  
**Purpose:** Complete guide to adding calculated fields, rollups, and advanced features via XML editing

---

## 📋 TABLE OF CONTENTS

1. [Strategy Overview](#strategy-overview)
2. [XML Structure Explained](#xml-structure-explained)
3. [Field Type Templates](#field-type-templates)
4. [Step-by-Step Implementation Process](#step-by-step-implementation-process)
5. [Python XML Generator Tool](#python-xml-generator-tool)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)

---

## STRATEGY OVERVIEW

### The XML Approach Benefits:
✅ **Speed** - Add 27 rollup fields in minutes vs hours  
✅ **Consistency** - All fields follow exact same pattern  
✅ **Reusability** - Save templates for future projects  
✅ **Version Control** - Track all changes in source control  
✅ **Learning** - Understand Power Platform at XML level  

### Our Implementation Plan:

```
Phase 1: CRITICAL FIXES (Manual in UI)
├─ Fix Apparatus_Type_Master (add 4 ATS/MTS columns)
├─ Fix NETA_Standard field (text → choice)
└─ Verify relationships
⏱️ Time: 3-4 hours

Phase 2: CALCULATED FIELDS (XML Automation)
├─ Extract current customizations.xml
├─ Generate XML for 20 calculated fields
├─ Add to customizations.xml
├─ Re-import solution
└─ Test calculations
⏱️ Time: 2-3 hours

Phase 3: ROLLUP FIELDS (XML Automation)
├─ Generate XML for 27 rollup fields  
├─ Add to customizations.xml
├─ Re-import solution
└─ Test rollups
⏱️ Time: 2-3 hours

Phase 4: BUSINESS RULES (Manual in UI)
├─ Create 9 business rules in UI
└─ Test validations
⏱️ Time: 2-3 hours

Total: 9-13 hours
```

---

## XML STRUCTURE EXPLAINED

### How Dataverse Solution XML is Organized:

```xml
<ImportExportXml>
  <Entities>
    <Entity>
      <Name>cr950_Projects</Name>           <!-- Table logical name -->
      <EntityInfo>                           <!-- Table metadata -->
        <entity Name="cr950_Projects">
          <attributes>
            
            <!-- EXISTING FIELDS -->
            <attribute PhysicalName="cr950_JobNumber">
              <Type>nvarchar</Type>
              <LogicalName>cr950_jobnumber</LogicalName>
              <!-- Field properties here -->
            </attribute>
            
            <!-- NEW FIELDS GO HERE -->
            <attribute PhysicalName="cr950_FullProjectID">
              <Type>nvarchar</Type>
              <LogicalName>cr950_fullprojectid</LogicalName>
              <!-- New calculated field properties -->
            </attribute>
            
          </attributes>
        </entity>
      </EntityInfo>
    </Entity>
  </Entities>
</ImportExportXml>
```

### Key XML Elements:

| Element | Purpose | Notes |
|---------|---------|-------|
| `<attribute>` | Defines a single field | One per field |
| `<Type>` | Data type (nvarchar, int, decimal, money, picklist) | Must match field type |
| `<LogicalName>` | API name (lowercase) | cr950_fieldname |
| `<PhysicalName>` | Display name in XML | cr950_FieldName |
| `<displaynames>` | User-facing label | What users see in UI |
| `<Descriptions>` | Field help text | Tooltips and guidance |
| `<FormulaDefinition>` | Calculated field formula | Power FX formula |
| `<SourceTypeMask>` | Field source type | 0=Simple, 1=Calculated, 3=Rollup |

---

## FIELD TYPE TEMPLATES

### 1. TEXT FIELD (Simple Field)

```xml
<attribute PhysicalName="cr950_FieldName">
  <Type>nvarchar</Type>
  <n>cr950_fieldname</n>
  <LogicalName>cr950_fieldname</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>auto</ImeMode>
  <ValidForUpdateApi>1</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>1</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings>
  <CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
  <SourceType>0</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled>
  <IsSortableEnabled>0</IsSortableEnabled>
  <Format>text</Format>
  <MaxLength>200</MaxLength>
  <Length>400</Length>
  <displaynames>
    <displayname description="Field Display Name" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="Field description" languagecode="1033" />
  </Descriptions>
</attribute>
```

---

### 2. CALCULATED TEXT FIELD (Concatenation)

**Example:** Full_Project_ID = Location_Code & "-" & Job_Number

```xml
<attribute PhysicalName="cr950_FullProjectID">
  <Type>nvarchar</Type>
  <n>cr950_fullprojectid</n>
  <LogicalName>cr950_fullprojectid</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>disabled</ImeMode>
  <ValidForUpdateApi>0</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>0</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings>
  <CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
  <SourceType>1</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled>
  <IsSortableEnabled>0</IsSortableEnabled>
  <Format>text</Format>
  <MaxLength>200</MaxLength>
  <Length>400</Length>
  <FormulaDefinition><![CDATA[Concatenate(cr950_locationcode, "-", Text(cr950_jobnumber))]]></FormulaDefinition>
  <displaynames>
    <displayname description="Full Project ID" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="Location code and job number (e.g., PHX-674414)" languagecode="1033" />
  </Descriptions>
</attribute>
```

**Key Differences for Calculated Fields:**
- `<SourceType>1</SourceType>` (1 = Calculated)
- `<ImeMode>disabled</ImeMode>` (Cannot edit)
- `<ValidForUpdateApi>0</ValidForUpdateApi>` (Read-only)
- `<ValidForCreateApi>0</ValidForCreateApi>` (Auto-calculated)
- `<FormulaDefinition>` contains Power FX formula

---

### 3. CALCULATED NUMBER FIELD (Date Difference)

**Example:** Days_Since_Start = DATEDIFF(Start_Date, Today(), Days)

```xml
<attribute PhysicalName="cr950_DaysSinceStart">
  <Type>int</Type>
  <n>cr950_dayssincestart</n>
  <LogicalName>cr950_dayssincestart</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>disabled</ImeMode>
  <ValidForUpdateApi>0</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>0</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings>
  <CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
  <SourceType>1</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled>
  <IsSortableEnabled>0</IsSortableEnabled>
  <MinValue>-2147483648</MinValue>
  <MaxValue>2147483647</MaxValue>
  <Format>none</Format>
  <FormulaDefinition><![CDATA[DateDiff(cr950_startdate, Today(), Days)]]></FormulaDefinition>
  <displaynames>
    <displayname description="Days Since Start" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="Number of days since project start date" languagecode="1033" />
  </Descriptions>
</attribute>
```

---

### 4. CALCULATED YES/NO FIELD (Boolean Logic)

**Example:** Is_Overdue = Target_Completion < Today() AND Status <> "Complete"

```xml
<attribute PhysicalName="cr950_IsOverdue">
  <Type>bit</Type>
  <n>cr950_isoverdue</n>
  <LogicalName>cr950_isoverdue</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>disabled</ImeMode>
  <ValidForUpdateApi>0</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>0</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings>
  <CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
  <SourceType>1</SourceType>
  <IsGlobalFilterEnabled>1</IsGlobalFilterEnabled>
  <IsSortableEnabled>1</IsSortableEnabled>
  <AppDefaultValue>0</AppDefaultValue>
  <FormulaDefinition><![CDATA[If(And(cr950_targetcompletiondate < Today(), cr950_projectstatus <> 934270003), true, false)]]></FormulaDefinition>
  <displaynames>
    <displayname description="Is Overdue" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="True if project is past target completion and not complete" languagecode="1033" />
  </Descriptions>
</attribute>
```

**Note:** For picklist comparisons, use the integer value (e.g., 934270003 for "Complete" status)

---

### 5. CALCULATED DECIMAL FIELD (Mathematical Formula)

**Example:** Percent_Complete = (Completed_Apparatus / Total_Apparatus) × 100

```xml
<attribute PhysicalName="cr950_PercentComplete">
  <Type>decimal</Type>
  <n>cr950_percentcomplete</n>
  <LogicalName>cr950_percentcomplete</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>disabled</ImeMode>
  <ValidForUpdateApi>0</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>0</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings>
  <CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
  <SourceType>1</SourceType>
  <IsGlobalFilterEnabled>1</IsGlobalFilterEnabled>
  <IsSortableEnabled>1</IsSortableEnabled>
  <MinValue>0</MinValue>
  <MaxValue>100</MaxValue>
  <Accuracy>2</Accuracy>
  <FormulaDefinition><![CDATA[If(IsBlank(cr950_totalapparatus) || cr950_totalapparatus = 0, 0, (cr950_completedapparatus / cr950_totalapparatus) * 100)]]></FormulaDefinition>
  <displaynames>
    <displayname description="Percent Complete" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="Percentage of apparatus completed (0-100)" languagecode="1033" />
  </Descriptions>
</attribute>
```

---

### 6. ROLLUP FIELD (COUNT)

**Example:** Total_Apparatus = COUNT(Apparatus where Project_ID matches)

⚠️ **IMPORTANT:** Rollup fields are MORE COMPLEX in XML. They require:
1. The field definition in customizations.xml
2. A separate XAML workflow file in /Formulas folder
3. Relationship references

**Recommended Approach for Rollups:**
- Create ONE rollup field manually in UI to see XML pattern
- Extract the generated XML and XAML
- Use as template for remaining rollups

**Basic Rollup XML Structure:**

```xml
<attribute PhysicalName="cr950_TotalApparatus">
  <Type>int</Type>
  <n>cr950_totalapparatus</n>
  <LogicalName>cr950_totalapparatus</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>disabled</ImeMode>
  <ValidForUpdateApi>0</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>0</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <SourceType>3</SourceType>
  <IsGlobalFilterEnabled>1</IsGlobalFilterEnabled>
  <IsSortableEnabled>1</IsSortableEnabled>
  <MinValue>-2147483648</MinValue>
  <MaxValue>2147483647</MaxValue>
  <Format>none</Format>
  <RollupState>0</RollupState>
  <displaynames>
    <displayname description="Total Apparatus" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="Total number of apparatus in this project" languagecode="1033" />
  </Descriptions>
</attribute>
```

**Key Rollup Markers:**
- `<SourceType>3</SourceType>` (3 = Rollup)
- `<RollupState>0</RollupState>` (Rollup configuration)
- Requires separate workflow XAML file

---

### 7. CHOICE (PICKLIST) FIELD

**Example:** NETA_Standard with ATS/MTS choices

```xml
<attribute PhysicalName="cr950_NETAStandard">
  <Type>picklist</Type>
  <n>cr950_netastandard</n>
  <LogicalName>cr950_netastandard</LogicalName>
  <RequiredLevel>required</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid|RequiredForForm</DisplayMask>
  <ImeMode>auto</ImeMode>
  <ValidForUpdateApi>1</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>1</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings>
  <CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
  <SourceType>0</SourceType>
  <IsGlobalFilterEnabled>1</IsGlobalFilterEnabled>
  <IsSortableEnabled>1</IsSortableEnabled>
  <AppDefaultValue>934270000</AppDefaultValue>
  <OptionSetName>cr950_netastandard</OptionSetName>
  <displaynames>
    <displayname description="NETA Standard" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="Testing standard: ATS (new installations) or MTS (maintenance)" languagecode="1033" />
  </Descriptions>
</attribute>
```

**Plus separate OptionSet definition:**

```xml
<optionset Name="cr950_netastandard" localizedName="NETA Standard">
  <IsGlobal>1</IsGlobal>
  <OptionSetType>Picklist</OptionSetType>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsCustomOptionSet>1</IsCustomOptionSet>
  <options>
    <option value="934270000" color="#0000ff">
      <labels>
        <label description="ATS" languagecode="1033" />
      </labels>
    </option>
    <option value="934270001" color="#00ff00">
      <labels>
        <label description="MTS" languagecode="1033" />
      </labels>
    </option>
  </options>
</optionset>
```

---

## STEP-BY-STEP IMPLEMENTATION PROCESS

### Phase 1: PREPARE (Setup & Backup)

#### Step 1.1: Export Current Solution

```bash
# In Power Apps maker portal
1. Go to Solutions
2. Select "RESA Power Project Management"
3. Click "Export"
4. Export as "Unmanaged"
5. Download ZIP file
6. Save as: RESAProjectManagement_1_0_0_2_BACKUP.zip
```

#### Step 1.2: Extract Solution Files

```bash
# Extract ZIP contents
unzip RESAProjectManagement_1_0_0_2.zip -d /working_directory/
```

You'll get:
- `customizations.xml` (main file to edit)
- `solution.xml` (version info)
- `[Content_Types].xml` (file manifest)
- `/Formulas` folder (if rollups exist)

#### Step 1.3: Create Working Directory Structure

```
/RESA_XML_Work/
├── /backups/
│   ├── customizations_original.xml
│   └── customizations_v1.xml
├── /templates/
│   ├── calculated_field_template.xml
│   ├── rollup_field_template.xml
│   └── choice_field_template.xml
├── /generated/
│   ├── projects_calculated_fields.xml
│   ├── scopes_calculated_fields.xml
│   └── tasks_calculated_fields.xml
└── /solution/
    ├── customizations.xml (working copy)
    ├── solution.xml
    └── [Content_Types].xml
```

---

### Phase 2: FIX CRITICAL ITEMS (Manual in UI First)

**Why Manual First:**
- Easier to understand what you're doing
- Less risk of XML syntax errors
- Can verify success immediately

#### Fix 1: Apparatus_Type_Master - Add ATS/MTS Columns

```
1. Open Power Apps > Tables > Apparatus_Type_Master
2. Add columns:
   - NETA_ATS_Section_Reference (Text, 50 chars)
   - NETA_ATS_Labor_Hours (Decimal, 2 decimal places)
   - NETA_MTS_Section_Reference (Text, 50 chars)
   - NETA_MTS_Labor_Hours (Decimal, 2 decimal places)
3. Save table
4. Export solution again
5. Extract to see XML changes
```

#### Fix 2: Scopes NETA_Standard - Convert to Choice

```
1. Open Scopes table
2. DELETE cr950_netastandard text field
3. CREATE new field:
   Name: NETA_Standard
   Type: Choice
   Sync with global choice: Yes
   Global choice: Create new "NETA Standard"
   Options:
     - ATS (value 934270000)
     - MTS (value 934270001)
   Default: ATS
   Required: Yes
4. Save table
5. Export solution
```

**After these fixes, export solution and extract XML - we'll use this as our base for XML edits.**

---

### Phase 3: XML AUTOMATION (Calculated Fields)

#### Step 3.1: Identify Your Target Entity in XML

Open `customizations.xml` and find your entity:

```xml
<Entity>
  <Name>cr950_Projects</Name>
  <EntityInfo>
    <entity Name="cr950_Projects">
      <attributes>
        <!-- EXISTING FIELDS ARE HERE -->
        <!-- WE'LL ADD NEW FIELDS AT THE END -->
      </attributes>
    </entity>
  </EntityInfo>
</Entity>
```

#### Step 3.2: Create Field XML Snippets

Using the templates above, create XML for each calculated field.

**Example: Projects Table Calculated Fields**

Create file: `projects_calculated_fields.xml`

```xml
<!-- Projects Calculated Fields -->

<!-- Field 1: Full_Project_ID -->
<attribute PhysicalName="cr950_FullProjectID">
  <Type>nvarchar</Type>
  <n>cr950_fullprojectid</n>
  <LogicalName>cr950_fullprojectid</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>disabled</ImeMode>
  <ValidForUpdateApi>0</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>0</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings>
  <CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
  <SourceType>1</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled>
  <IsSortableEnabled>0</IsSortableEnabled>
  <Format>text</Format>
  <MaxLength>200</MaxLength>
  <Length>400</Length>
  <FormulaDefinition><![CDATA[Concatenate(cr950_locationcode, "-", Text(cr950_jobnumber))]]></FormulaDefinition>
  <displaynames>
    <displayname description="Full Project ID" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="Location code and job number (e.g., PHX-674414)" languagecode="1033" />
  </Descriptions>
</attribute>

<!-- Field 2: Short_Display_Name -->
<attribute PhysicalName="cr950_ShortDisplayName">
  <Type>nvarchar</Type>
  <n>cr950_shortdisplayname</n>
  <LogicalName>cr950_shortdisplayname</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>disabled</ImeMode>
  <ValidForUpdateApi>0</ValidForUpdateApi>
  <ValidForReadApi>1</ValidForReadApi>
  <ValidForCreateApi>0</ValidForCreateApi>
  <IsCustomField>1</IsCustomField>
  <IsAuditEnabled>1</IsAuditEnabled>
  <IsSecured>0</IsSecured>
  <IntroducedVersion>1.0.0.0</IntroducedVersion>
  <IsCustomizable>1</IsCustomizable>
  <IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings>
  <CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
  <SourceType>1</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled>
  <IsSortableEnabled>0</IsSortableEnabled>
  <Format>text</Format>
  <MaxLength>500</MaxLength>
  <Length>1000</Length>
  <FormulaDefinition><![CDATA[Concatenate(Text(cr950_jobnumber), " - ", cr950_customershortname, " - ", cr950_projectname)]]></FormulaDefinition>
  <displaynames>
    <displayname description="Short Display Name" languagecode="1033" />
  </displaynames>
  <Descriptions>
    <Description description="Job Number - Customer - Project (e.g., 674414 - Goodman - LASNAP16)" languagecode="1033" />
  </Descriptions>
</attribute>

<!-- Continue for all calculated fields... -->
```

#### Step 3.3: Insert Fields into customizations.xml

```python
# Python script to insert fields (see next section for full script)
# This finds the closing </attributes> tag and inserts new fields before it

import xml.etree.ElementTree as ET

# Parse customizations.xml
tree = ET.parse('customizations.xml')
root = tree.getroot()

# Find Projects entity
for entity in root.findall('.//entity[@Name="cr950_Projects"]'):
    attributes = entity.find('.//attributes')
    
    # Parse new fields from your snippet file
    new_fields_tree = ET.parse('projects_calculated_fields.xml')
    
    # Append each new field
    for new_field in new_fields_tree.findall('.//attribute'):
        attributes.append(new_field)

# Write updated XML
tree.write('customizations_updated.xml', encoding='utf-8', xml_declaration=True)
```

#### Step 3.4: Re-package Solution

```bash
# Zip the files back together
cd /solution_directory/
zip -r RESAProjectManagement_1_0_0_3.zip customizations.xml solution.xml [Content_Types].xml
```

#### Step 3.5: Import Updated Solution

```
1. Power Apps > Solutions
2. Import solution
3. Select RESAProjectManagement_1_0_0_3.zip
4. Import
5. Wait for completion (3-5 minutes)
6. Check for errors
```

#### Step 3.6: Test Calculated Fields

```
1. Open Projects table
2. Create test record
3. Verify calculated fields populate automatically
4. Check formulas produce correct values
```

---

### Phase 4: ROLLUP FIELDS STRATEGY

**Rollups are Complex in XML** - Here's the recommended hybrid approach:

#### Option A: Create One Example, Extract Pattern (RECOMMENDED)

```
1. Manually create ONE rollup field in UI
   Example: Projects.Total_Scopes (COUNT of Scopes)
   
2. Export solution and extract

3. Find the rollup field XML in customizations.xml
   - Look for SourceType="3"
   - Note the structure
   
4. Find the XAML workflow in /Formulas folder
   - Named like: cr950_projects-cr950_totalscopes.xaml
   
5. Use these as templates for remaining rollups

6. Generate XML/XAML for all rollup fields using pattern

7. Bulk import via solution
```

#### Option B: Use UI for All Rollups (Slower but Safer)

```
- Create each rollup field manually in Power Apps UI
- More time consuming (15-20 minutes per field × 27 fields = 6-8 hours)
- Zero risk of XML syntax errors
- Immediate validation
```

**My Recommendation:** Option A - Create 2-3 rollup examples manually, extract patterns, then automate the rest.

---

## PYTHON XML GENERATOR TOOL

I'll create a Python script that generates all your calculated field XML based on specifications from the punch list:

```python
# This script will generate calculated field XML for all tables
# Run it to create XML snippets you can paste into customizations.xml

# See next section for full implementation
```

---

## TESTING & VALIDATION

### Validation Checklist:

After each XML import:

```
✅ Solution imports without errors
✅ All new fields visible in table designer
✅ Calculated fields show formula in properties
✅ Formulas calculate correctly with test data
✅ Field data types are correct
✅ Display names and descriptions are correct
✅ Required levels are set properly
✅ No existing fields were modified unintentionally
```

### Test Data Strategy:

```
1. Create test project: "TEST-001 - XML Test - Calculator"
2. Create test scope: "Scope A" (with NETA_Standard = ATS)
3. Create test task: "Task 1"
4. Create test apparatus: "Transformer 1"
5. Verify all calculated fields populate
6. Check rollup fields update when child records added
```

---

## TROUBLESHOOTING

### Common XML Errors:

| Error | Cause | Fix |
|-------|-------|-----|
| "Invalid XML" | Syntax error (missing tag, unclosed element) | Validate XML before import |
| "Attribute already exists" | Field LogicalName conflicts with existing | Change LogicalName |
| "Invalid formula" | Power FX syntax error | Test formula in UI first |
| "Import failed" | Corrupt ZIP file | Re-zip files |
| "Field not appearing" | Wrong entity or not in `<attributes>` section | Check entity name and placement |

### XML Validation:

Before importing, validate your XML:

```bash
# Use xmllint to check syntax
xmllint --noout customizations.xml

# Or use Python
python3 << EOF
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('customizations.xml')
    print("✓ XML is valid")
except ET.ParseError as e:
    print(f"✗ XML error: {e}")
EOF
```

### Rollback Strategy:

If import fails:

```
1. Keep backup of last working solution
2. Import backup solution
3. Fix XML errors
4. Try again
```

---

## NEXT STEPS

Now that you have this guide, here's what we should do:

1. ✅ **Fix CRITICAL items manually** (3-4 hours)
   - Add ATS/MTS columns to Apparatus_Type_Master
   - Fix NETA_Standard choice field
   - Export updated solution

2. 🔨 **Create XML Generator Script** (1 hour)
   - Python script that generates all calculated field XML
   - Takes field specifications from punch list
   - Outputs ready-to-paste XML snippets

3. ⚡ **Bulk Add Calculated Fields** (2 hours)
   - Run generator script
   - Paste XML into customizations.xml
   - Re-import solution
   - Test fields

4. 📊 **Create Rollup Example** (1 hour)
   - Manually create 2-3 rollup fields
   - Extract XML/XAML patterns
   - Document pattern for automation

5. ⚡ **Bulk Add Rollups** (2-3 hours)
   - Generate remaining rollup XML
   - Import solution
   - Test rollups

**Total Estimated Time: 9-12 hours**

---

**Ready to start? Let me know if you want me to:**
1. Create the Python XML generator script
2. Help you manually fix the CRITICAL items first
3. Walk through creating one calculated field example via XML

**Document Version:** 1.0  
**Last Updated:** November 10, 2025
