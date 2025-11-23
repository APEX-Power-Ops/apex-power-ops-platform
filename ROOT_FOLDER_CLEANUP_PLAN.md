# ROOT FOLDER CLEANUP PLAN
**Date**: November 23, 2025  
**Purpose**: Organize root directory for better project structure and security

---

## 📁 CURRENT ROOT FOLDER ANALYSIS

### **Files to KEEP in Root** ✅
```
.gitignore
PROJECT_CONTEXT.json
PROJECT_OVERVIEW.md
README.md
RESA_Power_Build.cdsproj
RESA_Power_Build.code-workspace
```

### **Files to MOVE** 📦

#### **Move to Documentation/99_Archive/**
```
API formatting for Column Creation.md
Claude Chat Session overview 1121225.md
D365_Project_Operations_Integration_Analysis.md
main[200~it (appears to be corrupted filename)
RESA_Power_Project_MASTER_REFERENCE.md (superseded by current docs)
```

#### **Move to Documentation/00_START_HERE/**
```
Dataverse MCP Server in VS Code.txt → Rename to DATAVERSE_MCP_SETUP.md
```

#### **Move to Documentation/99_Archive/Credentials/** (CREATE THIS FOLDER)
```
RESA-Dev-MCP-Access Certificates & Secrets.pdf
RESA-Dev-MCP-Access.pdf
```

#### **DELETE** (Sensitive/Temporary Files) ⚠️
```
I'm working on RESA Power Project T.txt (temp note)
RESA-Dev-MCP-Access.txt (contains secrets - should be in .gitignore)
The 401 Unauthorized error typicall.txt (temp note)
.env.example (not needed if not using .env files)
Github_generate_token.pdf (reference material - archive or delete)
```

---

## 🗂️ RECOMMENDED FOLDER STRUCTURE

```
RESA_Power_Build/
├── .claude/                          [Keep - IDE config]
├── .git/                             [Keep - Version control]
├── .gitignore                        [Keep - Updated with sensitive files]
├── PROJECT_CONTEXT.json              [Keep - Session continuity]
├── PROJECT_OVERVIEW.md               [Keep - Quick reference]
├── README.md                         [Keep - GitHub documentation]
├── RESA_Power_Build.cdsproj          [Keep - Solution file]
├── RESA_Power_Build.code-workspace   [Keep - VS Code workspace]
│
├── CSV_Templates/                    [Keep - Data import templates]
├── Documentation/                    [Keep - All documentation]
│   ├── 00_Project_Protocol/         [Keep]
│   ├── 00_START_HERE/               [Keep - Add MCP setup doc here]
│   ├── 01_Architecture/             [Keep]
│   ├── 02_Build_Guides/             [Keep]
│   ├── 02_Implementation/           [Keep]
│   ├── 03_Progress_Tracking/        [Keep - Add audit report here]
│   ├── 04_Data_Migration/           [Keep]
│   ├── 05_Reviews_Analysis/         [Keep]
│   ├── 06_Implementation_Guides/    [Keep]
│   ├── 06_MCP_Automation/           [Keep]
│   ├── 07_Application_Specs/        [Keep]
│   ├── 08_Testing_QA/               [Keep]
│   ├── 09_Training_Materials/       [Keep]
│   ├── 10_Analytics_Reporting/      [Keep]
│   ├── 11_Mobile_Apps/              [Keep]
│   └── 99_Archive/                  [Keep - Move old files here]
│       ├── Credentials/             [CREATE - Move PDFs here, add to .gitignore]
│       └── Old_Documentation/       [CREATE - Move superseded docs]
│
├── Import_Data/                      [Keep - Data files]
├── LASNAP16/                         [Keep - Excel reference files]
├── Logs/                             [Keep - System logs]
├── MCP_Servers/                      [Keep - MCP server code]
├── Reference_Files/                  [Keep - Reference materials]
├── Scripts/                          [Keep - PowerShell/Python scripts]
├── Solution_Exports/                 [Keep - Solution packages]
└── Working/                          [Keep - Temp working files]
```

---

## 🔒 SECURITY IMPROVEMENTS

### **Update .gitignore to Include:**
```gitignore
# Sensitive files (add these lines)
**/Credentials/
RESA-Dev-MCP-Access.txt
**/MCP-Access*.txt
*.env
.env.local
**/*secret*.txt
**/*password*.txt
**/*token*.txt

# Temporary files
I'm working on*.txt
The *error*.txt
```

