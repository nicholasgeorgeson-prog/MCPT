# VBA Analysis — MCPT Source Workbooks

Analysis of all Excel/VBA workbooks being replaced by MCPT.
Conducted 2026-03-31 using `olevba` (oletools).

---

## Workbooks Analyzed

| File | Modules | Key Function |
|---|---|---|
| `TrackerHelperV3.xlsm` | UpdateData, JamieEmail, MissingAuthorizations, PromoDSLCreation, AuthorizationDSL, TrackerFill | Main MCPT tracker + DSL generation + email automation |
| `GapAnalysis.xlsm` | Main, Helper, TFS | 22-step data pipeline for gap analysis |
| `Charging.xlsm` | ClnHrs, AllHours | SAP charging data processing + pivot |
| `NimbusBOE.xlsm` | CleanData, BOETable | BOE (Basis of Estimate) SAP data processing |

---

## TrackerHelperV3.xlsm

### Module: UpdateData.bas

**Purpose**: Reads fresh diagram data from a network share and updates the tracker spreadsheet.

**Key logic**:
- Reads from a hardcoded network share path (e.g., `\\server\share\NimbusData.xlsx`)
- Matches diagrams by GUID
- Updates status columns, authorization strings, modification dates
- Handles missing diagrams (new or removed from Nimbus)

**MCPT replacement**: This entire module is replaced by `GET /get-mcpt` API call. The Flask backend calls the backend REST API and returns fresh data. No more network share reading.

---

### Module: JamieEmail.bas

**Purpose**: Sends a director-level status email summarizing the promotion cycle.

**Key logic**:
- Iterates all rows in the tracker
- Groups by status (Engineering Approved, Claimed, Unclaimed, NTBC)
- Builds an HTML email body with counts and lists
- Sends via Outlook (CreateObject("Outlook.Application"))

**MCPT replacement**: Module 12 (Email Automation) → Email Type 1 (Status Summary Email). Uses smtplib → SMTP relay instead of Outlook automation. Triggered via Admin Panel button.

**Email structure** (preserved from VBA):
- Subject: `MCPT Status Update — {promotion_date}`
- Body sections: Engineering Approved (N diagrams), Claimed (N diagrams), Unclaimed (N diagrams), NTBC (N diagrams)
- Table format with Diagram Level, Title, Owner, Status

---

### Module: MissingAuthorizations.bas

**Purpose**: Identifies diagrams with authorization pending and sends reminder emails to authorizers who haven't signed off.

**Key logic**:
- Reads the Authorizations data (from `GET /get-trb` equivalent)
- Finds diagrams where `SignOffStatus` is not "Approved" and `DueDate` is past
- Groups by authorizer
- Sends one email per authorizer listing their pending sign-offs
- Uses Outlook automation

**MCPT replacement**: Module 12 (Email Automation) → Email Type 2 (Missing Authorization Reminder). Logic: query the authorization data for overdue/pending authorizations, group by authorizer, send via smtplib.

---

### Module: PromoDSLCreation.bas

**Purpose**: Generates the 5-category DSL files for Nimbus Batch Server.

**Key logic**:
```
For each diagram in tracker:
    If Status = "Engineering Approved" → write DraftDSLID to PromotionEngineeringApproved.dsl
    If Status = "Claimed"             → write DraftDSLID to PromotionClaimed.dsl
    If Status = "Unclaimed"           → write DraftDSLID to PromotionUnclaimed.dsl
    If Status = "Not To Be Claimed"   → write DraftDSLID to PromotionNTBC.dsl
    If PromoOnly flag = True          → write DraftDSLID to PromotionPromoOnly.dsl
```

**File output**: Plain text files, one DSLID per line. Written to a local temp folder then emailed/shared.

**MCPT replacement**: Module 3 (DSL File Generator). Uses DraftDSLID from the MCPT data, generates in-memory, packages as ZIP download.

**Critical note**: Uses `DraftDSLID` (not GUID). These are different fields.

---

### Module: AuthorizationDSL.bas

**Purpose**: Generates per-authorizer DSL files for the authorization step.

**Key logic**:
```
For each authorizer in the authorization data:
    Create file: AuthDSL_{FirstName}_{LastName}.dsl
    For each diagram where this authorizer has NOT signed off:
        write DraftDSLID to the file
```

**MCPT replacement**: Part of Module 3 (DSL File Generator) — specifically the per-authorizer section. Reads from authorization data via `GET /get-trb`.

---

### Module: TrackerFill.bas

**Purpose**: Fills in the tracker columns from the raw Nimbus data dump.

**Key logic**:
- Reads the master data Excel file
- Maps columns by header name
- Handles the 34-column structure of `Team_Dashboard-Diagrams.xlsx`
- Populates: SP Folder Created, Tool Entry Created, IC Assigned, Engineering Approved, Authorization status, etc.

