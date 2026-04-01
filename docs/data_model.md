# MCPT Data Model

Complete data model documentation: SQL schemas, Excel field mappings, data formats.

---

## Backend Database Tables (Separate Dev Team)

Source: `nicholasgeorgeson-prog/Reports` GitHub repo, `data/sql_schemas/` folder.

### Diagrams

Primary table. One row per Nimbus diagram. GUID is the primary key throughout the system.

```sql
CREATE TABLE "Diagrams" (
    "GUID"              TEXT NOT NULL,       -- Primary key; used in URLs and all API calls
    "MapName"           TEXT,                -- Nimbus map name
    "DraftLevel"        TEXT,                -- e.g., "1.3.8 Draft Copy"
    "MasterLevel"       TEXT,                -- e.g., "1.3.8"
    "DiagramType"       TEXT,                -- Type of diagram
    "Title"             TEXT,                -- Display name
    "Notation"          TEXT,                -- Diagram notation style
    "Author"            TEXT,                -- Original author
    "Owner"             TEXT,                -- Current owner
    "DraftVersion"      TEXT,
    "MasterVersion"     TEXT,
    "Date"              TIMESTAMP,
    "DraftAuthorization"  TEXT,              -- e.g., "Authorization Pending - 2/13/2026"
    "MasterAuthorization" TEXT,
    "DraftTemplate"     TEXT,
    "MasterTemplate"    TEXT,
    "DraftModified"     TIMESTAMP,
    "MasterModified"    TIMESTAMP,
    "DraftUserModified" TEXT,
    "MasterUserModified" TEXT,
    "DrillDown"         INTEGER,             -- 1 if diagram has child diagrams
    "Description"       TEXT,
    "Status"            TEXT,                -- MCPT tracking status
    "Organization"      TEXT,
    "URL"               TEXT,
    "Attatchments"      TEXT,                -- Note: intentional typo in schema
    "PrimaryContact"    TEXT,
    "ParentGUID"        TEXT,                -- FK → Diagrams(GUID)
    "Objects"           INTEGER,
    "DraftMapPath"      TEXT,
    "MasterMapPath"     TEXT,
    "DraftDSLID"        TEXT,                -- CRITICAL: NOT the same as GUID
    "MasterDSLID"       TEXT,                -- CRITICAL: NOT the same as GUID
    PRIMARY KEY("GUID"),
    CONSTRAINT "ParentGUID_CK" FOREIGN KEY("ParentGUID") REFERENCES "Diagrams"("GUID")
);
```

### Authorizations

One row per authorizer per diagram. Tracks sign-off status for the authorization workflow.

```sql
CREATE TABLE "Authorizations" (
    "DiagramGUID"   TEXT NOT NULL,    -- FK → Diagrams(GUID)
    "Type"          TEXT NOT NULL DEFAULT 'Draft',
    "User"          TEXT NOT NULL,    -- Authorizer's username
    "Authorization" TEXT,             -- Authorization level/type
    "SignOffStatus" TEXT,             -- e.g., "Approved", "Pending"
    "SignOffDate"   TIMESTAMP,
    "Sequence"      INTEGER,          -- Order of sign-off (1 = first to sign)
    "RequestFrom"   TEXT,             -- Who requested authorization
    "DueDate"       TIMESTAMP,
    "Date"          TIMESTAMP,
    "ActiveState"   TEXT,
    PRIMARY KEY("DiagramGUID","User","Type"),
    FOREIGN KEY("DiagramGUID") REFERENCES "Diagrams"("GUID") ON DELETE CASCADE
);
```

### Changes

Change log entries. One row per change per diagram.

```sql
CREATE TABLE "Changes" (
    "DiagramGUID"       TEXT NOT NULL,   -- FK → Diagrams(GUID)
    "ID"                INTEGER NOT NULL,
    "Type"              TEXT DEFAULT 'Draft',
    "Date"              TIMESTAMP,
    "Version"           NUMERIC,
    "ChangeDescription" TEXT,            -- Free text change description
    "User"              TEXT,
    PRIMARY KEY("DiagramGUID","ID","Type"),
    FOREIGN KEY("DiagramGUID") REFERENCES "Diagrams"("GUID") ON DELETE CASCADE
);
```

