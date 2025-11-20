# PROJECT CONTEXT UPDATE SCRIPTS
## Quick Reference for Updating PROJECT_CONTEXT.json

**Location**: `Scripts/PowerShell/Update-ProjectContext.ps1`  
**Created**: November 19, 2025  
**Purpose**: Easy updates to PROJECT_CONTEXT.json (your "memory server")

---

## 🚀 QUICK USAGE

### **Most Common: Quick Session Update**
```powershell
# Just update timestamp and session ID
.\Scripts\PowerShell\Update-ProjectContext.ps1 -SessionTopic "Your Work Here" -QuickUpdate
```

**Example:**
```powershell
.\Scripts\PowerShell\Update-ProjectContext.ps1 -SessionTopic "Date Tracking Implementation" -QuickUpdate
```

### **Add Critical Fact**
```powershell
.\Scripts\PowerShell\Update-ProjectContext.ps1 -AddCriticalFact "New rollup fields added: 18 date tracking fields"
```

### **Full Interactive Update**
```powershell
.\Scripts\PowerShell\Update-ProjectContext.ps1 -UpdateStatus
```

---

## 📋 USAGE EXAMPLES

### **Example 1: Session End (Quick)**
```powershell
# You completed some work, just update the timestamp
cd C:\RESA_Power_Build
.\Scripts\PowerShell\Update-ProjectContext.ps1 -SessionTopic "Memory MCP Documentation" -QuickUpdate

# Result: Updates lastUpdated and sessionId
```

### **Example 2: Add Important Discovery**
```powershell
# You discovered something critical that must be remembered
.\Scripts\PowerShell\Update-ProjectContext.ps1 -AddCriticalFact "Revenue rollups require KPI definitions from stakeholder"

# Result: Adds to criticalFacts array
```

### **Example 3: Full Status Update**
```powershell
# You completed a task, want to update status
.\Scripts\PowerShell\Update-ProjectContext.ps1 -UpdateStatus

# Interactive prompts walk you through:
# - Updating ready to implement tasks
# - Adding/removing blockers
# - Updating in planning items
```

### **Example 4: Combination**
```powershell
# Multiple updates at once
.\Scripts\PowerShell\Update-ProjectContext.ps1 `
    -SessionTopic "Revenue Architecture" `
    -AddCriticalFact "Decision made: Use aggregate rollups for revenue KPIs" `
    -UpdateStatus
```

---

## 🎯 WHEN TO USE EACH MODE

### **Use `-QuickUpdate` when:**
- ✅ Session ending
- ✅ No major changes to status
- ✅ Just need timestamp/sessionId refresh
- ✅ Want fast update (no prompts)

### **Use `-AddCriticalFact` when:**
- ✅ Discovered something important
- ✅ Made critical decision
- ✅ Found issue/blocker
- ✅ Need to remember specific information

### **Use `-UpdateStatus` when:**
- ✅ Completed a task
- ✅ New task ready to implement
- ✅ Blockers discovered or resolved
- ✅ Planning items changed

### **Use interactive mode (no params) when:**
- ✅ Major session milestone
- ✅ Version changed (e.g., v1.3.0.4 → v1.4.0.0)
- ✅ Need full review of context
- ✅ Want to update everything

---

## ⚙️ PARAMETERS REFERENCE

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `-SessionTopic` | String | Brief description of session | `"Date Tracking"` |
| `-AddCriticalFact` | String | New fact to remember | `"BusinessUnit is critical"` |
| `-UpdateStatus` | Switch | Interactive status update | `-UpdateStatus` |
| `-QuickUpdate` | Switch | Fast update (no prompts) | `-QuickUpdate` |
| `-ProjectRoot` | String | Path to project (default: C:\RESA_Power_Build) | `"D:\Projects\RESA"` |

---

## 🔄 TYPICAL WORKFLOW

### **At Session Start:**
```powershell
# AI reads context
# (You don't need to run script)
```

### **During Session:**
```powershell
# If you discover critical fact
.\Scripts\PowerShell\Update-ProjectContext.ps1 -AddCriticalFact "Important discovery here"
```

### **At Session End:**
```powershell
# Quick update
.\Scripts\PowerShell\Update-ProjectContext.ps1 -SessionTopic "What You Did" -QuickUpdate

