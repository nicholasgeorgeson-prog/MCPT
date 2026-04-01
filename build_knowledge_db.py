#!/usr/bin/env python3
"""
Builds project_knowledge.db from embedded knowledge entries.
Run: python3 build_knowledge_db.py
"""
import sqlite3, os, sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project_knowledge.db')

KNOWLEDGE = [
    # ─── ARCHITECTURE ────────────────────────────────────────────────────────
    {
        "category": "architecture",
        "title": "Tech stack decision — Flask + Waitress + Vanilla JS",
        "content": """Tech stack: Python 3, Flask, Waitress WSGI (NOT Flask dev server), Vanilla JS/HTML/CSS (no framework).
Same proven pattern as AEGIS. Reasons: no build toolchain required, works air-gapped/offline,
deploys identically to AEGIS on Windows, Nicholas already knows the patterns.
Port: 5060 (AEGIS is on 5050 — avoid conflict).
Deploy path: C:\\MCPT\\ — never OneDrive, never paths with spaces.""",
        "tags": "flask, waitress, vanilla-js, windows, deployment",
        "source": "architecture-decision"
    },
    {
        "category": "architecture",
        "title": "API proxy pattern — ALL backend calls through Flask routes",
        "content": """NEVER make direct browser-to-API calls. All backend API calls go through Flask route proxies.
Reasons: centralizes auth token injection, avoids CORS complexity, allows request/response
transformation, enables logging and error handling in one place.
Pattern: Browser → Flask route → Python requests → Backend API → Flask route → Browser.
This means the frontend JS calls /api/mcpt (our Flask endpoint), not the backend API directly.""",
        "tags": "api, proxy, cors, flask-routes",
        "source": "architecture-decision"
    },
    {
        "category": "architecture",
        "title": "Nimbus abstraction layer — future-proof for tool migration",
        "content": """TIBCO Nimbus reached final EOL September 1, 2025. NGAS is on legacy/extended support.
All Nimbus-specific code must be behind a clean adapter/abstraction layer.
Key abstraction points:
1. Nimbus base URL stored in config.json (not hardcoded): https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:9820E23DD3204072819C50B7A2E57093.{GUID}
2. DSLID concept abstracted as 'batch_operation_id' internally
3. Level format parsing (dotted notation) in a single utility function
4. Deep link construction in one config-driven function
When NGAS migrates to a successor tool: change config + adapter, zero frontend redesign.""",
        "tags": "nimbus, eol, abstraction, adapter-pattern, future-proof",
        "source": "architecture-decision"
    },
    {
        "category": "architecture",
        "title": "Local SQLite DB — notifications only, not app data",
        "content": """The app maintains exactly ONE local SQLite database: data/notifications.db (WAL mode).
Schema:
  CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    windows_username TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT,
    read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
ALL other data comes from the backend API. The app has no local copy of MCPT data —
each page load/refresh fetches fresh from API. No local caching of diagram data.""",
        "tags": "sqlite, notifications, local-db, wal",
        "source": "architecture-decision"
    },
    # ─── API CONTRACT ────────────────────────────────────────────────────────
    {
        "category": "api-contract",
        "title": "Known API endpoints (from developer email 2026-03-31)",
        "content": """GET  /get-mcpt              → Full MCPT table (array of row objects)
GET  /get-trb               → Authorization progress data
GET  /get-diagram?guid={}   → Single diagram details
POST /add-entry             → Add new MCPT tracking row (JSON body)
POST /remove-entry          → Remove row (JSON body with GUID)
POST /edit-entry            → Edit single field (JSON body: {guid, field, value})
POST /archive-entry         → Archive row (JSON body with GUID)

STATUS: Base URL, auth mechanism, and JSON schemas are PENDING (see developer_questions_email.md).
Build the API client layer to read base URL from config.json.""",
        "tags": "api, endpoints, get-mcpt, post-entry",
        "source": "developer-email-2026-03-31"
    },
    {
        "category": "api-contract",
        "title": "Diagrams table schema (from SQL file in Reports repo)",
        "content": """Diagrams table (confirmed from Diagrams.sql and Team_Dashboard-Diagrams.xlsx with 2801 rows):
GUID TEXT PK | MapName | DraftLevel | MasterLevel | DiagramType | Title | Notation
Author | Owner | DraftVersion | MasterVersion | Date | DraftAuthorization | MasterAuthorization
DraftTemplate | MasterTemplate | DraftModified | MasterModified | DraftUserModified | MasterUserModified
DrillDown INTEGER | Description | Status | Organization | URL | Attatchments (sic - typo in schema)
PrimaryContact | ParentGUID (FK self-ref) | Objects INTEGER | DraftMapPath | MasterMapPath
DraftDSLID | MasterDSLID

Excel confirmed additional derived fields: LastPromotedDate, LastChangedDate,
ChangesSinceLastPromotion, ChangeLog, MaxActivityCount, Hyperlink (pre-built Nimbus URL)

NOTE: 'Attatchments' is a typo in the schema — double-t. Use this exact spelling in code.""",
        "tags": "diagrams, sql-schema, dslid, guid, fields",
        "source": "reports-repo-sql"
    },
    {
        "category": "api-contract",
        "title": "Authorization table schema and data format",
        "content": """Authorizations table (confirmed from Authorizations.sql and Team_Dashboard-Authorization_Progress.xlsx with 4372 rows):
DiagramGUID TEXT NOT NULL → FK to Diagrams(GUID)
Type TEXT DEFAULT 'Draft'
User TEXT NOT NULL (authorizer name, e.g. 'Kathryn McKenzie')
Authorization TEXT (format: 'Authorization Pending - 2/13/2026' or 'Promotion Ready - 2/6/2026')
SignOffStatus TEXT ('Not Signed Off', 'Accepted')
SignOffDate TIMESTAMP
Sequence INTEGER (sequential authorization order — authorizers act in sequence)
RequestFrom TEXT (who requested auth, e.g. 'Chad Lauffer')
DueDate TIMESTAMP (the TRB meeting date)
Date TIMESTAMP (when record was created)
ActiveState TEXT ('Active', 'Inactive')

CRITICAL: Authorization field contains the DATE embedded: parse with regex to extract date component.""",
        "tags": "authorizations, sql-schema, sign-off, sequence, pending",
        "source": "reports-repo-sql"
    },
    {
        "category": "api-contract",
        "title": "Changes table schema — change log entries",
        "content": """Changes table (confirmed from Changes.sql and Team_Dashboard-Diagram_Change_Log.xlsx with 90,068 rows):
DiagramGUID TEXT NOT NULL → FK to Diagrams(GUID)
ID INTEGER NOT NULL
Type TEXT DEFAULT 'Draft'
Date TIMESTAMP
Version NUMERIC (decimal like 1.35)
ChangeDescription TEXT — the actual change log text, HTML-formatted with bullet points
User TEXT

Excel headers: Level, Map Name, Diagram Type, ID, Date, Version, Change Description, User,
Contains Drill Down?, GUID, Class Category

This maps to Column BB (54) in the original Excel tracker — the change log entries field.""",
        "tags": "changes, sql-schema, change-log, version",
        "source": "reports-repo-sql"
    },
    {
        "category": "api-contract",
        "title": "Schema bug — SIPOCs and Storyboards composite FK",
        "content": """BUG IN DEVELOPER SCHEMA (reported in developer_questions_email.md):
SIPOCs.sql and Storyboards.sql both have:
  CONSTRAINT "DiagramGUID_CK" FOREIGN KEY("DiagramGUID","Type") REFERENCES "Diagrams"("GUID","Type")
But Diagrams table has NO Type column — only GUID as primary key.
This FK will fail if SQLite FK enforcement (PRAGMA foreign_keys = ON) is enabled.
Correct FK should be: FOREIGN KEY("DiagramGUID") REFERENCES "Diagrams"("GUID")
Status: Reported to dev team. Awaiting fix confirmation.""",
        "tags": "schema-bug, sipocs, storyboards, fk, sqlite",
        "source": "analysis-2026-03-31"
    },
    # ─── DATA MODEL ──────────────────────────────────────────────────────────
    {
        "category": "data-model",
        "title": "DSLID vs GUID — two different identifiers, critical distinction",
        "content": """DSLID and GUID are completely different identifiers. Never confuse them.

GUID (e.g., 'ACDF1AE9385543888E91381F30D3F806'):
- Used in Nimbus web URLs: .../0:9820E23DD3204072819C50B7A2E57093.{GUID}
- Used as primary key in Diagrams table
- Used for API calls: GET /get-diagram?guid={GUID}

DSLID (e.g., '8B164C5A9AB84ADC80FFFC442CD1280F'):
- Used in .dsl batch operation files (one DSLID per line)
- Loaded into Nimbus batch server for bulk authorize/promote operations
- Stored in DraftDSLID and MasterDSLID columns of Diagrams table
- When DraftDSLID is blank → diagram is BLOCKED for batch promotion
- DSLID.xlsx contains mapping: Draft/Master Diagram Level → DSLID

DSL files are plain text, one DSLID per line:
  8B164C5A9AB84ADC80FFFC442CD1280F
  5C5BCCEA841241E5B03DDAABA16D490D
  ...""",
        "tags": "dslid, guid, identifier, dsl-files, batch-promotion",
        "source": "analysis-2026-03-31"
    },
    {
        "category": "data-model",
        "title": "DSL file types — 5 categories for batch promotion",
        "content": """DSL files are plain text files containing DSLIDs (one per line) used by Nimbus batch server.
Generated per promotion date. File naming:

PromotionEngineeringApproved{YYYY-MM-DD}.dsl  → Status = 'Engineering Approved'
PromotionClaimed{YYYY-MM-DD}.dsl               → Status = 'Claimed'
PromotionUnclaimed{YYYY-MM-DD}.dsl             → Status = 'Unclaimed'
PromotionNTBC{YYYY-MM-DD}.dsl                  → Status = 'Not To Be Claimed'
PromotionPromoOnly{YYYY-MM-DD}.dsl             → Diagram Category = 'Promotion Only'

Per-authorizer files (for Engineering Approved + Claimed):
{AuthorizerName}_{PackageTitle}_{YYYY-MM-DD}.dsl

VALIDATION: Any row with Authorizer but blank DraftDSLID → error. Block generation.
Show: 'X diagrams missing DSLIDs — update DSLID file'

Delivery: Browser ZIP download (JSZip or server-side zipfile module).
Also support showDirectoryPicker() API for Edge/Chrome folder write.""",
        "tags": "dsl-files, batch-promotion, zip, validation, missing-dslid",
        "source": "vba-analysis-PromoDSLCreation.bas"
    },
    {
        "category": "data-model",
        "title": "Diagram Level format and hierarchy",
        "content": """Level format in exports: '1.3.8 Draft Copy' or '1.3.8' (Master, no suffix)
Level NUMBER = count of dots + 1. Examples:
  '1'         → L1 (top level)
  '1.3'       → L2
  '1.3.8'     → L3
  '1.3.8.5'   → L4

Parse utility function needed:
  def parse_level(level_str):
      clean = level_str.replace(' Draft Copy', '').replace(' Master Copy', '').strip()
      return clean, clean.count('.') + 1  # (dotted_id, level_number)

Map GUID (applies to all diagrams in NGAS Process Model): 9820E23DD3204072819C50B7A2E57093
This is hardcoded in the base URL — all NGAS diagrams are in one Nimbus map.""",
        "tags": "level, hierarchy, format, l1-l4, map-guid",
        "source": "analysis-nimbus-research"
    },
    {
        "category": "data-model",
        "title": "Diagram Status values — org-specific Nimbus Status field",
        "content": """The Status field in Nimbus is a free-text/configurable field. NGAS uses:
- 'Unclaimed' — no owner assigned; NAT team can authorize independently
- 'Claimed' — owner is assigned; NAT must work with owner; owner must authorize
- 'Engineering Approved' — engineering process; requires TRB Chair sign-off in addition to owner
- 'Conceptual Image' — visual/conceptual diagram; treated like Unclaimed for auth purposes
- 'Not To Be Claimed' (NTBC) — diagram that will not go through claiming process

Authorization path by status:
  Unclaimed / Conceptual Image → NAT authorizes directly → promote
  Claimed → Owner must authorize → promote
  Engineering Approved → Owner + TRB Chair must both authorize → promote

Version rolling: Draft decimal (e.g., 1.35) → Master next whole integer (e.g., 2)""",
        "tags": "status, unclaimed, claimed, engineering-approved, ntbc, authorization-path",
        "source": "nimbus-research-vba-analysis"
    },
    {
        "category": "data-model",
        "title": "MCPT tracking columns (manually-filled) — columns A through Q from Excel",
        "content": """These columns are manually entered by the NAT team — NOT auto-populated from Nimbus:
A: Archive (bool) — moves row to archive tab/view
B: Promotion Date (date) — the bi-weekly promotion cycle date
C: Level (text) — auto from Diagrams, but manually set in tracker
D: Diagram Category (dropdown) — 'Promotion Only', standard types (admin-managed list)
E: Model Change Package Title (text) — groups related diagrams into a package
F: PEACE Portal TRB Change IDs (text) — manual copy-paste, may have multiple IDs
G: NAT Contact (dropdown) — team member responsible (admin-managed list with emails)
H: SP Folder Created (bool/Yes/No/NA)
I: Tool Entry Created (bool/Yes/No/NA)
J: Related Files Posted (bool/Yes/No/NA)
K: CR Package Ready (bool/Yes/No/NA)
L: Doc Registry Item Attached (bool/Yes/No/NA)
M: Updated Doc Registry URL (text/URL)
N: All Diagrams Included (bool/Yes/No/NA)
O: Peer Review Complete (bool/Yes/No/NA)
P: Notes (text, free-form)
Q: Disposition (enum: Primary / Secondary / blank) — overlap management

Column AG (also manual): Overlap disposition — which package is Primary vs Secondary
when two packages share the same promotion date.

STATUS: Exact JSON field names PENDING from dev team (see developer_questions_email.md #2)""",
        "tags": "mcpt-tracking, manual-columns, promotion-date, nat-contact, checklist",
        "source": "vba-analysis-excel-analysis"
    },
    # ─── NIMBUS ──────────────────────────────────────────────────────────────
    {
        "category": "nimbus",
        "title": "TIBCO Nimbus EOL and NGAS context",
        "content": """TIBCO Nimbus commercial retirement: September 2, 2024 (no new subscriptions)
Final end-of-life: September 1, 2025. Extended support available through September 2027.
NGAS is running on legacy/extended support Nimbus.

NGAS Nimbus server: https://nimbusweb.as.northgrum.com
NGAS map GUID: 9820E23DD3204072819C50B7A2E57093 (all NGAS process model diagrams in one map)
Deep link URL: https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:9820E23DD3204072819C50B7A2E57093.{DIAGRAM_GUID}

Nimbus Web Server is READ-ONLY for end users (IIS-hosted ISAPI). Authors use thick-client.
Batch Server handles: bulk authorization, promotion operations, scheduled reports.
Version: TIBCO Nimbus 10.4.x (SOAP API was removed in 10.6).
No REST API available — data access only via SQL export or Excel report exports.""",
        "tags": "nimbus, eol, server-url, map-guid, batch-server",
        "source": "nimbus-research-2026-03-31"
    },
    {
        "category": "nimbus",
        "title": "Nimbus promotion cycle — batch promotion mechanics",
        "content": """NGAS runs a bi-weekly promotion cycle (every other Friday).
Next promotion: April 4, 2026 (confirmed by user).

Promotion = converting authorized Draft diagrams to Master copies.
The Batch Server queues all promotions for the same map, archives current master atomically,
then runs all draft promotions through — ensures map is never in partially-promoted state.

Requirements before promotion:
1. ALL assigned authorizers must have signed off (unanimous, sequential)
2. Draft diagram must be fully authorized (not just partially)
3. DSLIDs must be populated (blank DSLID = blocked)
4. Version number must be rolled (Draft decimal → Master whole integer)

After promotion: Draft is LOCKED. Must be explicitly unlocked to edit again.
Previous master versions go to Archives folder.""",
        "tags": "promotion-cycle, batch-server, bi-weekly, authorization-unanimous, locked",
        "source": "nimbus-research-2026-03-31"
    },
    {
        "category": "nimbus",
        "title": "Nimbus authorization workflow — sequential, unanimous sign-off",
        "content": """Authorization model: SEQUENTIAL + UNANIMOUS. All assigned authorizers must sign off.
Authorizers notified by email in sequence — each must act before/after next in sequence.

Authorization states (from Authorization Progress export):
- 'Authorization Pending - {date}' — request sent, not yet signed
- 'Promotion Ready - {date}' — all authorizers have signed off
- 'Not Signed Off' (SignOffStatus) — individual authorizer status
- 'Accepted' (SignOffStatus) — individual authorizer signed off
- 'Inactive' (ActiveState) — superseded authorization request

TRB process (Engineering Approved diagrams):
- Owner signs off first
- TRB Chair is typically last in sequence
- TRB Chair sign-off is required for 'Engineering Approved' diagram type

Admin override: Admins can override an authorization cycle (provides reason + password).
This is for cases where an authorizer is unavailable (vacation, etc.).""",
        "tags": "authorization, sequential, unanimous, trb-chair, engineering-approved, override",
        "source": "nimbus-research-2026-03-31"
    },
    # ─── VBA LOGIC ───────────────────────────────────────────────────────────
    {
        "category": "vba-logic",
        "title": "Email automation — three email types from VBA",
        "content": """Three email types ported from TrackerHelperV3.xlsm VBA:

1. STATUS EMAIL (JamieEmail.bas → Director/Jamie):
   Recipient: Director (configurable)
   Content: HTML table of all diagrams for promotion date grouped by status
   (Approved, Pending Authorization, Update Pending). Includes hyperlinks, titles,
   change log entries, authorizer names.

2. MISSING AUTHORIZATIONS EMAIL (MissingAuthorizations.bas):
   Recipients: Each NAT Contact with diagrams in 'Update Pending' status for the date
   Content: HTML table of their diagrams needing authorization, with Nimbus links
   Filter: Diagram Category != 'Promotion Only' AND Authorization = 'Update Pending'

3. PER-AUTHORIZER REQUEST EMAIL (OutputModule.bas):
   Recipients: Each Authorizer with diagrams in a specific package
   Content: HTML table of their diagrams (grouped by package title), with change log
   Filter: Status in ('Claimed', 'Engineering Approved', 'Engineer Approved')
   Authorizer emails looked up from Helper sheet (admin-managed name→email table)

All emails: HTML format, styled tables with header row #D9E1F2 background, Calibri font.""",
        "tags": "email, jamie-email, missing-authorizations, per-authorizer, html-table",
        "source": "vba-analysis-TrackerHelperV3"
    },
    {
        "category": "vba-logic",
        "title": "VBA Dashboard metrics — textbox values extracted",
        "content": """VBA UpdateTextBoxes() function (UpdateData.bas) populates dashboard metrics:

Modeler Dashboard TextBoxes:
- TextBox 80: Count of unique Levels for current promotion date
- TextBox 85: Count of 'Update Pending' rows (excluding 'Promotion Only' category)
- TextBox 88: Count of unique values in Column E (Model Change Package Title) for date

Admin Dashboard TextBoxes:
- TextBox 69: Same as TextBox 80 (unique Level count)
- TextBox 72: Timestamp of last data update
- TextBox 73: Same as TextBox 85 (Update Pending count)
- TextBox 74: Same as TextBox 88 (unique package title count)

These translate to frontend dashboard cards showing:
- Total diagrams in current cycle
- Diagrams needing authorization action
- Distinct packages in cycle
- Last refresh timestamp""",
        "tags": "dashboard, metrics, textbox, unique-count, update-pending",
        "source": "vba-analysis-UpdateData.bas"
    },
    {
        "category": "vba-logic",
        "title": "Charging VBA logic — SAP data processing",
        "content": """Charging.xlsm VBA ported to Python:

cleanHours(): Column U has SAP format '8 H' → strip ' H' → numeric float
CreateDynamicTableWithMaxPayPeriod():
- Filters to max pay period value (current period only)
- Groups by: Employee Full Name, Network (charge #), Order, Supp2, Supp3, Ship
- Pivots on Fiscal Month columns
- Calculates Grand Total per group
- Output columns: Employee Full Name, Network, Order, Supp2, Supp3, Ship, [months], Grand Total

SAP export columns (confirmed from VBA column references):
- Col I (9): Employee Full Name
- Col P (16): Network
- Col Q (17): Order
- Col R (18): Ship
- Col S (19): Supplemental 2
- Col T (20): Supplemental 3
- Col U (21): Hours (raw, with ' H' suffix)
- Col V (22): Clean Hours (after processing)
- Col B (2): Fiscal Month
- Col C (3): Pay Period

Smart column detection: read headers dynamically, build column map by name.
Fallback to positional only if header not found.""",
        "tags": "charging, sap, hours, pivot, fiscal-month, smart-detection",
        "source": "vba-analysis-Charging.xlsm"
    },
    {
        "category": "vba-logic",
        "title": "NimbusBOE VBA logic — filter and BOE table",
        "content": """NimbusBOE.xlsm VBA ported to Python:

CreateCleanDataTable():
- Source sheet: 'Data'
- Filter: Order column = '9L99G054' (NAT team charge number, admin-editable)
- Exclude Att/Absence Type containing: 'PTO', 'HOL', 'UNP'
- Clean Hours: strip ' H' suffix
- Output columns: Fiscal Year, Fiscal Quarter, Fiscal Month, Pay Period Week Ending,
  Week Ending Date, Employee ID, Att/Absence Type, Supp1, Supp2, Supp3, Hours

Create_BOE_Table_2025():
- Groups into: dictNAT (NAT-specific), dictNATMisc (NAT misc), dictMisc (other)
- Key by Employee + Supp codes
- Pivots by Fiscal Month
- Handles normalization of Supp3 codes

NOTE: 'NimbusBOE' is NOT a Nimbus native term. It's NGAS-specific.
BOE = Basis of Estimate — maps employee SAP hours to Nimbus process functions.
The '9L99G054' order number is the NAT team's SAP charge code.""",
        "tags": "nimbusboe, boe, sap, filter-order, fiscal-month, supp-codes",
        "source": "vba-analysis-NimbusBOE.xlsm"
    },
    {
        "category": "vba-logic",
        "title": "GapAnalysis 22-step pipeline — module overview",
        "content": """GapAnalysis.xlsm (20MB) processes 22 data steps in sequence:
1. CreateReportingTableWithDynamicHeaders
2. CreateCCOMReviewSummaryTable_StructureOnly
3. UpdateDiagramsReport
4. UpdateDocReg
5. UpdateDrillDownRequiredTab
6. UpdateDRSM
7. UpdateLinkToFromTab
8. UpdateNeedsAttachment
9. PALData
10. CreatePrOPFilteredUniqueShortOrgTable
11. CreatePrOPReviewSummaryTable
12. UpdateSIPOC_WithInDRSM
13. UpdateStatementSetTracing
14. TFS_Working (Time/Function Sheet)
15. ToolsAnalysis
16. UpdateUnusedDocs
17. FillReportingTable_MainDataRows
18. FillReportingTable_MainDataRowsAll
19. FillSectorStandardToolsToProcessMapping
20. UpdateHealthData
21. PreviewReportingTableVisualization
22. StampUpdateDataTime

Key logic extracted:
- GetSubCOP(): Parses 'Org Owner' string to extract sub-COP code (e.g., 'Bus Mgmt (BM)' → 'BM')
- GetOrgOwnerType(): Classifies orgs as 'Engineering' or 'Other'
  Engineering: SE, T&E, FS, SW, VE, WSC, PS, AvI, AW, SI&O, SRV, PM&P, EP&T
  Other: NAT, PM, BM, Mission Assurance, TBD, GSC, IT, BD, Production, Operations, Facilities, Security, HR, Legal, ESH&M
- Levenshtein distance implemented for fuzzy title matching
- Function→Org mapping table (30+ function-to-code mappings)
- TFS = Time/Function Sheet (maps employee hours to process functions)""",
        "tags": "gap-analysis, pipeline, ccom, prop, sipoc, drsm, pal-data, tfs",
        "source": "vba-analysis-GapAnalysis.xlsm"
    },
    {
        "category": "vba-logic",
        "title": "TrackerFill — write-back to network share (REPLACED by new DB)",
        "content": """TrackerFill.bas in TrackerHelperV3.xlsm wrote data back to:
\\\\C30-YWVAP1393\\NimbusAS\\ReportsAS\\CleanReports\\Tracker\\Tracker.xlsx
This was the bidirectional sync mechanism for the Excel system.

In the new app: THIS IS REPLACED. The new SQLite DB is the source of truth (Q31 answer).
POST /add-entry and POST /edit-entry replace the TrackerFill write-back.
The network share \\\\C30-YWVAP1393 is NO LONGER written to by the new app.

The UpdateData.bas read path FROM that share is also replaced by GET /get-mcpt API call.""",
        "tags": "trackerFill, network-share, write-back, replaced, legacy",
        "source": "vba-analysis-TrackerFill.bas"
    },
    # ─── BUSINESS RULES ──────────────────────────────────────────────────────
    {
        "category": "business-rules",
        "title": "Promotion cycle — bi-weekly on Fridays",
        "content": """NGAS promotes Nimbus diagrams every other Friday.
Next promotion: April 4, 2026 (confirmed by user during pre-flight).
Promotions are batch — all diagrams with the same promotion date go together.
The app should default the MCPT view to the upcoming/current promotion date.

Two-week rule means:
- Cut-off for submitting diagrams is typically 1 week before the promotion date
- TRB review happens before the promotion date (Engineering Approved diagrams)
- Secondary packages must align their date to the Primary if there's an overlap conflict""",
        "tags": "promotion-cycle, bi-weekly, friday, cut-off, date",
        "source": "user-confirmed-preflight"
    },
    {
        "category": "business-rules",
        "title": "Authorization rules by diagram status",
        "content": """Authorization path depends on diagram Status field:

UNCLAIMED or CONCEPTUAL IMAGE or NTBC:
- NAT team (modelers) can authorize independently
- No external stakeholder needed
- Can promote without TRB

CLAIMED:
- Must work with the diagram Owner
- Owner must authorize
- Once owner authorizes, can promote

ENGINEERING APPROVED:
- TWO authorizers required: Owner (and/or Authorizer) + TRB Chair
- Must go through TRB process
- TRB Chair is the final/highest-priority sign-off
- Version number MUST be rolled before promotion

PROMOTION ONLY (Diagram Category, not Status):
- Diagram is being promoted without content changes
- Minimal process — no TRB needed regardless of status
- Excluded from 'Missing Authorizations' email filter""",
        "tags": "authorization-rules, unclaimed, claimed, engineering-approved, trb, promotion-only",
        "source": "user-confirmed-preflight-vba-analysis"
    },
    {
        "category": "business-rules",
        "title": "Overlap/disposition — Primary vs Secondary package conflict resolution",
        "content": """When two Model Change Packages have the SAME promotion date and overlapping diagrams:
- One package is designated 'Primary' — its promotion date stands
- Other package(s) are designated 'Secondary' — must adjust to match Primary date
- If Primary promotes later than Secondary, Secondary pushes to Primary's date

Column AG (manual field) in the tracker tracks this disposition.
The frontend should:
1. Flag when two packages on the same date share diagram GUIDs
2. Prompt user to assign Primary/Secondary disposition
3. Show warning banner when Secondary date doesn't match Primary""",
        "tags": "overlap, disposition, primary, secondary, conflict, promotion-date",
        "source": "user-confirmed-preflight"
    },
    {
        "category": "business-rules",
        "title": "User roles — three tiers with specific permissions",
        "content": """Three roles with enforced permissions (Q8 from preflight, confirmed):

IC (Individual Contributor):
- View ALL MCPT data (read-only on others' rows)
- Edit ONLY their own rows (matched by NAT Contact = their display name)
- Create/edit their own Weekly Tasking entries
- Upload SAP files for Charging/BOE
- Cannot delete, archive, or remove entries

Admin:
- All IC permissions
- Edit ANY row regardless of NAT Contact
- Add new rows (POST /add-entry)
- Archive rows (POST /archive-entry)
- Remove rows (POST /remove-entry)
- Manage user list (add/remove/edit roles)
- Manage dropdown lists (NAT contacts, categories)
- Send email notifications
- Grant temporary delegation ('acting as' permission with expiry)
- Configure SMTP and SAP settings

Director:
- All Admin permissions
- View charging/BOE module (admin-gated)
- Access consolidated tasking report
- Export executive Word document
- View all team members' tasking data

Delegation: Admin can grant an IC temporary Admin-level access with an expiry date.
Use case: team member going on vacation, someone needs to manage their diagrams.""",
        "tags": "roles, ic, admin, director, permissions, delegation",
        "source": "user-confirmed-preflight"
    },
    # ─── UI MODULES ──────────────────────────────────────────────────────────
    {
        "category": "ui-modules",
        "title": "Weekly Tasking Report — director executive output",
        "content": """Module replacing Weekly Tasking Report.xlsm.

Per-user data: Date, TaskID (auto), Category (dropdown, admin-managed), Description,
Status (In Progress / Complete / Blocked / On Hold), Notes, WeekStart (auto-calculated)

Director view: Consolidated ALL team members for selected week. Live updates on refresh.

Export formats (Q38 — all required, no stubs):
1. Word document (PRIMARY): python-docx. Formatted for paste into executive report template.
   - Section per team member
   - Summary table at top
   - Status color-coded
2. Excel: openpyxl, full data grid
3. HTML: styled, print-ready
4. Email body: formatted HTML, copy-to-clipboard for Outlook paste

The director's Word output must be structured for executive review.
Current manual process: director collects emails from 5 team members, formats manually.
New process: director opens app, selects week, clicks export — done.""",
        "tags": "weekly-tasking, director, word-export, python-docx, consolidated",
        "source": "user-confirmed-preflight"
    },
    {
        "category": "ui-modules",
        "title": "Notifications — both in-app AND email required",
        "content": """Q37 confirmed: BOTH in-app AND email notifications are required.
'There needs to be a way to force interaction with the tool and each team member likes a different method.'

In-app:
- Bell icon in nav bar with unread count badge
- Notification feed (expandable panel)
- Poll every 60 seconds (GET /api/notifications/unread)
- Mark as read on click
- Notifications persist in local notifications.db

Email (via SMTP relay):
- User-configurable: each user can set their email notification preferences
- Default: email for 'Package Complete' and 'Authorization Overdue'

Triggers:
- Package reaches 100% checklist → notify NAT Contact + Admin
- Authorization status → 'Promotion Ready' → notify Admin
- Diagram reaches DueDate with 'Not Signed Off' → notify Admin + NAT Contact
- DSL generation complete → notify initiating user
- New row added → notify Admin""",
        "tags": "notifications, in-app, email, bell-icon, triggers, poll",
        "source": "user-confirmed-preflight"
    },
    {
        "category": "ui-modules",
        "title": "PAL Checklist — 25 items, all Clerical category",
        "content": """PAL Checklist.xlsx contains exactly 25 checklist items (confirmed), all category 'Clerical'.
Items cover document review for TRB package preparation including:
- Document number formatting, front page fields
- Table of Contents, headers, pagination
- Revision letter, TRB date
- Nimbus spelling ('Nimbus' not 'NIMBUS'), hyperlinks to MASTER (not DRAFT)
- NGAS sector name ('Aeronautics' not 'Aerospace')
- No 'shalls' — state as fact
- Acronym list completeness
- Reference section validation

Frontend: Interactive checkbox list with save state per review session.
Sessions are named (e.g., 'ESM7800 Package Rev A') and stored locally.
Export: Word checklist document (python-docx).""",
        "tags": "pal-checklist, 25-items, review, trb-package, clerical",
        "source": "data-analysis-PAL-Checklist.xlsx"
    },
    {
        "category": "ui-modules",
        "title": "PAL Helper — SharePoint document browser by discipline",
        "content": """PALHelperFile.xlsx has 12 discipline tabs:
VE (Vehicle Engineering), T&E (Test & Evaluation), SW (Software), SRV (Survivability),
SE (Systems Engineering), PS (Product Support), PM&P, FS (Flight Sciences), EP&T,
Engineering, AWWSC, AvI (Avionics Integration)

Each sheet: Name, Title, Revision, Release Date, Owner, Author, Doc Type (or TD), File Size,
Item Type (Folder/Item), Path (sites/AS-ENG/PAL/{discipline}/...)

Doc Types: PAL Manual, Checklist, Formal Doc, Template, Appendix, CDM, Formal_Doc
SharePoint base path pattern: sites/AS-ENG/PAL/{DISCIPLINE}/

Frontend: 12 tabs, one per discipline. Table with sortable columns.
Click SharePoint path → open in browser if accessible on network.
Search across ALL disciplines simultaneously.
Filter by Doc Type.""",
        "tags": "pal-helper, sharepoint, disciplines, manuals, doc-types",
        "source": "data-analysis-PALHelperFile.xlsx"
    },
    # ─── DEPLOYMENT WINDOWS ──────────────────────────────────────────────────
    {
        "category": "deployment-windows",
        "title": "Windows deployment — AEGIS lessons applied to MCPT",
        "content": """Apply all AEGIS Windows deployment lessons to MCPT:
- Path: C:\\MCPT\\ (NOT OneDrive, no spaces, not a mapped drive)
- All open() calls: encoding='utf-8', errors='replace'
- setuptools: pin <81 (setuptools v82 removed pkg_resources)
- Windows-only deps: colorama, sspilib (must be in wheels/)
- daemon=False for threads + atexit cleanup (daemon=True breaks subprocess on Windows)
- SQLite WAL mode: PRAGMA journal_mode=WAL at connection time
- Port 5060 (5050 = AEGIS, avoid conflict)
- Start_MCPT.bat: detached process start
- NTLM auth: fresh requests.Session() per API call in threaded code (NEVER share sessions)
- File paths: use os.path.join() always, never string concatenation for paths""",
        "tags": "windows, deployment, utf8, wal, port-5060, aegis-lessons",
        "source": "aegis-lessons-applied"
    },
    {
        "category": "deployment-windows",
        "title": "SMTP relay setup — internal Exchange",
        "content": """Recommended email approach: internal Exchange SMTP relay (Q29 answer).
Python smtplib connects to internal Exchange SMTP server.
No credentials needed if Windows server is domain-joined AND IT whitelists the server IP.

Configuration (config.json):
  smtp_host: 'mail.northgrum.com' (or equivalent — confirm with IT)
  smtp_port: 25 (unauthenticated relay) or 587 (STARTTLS)
  from_address: 'mcpt-app@northgrum.com' (or similar service account)

One IT ticket needed: 'Please allow relay from IP {server_ip} on the Exchange SMTP server'
This is standard for application email on corporate networks.

Alternative if relay blocked: Microsoft Graph API (requires Azure AD app registration — IT involvement).
Start with SMTP relay; escalate to Graph API only if relay is rejected.""",
        "tags": "smtp, email, exchange, relay, it-ticket, smtplib",
        "source": "recommendation-q29"
    },
    {
        "category": "deployment-windows",
        "title": "Windows Auth — NTLM/Kerberos, no login screen",
        "content": """Q34 confirmed: Windows Integrated Authentication (NTLM/Kerberos).
Users NEVER type a password. Browser sends Windows credentials automatically on intranet.

Implementation options:
1. IIS + Windows Auth → IIS sets REMOTE_USER header → Flask reads it (simplest for IT-managed IIS)
2. sspilib in Flask middleware → handles NTLM handshake directly (no IIS required)
3. pywin32 → lower-level Windows API access

Recommended: sspilib approach (same as AEGIS auth patterns).
Session: Flask session stores windows_username + role for 8 hours.
On startup: call GET /get-user?username={windows_username} to get role from backend API.
If no user record: show 'Access Denied — contact administrator' page (not a crash).

Note: Edge and Firefox both support NTLM on Windows domain networks (Q20 answer).
Chrome on Windows also supports NTLM with proper intranet zone configuration.""",
        "tags": "ntlm, kerberos, windows-auth, sspilib, no-login-screen, iis",
        "source": "recommendation-q34"
    },
    # ─── PREFLIGHT QA ────────────────────────────────────────────────────────
    {
        "category": "preflight-qa",
        "title": "Scope — files being replaced vs reference data only",
        "content": """FILES BEING REPLACED (Q25):
- TrackerHelperV3.xlsm (main tracker — ModelChangePackageTracker sheet + dashboards + email macros)
- Charging.xlsm (SAP timesheet charging verification)
- DID Working.xlsm (Data Item Description government document tracker)
- GapAnalysis.xlsm (22-step gap analysis pipeline)
- NimbusBOE.xlsm (Basis of Estimate for NAT team hours)
- PAL Checklist.xlsx (25-item TRB package review checklist)
- PALHelperFile.xlsx (SharePoint PAL document library browser)
- Weekly Tasking Report.xlsm (individual + consolidated status reporting)

REFERENCE DATA ONLY (NOT replacing — these are Nimbus export reports fed into DB):
- Team_Dashboard-Diagrams.xlsx → Diagrams table
- Team_Dashboard-Authorization_Progress.xlsx → Authorizations table
- Team_Dashboard-Diagram_Change_Log.xlsx → Changes table
- Team_Dashboard-DraftDiagramLinks.xlsx → DiagramLinks table
- Team_Dashboard-Document_Links_Draft.xlsx → DocumentLinks table
- Team_Dashboard-Flow_Line_Links.xlsx → FlowLineLinks table
- Team_Dashboard-SIPOC.xlsx, Team_Dashboard-SIPOC_Master.xlsx → SIPOCs table
- Team_Dashboard-Resource.xlsx → Resources (not in SQL schema yet)
- Roles-SIPOC.xlsx → SIPOCs table
- DSLID.xlsx → DraftDSLID / MasterDSLID populated by backend process
- Document Registry Files List-All Documents.xlsx → DocumentLinks reference
- Linkto_FromObjectsReport.xlsx → DiagramLinks reference
- Needs Attachment Data Table Report.xlsx → DocumentLinks reference""",
        "tags": "scope, files-replaced, reference-data, team-dashboard, tracker",
        "source": "preflight-q25"
    },
    {
        "category": "preflight-qa",
        "title": "Timeline — 4 weeks, frontend only, backend separate team",
        "content": """Q26: Frontend must be built and running within 4 weeks.
Two developers separately building backend (SQLite DB + REST API).
App connects to their API — frontend is a client to their service.

Architecture confirmed (Q30/dev-email): REST API over HTTP, GET/POST.
The frontend does NOT have direct DB access — only through API.

SAP report ingestion (Q35): Daily desired, currently weekly. Smart column auto-detection.
Authorizer email list (Q36): Frequently changing — pulled from user list report.
Browser support (Q20): Edge and Firefox on Windows network.
Mobile: NOT required (Q24) — Windows desktop browser only.

Build order recommendation:
1. Auth layer + role enforcement (foundational)
2. MCPT table core (main value delivery)
3. DSL generator (critical automation)
4. Email automation (high business value)
5. Weekly Tasking (director priority)
6. Metrics modules (Charging, BOE, DID)
7. PAL modules
8. Admin panel
9. Integration testing (all 20 test cases in build_prompt.md)""",
        "tags": "timeline, 4-weeks, backend-separate, frontend-only, build-order",
        "source": "preflight-q26"
    },
    # ─── ADMIN SETTINGS ─────────────────────────────────────────────────────
    {
        "category": "business-rules",
        "title": "TRB Chair — admin-editable, currently Jamie Dunham",
        "content": """The Engineering Process TRB Chair name is an admin-configurable setting in MCPT.

Current value: "Jamie Dunham"
Location: Admin Panel → System Settings → TRB Chair Name

This value is used for:
1. The "Authorized by Eng Process TRB Chair" column in /get-mcpt output
   (determined by backend SQL: User = <TRB_chair> AND SignOffStatus = 'Signed Off')
2. Per-authorizer DSL file for the TRB Chair in the DSL Generator
3. Authorization Dashboard display — TRB Chair sign-off status column

When the TRB Chair changes:
- Admin updates the value in MCPT Admin Panel
- MCPT stores new value in local config (notifications.db or config.py constant)
- MCPT must also notify dev team to update backend SQL config parameter
  (pending dev team feature: support trb_chair parameter on /get-mcpt so the
   value can be passed dynamically without a backend redeploy)

MCPT local config key: trb_chair_name (string, default: "Jamie Dunham")""",
        "tags": "trb-chair, admin-settings, jamie-dunham, authorized-by-trb, configurable",
        "source": "user-confirmed-2026-04-01"
    },
    # ─── API CONTRACT CONFIRMED (2026-04-01) ────────────────────────────────
    {
        "category": "api-contract",
        "title": "CONFIRMED: /get-mcpt response format — 49 fields, Unix ms dates, three-state booleans",
        "content": """API contract confirmed 2026-04-01 from dev team response.

KEY FACTS:
- /get-mcpt returns ALL rows — no server-side filters. Filter promotion date client-side.
- Promotion Date = Unix MILLISECONDS timestamp (e.g. 1775174400000).
  Python: datetime.fromtimestamp(ts/1000). JS: new Date(ts)
- Booleans: THREE states — null (unknown/N/A), true, false. UI must handle all three.
  JS: val === null ? '—' : val ? '✓' : '✗'
- JSON keys have SPACES and special characters: use bracket notation in JS.
  e.g. row["SP Folder Created"], row["DSL UUID"]
- GUID = non-null primary key, always present.
- "DSL UUID" field = DraftDSLID (the identifier for DSL batch files and Draft Nimbus URL)
- "Last Promotion Date" = string "12/16/2025" (MM/DD/YYYY), NOT a timestamp
- No pagination currently. May be added if data grows.

API base URL: http://127.0.0.1:8000 (dev). Nimbus server IP:8000 (prod).
Auth: Open on internal network. Session token = future goal.
/get-user endpoint: BACKLOG — dev team building. Frontend must NOT manage user tables.
/get-trb: BACKLOG — POST with date param. Returns authorization progress data.
/edit-entry: JSON body {"guid": "...", "field": "FieldName", "value": "..."}.
  Field name must match exact API JSON key (e.g. "SP Folder Created" not "sp_folder_created").
/remove-entry: body is just {"guid": "..."}.""",
        "tags": "api-contract, confirmed, get-mcpt, boolean, unix-timestamp, filters, json-keys",
        "source": "dev-team-response-2026-04-01"
    },
    {
        "category": "api-contract",
        "title": "CONFIRMED: Tracker table schema — backend DB",
        "content": """The table is named 'Tracker' (NOT 'ModelChangePackageTracker').
/get-mcpt is a compiled SQL JOIN query reading from this table.

Tracker columns (from mcpt_query.sql analysis):
- DiagramGUID TEXT (FK → Diagrams.GUID)
- promotionDate → "Promotion Date" (Unix ms timestamp)
- diagramCategory → "Diagram Category (Identify Primary & Verify Selection)"
- modelChangePackageTitle → "Model Change Package Title"
- trbTitle → "PEACE Portal TRB Change Package Title OR Info Only"
- trbDescription → "PEACE Portal TRB Change Package Description"
- natContact → "NAT Contact"
- spFolderCreated → "SP Folder Created" (boolean)
- toolEntryCreated → "Tool Entry Created" (boolean)
- relatedFilesPosted → "Related Files Posted" (boolean)
- crPackageReady → "CR Package Ready" (boolean)
- docRegistryItemAttatched → "Doc Registry Item Attatched" (boolean, intentional typo)
- docRegistryURLUpdated → "Updated Doc Registry URL" (boolean)
- allDiagramsIncluded → "All Diagrams Included In Tracker" (boolean)
- peerReviewComplete → "Peer Review Complete" (boolean)
- notes → "Notes" (text)
- overlapDisposition → "Overlap Disposition" (boolean)

JOIN: LEFT JOIN Tracker t ON d.GUID = t.DiagramGUID
WHERE: WHERE d.GUID IN (SELECT DiagramGUID FROM Tracker) — only returns tracked diagrams.
Multiple Occurrences: YES if DiagramGUID appears > 1 time in Tracker (different promo cycles).

SQL placeholders (dev team will resolve):
- <TRB_chair> — Windows username of the Engineering Process TRB Chair authorizer
- <draft_url_sql> — Draft URL prefix string
- <master_url_sql> — Master URL prefix string
STRING_AGG used (non-standard SQLite) — dev team handles via Python custom aggregate.""",
        "tags": "tracker-table, schema, sql-query, placeholders, string-agg, multiple-occurrences",
        "source": "mcpt_query.sql-analysis-2026-04-01"
    },
    {
        "category": "nimbus",
        "title": "CORRECTED: GUID vs DraftDSLID vs MasterDSLID — three distinct identifiers",
        "content": """GUID is the CONCEPT-LEVEL key. It is shared by both Draft and Master versions of a diagram.
DraftDSLID and MasterDSLID are VERSION-SPECIFIC. They point to the Nimbus server page/entity.

Summary:
- GUID: identifies the diagram concept. Same value for Draft and Master. Use for ALL API/DB operations.
- DraftDSLID: points to the Draft version in Nimbus. Used in Draft URL + DSL batch files.
- MasterDSLID: points to the Master version in Nimbus. Used in Master URL + DSL batch files.

In /get-mcpt JSON:
- "GUID" = concept key (always present, non-null)
- "DSL UUID" = DraftDSLID (used in Draft URL + DSL files)
- "Master DSLID" = MasterDSLID (used in Master URL + batch files)

Draft and Master also live on DIFFERENT Nimbus map servers:
- Draft map GUID:  9820E23DD3204072819C50B7A2E57093
- Master map GUID: ED910D9C5F0C4F8491F8FD10A0C5695B

URLs:
- Draft: https://nimbusweb.../0:9820E23DD3204072819C50B7A2E57093.{DraftDSLID}
- Master: https://nimbusweb.../0:ED910D9C5F0C4F8491F8FD10A0C5695B.{MasterDSLID}

The /get-mcpt response pre-builds both "Draft Diagram Hyperlink" and "Master Diagram Hyperlink".
Use those directly — no URL construction needed in the UI.""",
        "tags": "guid, dslid, draft, master, nimbus-url, map-guid, identifier",
        "source": "user-clarification-2026-04-01"
    },
    {
        "category": "ui-modules",
        "title": "PAL Checklist — 25 confirmed items, all Clerical category",
        "content": """All 25 PAL Checklist items confirmed from PAL Checklist.xlsx in Reports repo.
ALL items are in the 'Clerical' category (document review for PAL manuals).

Items:
1. Document number formally reserved
2. Check front page is filled out properly (date = TRB date, doc number, doc owner)
3. Report title, document number, and revision letter in header
4. Table of Contents lowercase/uppercase check
5. Revision letter correct
6. Correct TRB date included
7. TOC correct
8. Roman Numerals for Table of Contents, up until page 1
9. All figures and tables numbered and referenced correctly
10. Margins, paragraph indentations and bullets/numbering correct
11. All sheets numbered correctly
12. Contract, Line Item Number, and Data Item correct
13. Distribution Statement correct
14. Nimbus spelled Nimbus not NIMBUS
15. Hyperlinks to Nimbus correct — MASTER version, not DRAFT
16. No "process documents" for PAL manuals
17. NGAS is Aeronautics sector, not Aerospace sector
18. No ref to old orgs (ISWR, DPTO → Aeronautics Systems)
19. No "shalls" — use "need", "will", "should", "do/does", "are/is"
20. Spell check passed + grammar suggestions reviewed
21. All references in reference section — correct
22. All docs in reference section are actually used
23. All hyperlinks work
24. First acronym use is spelled out
25. All acronyms in list are used""",
        "tags": "pal-checklist, 25-items, clerical, document-review, trb",
        "source": "PAL Checklist.xlsx-analysis-2026-04-01"
    },
    {
        "category": "ui-modules",
        "title": "PAL Helper — 12 discipline sheets, SharePoint paths confirmed",
        "content": """PALHelperFile.xlsx has 12 sheets, one per discipline:
VE (Vehicle Engineering), T&E (Test & Evaluation), SW (Software),
SRV (Survivability), SE (Systems Engineering), PS (Product Support),
PM&P (Program Management & Planning), FS (Flight Sciences),
EP&T (Engineering Processes & Tools), Engineering, AWWSC, AvI (Avionics & Integration)

Each sheet has columns: Name, Title, Revision, Release Date, Owner, Author, Doc Type,
TD (Technical Discipline), File Size, Item Child Count, Item Type, Path

SharePoint base path pattern: sites/AS-ENG/PAL/{discipline_code}/
Document types: Checklist, PAL Manual, Formal Doc, Template, Appendix
Item Types: Folder (subdirectory), Item (actual file)

Subfolders per discipline: Checklists, Formal Docs (or Formal_Docs), Manuals, Templates

For initial build: embed PALHelperFile as static JSON in the Flask app.
No live SharePoint queries needed — just serve the embedded data and construct links.
Live SP queries are a future enhancement.

SharePoint URL construction: https://{sp_host}/{path}/{name}""",
        "tags": "pal-helper, disciplines, sharepoint, 12-disciplines, static-data",
        "source": "PALHelperFile.xlsx-analysis-2026-04-01"
    },
    {
        "category": "api-contract",
        "title": "Authorization Progress data structure — future /get-trb response format",
        "content": """Team_Dashboard-Authorization_Progress.xlsx confirmed structure for future /get-trb endpoint.

Columns: GUID, Level, Authorization, Diagram Type, User, Group, Resource,
Sign Off Status, Sign Off Date, Sequence, Request From, Due Date, Diagram Title,
Contains Drill Down?, Date, Active State

Key values:
- Authorization: "Authorization Pending - 2/13/2026" or "Promotion Ready - 2/6/2026" (date embedded)
  NOTE: This is the DETAILED format — different from the MCPT main table "Update Pending" simple string.
- Sign Off Status: "Not Signed Off", "Accepted"
- Active State: "Active" or "Inactive"
- Sequence: integer (1 = first to sign)
- Request From: display name of who requested authorization

/get-trb will be a POST with date parameter. Status: BACKLOG.
Use this structure to design the Authorization Dashboard (Module 2) even before /get-trb is built.
Can query Authorizations table subset from the auth data included in /get-mcpt
(AuthorizationSent, AuthorizationAccepted, TotalAuthorizations fields).""",
        "tags": "authorization-progress, get-trb, sign-off, sequence, active-state, backlog",
        "source": "Team_Dashboard-Authorization_Progress.xlsx-2026-04-01"
    },
    {
        "category": "vba-logic",
        "title": "Weekly Tasking Report VBA — Tasks table structure and email report",
        "content": """Weekly Tasking Report.xlsm VBA (Version 3.1 FINAL).

Tasks table (Excel ListObject named 'Tasks') columns:
- A: Date (auto-filled with today when Col D is edited)
- B: TaskID (auto-incrementing integer, previous + 1)
- C: Category/type (data validation dropdown, copied from previous row)
- D: TRIGGER COLUMN (editing this auto-fills A and B)
- E: Secondary field (data validation, copied from previous row)

Source sheet: 'Source'. Historical archive: 'Historical' sheet.
Settings: 'ReportSettings' sheet (recipients, thresholds, max items = 10, long-running = 14 days).

Main function: SendWeeklyExecutiveReport()
1. Load settings from ReportSettings
2. Calculate current week start (Monday)
3. Collect report data (new tasks, completed, overdue, backlog trend)
4. Spell check if enabled
5. Show confirmation dialog
6. Build HTML email body with executive summary + task tables
7. Send via Outlook.Application CreateObject
8. Archive completed → Historical sheet
9. Delete completed from Source

Features: Executive summary auto-generated, backlog trend vs last week,
due date highlighting, spell check, historical archive, preview mode.

MCPT Module 4 replacement: Web form (no Excel). ICs submit tasks via browser.
Preserve: auto-increment ID, week-start calculation, executive summary logic.""",
        "tags": "weekly-tasking, tasks-table, executive-report, auto-increment, outlook, vba",
        "source": "Weekly Tasking Report.xlsm-analysis-2026-04-01"
    },
]


def build_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing DB: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE knowledge_fts USING fts5(
            title, content, category, tags,
            content='knowledge',
            content_rowid='id'
        )
    """)
    conn.execute("PRAGMA journal_mode=WAL")

    now = datetime.now().isoformat()[:19]
    for entry in KNOWLEDGE:
        conn.execute("""
            INSERT INTO knowledge (category, title, content, tags, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (entry['category'], entry['title'], entry['content'],
              entry.get('tags', ''), entry.get('source', ''), now))

    # Rebuild FTS index
    conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
    cats = conn.execute(
        "SELECT category, COUNT(*) FROM knowledge GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()

    print(f"\nBuilt {DB_PATH}")
    print(f"Total entries: {count}")
    print(f"\nBy category:")
    for cat, n in cats:
        print(f"  {cat:<30} {n:>3} entries")


if __name__ == '__main__':
    build_db()
    print("\nDone. Search with: python3 search_knowledge.py \"your query\"")