### **Create Documentation/99_Archive/Credentials/.gitignore:**
```gitignore
# Ignore all files in this directory
*
# Except this .gitignore file
!.gitignore
```

---

## 📋 CLEANUP SCRIPT

### **PowerShell Commands to Execute:**

```powershell
# Navigate to project root
cd C:\RESA_Power_Build

# Create new directories
New-Item -Path "Documentation\99_Archive\Credentials" -ItemType Directory -Force
New-Item -Path "Documentation\99_Archive\Old_Documentation" -ItemType Directory -Force

# Move files to Archive
Move-Item "API formatting for Column Creation.md" "Documentation\99_Archive\Old_Documentation\"
Move-Item "Claude Chat Session overview 1121225.md" "Documentation\99_Archive\Old_Documentation\"
Move-Item "D365_Project_Operations_Integration_Analysis.md" "Documentation\99_Archive\Old_Documentation\"
Move-Item "RESA_Power_Project_MASTER_REFERENCE.md" "Documentation\99_Archive\Old_Documentation\"

# Move credentials (PDFs only - txt file will be deleted)
Move-Item "RESA-Dev-MCP-Access Certificates & Secrets.pdf" "Documentation\99_Archive\Credentials\"
Move-Item "RESA-Dev-MCP-Access.pdf" "Documentation\99_Archive\Credentials\"
Move-Item "Github_generate_token.pdf" "Documentation\99_Archive\Credentials\" -ErrorAction SilentlyContinue

# Move MCP setup doc
Move-Item "Dataverse MCP Server in VS Code.txt" "Documentation\00_START_HERE\DATAVERSE_MCP_SETUP.txt"

# Delete temporary/sensitive files
Remove-Item "I'm working on RESA Power Project T.txt" -ErrorAction SilentlyContinue
Remove-Item "RESA-Dev-MCP-Access.txt" -ErrorAction SilentlyContinue
Remove-Item "The 401 Unauthorized error typicall.txt" -ErrorAction SilentlyContinue
Remove-Item ".env.example" -ErrorAction SilentlyContinue
Remove-Item "main[200~it" -ErrorAction SilentlyContinue

# Create .gitignore in Credentials folder
@"
# Ignore all files in this directory
*
# Except this .gitignore file
!.gitignore
"@ | Out-File "Documentation\99_Archive\Credentials\.gitignore" -Encoding UTF8

Write-Host "✅ Root folder cleanup complete!" -ForegroundColor Green
```

---

## ✅ POST-CLEANUP VERIFICATION

After running cleanup script, root folder should contain only:

**Files** (7):
- .gitignore
- PROJECT_CONTEXT.json
- PROJECT_OVERVIEW.md  
- README.md
- RESA_Power_Build.cdsproj
- RESA_Power_Build.code-workspace

**Folders** (11):
- .claude/
- .git/
- CSV_Templates/
- Documentation/
- Import_Data/
- LASNAP16/
- Logs/
- MCP_Servers/
- Reference_Files/
- Scripts/
- Solution_Exports/
- Working/

---

## 🔄 .GITIGNORE UPDATES

Add these lines to your .gitignore:

```gitignore
# === SENSITIVE CREDENTIALS ===
**/Credentials/
RESA-Dev-MCP-Access.txt
**/MCP-Access*.txt
*.env
.env.local
**/*secret*.txt
**/*password*.txt
**/*token*.txt
**/claude_desktop_config.json

# === TEMPORARY FILES ===
I'm working on*.txt
The *error*.txt
**/*temp*.txt
```

---

## 📝 CLEANUP CHECKLIST

- [ ] Review all files marked for deletion
- [ ] Backup credential PDFs before moving
- [ ] Create new directories (Credentials, Old_Documentation)
- [ ] Run PowerShell cleanup script
- [ ] Update .gitignore with new patterns
- [ ] Verify root folder only contains essential files
- [ ] Test git status (should not show credential files)
- [ ] Commit cleanup changes to Git
- [ ] Update PROJECT_CONTEXT.json if needed

---

## 🎯 BENEFITS

**After Cleanup**:
1. ✅ Clean, professional root directory
2. ✅ Sensitive files protected from Git commits
3. ✅ Old documentation archived but accessible
4. ✅ Clear folder structure for new contributors
5. ✅ Reduced clutter in file explorer
6. ✅ Better organization for documentation

---

**Created**: November 23, 2025  
**Status**: Ready to Execute  
**Estimated Time**: 5 minutes