# Git commit prompt will appear
# Press 'y' to commit and push
```

---

## 📊 WHAT GETS UPDATED

### **Always Updated (Quick Mode):**
- ✅ `lastUpdated` - Current timestamp
- ✅ `sessionId` - Generated from date + topic

### **Optional Updates (Interactive):**
- ⚙️ `project.version` - Project version
- ⚙️ `criticalFacts[]` - Important facts array
- ⚙️ `currentStatus.readyToImplement[]` - Available tasks
- ⚙️ `currentStatus.inPlanning[]` - Planning items
- ⚙️ `currentStatus.blockers[]` - Current blockers

---

## 💡 PRO TIPS

### **Tip 1: Use Aliases**
Create PowerShell alias for faster access:
```powershell
# Add to your PowerShell profile
Set-Alias -Name update-context -Value "C:\RESA_Power_Build\Scripts\PowerShell\Update-ProjectContext.ps1"

# Then use:
update-context -SessionTopic "Quick Work" -QuickUpdate
```

### **Tip 2: Git Auto-Commit**
Script prompts for Git commit/push at end. Just press 'y' twice for full automation.

### **Tip 3: Session ID Format**
Auto-generates format: `NOV19_Your_Topic`
- Uses abbreviated month + day
- Replaces spaces with underscores
- Easy to identify in Git history

### **Tip 4: View Current Context**
```powershell
# Quick view of current state
Get-Content .\PROJECT_CONTEXT.json | ConvertFrom-Json | ConvertTo-Json -Depth 2
```

### **Tip 5: Critical Facts Are Critical**
Only add facts that MUST survive session restarts:
- ✅ "BusinessUnit is multi-location, not unused"
- ✅ "Revenue rollups require aggregate formulas"
- ❌ "Created a new file today" (put in session summary)

---

## 🔧 TROUBLESHOOTING

### **Error: "PROJECT_CONTEXT.json not found"**
```powershell
# Check you're in project root
cd C:\RESA_Power_Build

# Or specify path
.\Scripts\PowerShell\Update-ProjectContext.ps1 -ProjectRoot "D:\Your\Path" -QuickUpdate
```

### **Error: "Failed to parse JSON"**
Your PROJECT_CONTEXT.json has syntax error. Check with:
```powershell
Get-Content .\PROJECT_CONTEXT.json | ConvertFrom-Json
```

Fix JSON syntax, then try again.

### **Git commit failed**
```powershell
# Manually commit
git add PROJECT_CONTEXT.json
git commit -m "chore: Update context"
git push public clean-main
```

### **Want to undo changes**
```powershell
# Restore from Git
git checkout PROJECT_CONTEXT.json
```

---

## 📝 OUTPUT EXAMPLES

### **Quick Update Output:**
```
=== PROJECT CONTEXT UPDATER ===
Updating: PROJECT_CONTEXT.json

✓ Loaded current context

QUICK UPDATE MODE
Session Topic: Date Tracking Implementation
Updated: lastUpdated = 2025-11-19T20:45:00Z
Updated: sessionId = NOV19_Date_Tracking_Implementation

✓ Context updated successfully!
```

### **Interactive Update Output:**
```
=== PROJECT CONTEXT UPDATER ===
Current Session: NOV19_Memory_MCP_Documentation
Last Updated: 2025-11-19T20:30:00Z

=== UPDATE SESSION INFO ===
Enter session topic: Revenue Rollups
✓ Session ID: NOV19_Revenue_Rollups
✓ Timestamp: 2025-11-19T21:00:00Z

=== UPDATE VERSION ===
New version: v1.4.0.0
✓ Version updated to: v1.4.0.0

=== ADD CRITICAL FACTS ===
Add new critical fact? (y/n): y
Enter critical fact: Revenue KPIs defined by stakeholder
✓ Added: Revenue KPIs defined by stakeholder

=== SUMMARY ===
Session ID: NOV19_Revenue_Rollups
Version: v1.4.0.0
Critical Facts: 5
Ready to Implement: 2
Blockers: 0

✓ Update complete!
```

---

## 🔗 RELATED DOCUMENTS

- **PROJECT_CONTEXT.json** - The file this script updates
- **VSCODE_SESSION_CONTINUITY.md** - Full guide on continuity system
- **PROJECT_STATUS_TRACKER.md** - Comprehensive project status (separate from context)
- **SESSION_RESUME_CHECKLIST.md** - Session startup protocol

---

## ✅ BEST PRACTICES

### **Do:**
- ✅ Run quick update at session end
- ✅ Add critical facts when discovered
- ✅ Commit to Git after updates
- ✅ Keep sessionId descriptive but brief
- ✅ Update status when tasks complete

### **Don't:**
- ❌ Add trivial facts (use session summary instead)
- ❌ Forget to commit changes
- ❌ Manually edit JSON (use script for safety)
- ❌ Update during work (only at milestones)
- ❌ Duplicate info from PROJECT_STATUS_TRACKER.md

---

**This script is your "memory server update tool" for VS Code/Copilot sessions.**

**END OF GUIDE**
