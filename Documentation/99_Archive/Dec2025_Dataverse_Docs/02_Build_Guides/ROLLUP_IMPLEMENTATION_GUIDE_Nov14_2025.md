# ROLLUP FIELDS IMPLEMENTATION GUIDE
## RESA Power Project Tracker - Complete Rollup Configuration

**Date:** November 14, 2025  
**Phase:** 2 - Rollup Fields Implementation  
**Total Fields:** 21 rollup fields (7 per table × 3 tables)  
**Estimated Time:** 45-60 minutes

---

## 🎯 IMPLEMENTATION ORDER

Build in this sequence:
1. **Tasks Table** - 7 rollup fields (20 minutes)
2. **Project Scope Table** - 7 rollup fields (20 minutes)
3. **Projects Table** - 7 rollup fields (20 minutes)
4. **PUBLISH** - Critical before calculated fields

---

## 📋 TASKS TABLE - 7 ROLLUP FIELDS

**Navigate to:** Solutions → RESA Power Project Tracker → Tables → Tasks → Columns

### **Rollup #1: Total_Apparatus_Hours**
```
Display name: Total Apparatus Hours
Name: cr950_total_apparatus_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Tasks
RELATED ENTITY: Apparatus (Task)  ← Critical!
FILTERS: If Task contains data
AGGREGATION: SUM of Labor_Hours
```

---

### **Rollup #2: Total_Completed_Hours**
```
Display name: Total Completed Hours
Name: cr950_total_completed_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Tasks
RELATED ENTITY: Apparatus (Task)
FILTERS: If Task contains data
AGGREGATION: SUM of Completed_Hours
```

---

### **Rollup #3: Total_Remaining_Hours**
```
Display name: Total Remaining Hours
Name: cr950_total_remaining_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Tasks
RELATED ENTITY: Apparatus (Task)
FILTERS: If Task contains data
AGGREGATION: SUM of Remaining_Hours
```

---

### **Rollup #4: Total_Actual_Hours**
```
Display name: Total Actual Hours
Name: cr950_total_actual_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Tasks
RELATED ENTITY: Apparatus (Task)
FILTERS: If Task contains data
AGGREGATION: SUM of Actual_Hours
```

---

### **Rollup #5: Total_Delays**
```
Display name: Total Delays
Name: cr950_total_delays
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Tasks
RELATED ENTITY: Apparatus (Task)
FILTERS: If Task contains data
AGGREGATION: SUM of Delays
```

---

### **Rollup #6: Total_Apparatus_Count**
```
Display name: Total Apparatus Count
Name: cr950_total_apparatus_count
Data type: Whole Number → Change to Rollup

SOURCE ENTITY: Tasks
RELATED ENTITY: Apparatus (Task)
FILTERS: If Task contains data
AGGREGATION: COUNT of [Primary Key - cr950_apparatusid]
```

---

### **Rollup #7: Completed_Apparatus_Count**
```
Display name: Completed Apparatus Count
Name: cr950_completed_apparatus_count
Data type: Whole Number → Change to Rollup

SOURCE ENTITY: Tasks
RELATED ENTITY: Apparatus (Task)
FILTERS: 
  - If Task contains data
  - + Add condition: Completion_Status Equals Complete
AGGREGATION: COUNT of [Primary Key - cr950_apparatusid]
```

**⚠️ Note:** This one has TWO filters - the relationship filter plus status filter

---

## 📋 PROJECT SCOPE TABLE - 7 ROLLUP FIELDS

**Navigate to:** Solutions → RESA Power Project Tracker → Tables → Project Scope → Columns

**⚠️ CRITICAL DIFFERENCE:** Related Entity = **Apparatus (Scope)** not (Task)!

### **Rollup #8: Total_Apparatus_Hours**
```
Display name: Total Apparatus Hours
Name: cr950_total_apparatus_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Project Scope
RELATED ENTITY: Apparatus (Scope)  ← NOTE: (Scope) not (Task)!
FILTERS: If Scope contains data
AGGREGATION: SUM of Labor_Hours
```

---

### **Rollup #9: Total_Completed_Hours**
```
Display name: Total Completed Hours
Name: cr950_total_completed_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Project Scope
RELATED ENTITY: Apparatus (Scope)
FILTERS: If Scope contains data
AGGREGATION: SUM of Completed_Hours
```

---

### **Rollup #10: Total_Remaining_Hours**
```
Display name: Total Remaining Hours
Name: cr950_total_remaining_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Project Scope
RELATED ENTITY: Apparatus (Scope)
FILTERS: If Scope contains data
AGGREGATION: SUM of Remaining_Hours
```

---

