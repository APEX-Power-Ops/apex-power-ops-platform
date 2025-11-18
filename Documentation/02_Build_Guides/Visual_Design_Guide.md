# RESA Power Field Tracker - Visual Design Guide

## Brand Colors

```
Primary Purple:    RGBA(116, 39, 116, 1)    #742774
Action Blue:       RGBA(0, 120, 212, 1)     #0078D4
Success Green:     RGBA(0, 176, 80, 1)      #00B050
Warning Yellow:    RGBA(255, 192, 0, 1)     #FFC000
Danger Red:        RGBA(192, 0, 0, 1)       #C00000
Gray Dark:         RGBA(60, 60, 60, 1)      #3C3C3C
Gray Medium:       RGBA(150, 150, 150, 1)   #969696
Gray Light:        RGBA(240, 240, 240, 1)   #F0F0F0
White:             RGBA(255, 255, 255, 1)   #FFFFFF
Black:             RGBA(0, 0, 0, 1)         #000000
```

## Typography Scale

```
Hero:              36px - Bold
Title:             24px - Bold
Heading:           18px - Semibold
Subheading:        16px - Semibold
Body:              14px - Regular
Caption:           12px - Regular
Small:             11px - Regular
```

## Spacing System (8px base)

```
XS:  4px   (0.5 units)
S:   8px   (1 unit)
M:   16px  (2 units)
L:   24px  (3 units)
XL:  32px  (4 units)
XXL: 48px  (6 units)
```

## Component Sizes

### Buttons
```
Large:    Width: Full-width   Height: 60px   BorderRadius: 8px
Medium:   Width: 150-200px    Height: 50px   BorderRadius: 8px
Small:    Width: 100-120px    Height: 40px   BorderRadius: 6px
Icon:     Width: 44px         Height: 44px   BorderRadius: 22px (circle)
```

### Touch Targets (Mobile)
```
Minimum: 44x44px (iOS), 48x48px (Android)
Recommended: 48x48px for all interactive elements
Spacing between: Minimum 8px
```

### Cards
```
Padding:         16px
Border Radius:   8px
Border:          1px solid RGBA(220, 220, 220, 1)
Shadow:          0px 2px 4px RGBA(0, 0, 0, 0.1)
Margin:          8px (between cards)
```

### Forms
```
Input Height:    44px
Label Height:    20px
Spacing:         12px (label to input), 20px (between fields)
Border Radius:   4px
Border:          1px solid RGBA(200, 200, 200, 1)
Focus Border:    2px solid RGBA(0, 120, 212, 1)
```

---

## Screen Mockups

### Home Screen Layout

```
┌─────────────────────────────────────┐
│  RESA Power                     👤  │  ← Header (100px)
│  Field Tracker                      │     Purple background
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│        12           5               │  ← Stats Cards
│   My Open Tasks  Due Today          │     (120px height)
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  📋 View My Tasks                   │  ← Quick Actions
├─────────────────────────────────────┤     (60px each)
│  ⏱️  Log Time                        │     +15px spacing
├─────────────────────────────────────┤
│  🔍 Search Projects                 │
└─────────────────────────────────────┘

  Recent Activity                       ← Section Header
┌─────────────────────────────────────┐
│ • Test breaker - Scope 1        ● │  ← Gallery Items
│   Project Alpha                     │     (80px each)
├─────────────────────────────────────┤
│ • Install sensor - Scope 2      ● │
│   Project Beta                      │
└─────────────────────────────────────┘
```

### Task List Screen Layout

```
┌─────────────────────────────────────┐
│ ← My Tasks                      ⋮   │  ← Header
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ All | Not Started | In Progress | ✓ │  ← Filter Bar (50px)
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ 🔍 Search tasks...                  │  ← Search (44px)
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ │ Install Breaker Switch         ● │  ← Task Card
│ │ Equipment: 1200A Breaker          │     (100px)
│ │ Due: Nov 10, 2025    12.5 hrs     │
├─────────────────────────────────────┤
│ │ Visual Inspection              ⚠ │  ← Priority bar
│ │ Equipment: Motor Control          │     on left (5px)
│ │ Due: Nov 08, 2025    3.0 hrs      │
└─────────────────────────────────────┘
```

