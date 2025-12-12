# Implementation Roadmap

**Version:** 1.0  
**Last Updated:** November 17, 2025  
**Purpose:** Planning document for phased rollout across business units

---

## Overview

This roadmap outlines the plan for expanding the project tracker from initial pilot to broader deployment. Built incrementally based on user feedback and operational needs.

---

## Current State (November 2025)

**What's Complete:**
- ✅ 8 custom Dataverse tables with revenue architecture
- ✅ 137 custom fields with calculated formulas
- ✅ Core functionality built (project tracking, labor costs, revenue calculation)
- ✅ Solution v1.3.0.1 ready for pilot deployment
- ✅ Documentation complete (technical specs, user guides, training materials)

**What's Not Built Yet:**
- ❌ Power Automate revenue recognition flow (needed next)
- ❌ Power BI dashboards (planned after pilot)
- ❌ Mobile field app (future phase)
- ❌ Cross-location reporting (future phase)

---

## Phase 1: Pilot Deployment (Q1 2026)

### **Goal:** 
Validate the system works with real users and real projects before expanding.

### **Scope:**
- Deploy to 4 Phoenix-region business units
- 2 pilot Project Managers run actual projects
- Test for 30-60 days with real work

### **What Gets Built:**
1. **Revenue Recognition Flow (December 2025)**
   - Power Automate workflow
   - Automatic calculation when apparatus marked complete
   - Status changes (Pending → Recognized)
   - Time estimate: 30-45 minutes

2. **Work Assignment Features (January 2026)**
   - Apparatus.Assigned_To field
   - "My Work" view for field techs
   - Assignment date tracking
   - Time estimate: 30-45 minutes

3. **Date Tracking (January 2026)**
   - Start dates, target dates, actual completion
   - Enable scheduling and utilization tracking
   - Time estimate: 20-30 minutes

4. **Training Materials (January-February 2026)**
   - Quick-start guides for each role (2-page PDFs)
   - Video tutorials (5-10 minutes each)
   - Hands-on workshop for pilot PMs

5. **Basic Power BI Dashboard (February-March 2026)**
   - Project Manager view (my projects, hours, revenue)
   - Financial view (revenue recognized, pending, billed)
   - Simple visualizations, no advanced analytics yet

### **Success Criteria:**
- System stays up and running (no major outages)
- Pilot PMs use it consistently (90%+ adoption)
- Feedback is positive (4.0+ satisfaction rating)
- Revenue calculations match Excel verification
- Month-end close time improves

### **Timeline:**
- **December 2025:** Build remaining flows and fields
- **January 2026:** Deploy to pilot, start UAT
- **February 2026:** Training materials and dashboards
- **March 2026:** Gather feedback, document lessons learned

---

## Phase 2: Regional Expansion (Q2-Q3 2026)

### **Goal:**
Expand to additional business units based on pilot results.

### **Scope:**
- Deploy to 10+ additional business units (if pilot successful)
- Add locations in California, Colorado, Nevada
- Build additional features based on pilot feedback

### **What Gets Built:**
1. **Enhanced Dashboards**
   - Location Manager view (multi-project oversight)
   - Executive summary view (portfolio-level reporting)
   - Drill-down capabilities

2. **Mobile App (Initial Version)**
   - Canvas app for field technicians
   - Simple apparatus completion on phone/tablet
   - Basic offline capability

3. **Additional Training**
   - Role-based workshops for each location
   - Train-the-trainer program for Location Managers
   - Help desk infrastructure

4. **BusinessUnit Enhancements**
   - Rollup fields (total projects, revenue, hours)
   - Location scorecards
   - Cross-location comparison views

### **Timeline:**
- **April-June 2026:** Incremental deployment (2-3 locations per month)
- **July-September 2026:** Build mobile app and enhanced dashboards
- **October 2026:** Assess readiness for broader rollout

---

## Phase 3: Broader Deployment (Q4 2026 - Q1 2027)

