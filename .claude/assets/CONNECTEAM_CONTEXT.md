# Boss Pain Point: Connecteam Scheduling View

**Screenshot:** `connecteam-weekly-schedule.png` (save to this folder)

---

## What The Screenshot Shows

**Connecteam Week View:** Dec 15-21, 2025

### Structure
- **Two Project Groups:** LJT Projects, NETA Projects
- **14 Employees** listed with weekly hours
- **74 Shifts** scheduled across the week
- **604 total hours** for the week

### Employees Visible
| Name | Weekly Hours | Assignment Pattern |
|------|-------------|-------------------|
| Ace Randolph | 40:00 | Multi-day at City of Tempe |
| Kole Ellertson | 16:00 | Split days - multiple sites |
| William Thomas | 40:00 | Multi-day at City of Tempe |
| Aaron Carter | 40:00 | Full week on Sturgeon - Project Alpha |
| Austin Painter | 50:00 | Full week on Garney Companies |
| Fernando Morales | 50:00 | Full week on RES - Catclaw |
| Jacobo Ortiz | 50:00 | Full week on RES - Catclaw |
| John Czelenski | 48:00 | Mix of Garney + Travel |
| Josh Ganter | 50:00 | Full week on Cannon & Wendt |
| Juan Salcido | 40:00 | All day assignments - Aligned Cx Scripts |
| Peter Lujan | 50:00 | Full week on Cannon & Wendt |
| Phillip Pentecost | 50:00 | Full week on Garney Companies |
| Ryan Leliefeld | -- | Unavailable all week |

### Assignment Format Observed
Each block shows:
- **Time range:** `7:00a - 3:00p` or `6:00a - 4:00p`
- **Client:** Company name
- **Project:** Project name + ID number
- **Duration indicators:** Clock icon, shift count, user count

### Pain Points Visible
1. **Dense information** - Hard to scan quickly
2. **Partial days mixed with full days** - No visual distinction
3. **Multi-day assignments** - Each day is a separate block, no "spanning" view
4. **Multiple assignments per person per day** - e.g., Kole has morning + afternoon
5. **No aggregate "who's where" summary** - Have to read each row

---

## The Real Problem

**Boss needs to answer:** "On Thursday, who's at which jobsite and for how long?"

**Current process:** Scan each row, read each block, mentally aggregate.

**Ideal:** Quick visual or summary showing:
- By Site: Who's there, what hours
- By Person: Where they'll be, how long
- Availability gaps at a glance

---

## MVP Implication

The boss doesn't need a full project management system.

He needs a **scheduling dashboard** that answers:
1. "Where is everyone today?"
2. "Who's available on [date]?"
3. "How long has [person] been assigned to [project]?"

This could be:
- A simple read-only view pulling from Connecteam API
- Or if we're replacing Connecteam, a cleaner scheduling UI

**Question for Jason:** Does this need to REPLACE Connecteam, or AUGMENT it with better visualization?
