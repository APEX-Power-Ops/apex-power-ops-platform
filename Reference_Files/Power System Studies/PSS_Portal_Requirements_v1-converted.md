Power System Studies

**Project Management Portal**

Requirements Document

**RESA Power**

Version 1.0 - Draft

December 2025

# 1. Executive Summary

RESA Power provides Arc Flash and Power System Studies (PSS) to clients by coordinating between the client and contracted engineering firms. The current process relies entirely on email communication, manual tracking via Excel spreadsheets, and institutional knowledge held by individual employees.

This document defines requirements for a multi-party project portal that will automate workflow management, provide visibility to all stakeholders, and eliminate the inefficiencies of the current email-based process.

## 1.1 Project Goals

1. Eliminate RESA as a manual relay point for routine communications
2. Provide real-time project visibility to clients, RESA staff, and engineers
3. Automate document requests, reminders, and status notifications
4. Standardize intake processes with checklists and templates
5. Enable seamless handoff between staff members without loss of project context
6. Reduce project cycle time and improve client satisfaction

# 2. Current State Analysis

## 2.1 Existing Process

Currently, RESA Power manages PSS projects using:

* Excel spreadsheet for basic project tracking (job number, client, dates, notes)
* Email chains for all communication between clients and engineers
* Dropbox for file sharing with engineering vendor (Shaw)
* Manual copy/paste of information requests and responses
* No standardized intake form or document checklist

## 2.2 Key Problems Identified

1. No document-level tracking: Tracker shows "Partial Data Sent" but doesn't specify what's missing
2. Communication history buried in email: Impossible to search or hand off to another employee
3. No standardized intake: Each project starts differently with no consistent checklist
4. No accountability mechanism: No automated reminders, aging reports, or bottleneck visibility
5. RESA staff as relay point: Every RFI from engineer requires manual forwarding to client
6. Knowledge silos: Project status exists only in one person's head and email inbox

# 3. User Roles and Permissions

The portal must support three distinct user types with different access levels and capabilities.

| **Role** | **Description** | **Key Permissions** |
| --- | --- | --- |
| Client | External customer who requests and receives studies. Primary contact at customer organization. | View own projects only; Upload documents; Respond to RFIs; Approve deliverables; Receive notifications |
| RESA Admin | Internal RESA Power staff who manage project coordination and oversight. | Full access to all projects; Create projects; Assign engineers; Override statuses; Access all reports; Manage users; Configure templates |
| Engineer | External engineering firm (e.g., Shaw) contracted to perform studies. | View assigned projects; Download client documents; Submit RFIs; Upload deliverables; Update study status |

## 3.1 Role-Specific Portal Views

### Client Portal View

* Dashboard showing their active projects and status
* Document upload area with checklist of required items
* RFI inbox to respond to engineer questions
* Deliverables area to review and approve final reports
* Communication log (read-only view of project correspondence)

### RESA Admin Portal View

* Master dashboard with all projects, filterable by status, client, engineer, age
* Project creation and configuration screens
* Document tracking matrix showing all items across all projects
* Aging and bottleneck reports
* Template and checklist management
* User management and access control

### Engineer Portal View

* Dashboard of assigned projects with status and target dates
* Document download area to retrieve client-submitted files
* RFI submission form to request additional information from client
* Deliverable upload area for draft and final reports
* Status update controls to mark study milestones complete

# 4. Project Lifecycle and Status Definitions

Each project moves through defined stages. Status changes trigger notifications and update dashboards automatically.

| **Stage** | **Status** | **Description** | **Trigger to Next Stage** |
| --- | --- | --- | --- |
| 1. Intake | New Request | Client has requested a study; project record created | RESA assigns engineer and sends document checklist |
| 2. Data Collection | Awaiting Documents | Checklist sent to client; waiting for required documents | All required documents received |
| 2. Data Collection | Partial Documents | Some documents received; others still outstanding | All required documents received |
| 3. Engineer Handoff | Ready for Engineer | All documents received; package ready for engineer | Engineer confirms receipt |
| 4. Study In Progress | In Progress | Engineer actively working on study | Engineer submits RFI or draft report |
| 4. Study In Progress | RFI Pending | Engineer has submitted RFI; awaiting client response | Client responds to all open RFIs |
| 5. Review | Draft Submitted | Engineer has uploaded draft report for review | Client approves or requests revisions |
| 5. Review | Revisions Requested | Client has requested changes to draft | Engineer submits revised report |
| 6. Final Delivery | Report Approved | Client has approved final report | Stickers/settings delivered (if applicable) |
| 6. Final Delivery | Stickers Pending | Report complete; stickers/settings to be applied | Field work completed |
| 7. Complete | Closed | All deliverables complete; project archived | N/A - Terminal state |