**MCPT replacement**: This entire module is replaced by the MCPT database and `GET /get-mcpt` endpoint. The tracking columns are now managed in the backend DB with API endpoints for updates.

---

## GapAnalysis.xlsm

### Module: Main.bas — UpdateAllGapData()

**Purpose**: 22-step pipeline that processes diagram data to compute coverage gaps.

**Key steps** (summarized):
1. Clear previous gap data
2. Load all diagrams from network share
3. Build organization hierarchy tree
4. Map each diagram to its owning organization (GetOrgOwnerType)
5. Calculate coverage metrics per org node
6. Identify gaps (orgs with insufficient diagram coverage)
7. Apply Levenshtein distance matching for fuzzy org name matching
8. Map to function categories (GetSubCOP)
9. Cross-reference against TFS (Team Function Summary) data
10. Generate gap report table
11. Apply color coding by gap severity
12. Save output

**MCPT replacement**: Module 7 (Metrics: DID Working) captures the concept of gap tracking. The specific GapAnalysis pipeline may be partially preserved as an import/analysis feature, but the core gap tracking is less relevant once MCPT manages the diagram lifecycle.

---

### Module: Helper.bas

**Purpose**: Utility functions for the gap analysis pipeline.

**Key functions**:

```vba
Function GetSubCOP(orgCode As String) As String
' Maps an org code to its Sub-COP (Community of Practice) category
' Uses a lookup table of org → function mappings
```

```vba
Function GetOrgOwnerType(diagramGUID As String) As String
' Determines if an org is a Primary Owner, Secondary Owner, or Consumer
' of a given diagram based on the diagram's organization field
```

```vba
Function Levenshtein(s1 As String, s2 As String) As Integer
' Edit distance for fuzzy org name matching
' Used when org names differ slightly between data sources
```

**MCPT notes**: The Levenshtein distance function may be useful if MCPT needs to match organization names across data sources (e.g., matching SAP org names to Nimbus org names).

---

### Module: TFS.bas

**Purpose**: Team Function Summary lookup table.

**Key logic**:
- Hardcoded table mapping function codes to organization groups
- Used by GetSubCOP to categorize diagrams by discipline (e.g., Systems Engineering, Manufacturing, Quality)
- ~50-100 entries in the lookup table

---

## Charging.xlsm

### Module: ClnHrs.bas

**Purpose**: Cleans SAP hours data from raw export format.

**Key logic**:
- SAP exports hours in Column U with format `"8.0 H"` (number + space + "H")
- Strips the `" H"` suffix to get a pure numeric value in Column V
- Formula approach: `=VALUE(LEFT(U2, LEN(U2)-2))`

**MCPT Module 5 (Metrics: Charging)**:
- Smart column detection: scan the Excel headers to find the hours column (may be labeled "Hours", "Hrs", "Actual Hours", etc.)
- Strip `" H"` suffix from hours values using same logic
- Store cleaned values for pivot table

---

### Module: AllHours.bas

**Purpose**: Creates a pivot table of Employee × FiscalMonth showing hours.

**Key logic**:
- Reads cleaned hours data (after ClnHrs processing)
- Groups by Employee and FiscalMonth
- Takes the maximum pay period value for each cell (not sum — SAP data has cumulative values within a pay period)
- Outputs a matrix: rows = employees, columns = fiscal months, values = max hours

**MCPT Module 5 (Metrics: Charging)**:
- `openpyxl` to build the pivot table
- Group by Employee (Column: employee name or ID) × FiscalMonth
- Aggregate using MAX (not SUM) — matches the original VBA logic
- Export as styled Excel with the pivot table

**Important**: The MAX aggregation is critical. SAP exports cumulative values within a pay period, so summing would double-count. VBA used Max, MCPT must also.

---

## NimbusBOE.xlsm

### Module: CleanData.bas

**Purpose**: Filters SAP BOE (Basis of Estimate) data to the NAT team's charge order.

**Key logic**:
```vba
' Keep only rows where:
'   Order = "9L99G054"  (NAT team SAP order)
'   AND SuppCode NOT IN ("PTO", "HOL", "UNP")  (exclude non-work time)
```

**MCPT Module 6 (Metrics: NimbusBOE)**:
- SAP ingest: read uploaded Excel file
- Filter rows: `Order == "9L99G054"` AND `SuppCode not in ['PTO', 'HOL', 'UNP']`
- The SAP order number `9L99G054` is admin-configurable in MCPT (default: `9L99G054`)
- Admin can update it via Admin Panel if the charge order changes

---

### Module: BOETable.bas

**Purpose**: Builds the BOE summary table from cleaned SAP data.

