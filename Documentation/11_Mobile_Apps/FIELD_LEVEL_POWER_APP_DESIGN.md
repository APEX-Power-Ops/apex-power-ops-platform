# Field-Level Power App Design

**Version:** 1.0  
**Status:** 🚧 IN DEVELOPMENT  
**Last Updated:** November 17, 2025

---

## 🎯 Overview

Mobile-first canvas app designed for field technicians and job leads to update apparatus status, track hours, and capture completion data in real-time from job sites.

---

## 📱 App Design Philosophy

### **Core Principles:**
1. **Mobile-First:** Optimized for phones/tablets, works offline
2. **Minimal Clicks:** Complete common tasks in ≤3 taps
3. **Offline Capable:** Cache data, sync when connected
4. **Voice-Friendly:** Voice input for notes/comments
5. **Photo Capture:** Document equipment conditions

---

## 👥 Target Users

### **Primary User: Field Technician**
- **Use Case:** Update apparatus completion status from job site
- **Frequency:** 5-10 updates per day
- **Environment:** Industrial sites (limited connectivity, gloves, safety gear)
- **Pain Point:** Current process requires calling job lead or waiting until office

### **Secondary User: Job Lead**
- **Use Case:** Review team progress, assign work, approve completions
- **Frequency:** 15-20 interactions per day
- **Environment:** Mix of field and office
- **Pain Point:** No real-time visibility into team status

---

## 📱 App Screens & Workflows

### **1. Home Screen (Dashboard)**
**Layout:** Card-based, scrollable  
**Status:** 📅 Planned Q2 2026

**Widgets:**
- 🎯 "My Work Today" (assigned apparatus)
- ⏱️ Hours logged today (auto-calculated)
- 🔴 Overdue items (alert count)
- 📋 Quick actions (New Entry, Scan Barcode)

**Gestures:**
- Swipe left on apparatus → Mark complete
- Swipe right → Add note
- Long press → View details

---

### **2. Apparatus Entry Screen**
**Layout:** Form-based, vertical scroll  
**Status:** 🚧 High Priority

**Fields (Minimal Input Design):**
1. **Apparatus Number** (barcode scan or voice input)
2. **Completion Status** (large toggle buttons: Not Started / In Progress / Complete)
3. **Hours Worked** (numeric keypad, quick presets: 2hr, 4hr, 8hr)
4. **Delays** (optional, numeric keypad)
5. **Notes** (voice input or text)
6. **Photos** (optional, camera integration)

**Smart Features:**
- Auto-populate from barcode scan
- Voice-to-text for notes
- Offline mode (queue for sync)
- GPS tagging (optional location stamp)

**Validation:**
- Required fields highlighted
- "Are you sure?" prompt for completion
- Hours cannot exceed 24 in single day

---

### **3. Work Assignment View (Job Lead Only)**
**Layout:** List-based, filterable  
**Status:** 📅 Planned Q2 2026

**Features:**
- Drag-and-drop work assignment
- Filter by technician, project, status
- Bulk actions (assign 5 apparatus to tech)
- Real-time status updates (color-coded)

**Visualizations:**
- 🟢 Complete
- 🟡 In Progress
- ⚪ Not Started
- 🔴 Overdue

---

### **4. Daily Summary Screen**
**Layout:** Report-based  
**Status:** 📅 Planned Q2 2026

**End-of-Day Summary:**
- Total hours logged
- Apparatus completed count
- Photos captured
- Outstanding work (carry to tomorrow)

**Actions:**
- "Submit Timesheet" (one-tap)
- "Add Missing Entry"
- "Review & Sign"

---

## 🎨 UI/UX Design