### DiagramLinks

Relationships between diagrams.

```sql
CREATE TABLE "DiagramLinks" (
    "UUID"       INTEGER UNIQUE,
    "FromGUID"   TEXT,    -- FK → Diagrams(GUID)
    "ToGUID"     TEXT,    -- FK → Diagrams(GUID)
    "LinkGUID"   TEXT,
    "ActivityID" TEXT,
    "Type"       TEXT DEFAULT 'Draft',
    "ObjectText" TEXT,
    "Exists"     INTEGER,
    PRIMARY KEY("UUID" AUTOINCREMENT)
);
```

### DocumentLinks

External document attachments to diagrams.

```sql
CREATE TABLE "DocumentLinks" (
    "UUID"              INTEGER NOT NULL UNIQUE,
    "DiagramGUID"       TEXT,       -- FK → Diagrams(GUID)
    "Type"              TEXT,
    "DocumentNo"        INTEGER,
    "InRegistry"        INTEGER,
    "ActivityID"        TEXT,
    "LinkTitle"         TEXT,
    "FileName"          TEXT,
    "FileType"          TEXT,
    "Exists"            INTEGER,
    "DocumentOwner"     TEXT,
    "ActivityResources" TEXT,
    "ObjectText"        TEXT,
    PRIMARY KEY("UUID" AUTOINCREMENT)
);
```

### FlowLineLinks

Flow line connections between diagrams (process flow arrows that connect to other diagrams).

```sql
CREATE TABLE "FlowLineLinks" (
    "UUID"             INTEGER UNIQUE,
    "FromGUID"         TEXT,     -- FK → Diagrams(GUID)
    "ToGUID"           TEXT,     -- FK → Diagrams(GUID)
    "LinkGUID"         TEXT,
    "Type"             TEXT,
    "LinkType"         TEXT,
    "LinkTitle"        TEXT,
    "ToMapName"        TEXT,
    "ToLevel"          TEXT,
    "Exists"           INTEGER,
    "ToLineText"       TEXT,
    "ToActivityText"   TEXT,
    "FromActivityText" TEXT,
    "FromLineText"     TEXT,
    PRIMARY KEY("UUID" AUTOINCREMENT)
);
```

### SIPOCs

SIPOC (Suppliers, Inputs, Process, Outputs, Customers) data per diagram activity.

```sql
CREATE TABLE "SIPOCs" (
    "DiagramGUID"        TEXT NOT NULL,
    "Type"               TEXT NOT NULL,
    "ObjectID"           INTEGER NOT NULL,
    "ActivityID"         INTEGER,
    "Inputs"             TEXT,
    "ActivityText"       TEXT,
    "Outputs"            TEXT,
    "Resources"          TEXT,
    "ActivityCommentary" TEXT,
    "Attatchments"       TEXT,    -- Note: intentional typo
    "ActivityStatements" TEXT,
    "TaskType"           TEXT,
    "Suppliers"          TEXT,
    "Customers"          TEXT,
    PRIMARY KEY("DiagramGUID","Type","ObjectID"),
    -- ⚠️ BUG: FK references Diagrams(GUID, Type) but Diagrams has no Type column
    CONSTRAINT "DiagramGUID_CK" FOREIGN KEY("DiagramGUID","Type") REFERENCES "Diagrams"("GUID","Type")
);
```

### Storyboards

Storyboard steps for diagram activities.

```sql
CREATE TABLE "Storyboards" (
    "UUID"            INTEGER NOT NULL UNIQUE,
    "DiagramGUID"     TEXT,
    "ActivityNumber"  INTEGER,
    "Type"            TEXT,
    "StoryboardTitle" TEXT,
    "StepNumber"      INTEGER,
    "StepType"        TEXT,
    "StoryboardOwner" TEXT,
    PRIMARY KEY("UUID" AUTOINCREMENT),
    -- ⚠️ BUG: same composite FK bug as SIPOCs
    CONSTRAINT "DiagramGUID_CK" FOREIGN KEY("DiagramGUID","Type") REFERENCES "Diagrams"("GUID","Type")
);
```

---

## Known Schema Bugs