### **Rollup #11: Total_Actual_Hours**
```
Display name: Total Actual Hours
Name: cr950_total_actual_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Project Scope
RELATED ENTITY: Apparatus (Scope)
FILTERS: If Scope contains data
AGGREGATION: SUM of Actual_Hours
```

---

### **Rollup #12: Total_Delays**
```
Display name: Total Delays
Name: cr950_total_delays
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Project Scope
RELATED ENTITY: Apparatus (Scope)
FILTERS: If Scope contains data
AGGREGATION: SUM of Delays
```

---

### **Rollup #13: Total_Apparatus_Count**
```
Display name: Total Apparatus Count
Name: cr950_total_apparatus_count
Data type: Whole Number → Change to Rollup

SOURCE ENTITY: Project Scope
RELATED ENTITY: Apparatus (Scope)
FILTERS: If Scope contains data
AGGREGATION: COUNT of [Primary Key - cr950_apparatusid]
```

---

### **Rollup #14: Completed_Apparatus_Count**
```
Display name: Completed Apparatus Count
Name: cr950_completed_apparatus_count
Data type: Whole Number → Change to Rollup

SOURCE ENTITY: Project Scope
RELATED ENTITY: Apparatus (Scope)
FILTERS: 
  - If Scope contains data
  - + Add condition: Completion_Status Equals Complete
AGGREGATION: COUNT of [Primary Key - cr950_apparatusid]
```

---

## 📋 PROJECTS TABLE - 7 ROLLUP FIELDS

**Navigate to:** Solutions → RESA Power Project Tracker → Tables → Projects → Columns

**⚠️ CRITICAL DIFFERENCE:** Related Entity = **Apparatus (Project)** not (Task) or (Scope)!

### **Rollup #15: Total_Apparatus_Hours**
```
Display name: Total Apparatus Hours
Name: cr950_total_apparatus_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Projects
RELATED ENTITY: Apparatus (Project)  ← NOTE: (Project)!
FILTERS: If Project contains data
AGGREGATION: SUM of Labor_Hours
```

---

### **Rollup #16: Total_Completed_Hours**
```
Display name: Total Completed Hours
Name: cr950_total_completed_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Projects
RELATED ENTITY: Apparatus (Project)
FILTERS: If Project contains data
AGGREGATION: SUM of Completed_Hours
```

---

### **Rollup #17: Total_Remaining_Hours**
```
Display name: Total Remaining Hours
Name: cr950_total_remaining_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Projects
RELATED ENTITY: Apparatus (Project)
FILTERS: If Project contains data
AGGREGATION: SUM of Remaining_Hours
```

---

### **Rollup #18: Total_Actual_Hours**
```
Display name: Total Actual Hours
Name: cr950_total_actual_hours
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Projects
RELATED ENTITY: Apparatus (Project)
FILTERS: If Project contains data
AGGREGATION: SUM of Actual_Hours
```

---

### **Rollup #19: Total_Delays**
```
Display name: Total Delays
Name: cr950_total_delays
Data type: Decimal → Change to Rollup

SOURCE ENTITY: Projects
RELATED ENTITY: Apparatus (Project)
FILTERS: If Project contains data
AGGREGATION: SUM of Delays
```

---

### **Rollup #20: Total_Apparatus_Count**
```
Display name: Total Apparatus Count
Name: cr950_total_apparatus_count
Data type: Whole Number → Change to Rollup

SOURCE ENTITY: Projects
RELATED ENTITY: Apparatus (Project)
FILTERS: If Project contains data
AGGREGATION: COUNT of [Primary Key - cr950_apparatusid]
```

---

### **Rollup #21: Completed_Apparatus_Count**
```
Display name: Completed Apparatus Count
Name: cr950_completed_apparatus_count
Data type: Whole Number → Change to Rollup

SOURCE ENTITY: Projects
RELATED ENTITY: Apparatus (Project)
FILTERS: 
  - If Project contains data
  - + Add condition: Completion_Status Equals Complete
AGGREGATION: COUNT of [Primary Key - cr950_apparatusid]
```

---

## ⚠️ CRITICAL REMINDERS

### **Related Entity Changes Per Table:**
- **Tasks:** `Apparatus (Task)`
- **Project Scope:** `Apparatus (Scope)`
- **Projects:** `Apparatus (Project)`

**This tells Dataverse which relationship path to follow for the aggregation!**

---

### **Data Types:**
- **SUM rollups:** Use Decimal data type
- **COUNT rollups:** Use Whole Number data type

---

### **Filters:**
- **Most rollups:** Single filter (If [relationship] contains data)
- **Completed_Count:** Two filters (relationship + Status = Complete)

---

### **Aggregation Fields:**
- **For SUM:** Select the specific field (Labor_Hours, Completed_Hours, etc.)
- **For COUNT:** Select Primary Key (cr950_apparatusid)

