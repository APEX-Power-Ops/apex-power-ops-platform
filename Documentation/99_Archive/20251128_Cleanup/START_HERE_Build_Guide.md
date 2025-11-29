# 🚀 RESA POWER - START HERE BUILD GUIDE
## Get LASNAP16 into Dataverse - Step by Step

**Goal:** Get your 1,905 tasks from LASNAP16 into Dataverse by end of week  
**Time:** 3-5 hours total  
**Difficulty:** Beginner-friendly (I'll walk you through every click)

---

## ✅ BEFORE YOU START - Checklist

Do you have:
- [ ] Power Apps license (check: go to make.powerapps.com - can you sign in?)
- [ ] Your three CSV files (Project_Import.csv, Scopes_Import.csv, Tasks_Import.csv)
- [ ] Admin rights to create environments (if not, ask your IT/boss)
- [ ] 3-5 hours of uninterrupted time this week

**If you answered YES to all → Continue**  
**If NO to any → Let me know which one, we'll solve it**

---

## 🎯 STEP 1: Create Your Dataverse Environment (30 minutes)

### What You're Doing:
Creating a "workspace" in the cloud where your project data will live

### Why:
Dataverse is like a database in the cloud. You need a place to put your tables before you can import data.

---

### 1.1 - Go to Power Platform Admin Center

**Action:**
1. Open browser (Chrome or Edge work best)
2. Go to: https://admin.powerplatform.microsoft.com
3. Sign in with your work email
4. You should see "Power Platform admin center"

**Checkpoint:** Can you see the admin center home page?
- ✅ YES → Continue to 1.2
- ❌ NO → You might not have admin rights. Message me the error.

---

### 1.2 - Create New Environment

**Action:**
1. Click **"Environments"** in left menu
2. Click **"+ New"** button at top
3. Fill in the form:

```
Name: RESA Power Production
Type: Production (not Sandbox)
Region: (Choose your region - probably United States)
Purpose: Project tracking and field management
```

4. Click **"Next"**

**Checkpoint:** Did the form submit without errors?
- ✅ YES → Continue to 1.3
- ❌ NO → Screenshot the error, send to me

---

### 1.3 - Add Dataverse Database

**Action:**
1. You'll see "Add a Dataverse data store?"
2. Toggle to **YES**
3. Fill in:

```
Language: English
Currency: USD - US Dollar
Enable Dynamics 365 apps: YES
Deploy sample apps: NO (we don't need them)
```

4. Click **"Save"**

**What Happens:**
- Environment creation starts (takes 5-10 minutes)
- You'll see a progress spinner
- Status will say "Preparing"

**Action While Waiting:**
- Get coffee ☕
- Find your three CSV files (download them if you haven't)
- Check they're saved somewhere you can find easily

**Checkpoint:** After 10 minutes, refresh page. Status should say "Ready"
- ✅ YES → Continue to Step 2
- ❌ STILL "Preparing" → Wait another 5 min, refresh again
- ❌ ERROR → Screenshot and send to me

---

## 🎯 STEP 2: Create Your First Table - "Projects" (45 minutes)

### What You're Doing:
Creating the "Projects" table to hold project information (Job #, Client, Location, etc.)

### Why:
Everything connects to a Project. This is the top-level container.

---

### 2.1 - Go to Power Apps

**Action:**
1. Open new tab: https://make.powerapps.com
2. Top right corner → Click environment dropdown
3. Select **"RESA Power Production"** (the one you just created)
4. Left menu → Click **"Tables"**

**Checkpoint:** Do you see a list of existing tables (like "Account", "Contact")?
- ✅ YES → These are default tables, that's normal. Continue to 2.2
- ❌ NO → You might be in wrong environment. Check dropdown again.

---

### 2.2 - Create New Table

**Action:**
1. Click **"+ New table"** at top
2. Choose **"Add columns and data"** (the easy way)
3. In the popup, name it: **Projects**
4. Click **"Create"**

**What You'll See:**
- Excel-like grid appears
- Default column called "Name" exists
- You're in "edit mode"

**Checkpoint:** Do you see the grid with "Name" column?
- ✅ YES → Continue to 2.3
- ❌ NO → Try refreshing page, or screenshot error

---

### 2.3 - Add Project Columns

**Action:**
We need to add columns for: Job Number, Client, Location, Lead Tech, Status

**For each column below, do this:**
1. Click **"+ New column"** (or click + in grid header)
2. Fill in exactly as shown
3. Click "Save"

---

#### Column 1: Job Number

```
Display name: Job Number
Data type: Single line of text
Required: Business required
Searchable: Yes
Max length: 50
```

Click **"Save"**

---

#### Column 2: Client Name

```
Display name: Client Name
Data type: Single line of text
Required: Business required
Searchable: Yes
Max length: 100
```

Click **"Save"**

---

#### Column 3: Location

```
Display name: Location
Data type: Single line of text
Required: Optional
Searchable: Yes
Max length: 200
```

Click **"Save"**

---

#### Column 4: Lead Technician

```
Display name: Lead Technician
Data type: Single line of text
Required: Optional
Searchable: Yes
Max length: 100
```

Click **"Save"**

---

#### Column 5: Project Status

```
Display name: Project Status
Data type: Choice
Required: Business required
Choices (add these):
  - Active
  - On Hold
  - Complete
  - Quoted
Default value: Active
```

Click **"Save"**

---

**Checkpoint:** Do you now see 6 columns total?
- Name (was there by default)
- Job Number
- Client Name
- Location
- Lead Technician
- Project Status

- ✅ YES → Continue to 2.4
- ❌ NO → Count again, something missing? Try adding it again.

---

### 2.4 - Import Your First Project

**Action:**
1. You should still be in the grid view
2. Click in the first empty row
3. Type this data:

```
Name: LASNAP16
Job Number: 634414
Client Name: LASNAP
Location: Las Vegas, NV
Lead Technician: Brandon Valdavis
Project Status: Active
```

4. Press Enter or Tab to move through cells
5. After last cell, data auto-saves (you'll see checkmark)

**Checkpoint:** Do you see your LASNAP16 project in the grid?
- ✅ YES → **HUGE WIN!** You just created your first record in Dataverse! Continue to Step 3.
- ❌ NO → Did you get an error? Screenshot it.

---

## 🎯 STEP 3: Create "Scopes" Table (30 minutes)

### What You're Doing:
Creating the Scopes table (PPM01, PPM02, GDB, HOUSE, MV, etc.)

### Why:
Each project has multiple scopes. This is the second level of your hierarchy.

---

### 3.1 - Create Scopes Table

**Action:**
1. Left menu → Click **"Tables"** (to go back to tables list)
2. Click **"+ New table"**
3. Choose **"Add columns and data"**
4. Name it: **Scopes**
5. Click **"Create"**

---

### 3.2 - Add Scope Columns

Add these columns (same process as before):

#### Column 1: Scope Name

```
Display name: Scope Name
Data type: Single line of text
Required: Business required
Searchable: Yes
Max length: 100
```

---

#### Column 2: Drawing Reference

```
Display name: Drawing Reference
Data type: Single line of text
Required: Optional
Max length: 100
```

---

#### Column 3: Total Hours Quoted

```
Display name: Total Hours Quoted
Data type: Decimal number
Required: Optional
Minimum value: 0
Maximum value: 999999
Decimal places: 2
```

---

#### Column 4: Scope Status

```
Display name: Scope Status
Data type: Choice
Choices:
  - Not Started
  - In Progress
  - Complete
Default: Not Started
```

---

#### Column 5: Project (RELATIONSHIP - IMPORTANT!)

This connects Scopes to Projects

```
Display name: Project
Data type: Lookup
Related table: Projects (select from dropdown)
Required: Business required
```

**This is your first RELATIONSHIP!** Each scope belongs to one project.

---

**Checkpoint:** Do you now have these columns?
- Name
- Scope Name
- Drawing Reference
- Total Hours Quoted
- Scope Status
- Project (with lookup icon)

- ✅ YES → Continue to 3.3
- ❌ NO → Which one is missing?

---

### 3.3 - Add Your First Scope

**Action:**
1. Click in first empty row
2. Type:

```
Name: PPM01
Scope Name: PPM01
Drawing Reference: (leave blank for now)
Total Hours Quoted: 150
Scope Status: In Progress
Project: LASNAP16 (start typing, it will search and let you select)
```

3. Press Enter after last cell

**IMPORTANT:** When you click in the "Project" field, it should let you SEARCH for and SELECT "LASNAP16"

**Checkpoint:** Does your PPM01 scope show with "LASNAP16" in the Project column?
- ✅ YES → **You just created your first relationship!** Continue to Step 4.
- ❌ NO → Can't select project? Screenshot error.

---

## 🎯 STEP 4: Create "Tasks" Table (30 minutes)

### What You're Doing:
Creating the Tasks table (your 1,905 apparatus items)

### Why:
This is where your actual work items live. Everything rolls up from here.

---

### 4.1 - Create Tasks Table

**Action:**
1. Left menu → **"Tables"**
2. **"+ New table"**
3. **"Add columns and data"**
4. Name: **Tasks**
5. **"Create"**

---

### 4.2 - Add Task Columns

Add these columns:

#### Column 1: Task Name

```
Display name: Task Name
Data type: Single line of text
Required: Business required
Searchable: Yes
Max length: 200
```

---

#### Column 2: Apparatus Type

```
Display name: Apparatus Type
Data type: Single line of text
Required: Optional
Max length: 200
```

---

#### Column 3: Quantity Quoted

```
Display name: Quantity Quoted
Data type: Whole number
Required: Optional
Minimum value: 0
Maximum value: 999999
```

---

#### Column 4: Quantity Completed

```
Display name: Quantity Completed
Data type: Whole number
Required: Optional
Minimum value: 0
Maximum value: 999999
```

---

#### Column 5: Hours per Unit

```
Display name: Hours per Unit
Data type: Decimal number
Required: Optional
Minimum value: 0
Maximum value: 9999
Decimal places: 2
```

---

#### Column 6: Task Status

```
Display name: Task Status
Data type: Choice
Choices:
  - Not Started
  - In Progress
  - Completed
Default: Not Started
```

---

#### Column 7: Priority

```
Display name: Priority
Data type: Choice
Choices:
  - High
  - Medium
  - Low
Default: Medium
```

---

#### Column 8: Availability

```
Display name: Availability
Data type: Choice
Choices:
  - Ready
  - On Hold
  - Not Available
Default: Ready
```

---

#### Column 9: Project (Relationship)

```
Display name: Project
Data type: Lookup
Related table: Projects
Required: Business required
```

---

#### Column 10: Scope (Relationship)

```
Display name: Scope
Data type: Lookup
Related table: Scopes
Required: Optional
```

---

**Checkpoint:** You should have 12 columns total (Name + 11 you added)

- ✅ YES → Continue to 4.3
- ❌ NO → Which ones are missing?

---

### 4.3 - Add Your First Task

**Action:**
1. Click first empty row
2. Type:

```
Name: Transformer T001
Task Name: Pad Mount Transformer
Apparatus Type: Transformer - Pad Mount Oil
Quantity Quoted: 19
Quantity Completed: 17
Hours per Unit: 12
Task Status: In Progress
Priority: High
Availability: Ready
Project: LASNAP16 (search and select)
Scope: PPM01 (search and select)
```

3. Press Enter

**Checkpoint:** Does your task show with both Project and Scope linked?
- ✅ YES → **AMAZING!** You've built the core structure! Continue to Step 5.
- ❌ NO → What's not working?

---

## 🎯 STEP 5: Import Your Real Data (1-2 hours)

### What You're Doing:
Importing all 1,905 tasks from your CSV files

### Two Options:

---

### OPTION A: Excel Import (Easier, Slower)

**Best if:** You're comfortable with Excel

**Action:**
1. Download your Tasks_Import.csv
2. Open in Excel
3. Add column headers to match your Dataverse columns:
   - Name
   - Task Name
   - Apparatus Type
   - Quantity Quoted
   - Quantity Completed
   - Hours per Unit
   - Task Status
   - Priority
   - Availability
   - Project (put "LASNAP16" in every row)
   - Scope (put the scope name that matches)

4. Save as .xlsx
5. In Power Apps:
   - Go to Tasks table
   - Click "Import" → "Import from Excel"
   - Select your file
   - Map columns
   - Import

---

### OPTION B: Power Query (Faster, Learning Curve)

**Best if:** You want to learn the "right" way

I'll give you a separate guide for this if you want it.

---

### My Recommendation:

**Do Option A first** - Import just 20 tasks manually to test.

Once that works and you see data in your tables, we'll do bulk import.

---

**Checkpoint:** Do you see multiple tasks in your Tasks table?
- ✅ YES → **YOU DID IT!** Continue to Step 6 to see it in action.
- ❌ NO → Where did it fail? Import errors?

---

## 🎯 STEP 6: Build Your First Model-Driven App (30 minutes)

### What You're Doing:
Creating the app interface so you can actually USE your data

---

### 6.1 - Create App

**Action:**
1. Go to: https://make.powerapps.com
2. Left menu → **"Apps"**
3. **"+ New app"** → **"Model-driven"**
4. Name it: **RESA Power Tracker**
5. Click **"Create"**

---

### 6.2 - Add Your Tables

**Action:**
1. In the app designer, left side → Click **"Add page"**
2. Choose **"Table based view and form"**
3. Select **"Projects"** table
4. Click **"Add"**

5. Repeat for **"Scopes"** table
6. Repeat for **"Tasks"** table

---

### 6.3 - Publish and Test

**Action:**
1. Top right → Click **"Publish"**
2. Wait 30 seconds for publish to complete
3. Click **"Play"** button

**What You Should See:**
- Your app opens
- Left menu shows: Projects, Scopes, Tasks
- Click Projects → See LASNAP16
- Click into it → See details
- Related tab → See Scopes (if you added them)

**Checkpoint:** Can you navigate and see your data?
- ✅ YES → **🎉 YOU BUILT YOUR FIRST POWER APP!**
- ❌ NO → What do you see instead?

---

## 🎯 STEP 7: Connect Power BI (30 minutes)

### What You're Doing:
Pointing your existing Power BI dashboard at Dataverse instead of Excel

---

### 7.1 - Open Your Power BI File

**Action:**
1. Open your LASNAP16_Dashboard.pbix file
2. Home ribbon → **"Transform data"** → **"Data source settings"**

---

### 7.2 - Add Dataverse Connection

**Action:**
1. Home ribbon → **"Get data"** → **"More"**
2. Search for: **"Dataverse"**
3. Select **"Dataverse"**
4. Click **"Connect"**
5. Enter your environment URL:
   - Format: https://orgXXXXXXXX.crm.dynamics.com
   - Find this in Power Platform Admin Center → Environments → Your environment → Details

---

### 7.3 - Select Your Tables

**Action:**
1. Navigator window opens
2. Find and check:
   - Projects
   - Scopes
   - Tasks
3. Click **"Load"**

---

### 7.4 - Replicate Your Measures

**Action:**
This is where we use your Tabular Editor script!

1. In Power BI, External Tools → **Tabular Editor** (if installed)
2. Or manually recreate measures in Power BI
3. Your measures will work exactly the same, just point to new tables

**I'll help you with this part if needed.**

---

**Checkpoint:** Does your dashboard show data from Dataverse?
- ✅ YES → **YOU'RE LIVE! This is the finish line!**
- ❌ NO → Let me know what's not working

---

## 🎉 WHEN YOU'RE DONE - You'll Have:

✅ Dataverse environment with real data  
✅ Projects, Scopes, Tasks tables with relationships  
✅ Model-Driven app to view/edit data  
✅ Power BI connected to Dataverse  
✅ Foundation to build field tech mobile app  
✅ Proof that this works!

---

## 🚨 IF YOU GET STUCK:

**Take a screenshot and tell me:**
1. Which step number (e.g., "Step 2.3")
2. What you were doing
3. What error you got
4. I'll unstick you immediately

---

## 📞 START HERE - First Action:

**Right now, go to:** https://admin.powerplatform.microsoft.com

**Can you sign in?**
- YES → Start Step 1.2 (Create New Environment)
- NO → Tell me what happens, we'll fix it

**Let's build this thing.** 🚀