### **Goal:**
Deploy to remaining business units if value is proven.

### **Scope:**
- Expand to additional regions based on demand
- Continue iteration and refinement
- Build advanced features as needed

### **Possible Enhancements:**
- Advanced analytics (trend analysis, forecasting)
- Integration with accounting system
- Customer portal (if needed)
- Automated reporting and notifications
- Enhanced mobile app features

### **Approach:**
- Incremental rollout based on location readiness
- Continue gathering feedback and improving
- Build only what users actually need (avoid over-engineering)

---

## Resources & Support

### **Development Time Estimate:**
- **Phase 1 (Pilot):** 10-15 hours remaining work
- **Phase 2 (Expansion):** 40-60 hours (dashboards, mobile app)
- **Phase 3 (Broader):** TBD based on feedback

### **Training Time Per Location:**
- Field Technicians: 15 minutes each
- Job Leads: 30 minutes each
- Project Managers: 90 minutes each
- Location Managers: 60 minutes each

### **Support Model:**
- **Tier 1:** Documentation and video tutorials (self-service)
- **Tier 2:** Help desk for common questions (<24 hour response)
- **Tier 3:** Technical support for system issues (<4 hour critical)

---

## Risk Management

### **Potential Issues:**

**1. User Resistance**
- Risk: "We like Excel, why change?"
- Mitigation: Show immediate value, involve users early, make training simple

**2. Data Quality**
- Risk: Garbage in, garbage out
- Mitigation: Validation rules, duplicate prevention, mandatory fields

**3. System Performance**
- Risk: Slow dashboards or app response times
- Mitigation: Load testing, optimize queries, cache frequently-used data

**4. Integration Challenges**
- Risk: Doesn't work well with other systems
- Mitigation: Start standalone, add integrations incrementally

**5. Scope Creep**
- Risk: Too many feature requests, never finish
- Mitigation: Prioritize ruthlessly, focus on core value first

---

## Decision Points

### **After Pilot (March 2026):**
**Decision:** Continue expansion or pause?
- If pilot successful → Proceed to Phase 2
- If major issues → Fix before expanding
- If not valuable → Reconsider approach

### **After Regional Expansion (September 2026):**
**Decision:** Deploy broadly or keep regional?
- If working well → Expand to remaining locations
- If needs work → Improve before continuing
- If not needed elsewhere → Keep as regional tool

### **Ongoing:**
**Decision:** Which features to build next?
- Based on user requests and operational needs
- Focus on high-value, low-effort improvements
- Avoid building features that won't be used

---

## Success Metrics

### **Adoption Metrics:**
- % of users actively using the system weekly
- % of projects tracked in system vs. Excel
- Time to onboard new users

### **Operational Metrics:**
- Month-end close time (hours)
- Data entry errors (count)
- Duplicate apparatus entries (count)
- Report generation time (hours → minutes)

### **User Satisfaction:**
- User satisfaction survey (1-5 scale)
- Feature request volume
- Support ticket volume and resolution time

### **Business Value:**
- Time saved per month (hours)
- Improved visibility (qualitative)
- Easier consolidation across locations (qualitative)

---

## Next Actions

### **Immediate (December 2025):**
1. ✅ Complete documentation (done)
2. 🚧 Build Revenue Recognition Flow (Phase 5E)
3. 🚧 Test end-to-end with sample data
4. 🚧 Create quick-start guide for pilot PMs

### **Short-Term (January 2026):**
1. Deploy to pilot business units
2. Train 2 pilot Project Managers
3. Monitor usage and gather feedback
4. Document issues and lessons learned

### **Medium-Term (February-March 2026):**
1. Build basic Power BI dashboards
2. Create video tutorials
3. Assess pilot results
4. Plan Phase 2 expansion (if warranted)

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| November 17, 2025 | 1.0 | Initial roadmap created |

---

*This is a living document that will be updated based on pilot results and user feedback.*
