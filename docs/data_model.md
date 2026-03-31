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

## MCPT Tracking Table (Pending Dev Team Response)

The MCPT tracking table structure is not yet confirmed — awaiting backend dev team response (Question #2 in developer_questions_email.md). Based on VBA analysis and Excel column mapping, the table is expected to include:

**Derived from Diagrams table** (via JOIN or embedded):
- GUID, Title, DraftLevel, MasterLevel, Status, Organization, Owner, DraftAuthorization, DraftDSLID

**MCPT-specific tracking columns**:
- `SP_Folder_Created` (boolean) — SharePoint folder created for this diagram
- `Tool_Entry_Created` (boolean) — Tool entry exists in the tool registry
- `IC_Assigned` (text) — Windows username of the assigned Individual Contributor
- `Notes` (text) — Free text notes field (can be long)
- `Change_Log` (text) — History of changes made in MCPT

**Response type questions** (Question #1 in developer_questions_email.md):
- Boolean columns: Do they return `true/false`, `"Yes"/"No"`, or `1/0`?
- Does endpoint return all records or only current (non-archived)?
- Is there a promotion_date filter parameter?

---

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