### Task Detail Screen Layout

```
┌─────────────────────────────────────┐
│ ← Task Details                  ⋮   │  ← Header
└─────────────────────────────────────┘
┌─────────────────────────────────────┐ ← Scrollable
│                                     │    Content Area
│  Task Information                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Task: Install Breaker Switch       │
│  Project: Alpha Upgrade             │
│  Scope: Scope 1                     │
│  Apparatus: 1200A Breaker           │
│                                     │
│  Status                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  [In Progress        ▼]             │
│                                     │
│  Completion: 65%                    │
│  ━━━━━━●━━━━━━━━━━━━━━━━━━━━━    │
│                                     │
│  Hours                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Quoted: 15.0 hrs                   │
│  Actual: 9.5 hrs                    │
│  Remaining: 5.5 hrs                 │
│                                     │
│  Notes                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  [                              ]   │
│  [  Text area for notes...      ]   │
│  [                              ]   │
│                                     │
│  📷 Datasheet Photo                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  [      Add Picture         ]       │
│                                     │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  💾 Save Changes  │  ⏱️ Log Time    │  ← Action Bar
└─────────────────────────────────────┘    (80px)
```

### Time Entry Screen Layout

```
┌─────────────────────────────────────┐
│ ← Log Time                          │  ← Header
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Task                               │
│  [Select task...            ▼]     │
│                                     │
│  Date                               │
│  [11/07/2025            📅]         │
│                                     │
│  Hours                              │
│  [8.0                          ]    │
│                                     │
│  Labor Type                         │
│  [Base Rate             ▼]         │
│                                     │
│  Notes                              │
│  [                              ]   │
│  [  Optional notes...           ]   │
│  [                              ]   │
│                                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│       ✓ Submit Time Entry           │  ← Submit Button
└─────────────────────────────────────┘    (60px)
```

---

## Status Indicators

### Color Coding

```
Completed:         Green circle    ●  RGBA(0, 176, 80, 1)
In Progress:       Yellow clock    🕐  RGBA(255, 192, 0, 1)
Not Started:       Gray circle     ⚪  RGBA(200, 200, 200, 1)
Overdue:           Red warning     ⚠   RGBA(192, 0, 0, 1)
```

### Priority Indicators

```
High:              Red bar         │  RGBA(192, 0, 0, 1)
Medium:            Yellow bar      │  RGBA(255, 192, 0, 1)
Low:               Green bar       │  RGBA(0, 176, 80, 1)
None:              Gray bar        │  RGBA(200, 200, 200, 1)
```

---

## Icons & Emojis

### Navigation Icons
```
Back:              ← (Back arrow)
Home:              🏠 or ⌂
Menu:              ☰ (hamburger)
Close:             ✕
More:              ⋮ (vertical dots)
```

### Action Icons
```
Add:               ➕ or +
Edit:              ✏️ or 🖊
Delete:            🗑️ or ✕
Save:              💾 or ✓
Search:            🔍
Filter:            🔽
Camera:            📷
Clock/Time:        ⏱️
Calendar:          📅
```

### Status Icons
```
Complete:          ✓ or ✅
Warning:           ⚠️
Error:             ❌
Info:              ℹ️
```

### Feature Icons
```
Tasks:             📋
Projects:          📁
Time:              ⏱️
Profile:           👤
Settings:          ⚙️
Notifications:     🔔
```

---

## Animation Guidelines

### Transitions
```
Screen Navigation: Fade (300ms) or Cover (400ms)
Card Expand:       SlideIn (250ms)
Button Press:      Scale(0.95) on TouchStart
Loading:           Fade + Spin (continuous)
```