**SIPOCs and Storyboards composite FK bug**:
- Both tables define: `FOREIGN KEY("DiagramGUID","Type") REFERENCES "Diagrams"("GUID","Type")`
- But `Diagrams` table has NO `Type` column — only `GUID` as primary key
- If SQLite FK enforcement is enabled (`PRAGMA foreign_keys = ON`), this FK will fail validation
- Should be: `FOREIGN KEY("DiagramGUID") REFERENCES "Diagrams"("GUID")`
- Reported in `docs/developer_questions_email.md` Question #9

---

## /get-mcpt Response Schema — CONFIRMED 2026-04-01

**No MCPT table exists** — `/get-mcpt` is a compiled SQL JOIN query. There is no `ModelChangePackageTracker` table. The data is assembled from Diagrams, Authorizations, and related tables.

**Primary key**: `GUID` (non-null string, always present)

**Response format**: JSON array of objects. All keys use the original Excel column names (with spaces and special characters).

**Boolean fields**: Three states — `null` (unknown/N/A), `true`, `false`

**Promotion Date field**: Unix milliseconds timestamp (e.g., `1775174400000`)
- Python: `datetime.fromtimestamp(row["Promotion Date"] / 1000)`
- JavaScript: `new Date(row["Promotion Date"])`

### Complete Field List (49 fields)