---

## ✅ COMPLETION CHECKLIST

### **Tasks Table:**
- [ ] Total_Apparatus_Hours
- [ ] Total_Completed_Hours
- [ ] Total_Remaining_Hours
- [ ] Total_Actual_Hours
- [ ] Total_Delays
- [ ] Total_Apparatus_Count
- [ ] Completed_Apparatus_Count

### **Project Scope Table:**
- [ ] Total_Apparatus_Hours
- [ ] Total_Completed_Hours
- [ ] Total_Remaining_Hours
- [ ] Total_Actual_Hours
- [ ] Total_Delays
- [ ] Total_Apparatus_Count
- [ ] Completed_Apparatus_Count

### **Projects Table:**
- [ ] Total_Apparatus_Hours
- [ ] Total_Completed_Hours
- [ ] Total_Remaining_Hours
- [ ] Total_Actual_Hours
- [ ] Total_Delays
- [ ] Total_Apparatus_Count
- [ ] Completed_Apparatus_Count

---

## 🎯 QUICK REFERENCE PATTERNS

### **Pattern A: SUM Rollups** (5 per table)
```
Data type: Decimal → Rollup
Related Entity: Apparatus ([Task/Scope/Project])
Filters: If [relationship] contains data
Aggregation: SUM of [specific field]
```

**Fields that use this pattern:**
- Total_Apparatus_Hours (SUM Labor_Hours)
- Total_Completed_Hours (SUM Completed_Hours)
- Total_Remaining_Hours (SUM Remaining_Hours)
- Total_Actual_Hours (SUM Actual_Hours)
- Total_Delays (SUM Delays)

---

### **Pattern B: Simple COUNT** (1 per table)
```
Data type: Whole Number → Rollup
Related Entity: Apparatus ([Task/Scope/Project])
Filters: If [relationship] contains data
Aggregation: COUNT of Primary Key
```

**Fields that use this pattern:**
- Total_Apparatus_Count

---

### **Pattern C: Filtered COUNT** (1 per table)
```
Data type: Whole Number → Rollup
Related Entity: Apparatus ([Task/Scope/Project])
Filters: 
  1. If [relationship] contains data
  2. Completion_Status Equals Complete
Aggregation: COUNT of Primary Key
```

**Fields that use this pattern:**
- Completed_Apparatus_Count

---

## 💡 TIME-SAVING TIPS

1. **Create all fields in one table before moving to next**
   - Easier to maintain context
   - Can verify pattern is correct

2. **Copy/paste display names carefully**
   - Avoid typos
   - Maintain consistency

3. **Double-check Related Entity for each table**
   - Tasks: (Task)
   - Scope: (Scope)
   - Projects: (Project)

4. **Save each field before starting next**
   - Prevents loss of work
   - Allows incremental progress

5. **Don't publish until all 21 are created**
   - Batch publishing is more efficient
   - Easier to fix errors before publishing

---

## 🚀 AFTER ALL 21 ROLLUPS

**Once all rollup fields are created:**

1. **Review the list** - verify all 21 exist
2. **Check for typos** - field names should be consistent
3. **Click "Publish all customizations"** (top right)
4. **Wait for publish to complete** (~2-3 minutes)
5. **Then proceed to Phase 3** - Calculated Fields

---

## 📊 WHAT YOU'LL ACHIEVE

After completing these 21 rollups, you'll have:

**At Task Level:**
- Automatic totaling of all apparatus hours
- Real-time completion tracking
- Delay accumulation
- Progress visibility

**At Scope Level:**
- Scope-wide hour tracking
- Multi-task aggregation
- Scope completion metrics

**At Project Level:**
- Portfolio view of all work
- Project-wide totals
- Executive dashboard data
- Earned value metrics

---

## ⚠️ COMMON MISTAKES TO AVOID

### **Mistake #1: Wrong Related Entity**
❌ Using Apparatus (Task) for all tables  
✅ Change to (Scope) for Project Scope, (Project) for Projects

### **Mistake #2: Wrong Data Type**
❌ Using Whole Number for SUM rollups  
✅ Use Decimal for SUM, Whole Number for COUNT

### **Mistake #3: Missing Second Filter**
❌ Completed_Count with only relationship filter  
✅ Add Status = Complete as second filter

### **Mistake #4: Wrong Aggregation Field**
❌ Using Labor_Hours for all SUM rollups  
✅ Match field to rollup name (Completed_Hours for Total_Completed_Hours)

---

**END OF ROLLUP IMPLEMENTATION GUIDE**

**Print or reference this document while building all 21 rollup fields.**

**Total Time:** 45-60 minutes for all 21 fields  
**Next Phase:** 6 calculated fields (after publishing rollups)
