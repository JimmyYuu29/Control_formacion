# PRD Template: Excel-Email Automation App

> **Instructions:** Copy this template for each new app in the Excel-Email Automation category.
> Replace all `{placeholders}` and `[bracketed instructions]` with actual content.
> Delete these instructions before finalizing.

---

# Product Requirements Document (PRD)

## {App Name} — Excel-Email Automation

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 |
| **Author** | {Author Name} |
| **Date Created** | {YYYY-MM-DD} |
| **Last Updated** | {YYYY-MM-DD} |
| **Status** | Draft / In Review / Approved |
| **Stakeholders** | {List of stakeholders} |
| **Target Users** | {Department / Team} |
| **Priority** | P0 (Critical) / P1 (High) / P2 (Medium) / P3 (Low) |

---

## 1. Executive Summary

[2-3 sentences describing what this app does, who uses it, and the business value it provides.]

**Example:**
> This application automates the distribution of monthly debt reports to responsible persons via email. It replaces the manual process of splitting Excel files and sending individual emails, reducing processing time from 2 hours to 5 minutes.

---

## 2. Problem Statement

### 2.1 Current State

[Describe the current manual process:]

- How is the task currently performed?
- How long does it take?
- What are the pain points?
- What errors occur?

### 2.2 Desired State

[Describe what the automated process should look like:]

- What should happen automatically?
- What time savings are expected?
- What errors should be eliminated?

---

## 3. User Personas

### Primary User

| Attribute | Description |
|-----------|-------------|
| **Role** | {e.g., Treasury Analyst, Finance Manager} |
| **Department** | {e.g., Finance, Accounting, HR} |
| **Technical Level** | Low / Medium / High |
| **Frequency of Use** | Daily / Weekly / Monthly / Quarterly |
| **Number of Users** | {estimated count} |

### Secondary User(s)

[If applicable, describe other users who interact with the system or receive outputs.]

---

## 4. Input Specification

### 4.1 Excel File Structure

| Attribute | Value |
|-----------|-------|
| **File Format** | .xlsx |
| **Typical File Size** | {e.g., 500KB - 5MB} |
| **Number of Rows** | {typical range, e.g., 100-5000} |
| **Number of Columns** | {e.g., 10-15} |
| **Has Header** | Yes / No |
| **Header Row(s)** | {e.g., Row 1, Rows 1-3} |

### 4.2 Column Definitions

[List all columns in the Excel file:]

| Column | Letter | Name | Type | Required | Description |
|--------|--------|------|------|----------|-------------|
| 1 | A | {Column Name} | Text / Number / Date / Currency | Yes/No | {What this column contains} |
| 2 | B | {Column Name} | Text / Number / Date / Currency | Yes/No | {Description} |
| ... | ... | ... | ... | ... | ... |

### 4.3 Split Criteria

| Attribute | Value |
|-----------|-------|
| **Split By** | {e.g., "Responsable Code", "Client Name", "Department"} |
| **Split Column** | {Column letter and name, e.g., "Column A - Responsable"} |
| **Block Identifier** | {How blocks are identified, e.g., "Row starts with 'Responsable:'"} |
| **Subtotals** | {Are there subtotal rows? Where?} |
| **Grand Total** | {Is there a grand total? Where?} |

### 4.4 Sample Data

[Provide a simplified example of the Excel structure:]

```
Row 1: Company Name Header
Row 2: Date Information
Row 3: Column Headers
Row 4: Responsable: 00001 - PAULA GARRIDO
Row 5: Data row 1
Row 6: Data row 2
Row 7: Subtotal
Row 8: Responsable: 00002 - JUAN VERA
Row 9: Data row 1
...
Row N: Grand Total
```

---

## 5. Split Modes

[Define each way the file can be split. Most apps have one mode, some have multiple.]

### Mode: {Mode Name} (e.g., "By Responsable")

| Attribute | Value |
|-----------|-------|
| **Mode Identifier** | {e.g., "responsable"} |
| **Block Start Keyword** | {e.g., "responsable"} |
| **Block Identification Logic** | {How to detect the start of a new block} |
| **Code Extraction** | {How to extract the recipient code from the block header} |
| **Name Extraction** | {How to extract the recipient name} |
| **Data Rows** | {Which rows contain data vs. headers/totals} |
| **Total Row** | {How to identify the subtotal row} |
| **Amount Column** | {Which column contains the amount for totaling} |

[Repeat this section for each additional mode.]

---

## 6. Output Specification

### 6.1 Generated Excel Files