| JSON Key (exact) | Python Pydantic Name | Type | Notes |
|---|---|---|---|
| `"Promotion Date"` | `Promotion_Date` | Optional[datetime] / Unix ms int | Current cycle date |
| `"Level"` | `Level` | Optional[str] | e.g., `"1.11.2.1"` (without "Draft Copy") |
| `"Diagram Category (Identify Primary & Verify Selection)"` | `Diagram_Category_...` | Optional[str] | e.g., `"Eng TRB Return (primary)"` |
| `"Model Change Package Title"` | `Model_Change_Package_Title` | Optional[str] | MCP title |
| `"PEACE Portal TRB Change Package Title OR Info Only"` | `PEACE_Portal_TRB_Change_Package_Title_OR_Info_Only` | Optional[str] | TRB title |
| `"PEACE Portal TRB Change Package Description"` | `PEACE_Portal_TRB_Change_Package_Description` | Optional[str] | TRB description |
| `"NAT Contact"` | `NAT_Contact` | Optional[str] | e.g., `"David"` |
| `"SP Folder Created"` | `SP_Folder_Created` | Optional[bool] | null/true/false |
| `"Tool Entry Created"` | `Tool_Entry_Created` | Optional[bool] | null/true/false |
| `"Related Files Posted"` | `Related_Files_Posted` | Optional[bool] | null/true/false |
| `"CR Package Ready"` | `CR_Package_Ready` | Optional[bool] | null/true/false |
| `"Doc Registry Item Attatched"` | `Doc_Registry_Item_Attatched` | Optional[bool] | Typo is intentional |
| `"Updated Doc Registry URL"` | `Updated_Doc_Registry_URL` | Optional[bool] | null/true/false |
| `"All Diagrams Included In Tracker"` | `All_Diagrams_Included_In_Tracker` | Optional[bool] | null/true/false |
| `"Peer Review Complete"` | `Peer_Review_Complete` | Optional[bool] | null/true/false |
| `"Notes"` | `Notes` | Optional[str] | Free text, can be long |
| `"DSL UUID"` | `DSL_UUID` | Optional[str] | = DraftDSLID. Used in Draft URL and DSL batch files |
| `"Diagram Level"` | `Diagram_Level` | Optional[str] | e.g., `"1.11.2.1 Draft Copy"` |
| `"Draft Diagram Hyperlink"` | `Draft_Diagram_Hyperlink` | Optional[str] | Pre-built URL using Draft map GUID + DraftDSLID |
| `"Master Diagram Hyperlink"` | `Master_Diagram_Hyperlink` | Optional[str] | Pre-built URL using Master map GUID + MasterDSLID |
| `"Diagram Title"` | `Diagram_Title` | Optional[str] | Display name |
| `"Diagram Ownership by Function / CoP"` | `Diagram_Ownership_by_Function_CoP` | Optional[str] | e.g., `"AW"` |
| `"Draft Status"` | `Draft_Status` | Optional[str] | e.g., `"Engineering Approved"` |
| `"Master Status"` | `Master_Status` | Optional[str] | Same source as Draft Status in query |
| `"Draft Template"` | `Draft_Template` | Optional[str] | e.g., `"2c_(In-work) Engineering Approved"` |
| `"Master Template"` | `Master_Template` | Optional[str] | e.g., `"1c_(Standard) Engineering Approved"` |
| `"Owner"` | `Owner` | Optional[str] | e.g., `"Kent Nelson"` |
| `"Version"` | `Version` | Optional[str] | Draft version number (string) |
| `"Master Version"` | `Master_Version` | Optional[str] | Master version number (string) |
| `"Authorization"` | `Authorization` | Optional[str] | e.g., `"Update Pending"` |
| `"Authorizer"` | `Authorizer` | Optional[str] | Authorizer's name (single, current) |
| `"Overlap Disposition"` | `Overlap_Disposition` | Optional[bool] | null/true/false |
| `"Multiple Occurrences"` | `Multiple_Occurrences` | Optional[str] | `"Yes"` or `"No"` |
| `"AuthorizationSent"` | `AuthorizationSent` | Optional[int] | Count sent |
| `"AuthorizationAccepted"` | `AuthorizationAccepted` | Optional[int] | Count accepted |
| `"TotalAuthorizations"` | `TotalAuthorizations` | Optional[int] | Total required |
| `"Authorized by POC"` | `Authorized_by_POC` | Optional[str] | `"Yes"` or `"No"` |
| `"Authorized by Eng Process TRB Chair"` | `Authorized_by_Eng_Process_TRB_Chair` | Optional[str] | `"Yes"`, `"No"`, or `"N/A"` |
| `"Last Promotion Date"` | `Last_Promotion_Date` | Optional[str] | String `"12/16/2025"` (MM/DD/YYYY) |
| `"Post-Promotion Template Changed in Draft (Not In-work)"` | `Post_Promotion_Template_Changed_in_Draft_Not_In_work` | Optional[str] | `"Yes"` or `"No"` |
| `"Post-Promotion Template Changed in Master (Not In-work)"` | `Post_Promotion_Template_Changed_in_Master_Not_In_work` | Optional[str] | `"Yes"` or `"No"` |
| `"Non-engineering Approved Diagram Templates"` | `Non_engineering_Approved_Diagram_Templates` | Optional[str] | `"Good"` or `"Warning"` |
| `"Links from Draft to Archive"` | `Links_from_Draft_to_Archive` | Optional[int] | Error count |
| `"Links from Draft to Master"` | `Links_from_Draft_to_Master` | Optional[int] | Link count |
| `"Links from Master to Draft"` | `Links_from_Master_to_Draft` | Optional[int] | Error — should be 0 |
| `"Links from Sandbox"` | `Links_from_Sandbox` | Optional[int] | Error — should be 0 |
| `"Diagram Links Errors"` | `Diagram_Links_Errors` | Optional[int] | Error count |
| `"Document Links Errors"` | `Document_Links_Errors` | Optional[int] | Error count |
| `"Broken FLL"` | `Broken_FLL` | Optional[int] | Broken flow line links count |
| `"Total Errors"` | `Total_Errors` | Optional[int] | Sum of all error counts |
| `"URL"` | `URL` | Optional[str] | e.g., `"AW-0100"` — short reference code, or null |
| `"Storyboard Impact"` | `Storyboard_Impact` | Optional[str] | Comma-separated storyboard names |
| `"Changes Since Last Promotion"` | `Changes_Since_Last_Promotion` | Optional[int] | Count |
| `"Change Log Entries"` | `Change_Log_Entries` | Optional[str] | Bullet-point string with Unicode bullets (•) |
| `"Master DSLID"` | `Master_DSLID` | Optional[str] | Used in Master URL and batch files |
| `"GUID"` | `GUID` | str (non-null) | Primary key — always present, never null |

### Accessing Keys in JavaScript

Because keys have spaces and special characters, always use bracket notation:
```javascript
row["DSL UUID"]                                          // DraftDSLID
row["SP Folder Created"]                                 // boolean or null
row["Diagram Category (Identify Primary & Verify Selection)"]  // category string
row["Authorized by Eng Process TRB Chair"]               // "Yes"/"No"/"N/A"
new Date(row["Promotion Date"])                          // convert Unix ms to Date
```