### **Color Palette:**
- **Primary:** RESA Blue (#003366)
- **Success:** Green (#28a745)
- **Warning:** Yellow (#ffc107)
- **Danger:** Red (#dc3545)
- **Neutral:** Gray (#6c757d)

### **Typography:**
- **Large Buttons:** 24pt (glove-friendly)
- **Body Text:** 16pt (readable in sunlight)
- **Labels:** 12pt (clear but compact)

### **Accessibility:**
- High contrast mode for outdoor visibility
- Voice input for hands-free operation
- Large touch targets (48x48 pixels minimum)
- Screen reader support

---

## 🔌 Technical Architecture

### **Power Apps Canvas App**
- **Platform:** Power Apps (Canvas)
- **Data Source:** Dataverse (Apparatus, Tasks, Projects)
- **Authentication:** Azure AD (SSO)
- **Offline Mode:** Power Apps offline capability

### **Data Flow:**
```
Field Tech Device
    ↓ (Online/Offline)
Power Apps Canvas App
    ↓ (Dataverse Connector)
Dataverse (Apparatus table)
    ↓ (Trigger)
Power Automate (Revenue Recognition Flow)
    ↓ (Create)
ApparatusRevenue (Financial tracking)
```

### **Offline Strategy:**
- Cache current user's assigned work (last 7 days)
- Queue updates locally when offline
- Auto-sync when connection restored
- Conflict resolution (last write wins)

---

## 📊 Integration Points

### **Barcode Scanning:**
- Camera-based barcode reader (built-in)
- Supports Code 39, Code 128, QR codes
- Auto-populate apparatus designation

### **GPS Location:**
- Optional location tagging for completion
- Validates tech is on-site
- Timestamps all entries

### **Photo Capture:**
- Integrated camera access
- Compress images (max 2MB per photo)
- Store in SharePoint (linked to apparatus)
- Max 5 photos per apparatus

### **Voice Input:**
- Microsoft Speech Service integration
- Convert speech to text for notes
- Languages: English (primary), Spanish (future)

---

## 🔐 Security & Permissions

### **Field Technician Role:**
- ✅ View assigned apparatus
- ✅ Update completion status
- ✅ Add hours and notes
- ✅ Capture photos
- ❌ Cannot delete records
- ❌ Cannot see other techs' work
- ❌ Cannot edit financial data

### **Job Lead Role:**
- ✅ All Field Tech permissions
- ✅ View team's work
- ✅ Assign work to techs
- ✅ Approve completions
- ✅ Override completion status

---

## 📱 Performance Optimization

### **Load Time Targets:**
- App startup: <3 seconds
- Screen transitions: <1 second
- Data sync: <5 seconds (typical)
- Offline queue processing: Background

### **Data Optimization:**
- Delegate filters to Dataverse (no client-side filtering)
- Limit records loaded (last 30 days only)
- Lazy load images (on-demand)
- Cache user preferences locally

---

## 🧪 Testing Plan

### **Device Testing:**
- iPhone (iOS 15+)
- Android (Samsung Galaxy, Google Pixel)
- iPad (field supervisor use)
- Rugged tablets (Panasonic Toughbook)

### **Connectivity Testing:**
- Full connectivity (4G/5G/WiFi)
- Limited connectivity (2G/3G)
- Offline mode (no connectivity)
- Intermittent connection (sync behavior)

### **Field Testing:**
- 2-week pilot with 5 techs (Phoenix location)
- Real job sites (industrial environments)
- Feedback collection via in-app survey

**Status:** 📅 Planned Q2 2026

---

## 🚀 Development Roadmap

### **Phase 1: MVP (Q2 2026)**
- ✅ Core apparatus update functionality
- ✅ Hours entry
- ✅ Completion status toggle
- ✅ Basic offline mode
- 🚧 Barcode scanning
- 🚧 Photo capture

### **Phase 2: Enhanced (Q3 2026)**
- 📅 Voice input for notes
- 📅 GPS location tagging
- 📅 Work assignment view (Job Lead)
- 📅 Daily summary screen
- 📅 Push notifications

### **Phase 3: Advanced (Q4 2026)**
- 📅 Predictive text (common notes)
- 📅 Batch entry mode (multiple apparatus)
- 📅 Signature capture (customer sign-off)
- 📅 Integration with time tracking systems

---

## 📚 Related Model-Driven App

### **Desktop/Office Experience:**
Project Managers and back-office staff use **Model-Driven App** for:
- Full project management
- Financial tracking
- Reporting and analytics
- Administrative functions

**Integration:**
Field app data flows seamlessly into model-driven app for PM visibility.

---

## 💡 User Experience Scenarios

### **Scenario 1: Complete Apparatus in 3 Taps**
1. **Tap 1:** Open "My Work Today" from home screen
2. **Tap 2:** Select apparatus from list
3. **Tap 3:** Tap "Mark Complete" button
   - Auto-fills hours from timer
   - Triggers revenue recognition flow
   - Confirms with green checkmark

**Total time: <30 seconds**

---

### **Scenario 2: Barcode Scan Entry**
1. Tap "Scan Barcode" from home screen
2. Point camera at apparatus tag
3. Auto-populates apparatus details
4. Tap completion status
5. Save

**Total time: <45 seconds**

---

### **Scenario 3: Offline Work Logging**
1. Tech arrives at remote site (no signal)
2. App shows cached assigned work
3. Updates 8 apparatus throughout day
4. Returns to office (WiFi connects)
5. App auto-syncs all updates
6. Revenue flows trigger automatically

**User experience: Seamless, no data loss**

---

## 📊 Success Metrics

### **Adoption Targets:**
- Field Tech usage: 90%+ (within 60 days)
- Daily active users: 80%+
- Offline mode usage: 40%+ (indicates real field use)

### **Performance Metrics:**
- Average time to complete entry: <60 seconds
- User satisfaction: 4.0+ out of 5.0
- Support tickets: <2 per 100 users/month

### **Business Impact:**
- Real-time data visibility (vs. 1-2 day delay with manual entry)
- Reduced administrative burden (no PM data entry)
- Improved revenue recognition accuracy (same-day vs. monthly)

---

## 📁 Related Documentation

- `Documentation/01_Architecture/USER_EXPERIENCE_SYSTEM_ARCHITECTURE.md` - Field Tech persona
- `Documentation/09_Training_Materials/TRAINING_PROGRAM_OVERVIEW.md` - Field Tech training plan
- `Documentation/10_Analytics_Reporting/POWER_BI_DASHBOARD_STRATEGY.md` - Integration with reporting

---

**Document Owner:** Jason Swenson  
**Status:** Design phase, development starting Q2 2026  
**Priority:** HIGH - Critical for field adoption and data accuracy