# 5. Document Requirements by Study Type

Each study type requires specific documents from the client. The portal should present a dynamic checklist based on the study type selected.

## 5.1 Power System Study (PSS) - Required Documents

* Single-line diagram (one-line)
* Equipment schedules (panel schedules, transformer data)
* Utility information (fault current data from utility provider)
* Main breaker information (manufacturer, catalog number, trip unit catalog number)
* Cable/conductor schedules (sizes, lengths, types)
* Motor schedules (HP, FLA, starting method)
* Generator data (if applicable)
* Existing protective device settings (if applicable)

## 5.2 Arc Flash Study - Additional Requirements

* All PSS requirements above, plus:
* Working distances for each piece of equipment
* Equipment enclosure types
* Existing arc flash labels (if any)

## 5.3 Document Status Tracking

Each document in the checklist should have an individual status:

| **Document Status** | **Description** | **Visual Indicator** |
| --- | --- | --- |
| Not Requested | Document not yet formally requested from client | Gray / Inactive |
| Requested | Request sent to client; awaiting upload | Yellow / Pending |
| Received | Client has uploaded the document | Green / Complete |
| Under Review | Engineer is reviewing for completeness | Blue / In Progress |
| Rejected | Document insufficient; new version needed | Red / Action Required |
| Accepted | Document approved for use in study | Green / Checkmark |
| N/A | Document not applicable to this project | Gray / Strikethrough |

# 6. Notification and Reminder Rules

Automated notifications are critical to reducing manual follow-up. The system should send emails and/or in-app notifications based on the following triggers.

## 6.1 Automatic Notifications

| **Trigger Event** | **Recipient(s)** | **Notification Content** |
| --- | --- | --- |
| New project created | Client, Engineer | Welcome message with login link and next steps |
| Document uploaded by client | RESA, Engineer | "[Client] uploaded [Document Name] for [Project]" |
| All documents received | Engineer, RESA | "Data collection complete for [Project] - Ready for study" |
| RFI submitted by engineer | Client, RESA | "[Engineer] has a question about [Project] - Response needed" |
| RFI responded by client | Engineer, RESA | "[Client] responded to your RFI for [Project]" |
| Draft report uploaded | Client, RESA | "Draft report ready for review on [Project]" |
| Report approved by client | Engineer, RESA | "[Client] approved the report for [Project]" |
| Status change (any) | All project parties | "[Project] status changed from [Old] to [New]" |

## 6.2 Automated Reminders

| **Condition** | **Timing** | **Recipient** | **Message** |
| --- | --- | --- | --- |
| Documents requested but not received | 3, 7, 14 days | Client | Reminder: Documents still needed for [Project] |
| RFI pending response | 2, 5 days | Client | Reminder: Engineer awaiting your response |
| Draft report pending approval | 3, 7 days | Client | Reminder: Please review draft report |
| Project idle (no activity) | 14, 30 days | RESA | Alert: [Project] has had no activity |
| Target date approaching | 7, 3, 1 days before | Engineer, RESA | Reminder: Report due date approaching |

# 7. Dashboard and Reporting Requirements

## 7.1 RESA Admin Dashboard

The primary dashboard for RESA staff should provide at-a-glance visibility into all projects:

* Project count by status (cards or pipeline view)
* Aging report: Projects stuck in a stage beyond threshold (e.g., >7 days awaiting documents)
* Upcoming deadlines: Reports due in next 7/14/30 days
* Action items: Items requiring RESA intervention
* Filterable project list: By client, engineer, status, date range

## 7.2 Client Dashboard

* My Projects: List of active projects with current status
* Action Required: Documents to upload, RFIs to answer, reports to approve
* Project Timeline: Visual progress indicator for each project
* Document Status: Checklist showing submitted vs. outstanding items