### Three-State Boolean Rendering

Boolean fields (`SP Folder Created`, `Tool Entry Created`, etc.) have three values:
```javascript
function renderBool(val) {
    if (val === null || val === undefined) return '—';     // Unknown/N/A
    return val ? '✓' : '✗';                               // true/false
}
```

---

## Tracker Table (Backend DB — CONFIRMED from mcpt_query.sql)

The table is named `Tracker` (not `ModelChangePackageTracker`). The `/get-mcpt` SQL JOIN query reads from this table. Confirmed columns from `mcpt_query.sql`:

```sql
-- Tracker table columns (inferred from SQL SELECT aliases)
SELECT
    t.promotionDate,           -- Promotion Date (Unix ms timestamp)
    t.diagramCategory,         -- "Diagram Category (Identify Primary & Verify Selection)"
    t.modelChangePackageTitle, -- "Model Change Package Title"
    t.trbTitle,                -- "PEACE Portal TRB Change Package Title OR Info Only"
    t.trbDescription,          -- "PEACE Portal TRB Change Package Description"
    t.natContact,              -- "NAT Contact"
    t.spFolderCreated,         -- "SP Folder Created" (boolean)
    t.toolEntryCreated,        -- "Tool Entry Created" (boolean)
    t.relatedFilesPosted,      -- "Related Files Posted" (boolean)
    t.crPackageReady,          -- "CR Package Ready" (boolean)
    t.docRegistryItemAttatched,-- "Doc Registry Item Attatched" (boolean, note typo)
    t.docRegistryURLUpdated,   -- "Updated Doc Registry URL" (boolean)
    t.allDiagramsIncluded,     -- "All Diagrams Included In Tracker" (boolean)
    t.peerReviewComplete,      -- "Peer Review Complete" (boolean)
    t.notes,                   -- "Notes" (text)
    t.overlapDisposition,      -- "Overlap Disposition" (boolean)
    t.DiagramGUID              -- FK → Diagrams(GUID)
```

The query JOIN: `LEFT JOIN Tracker t ON d.GUID = t.DiagramGUID`
The query WHERE: `WHERE d.GUID IN (SELECT DiagramGUID FROM Tracker)` — only returns diagrams in Tracker.

**Multiple Occurrences logic**: A diagram can appear multiple times in Tracker (different promotion cycles). The `Multiple Occurrences` field = 'Yes' if count > 1 for the same DiagramGUID.

**Placeholders in SQL** (dev team will resolve before production):
- `<TRB_chair>` — the username of the Engineering Process TRB Chair authorizer
- `<draft_url_sql>` — Draft URL prefix (resolves to `https://nimbusweb.../0:9820E23DD3204072819C50B7A2E57093.`)
- `<master_url_sql>` — Master URL prefix (resolves to `https://nimbusweb.../0:ED910D9C5F0C4F8491F8FD10A0C5695B.`)

**STRING_AGG**: Used in the SQL (non-standard SQLite). Dev team is handling this via Python sqlite3 custom aggregate or SQLite extension.

## Team_Dashboard-Authorization_Progress.xlsx — Column Structure

This file represents what `/get-trb` (backlog endpoint) will return:

| Column | Example | Notes |
|---|---|---|
| `GUID` | `E12D5679F8834820AF9E6EDE234B710A` | Diagram GUID |
| `Level` | `1.12.14.3 Draft Copy` | Draft level string |
| `Authorization` | `Authorization Pending - 2/13/2026` | Status + embedded date string |
| `Diagram Type` | `Standard` | Nimbus diagram type |
| `User` | `Kathryn McKenzie` | Authorizer name |
| `Group` | `` | (often empty) |
| `Resource` | `` | (often empty) |
| `Sign Off Status` | `Not Signed Off`, `Accepted` | Authorization state |
| `Sign Off Date` | `2/6/2026` | When signed (empty if not yet signed) |
| `Sequence` | `1` | Order in authorization chain |
| `Request From` | `Chad Lauffer` | Who requested authorization |
| `Due Date` | `2/13/2026` | Deadline |
| `Diagram Title` | `Manage Space Utilization Requirements` | Full diagram title |
| `Contains Drill Down?` | `Yes` | Whether diagram has children |
| `Date` | `3/21/2025` | Date record was created |
| `Active State` | `Active`, `Inactive` | Authorization lifecycle state |

