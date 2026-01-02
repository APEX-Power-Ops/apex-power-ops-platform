# Excel Structure Extractor Tools

Two versions available depending on your system setup:

## 🟢 **Recommended: No Excel Required** (Works on any Windows system)

**Files:**
- `Extract-Excel-Drag-Drop-NoExcel.bat` - Drag & drop interface
- `Extract-ExcelStructure-NoExcel.ps1` - PowerShell script

**Requirements:**
- PowerShell ImportExcel module
- Install once with: `Install-Module ImportExcel -Scope CurrentUser`

**Pros:**
- ✅ Works without Excel installed
- ✅ Faster performance
- ✅ No COM object issues
- ✅ More reliable

**Limitations:**
- ❌ Cannot extract VBA code from .xlsm files
- ❌ Some advanced features may not be available

---

## 🔴 **Excel COM Version** (Requires Excel installation)

**Files:**
- `Extract-Excel-Drag-Drop.bat` - Drag & drop interface
- `Extract-ExcelStructure.ps1` - PowerShell script

**Requirements:**
- Microsoft Excel installed
- Excel COM automation enabled

**Pros:**
- ✅ Can extract VBA code
- ✅ Can read .xls files
- ✅ Access to all Excel features

**Limitations:**
- ❌ Requires Excel installation
- ❌ COM object errors on some systems
- ❌ Slower performance

---

## Usage

1. **Drag and drop** an Excel file onto the `.bat` file
2. Wait for processing to complete
3. Find extracted content in a new folder next to your Excel file

## Extracted Content

Both versions create a folder with:

- `_Summary.txt` - Overview of workbook structure
- `_Formulas.txt` - All formulas organized by sheet
- `_NamedRanges.txt` - Named range definitions
- `SheetName_Data.csv` - Data from each sheet
- `SheetName_Structure.txt` - Detailed structure per sheet

---

## Troubleshooting

### ImportExcel module not found
```powershell
Install-Module ImportExcel -Scope CurrentUser
```

### COM object errors (Excel version)
Use the NoExcel version instead

### Permission errors
Right-click PowerShell → Run as Administrator, then:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

**Recommendation:** Start with the **NoExcel version** - it's faster and more reliable for most use cases.