### Hover/Press States (if desktop)
```
Button Hover:      Darken(Fill, 10%)
Button Press:      Darken(Fill, 20%)
Card Hover:        Shadow(0 4px 8px rgba(0,0,0,0.15))
```

---

## Responsive Breakpoints

```
Phone Portrait:    375px - 428px width
Phone Landscape:   667px - 926px width  (not recommended)
Tablet Portrait:   768px - 834px width
Tablet Landscape:  1024px - 1366px width
```

### Layout Adjustments
```
< 400px:   Single column, full-width buttons
400-600px: Single column, some side-by-side buttons
> 600px:   Consider two-column layout for tablets
```

---

## Accessibility Guidelines

### Color Contrast
```
AA Standard:  4.5:1 for normal text
              3:1 for large text (18pt+)
AAA Standard: 7:1 for normal text
              4.5:1 for large text
```

### Touch Targets
```
Minimum:      44x44px
Recommended:  48x48px
Spacing:      8px minimum between targets
```

### Text Sizing
```
Body Text:    14px minimum (16px recommended)
Buttons:      16px minimum
Headers:      18px minimum
```

### Focus States
```
Visible:      2px solid border
Color:        Action Blue #0078D4
Offset:       2px from element
```

---

## Component Library (Copy/Paste Ready)

### Standard Button
```
Fill: RGBA(0, 120, 212, 1)
Color: White
BorderRadius: 8
Height: 50
FontSize: 16
PressedFill: RGBA(0, 90, 158, 1)
HoverFill: RGBA(0, 100, 180, 1)
```

### Primary Button (CTA)
```
Fill: RGBA(116, 39, 116, 1)
Color: White
BorderRadius: 8
Height: 60
FontSize: 18
FontWeight: Semibold
```

### Secondary Button
```
Fill: RGBA(240, 240, 240, 1)
Color: RGBA(60, 60, 60, 1)
BorderRadius: 8
Height: 50
FontSize: 16
BorderColor: RGBA(200, 200, 200, 1)
BorderThickness: 1
```

### Danger Button
```
Fill: RGBA(192, 0, 0, 1)
Color: White
BorderRadius: 8
Height: 50
FontSize: 16
```

### Text Input
```
Fill: White
BorderColor: RGBA(200, 200, 200, 1)
BorderThickness: 1
BorderRadius: 4
Height: 44
PaddingLeft: 12
PaddingRight: 12
FontSize: 14
FocusedBorderColor: RGBA(0, 120, 212, 1)
FocusedBorderThickness: 2
```

### Card Container
```
Fill: White
BorderColor: RGBA(220, 220, 220, 1)
BorderThickness: 1
BorderRadius: 8
PaddingTop: 16
PaddingBottom: 16
PaddingLeft: 16
PaddingRight: 16
```

### Section Header
```
Size: 18
FontWeight: Semibold
Color: RGBA(60, 60, 60, 1)
PaddingBottom: 8
```

### Label (Form)
```
Size: 12
Color: RGBA(100, 100, 100, 1)
PaddingBottom: 4
```

### Value Text
```
Size: 14
Color: RGBA(0, 0, 0, 1)
```

---

## Dark Mode (Future Enhancement)

### Colors
```
Background:        RGBA(18, 18, 18, 1)
Surface:           RGBA(30, 30, 30, 1)
Primary:           RGBA(187, 134, 252, 1)  // Lighter purple
Text Primary:      RGBA(255, 255, 255, 0.87)
Text Secondary:    RGBA(255, 255, 255, 0.6)
```

---

## Loading States

### Spinner
```
Icon: LoadingDots
Color: RGBA(116, 39, 116, 1)
Size: 40x40
Position: Centered
Background: RGBA(255, 255, 255, 0.9)
```

### Skeleton Screen
```
Use for gallery items while loading:
- Gray rectangles (RGBA(240, 240, 240, 1))
- Animate with shimmer effect
- Match actual content dimensions
```