| Attribute | Value |
|-----------|-------|
| **File Naming Convention** | {e.g., "{Responsable_Name}_{Date}.xlsx"} |
| **Template File** | {Template filename or "None"} |
| **Include Header** | Yes / No — {describe header content} |
| **Include Subtotal** | Yes / No |
| **Column Selection** | User-selectable / Fixed |
| **Default Columns** | {List of default column letters} |
| **Formatting** | {Preserve original / Apply template / Custom} |

### 6.2 Email Specification

| Attribute | Value |
|-----------|-------|
| **Default Subject** | {e.g., "Reclamación de deuda - {{nombre}} - {{fecha}}"} |
| **Default Body** | [See template below] |
| **CC Recipients** | {Default CC list, if any} |
| **Attachment** | Individual Excel file per recipient |
| **Format** | HTML |

**Default Email Body Template:**
```html
[Provide the default email body with variable placeholders]

Example:
<p>Estimado/a {{nombre}},</p>
<p>Adjunto encontrará el detalle de deuda con vencimiento {{fecha_vencimiento}}.</p>
<p>Total pendiente: {{total_deuda}}</p>
<p>Saludos cordiales,</p>
<p>Departamento de Tesorería</p>
```

**Available Template Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `{{nombre}}` | Recipient full name | "PAULA GARRIDO" |
| `{{codigo}}` | Recipient code | "00001" |
| `{{fecha_vencimiento}}` | Due date (DD/MM/YYYY) | "15/03/2026" |
| `{{total_deuda}}` | Total amount (formatted) | "1.234,56" |
| `{{custom_var}}` | [Add app-specific variables] | |

---

## 7. Contact Management

### 7.1 Contact Source

| Attribute | Value |
|-----------|-------|
| **Default Contacts File** | {filename, e.g., "Contactos.xlsx"} |
| **Contact Upload** | Required / Optional |
| **Persistent Storage** | Yes / No |
| **Contact Fields** | [See table below] |

### 7.2 Contact File Columns

| Column | Letter | Field | Required |
|--------|--------|-------|----------|
| 1 | A | Code | Yes |
| 2 | B | First Name | Yes |
| 3 | C | Last Name | No |
| 4 | D | Email | Yes |
| 5 | E | CC Email | No |

### 7.3 Contact Matching Logic

[Describe how recipients are matched to contacts:]

- Primary match by: {e.g., "Code (exact match)"}
- Fallback match by: {e.g., "Full name (fuzzy match)"}
- Unmatched behavior: {e.g., "Marked as unmapped, user can provide email manually or exclude"}

---

## 8. SharePoint Integration (Optional)

[If this app requires saving files to SharePoint, complete this section. Otherwise, write "Not applicable."]

| Attribute | Value |
|-----------|-------|
| **Required** | Yes / No |
| **SharePoint Site** | {Site URL or name} |
| **Target Library** | {e.g., "Shared Documents"} |
| **Folder Structure** | {e.g., "/Reports/{Year}/{Month}/"} |
| **Upload Timing** | Before email / After email / Parallel |
| **File Format** | Same as attachment / ZIP / Both |

---

## 9. Functional Requirements

### 9.1 Core Requirements (Standard — inherited from standard spec)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Upload .xlsx file via web interface | P0 |
| FR-02 | Parse file and split by configured criteria | P0 |
| FR-03 | Display parsed groups with totals | P0 |
| FR-04 | Allow column selection for output | P1 |
| FR-05 | Load and map contacts | P0 |
| FR-06 | Configure email subject and body | P0 |
| FR-07 | Preview email before sending | P1 |
| FR-08 | Send emails via Power Automate | P0 |
| FR-09 | Display send results (success/failed) | P0 |
| FR-10 | Download generated files as ZIP | P1 |
| FR-11 | Persist contacts across sessions | P1 |
| FR-12 | Check Power Automate connectivity | P1 |

### 9.2 App-Specific Requirements

[Add requirements unique to this app:]

| ID | Requirement | Priority | Notes |
|----|-------------|----------|-------|
| FR-A01 | {Specific requirement} | P0/P1/P2 | {Notes} |
| FR-A02 | {Specific requirement} | P0/P1/P2 | {Notes} |
| ... | ... | ... | ... |

---

## 10. Non-Functional Requirements

| ID | Requirement | Specification |
|----|-------------|---------------|
| NFR-01 | File size limit | Max 50MB upload |
| NFR-02 | Processing time | < 30s for parse, < 60s per email send |
| NFR-03 | Availability | Office hours (8:00-20:00 local time) |
| NFR-04 | Browser support | Chrome 90+, Edge 90+, Firefox 90+ |
| NFR-05 | Concurrent users | 1 (single-user design) |
| NFR-06 | Data retention | Session data cleared on new upload |
| NFR-07 | Contact retention | Persistent until manual deletion |
| NFR-08 | Deployment | Docker or systemd on Linux |