## 7.3 Engineer Dashboard

* Assigned Projects: List with target dates and current status
* Ready for Work: Projects with all documents received
* Pending RFIs: RFIs awaiting client response
* Upcoming Deadlines: Reports due soon

## 7.4 Reports

The following reports should be available to RESA Admin users:

* Project Status Report: All projects with current stage, age, and next action
* Client Activity Report: Projects by client with status and revenue
* Engineer Performance Report: Projects by engineer with cycle times
* Bottleneck Report: Projects stuck at each stage beyond threshold
* Revenue Pipeline: Projects by stage with PO amounts

# 8. Templates and Standardized Forms

The portal should include templates for common communications and forms for structured data capture.

## 8.1 Required Templates

| **Template Name** | **Purpose** |
| --- | --- |
| Project Kickoff Email | Sent to client when project is created; includes login instructions and document checklist |
| Document Request | Formal request for specific missing documents with descriptions of what's needed |
| Document Reminder | Follow-up reminder for outstanding documents (3/7/14 day versions) |
| RFI Form | Structured form for engineers to request additional information |
| RFI Response Request | Notification to client that an RFI needs their response |
| Draft Report Cover Letter | Accompanies draft report delivery with review instructions |
| Final Report Cover Letter | Accompanies approved final report with next steps |
| Project Completion Summary | Summary sent at project close with all deliverables and documentation |

## 8.2 Required Forms

* Project Intake Form: Client name, project name, site address, study type, scope, timeline preferences
* Submittal Cover Sheet: Generated document listing all files submitted with the package
* RFI Form: Reference number, subject, detailed question, related documents, urgency level
* Report Approval Form: Client sign-off with optional comments

# 9. Technical Requirements

## 9.1 Core Functional Requirements

* Multi-tenant portal with role-based access control
* Secure file upload/download with virus scanning
* Email integration for notifications (SMTP or email service)
* Audit trail for all actions (who did what, when)
* Search functionality across projects, documents, and communications
* Mobile-responsive design for field access

## 9.2 Integration Requirements

* Potential integration with RESA CRM system (for job numbers, client data)
* Potential integration with accounting system (for PO and invoicing)
* Email system integration (Microsoft 365 preferred)

## 9.3 Non-Functional Requirements

* 99.9% uptime availability
* Data backup and disaster recovery
* SOC 2 compliance or equivalent security standards
* User-friendly interface requiring minimal training

# 10. Recommended Implementation Approach

## 10.1 Phased Rollout

1. Phase 1 - Foundation (4-6 weeks): Project database, basic portal for all three roles, document upload/download, status tracking
2. Phase 2 - Automation (2-4 weeks): Email notifications, automated reminders, status change triggers
3. Phase 3 - Enhancement (2-4 weeks): Dashboards, reports, templates, RFI workflow
4. Phase 4 - Integration (as needed): CRM integration, accounting integration, advanced analytics

## 10.2 Platform Options to Evaluate

Based on the requirements in this document, the following platforms should be evaluated:

* Airtable + Softr: Flexible database with portal front-end; good for rapid prototyping
* Moxo: Purpose-built for multi-party client collaboration; strong automation
* Copilot (Portal): Modern client portal with built-in file sharing and messaging
* Smartsheet + WorkApps: Spreadsheet-like familiarity with portal capabilities
* Microsoft Power Platform: SharePoint + Power Apps + Power Automate (if already licensed)

# 11. Next Steps

1. Review and refine this requirements document with stakeholders
2. Identify 2-3 platforms for detailed evaluation/demo
3. Conduct vendor demos with this document as the evaluation criteria
4. Select platform and develop detailed implementation plan
5. Pilot with 2-3 active projects before full rollout

# Appendix A: Data Migration Considerations

Existing projects in the Excel tracker should be migrated to the new system. Key fields to migrate:

* RESA Job Number (unique identifier)
* Client Name and Project Name
* Service Type (PSS, Arc Flash, etc.)
* Vendor/Engineer Assignment
* PO Number and Amount
* Key Dates (order date, target date, completion date)
* Current Status and Notes

*— End of Document —*