**Note**: `Authorization` format here IS `"Authorization Pending - 2/13/2026"` — different from the MCPT main table's simpler `"Update Pending"` value.

## Local Database (notifications.db)

SQLite WAL mode. Managed entirely by MCPT Flask app. Does NOT live in the backend team's DB.

```sql
CREATE TABLE notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT NOT NULL,          -- Windows username
    type        TEXT NOT NULL,          -- 'row_edit', 'auth_request', 'promo_ready', 'system'
    message     TEXT NOT NULL,
    target_guid TEXT,                   -- Related diagram GUID (nullable)
    read        INTEGER DEFAULT 0,      -- 0=unread, 1=read
    created_at  TIMESTAMP DEFAULT (datetime('now'))
);
```

---

## Key Data Formats

### Authorization String Format
```
"Authorization Pending - 2/13/2026"   → pending, date = Feb 13 2026
"Promotion Ready - 2/6/2026"          → ready, date = Feb 6 2026
"Authorized"                           → fully authorized
""                                     → not yet requested
```

**Parse with**:
```python
import re
AUTH_PATTERN = re.compile(
    r'^(Authorization Pending|Promotion Ready|Authorized)\s*(?:-\s*(\d+/\d+/\d+))?$'
)
```

### Level Format
```
"1.3.8 Draft Copy"   → Draft, level 3
"1.3.8"              → Master, level 3
"1"                  → Level 1
"1.3"                → Level 2
```

**Parse level number**: `level_num = level.replace(' Draft Copy', '').count('.') + 1`

### Nimbus Deep Link URL
```
https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:{MAP_GUID}.{DIAGRAM_GUID}
```

- MAP_GUID = `9820E23DD3204072819C50B7A2E57093` (hardcoded, same for all NGAS diagrams)
- DIAGRAM_GUID = the GUID column value (e.g., `ACDF1AE9385543888E91381F30D3F806`)

### GUID Format
Uppercase hexadecimal, 32 characters, no dashes:
```
ACDF1AE9385543888E91381F30D3F806
```

### DSL File Format
Plain text, one DSLID per line:
```
DSLID001
DSLID002
DSLID003
```

### SAP Data Formats
- Hours column format: `"8.0 H"` → strip `" H"` → `8.0`
- Charge order: `"9L99G054"` (string, admin-configurable)
- Fiscal month: typically `"2026-03"` or `"Mar-26"` (confirm from actual SAP export)
- Supp codes: `"PTO"`, `"HOL"`, `"UNP"`, `"NWRK"`, `"ADMN"`, direct charge codes

---

## Excel Source File Structure

### Team_Dashboard-Diagrams.xlsx (in Reports repo)
- 194 rows (current dataset as of research date)
- 34 columns (confirmed from DSLID.xlsx cross-reference)
- Contains pre-built `Hyperlink` column with Nimbus deep links
- Columns map to `Diagrams` table fields (see `docs/vba_analysis.md` for full mapping)

### DSLID.xlsx (in Reports repo)
4 columns:
- `Draft Diagram Levels` — draft level notation
- `Draft Diagram DSLID` — DSLID for the Draft version
- `Master Diagram Levels` — master level notation
- `Master Diagram DSLID` — DSLID for the Master version

**Confirms**: DraftDSLID and MasterDSLID are separate values, and both differ from GUID.

---

## Data Relationships

```
Diagrams (GUID PK)
    ├── Authorizations (DiagramGUID FK) — one per authorizer per diagram
    ├── Changes (DiagramGUID FK) — change log entries
    ├── DiagramLinks (FromGUID, ToGUID FK) — diagram-to-diagram relationships
    ├── DocumentLinks (DiagramGUID FK) — attached documents
    ├── FlowLineLinks (FromGUID, ToGUID FK) — flow connections
    ├── SIPOCs (DiagramGUID FK) — SIPOC activity data
    └── Storyboards (DiagramGUID FK) — storyboard steps
```

All child tables CASCADE DELETE on parent removal (except DiagramLinks → ON DELETE CASCADE is defined per FK).