### Progress Bar
```
Height: 4px
Fill: RGBA(116, 39, 116, 1)
Background: RGBA(240, 240, 240, 1)
BorderRadius: 2px
```

---

## Empty States

### No Tasks
```
Icon: 📋 (large, 48px)
Text: "No tasks found"
Subtext: "Try adjusting your filters"
Action: "View All Tasks" button
```

### No Search Results
```
Icon: 🔍 (large, 48px)
Text: "No results found"
Subtext: "Try different keywords"
Action: "Clear Search" button
```

### Offline
```
Icon: ⚠️ (large, 48px)
Text: "You're offline"
Subtext: "Some features are limited"
Action: "Retry Connection" button
```

---

## Sample Color Formulas (Copy/Paste)

### Status-Based Color
```javascript
Switch(
    ThisItem.Status.Value,
    "Completed", RGBA(0, 176, 80, 1),
    "In Progress", RGBA(255, 192, 0, 1),
    "Overdue", RGBA(192, 0, 0, 1),
    RGBA(200, 200, 200, 1)
)
```

### Priority-Based Color
```javascript
Switch(
    ThisItem.Priority.Value,
    "High", RGBA(192, 0, 0, 1),
    "Medium", RGBA(255, 192, 0, 1),
    "Low", RGBA(0, 176, 80, 1),
    RGBA(200, 200, 200, 1)
)
```

### Overdue Check Color
```javascript
If(
    DateValue(Text(ThisItem.'Due Date')) < Today(),
    RGBA(192, 0, 0, 1),  // Red
    RGBA(0, 0, 0, 0.6)   // Gray
)
```

### Button Hover Effect
```javascript
If(
    Self.Pressed,
    RGBA(0, 90, 158, 1),      // Darker blue
    If(
        Self.Hover,
        RGBA(0, 100, 180, 1),  // Medium blue
        RGBA(0, 120, 212, 1)   // Normal blue
    )
)
```

---

## Best Practices Checklist

### Before Publish
- [ ] All text is at least 14px
- [ ] All buttons are at least 48px tall
- [ ] Color contrast meets AA standards
- [ ] No visual-only information (use icons + text)
- [ ] Tested on actual mobile device
- [ ] All screens have back navigation
- [ ] Loading states implemented
- [ ] Empty states designed
- [ ] Error messages are helpful
- [ ] Success confirmations shown

### Performance
- [ ] Galleries limited to <100 items
- [ ] Images optimized (<200KB each)
- [ ] No nested galleries
- [ ] Collections used for reference data
- [ ] Delegation warnings resolved

### User Experience
- [ ] Consistent spacing throughout
- [ ] Visual hierarchy clear
- [ ] Actions clearly labeled
- [ ] Confirmation before destructive actions
- [ ] Helpful placeholder text
- [ ] Progress indicators for long operations

---

## Quick Copy: Full Color Palette

```javascript
// Add to App.OnStart for easy reference

Set(clrPrimary, RGBA(116, 39, 116, 1));
Set(clrAction, RGBA(0, 120, 212, 1));
Set(clrSuccess, RGBA(0, 176, 80, 1));
Set(clrWarning, RGBA(255, 192, 0, 1));
Set(clrDanger, RGBA(192, 0, 0, 1));
Set(clrGrayDark, RGBA(60, 60, 60, 1));
Set(clrGrayMed, RGBA(150, 150, 150, 1));
Set(clrGrayLight, RGBA(240, 240, 240, 1));
Set(clrWhite, RGBA(255, 255, 255, 1));
Set(clrBlack, RGBA(0, 0, 0, 1));
```

Then use: `Fill: clrPrimary` instead of `Fill: RGBA(116, 39, 116, 1)`

---

*Design Guide Version: 1.0*
*Created: November 7, 2025*
*For: RESA Power Field Tracker*