**Key logic**:
- Groups cleaned rows by Employee
- For each employee: sum hours by "Supp Code" (supplemental activity code)
- Outputs a table: Employee | SuppCode1 | SuppCode2 | ... | Total
- Common supp codes: NWRK (non-work), ADMN (admin), direct charge codes

**MCPT Module 6 (Metrics: NimbusBOE)**:
- Build BOE table using pandas or manual aggregation
- Group by Employee × SuppCode
- Sum hours (BOE data uses actual values, not cumulative like Charging)
- Display as formatted table with totals row
- Export via openpyxl

---

## Weekly Tasking Report.xlsm

### Sheet: Source (main data sheet)
Contains a `Tasks` table (Excel ListObject) with columns:
- Column A: `Date` — auto-filled with today's date when row is triggered
- Column B: `TaskID` — auto-incrementing integer (previous ID + 1)
- Column C: (has data validation — type/category dropdown, copied from previous row)
- Column D: (trigger column — editing this column auto-fills Date and TaskID)
- Column E: (has data validation — copied from previous row)

### Module: Main.bas — SendWeeklyExecutiveReport()

**Purpose**: Generates and emails a weekly executive summary report.

**Features** (Version 3.1):
- Executive Summary: Auto-generated 2-3 sentence overview at top
- Backlog Trend: Shows task count change vs. last week
- Preview Mode: Review before sending
- Settings Sheet (`ReportSettings`): Configure recipients, thresholds, options
- Due Date Tracking: Highlight overdue items
- Spell Check: Validates before sending
- Historical Archive: Backs up data before deleting completed items

**Logic**:
1. Load settings from `ReportSettings` sheet
2. Get `Tasks` table from `Source` sheet
3. Calculate current week start (Monday)
4. Collect all report data (`CollectReportData`)
5. Optional spell check
6. Show confirmation dialog
7. Build HTML email body
8. Send via Outlook automation
9. Archive completed tasks → Historical sheet
10. Delete completed tasks from Source

**MCPT replacement** (Module 4 — Weekly Tasking Report): The MCPT version captures the same concept (weekly task tracking + executive report) but as a web form rather than Excel. ICs enter tasks via the web UI. Director exports/emails the consolidated report. The auto-increment TaskID pattern is preserved.

---

## Column Mapping: Team_Dashboard-Diagrams.xlsx

The `Team_Dashboard-Diagrams.xlsx` file in the Reports repo has 34 columns that map to the MCPT tracking table:

| # | Excel Column | Maps To |
|---|---|---|
| 1 | GUID | Diagrams.GUID (primary key) |
| 2 | Map Name | Diagrams.MapName |
| 3 | Draft Level | Diagrams.DraftLevel |
| 4 | Master Level | Diagrams.MasterLevel |
| 5 | Diagram Type | Diagrams.DiagramType |
| 6 | Title | Diagrams.Title |
| 7 | Notation | Diagrams.Notation |
| 8 | Author | Diagrams.Author |
| 9 | Owner | Diagrams.Owner |
| 10 | Draft Version | Diagrams.DraftVersion |
| 11 | Master Version | Diagrams.MasterVersion |
| 12 | Date | Diagrams.Date |
| 13 | Draft Authorization | Diagrams.DraftAuthorization |
| 14 | Master Authorization | Diagrams.MasterAuthorization |
| 15 | Draft Template | Diagrams.DraftTemplate |
| 16 | Master Template | Diagrams.MasterTemplate |
| 17 | Draft Modified | Diagrams.DraftModified |
| 18 | Master Modified | Diagrams.MasterModified |
| 19 | Draft User Modified | Diagrams.DraftUserModified |
| 20 | Master User Modified | Diagrams.MasterUserModified |
| 21 | Drill Down | Diagrams.DrillDown |
| 22 | Description | Diagrams.Description |
| 23 | Status | Diagrams.Status (MCPT tracking status) |
| 24 | Organization | Diagrams.Organization |
| 25 | URL | Diagrams.URL (or auto-constructed Nimbus deep link) |
| 26 | Attachments | Diagrams.Attatchments (note: typo in schema) |
| 27 | Primary Contact | Diagrams.PrimaryContact |
| 28 | Parent GUID | Diagrams.ParentGUID |
| 29 | Objects | Diagrams.Objects |
| 30 | Draft Map Path | Diagrams.DraftMapPath |
| 31 | Master Map Path | Diagrams.MasterMapPath |
| 32 | Draft DSLID | Diagrams.DraftDSLID |
| 33 | Master DSLID | Diagrams.MasterDSLID |
| 34 | Hyperlink | Constructed: `https://nimbusweb.../0:{MAP_GUID}.{GUID}` |

The MCPT tracking table adds additional columns not in Diagrams:
- SP Folder Created (boolean)
- Tool Entry Created (boolean)
- IC Assigned (text — windows username)
- Notes (text — free text)
- Change Log (JSON or text — history of changes)