---

## 11. User Interface

### 11.1 Workflow Steps

[Describe the step-by-step user flow:]

| Step | Name | User Action | System Response |
|------|------|-------------|----------------|
| 1 | Upload | Drag-and-drop or click to upload Excel | Parse file, show summary |
| 2 | Review | View parsed groups, select columns | Display groups and column options |
| 3 | Contacts | Upload contacts or use stored | Show mapping results |
| 4 | Email | Edit subject/body, set CC | Show email preview |
| 5 | Send | Click send button | Send emails, show results |

### 11.2 UI Mockup / Wireframe

[Include ASCII mockups or link to design files:]

```
┌─────────────────────────────────────────────┐
│  {App Name}                                  │
├─────────────────────────────────────────────┤
│  [1.Upload] → [2.Review] → [3.Send]        │
├─────────────────────────────────────────────┤
│                                              │
│  [Current step content area]                 │
│                                              │
├─────────────────────────────────────────────┤
│  Status: ● Power Automate Connected         │
└─────────────────────────────────────────────┘
```

---

## 12. Power Automate Configuration

| Attribute | Value |
|-----------|-------|
| **Email Flow Name** | {e.g., "DeudaApp - Send Email"} |
| **Email Flow Owner** | {Service account or user} |
| **SharePoint Flow Name** | {If applicable} |
| **Sending Account** | {Email address that sends emails} |
| **Environment** | {e.g., "Default", "Production"} |

---

## 13. Deployment

| Attribute | Value |
|-----------|-------|
| **Target Server** | {Server name or IP} |
| **Deployment Method** | Docker / systemd / NSSM |
| **Port** | {e.g., 8000, 8001, 8002} |
| **Domain/URL** | {e.g., deuda.internal.company.com} |
| **SSL Required** | Yes / No |

---

## 14. Testing Plan

### 14.1 Test Scenarios

| ID | Scenario | Expected Result | Priority |
|----|----------|----------------|----------|
| TC-01 | Upload valid Excel file | File parsed successfully, groups displayed | P0 |
| TC-02 | Upload invalid file type (.csv) | Error message displayed | P0 |
| TC-03 | Parse file with 1 group | Single group shown | P0 |
| TC-04 | Parse file with 50+ groups | All groups shown, performance acceptable | P1 |
| TC-05 | Map contacts — all matched | 0 unmapped contacts | P0 |
| TC-06 | Map contacts — some unmapped | Unmapped contacts highlighted | P0 |
| TC-07 | Send test email | Email received with correct attachment | P0 |
| TC-08 | Send batch (10+ emails) | All sent successfully | P0 |
| TC-09 | Power Automate URL invalid | Error displayed on status check | P1 |
| TC-10 | Large file upload (50MB) | Processed within limits | P2 |

### 14.2 Acceptance Criteria

[Define what "done" looks like:]

- [ ] All P0 test scenarios pass
- [ ] Email delivery confirmed to at least 3 different recipients
- [ ] File generation produces correctly formatted Excel files
- [ ] Contact persistence works across app restarts
- [ ] Power Automate status check returns correctly
- [ ] Error messages are clear and actionable

---

## 15. Timeline & Milestones

| Milestone | Description | Target Date | Status |
|-----------|-------------|-------------|--------|
| M1 | PRD approved | {date} | {status} |
| M2 | Backend development complete | {date} | {status} |
| M3 | Frontend development complete | {date} | {status} |
| M4 | Power Automate flows configured | {date} | {status} |
| M5 | Testing complete | {date} | {status} |
| M6 | Deployment to production | {date} | {status} |
| M7 | User training | {date} | {status} |

---

## 16. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|------------|------------|
| Power Automate URL expires | Emails stop sending | Medium | Monitor, document regeneration process |
| Excel format changes | Parse fails | Low | Document expected format, validate |
| Service account password expires | Flows stop | Medium | Calendar reminder, service account |
| {App-specific risk} | {Impact} | {Probability} | {Mitigation} |

---

## 17. Appendix

### A. Glossary

| Term | Definition |
|------|-----------|
| {Term} | {Definition} |

### B. Related Documents

| Document | Location |
|----------|----------|
| Technical Specification | `standard/TECH_SPEC.md` |
| Architecture Design | `standard/ARCHITECTURE.md` |
| Process Flow | `standard/PROCESS_FLOW.md` |
| Deployment Guide | `standard/DEPLOYMENT.md` |
| Power Automate Guide | `standard/POWER_AUTOMATE.md` |
| Conventions | `standard/CONVENTIONS.md` |

### C. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | {date} | {author} | Initial version |
