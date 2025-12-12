# Rollup Fields Creation Guide
## Manual UI Configuration Required

**Created:** November 22, 2025  
**Time Required:** 3-4 hours  
**Fields to Create:** 32 rollup fields (18 date + 14 revenue)

---

## ⚠️ Why Manual Configuration?

Rollup fields **cannot** be created via:
- ❌ Dataverse Web API (doesn't support rollup metadata)
- ❌ PAC CLI (no rollup field commands)
- ✅ Only via **Dataverse UI** or **Solution XML import**

---

## 🚀 Quick Start - Use Dataverse UI

**Access:** https://make.powerapps.com → Select your environment (org99cd6c6e)

### Navigation:
1. Click **Solutions** (left sidebar)
2. Open your solution
3. Click **Tables**
4. Select table → **Columns** → **+ New column**
5. Choose **Data type: Rollup**

---

## 📋 PHASE 1: Date Rollup Fields (18 fields)

### Tasks Table - 6 Rollup Fields

**Navigate to:** Solutions → [Your Solution] → Tables → Tasks → Columns

#### 1. Earliest Anticipated Start
```
Display Name: Earliest Anticipated Start
Name: cr950_earliest_anticipated_start
Data Type: Date and Time (Date Only format)
Format: Date Only
Rollup Field: Yes

Related Entity: Apparatus (cr950_apparatus)
  Relationship: Task → Apparatus (1:N)
Aggregate Function: MIN
Source Field: Anticipated Start (cr950_anticipated_start)
Filter: None
```

#### 2. Latest Anticipated Start
```
Display Name: Latest Anticipated Start
Name: cr950_latest_anticipated_start
Data Type: Date and Time (Date Only format)
Format: Date Only
Rollup Field: Yes

Related Entity: Apparatus (cr950_apparatus)
Aggregate Function: MAX
Source Field: Anticipated Start (cr950_anticipated_start)
Filter: None
```

#### 3. Earliest Actual Start
```
Display Name: Earliest Actual Start
Name: cr950_earliest_actual_start
Data Type: Date and Time (Date Only format)
Format: Date Only
Rollup Field: Yes

Related Entity: Apparatus (cr950_apparatus)
Aggregate Function: MIN
Source Field: Actual Start (cr950_actual_start)
Filter: None
```

#### 4. Latest Actual Start
```
Display Name: Latest Actual Start
Name: cr950_latest_actual_start
Data Type: Date and Time (Date Only format)
Format: Date Only
Rollup Field: Yes

Related Entity: Apparatus (cr950_apparatus)
Aggregate Function: MAX
Source Field: Actual Start (cr950_actual_start)
Filter: None
```

#### 5. Earliest Completion Date
```
Display Name: Earliest Completion Date
Name: cr950_earliest_completion_date
Data Type: Date and Time (Date Only format)
Format: Date Only
Rollup Field: Yes

Related Entity: Apparatus (cr950_apparatus)
Aggregate Function: MIN
Source Field: Date Completed (cr950_date_completed)
Filter: None
```

#### 6. Latest Completion Date
```
Display Name: Latest Completion Date
Name: cr950_latest_completion_date
Data Type: Date and Time (Date Only format)
Format: Date Only
Rollup Field: Yes

Related Entity: Apparatus (cr950_apparatus)
Aggregate Function: MAX
Source Field: Date Completed (cr950_date_completed)
Filter: None
```

---

### Scopes Table - 6 Rollup Fields

**Navigate to:** Solutions → [Your Solution] → Tables → Scopes → Columns

**Use EXACT same pattern as Tasks:**
- Replace "Tasks" references with "Scopes"
- Source: Still Apparatus table (Scope → Apparatus relationship)
- Same 6 fields: Earliest/Latest for Anticipated Start, Actual Start, Completion Date

---

### Projects Table - 6 Rollup Fields

**Navigate to:** Solutions → [Your Solution] → Tables → Projects → Columns

**DIFFERENT SOURCE:**

#### 1. Earliest Anticipated Start
```
Display Name: Earliest Anticipated Start
Name: cr950_earliest_anticipated_start
Data Type: Date and Time (Date Only format)
Rollup Field: Yes

Related Entity: Project Scope (cr950_projectscope)  ← DIFFERENT!
  Relationship: Project → Scopes (1:N)
Aggregate Function: MIN
Source Field: Earliest Anticipated Start (cr950_earliest_anticipated_start)  ← FROM SCOPES!
Filter: None
```

**Repeat for remaining 5 fields**, sourcing from **Scopes table** (not Apparatus):
- Latest Anticipated Start (MAX from Scopes)
- Earliest Actual Start (MIN from Scopes)
- Latest Actual Start (MAX from Scopes)
- Earliest Completion Date (MIN from Scopes)
- Latest Completion Date (MAX from Scopes)

---

## 💰 PHASE 2: Revenue Rollup Fields (14 fields)

### Scope Financial Summary Table - 7 Rollup Fields

**Navigate to:** Solutions → [Your Solution] → Tables → Scope Financial Summary → Columns

#### 1. Total Revenue Recognized
```
Display Name: Total Revenue Recognized
Name: cr950_total_revenue_recognized
Data Type: Currency
Rollup Field: Yes

Related Entity: Apparatus Revenue (cr950_apparatusrevenue)
  Relationship: Via Scope lookup
Aggregate Function: SUM
Source Field: Revenue Amount (cr950_revenue_amount)
Filter: Revenue Status = RECOGNIZED (value = 2)
```

#### 2. Total Revenue Pending
```
Display Name: Total Revenue Pending
Name: cr950_total_revenue_pending
Data Type: Currency
Rollup Field: Yes

Related Entity: Apparatus Revenue (cr950_apparatusrevenue)
Aggregate Function: SUM
Source Field: Revenue Amount (cr950_revenue_amount)
Filter: Revenue Status = PENDING (value = 1)
```

#### 3. Total Billable Hours
```
Display Name: Total Billable Hours
Name: cr950_total_billable_hours
Data Type: Decimal
Precision: 2
Rollup Field: Yes

Related Entity: Apparatus Revenue (cr950_apparatusrevenue)
Aggregate Function: SUM
Source Field: Apparatus Hours (cr950_apparatus_hours)
Filter: None
```

#### 4. Total Delay Hours
```
Display Name: Total Delay Hours
Name: cr950_total_delay_hours
Data Type: Decimal
Precision: 2
Rollup Field: Yes

Related Entity: Apparatus Revenue (cr950_apparatusrevenue)
Aggregate Function: SUM
Source Field: Delays (cr950_delays)
Filter: None
```

#### 5. Revenue Record Count
```
Display Name: Revenue Record Count
Name: cr950_revenue_record_count
Data Type: Whole Number
Rollup Field: Yes

Related Entity: Apparatus Revenue (cr950_apparatusrevenue)
Aggregate Function: COUNT
Source Field: (Any field - typically the primary key)
Filter: None
```

#### 6. Average Revenue Per Apparatus
```
Display Name: Average Revenue Per Apparatus
Name: cr950_average_revenue_per_apparatus
Data Type: Currency
Rollup Field: Yes

Related Entity: Apparatus Revenue (cr950_apparatusrevenue)
Aggregate Function: AVG
Source Field: Revenue Amount (cr950_revenue_amount)
Filter: Revenue Status = RECOGNIZED (value = 2)
```

#### 7. Latest Revenue Date
```
Display Name: Latest Revenue Date
Name: cr950_latest_revenue_date
Data Type: Date and Time (Date Only format)
Rollup Field: Yes

Related Entity: Apparatus Revenue (cr950_apparatusrevenue)
Aggregate Function: MAX
Source Field: Created On (createdon)
Filter: None
```

---

### Project Financial Summary Table - 7 Rollup Fields

**Navigate to:** Solutions → [Your Solution] → Tables → Project Financial Summary → Columns

**DIFFERENT SOURCE:**

#### 1. Total Revenue Recognized
```
Display Name: Total Revenue Recognized
Name: cr950_total_revenue_recognized
Data Type: Currency
Rollup Field: Yes

Related Entity: Scope Financial Summary (cr950_scopefinancialsummary)  ← DIFFERENT!
  Relationship: Via Project lookup
Aggregate Function: SUM
Source Field: Total Revenue Recognized (cr950_total_revenue_recognized)  ← FROM SCOPE FINANCIAL!
Filter: None
```

**Repeat for remaining 6 fields**, sourcing from **Scope Financial Summary**:
- Total Revenue Pending (SUM from Scope Financial)
- Total Billable Hours (SUM from Scope Financial)
- Total Delay Hours (SUM from Scope Financial)
- Revenue Record Count (SUM from Scope Financial)
- Average Revenue Per Scope (AVG from Scope Financial)
- Latest Revenue Date (MAX from Scope Financial)

---

## ✅ Verification Checklist

After creating fields, verify:

### Date Rollups:
- [ ] Tasks: 6 fields visible in columns list
- [ ] Scopes: 6 fields visible in columns list
- [ ] Projects: 6 fields visible in columns list
- [ ] Create test Apparatus with dates → verify rollups calculate

### Revenue Rollups:
- [ ] Scope Financial Summary: 7 fields visible
- [ ] Project Financial Summary: 7 fields visible
- [ ] Complete test Apparatus → verify revenue flows → check rollups

---

## 🔄 Rollup Calculation

**Important:** Rollups calculate asynchronously (every 12 hours by default)

**Manual recalculation:**
1. Open a record
2. Click **...** (More commands)
3. Select **Recalculate**

**Or trigger via workflow/Power Automate**

---

## 📦 After Completion

1. **Add to Solution** (if not already)
2. **Update Forms** - add rollup fields (read-only)
3. **Create Views** - show KPI fields
4. **Test thoroughly** with sample data
5. **Export solution** as v1.5.0.0

---

## 🆘 Troubleshooting

**Rollup not calculating:**
- Wait 5-10 minutes (async process)
- Check relationship exists
- Verify source field name correct
- Manually recalculate

**Can't find related entity:**
- Ensure lookup relationship created first
- Check entity logical names match

**Filter not working:**
- Use numeric values for option sets (e.g., 2 not "RECOGNIZED")
- Test filter in Advanced Find first

---

## ⏱️ Time Estimates

- **Tasks rollups (6):** 30 minutes
- **Scopes rollups (6):** 30 minutes  
- **Projects rollups (6):** 30 minutes
- **Scope Financial rollups (7):** 45 minutes
- **Project Financial rollups (7):** 45 minutes
- **Testing & verification:** 30 minutes

**Total: 3.5-4 hours**

---

## 📖 Reference Documents

- Full specs: `KPI_FIELDS_IMPLEMENTATION_PRIORITY.md`
- Date details: `DATE_TRACKING_IMPLEMENTATION.md`
- Revenue flow: `REVENUE_RECOGNITION_FLOW_SPEC.md`

---

**Ready to start? Begin with Tasks table (easiest) to get familiar with the UI!**
