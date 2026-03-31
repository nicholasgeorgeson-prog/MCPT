# TIBCO Nimbus Research Findings

Research conducted 2026-03-31 in support of MCPT pre-flight planning.

---

## What Is TIBCO Nimbus?

TIBCO Nimbus is an enterprise business process management (BPM) tool designed for process mapping, documentation, and governance. It organizes process maps hierarchically, supports version control (Draft/Master), and has a built-in authorization workflow for promoting diagrams from Draft to Master.

**NGAS usage**: The NAT (Nimbus Admin Team) at Northrop Grumman Aeronautics Systems manages TIBCO Nimbus diagram assets for the NGAS organization. MCPT is the tracking and automation layer on top of Nimbus.

---

## End of Life

**TIBCO Nimbus reached End of Life on September 1, 2025.**

NGAS is operating on extended legacy support — the product still runs but receives no new updates. A replacement tool selection is expected within 2-3 years.

**MCPT implication**: All Nimbus-specific code (URLs, DSL format, GUID handling) is behind an abstraction layer (`nimbus_adapter.py`). When Nimbus is replaced, only the adapter changes.

---

## Nimbus Architecture

### Map Hierarchy
Nimbus organizes diagrams in a hierarchical map structure:
- **L1**: Top-level process areas
- **L2**: Sub-processes
- **L3**: Detailed process maps
- **L4**: Procedure-level maps

All NGAS diagrams live in a single map identified by the Map GUID: `9820E23DD3204072819C50B7A2E57093`

### Diagram Levels
Level notation: `"1.3.8"` — each dot adds a level.
- Level 1 = one number (e.g., `"1"`)
- Level 2 = two numbers (e.g., `"1.3"`)
- Level 3 = three numbers (e.g., `"1.3.8"`)
- Draft copies append `" Draft Copy"`: `"1.3.8 Draft Copy"`

**Parsing level number**: `level_num = len(level.split('.'))` where level = `"1.3.8"` → 3

### Diagram Identifiers
Two completely different identifiers exist for every diagram:

| Identifier | Purpose | Example | Where Used |
|---|---|---|---|
| `GUID` | Primary key in DB; used in Nimbus deep-link URLs | `ACDF1AE9385543888E91381F30D3F806` | URLs, API calls, DB lookups |
| `DSLID` | Used in `.dsl` batch operation files | (different format) | Nimbus Batch Server operations |

**CRITICAL**: Never interchange GUID and DSLID. They are not the same value.

---

## Nimbus Deep Link URL

```
https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:{MAP_GUID}.{DIAGRAM_GUID}
```

**Hardcoded Map GUID**: `9820E23DD3204072819C50B7A2E57093`

**Example full URL**:
```
https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:9820E23DD3204072819C50B7A2E57093.ACDF1AE9385543888E91381F30D3F806
```

The `Team_Dashboard-Diagrams.xlsx` file in the Reports repo has a pre-built `Hyperlink` column with this exact format, confirming the URL pattern.

---

## Diagram Lifecycle

```
Draft Created
    │
    ▼
Claimed (IC takes ownership)
    │
    ▼
Engineering Approved (IC marks complete)
    │
    ▼
Authorization Requested
    │
    ▼ (each authorizer must sign off — sequential, unanimous)
Authorization Pending → Promotion Ready
    │
    ▼
Batch Server Promotes Draft → Master
    │
    ▼
Master Published
```

### Diagram Statuses (MCPT Tracking)
- `Unclaimed` — no IC has taken this diagram
- `Claimed` — an IC has claimed it and is working it
- `Engineering Approved` — IC marked it ready for authorization
- `Conceptual Image` — special type, no change needed
- `Not To Be Claimed` — excluded from this promotion cycle

---

## Authorization System

### Authorization Field Format
The `DraftAuthorization` field in the Diagrams table (and the corresponding MCPT tracking column) stores authorization status as a string with an embedded date:

```
"Authorization Pending - 2/13/2026"
"Promotion Ready - 2/6/2026"
"Authorized"
""  (empty = not yet requested)
```

**Parsing**: Use regex to extract status and date:
```python
import re
match = re.match(r'^(Authorization Pending|Promotion Ready|Authorized)\s*(?:-\s*(\d+/\d+/\d+))?$', auth_str)
```

### Authorization Workflow
1. IC submits diagram for authorization
2. Authorization email sent to each required authorizer
3. Authorizers sign off sequentially (order defined by `Sequence` column in Authorizations table)
4. All authorizers must approve (unanimous sign-off)
5. When all signed: status → `"Promotion Ready - {date}"`
6. Diagram included in next DSL batch

### Authorizations Table
```sql
CREATE TABLE "Authorizations" (
    "DiagramGUID" TEXT NOT NULL,
    "Type" TEXT NOT NULL DEFAULT 'Draft',
    "User" TEXT NOT NULL,
    "Authorization" TEXT,
    "SignOffStatus" TEXT,
    "SignOffDate" TIMESTAMP,
    "Sequence" INTEGER,        -- order of sign-off
    "RequestFrom" TEXT,
    "DueDate" TIMESTAMP,
    "Date" TIMESTAMP,
    "ActiveState" TEXT,
    PRIMARY KEY("DiagramGUID","User","Type")
);
```

---

## DSL Files — Batch Operations

DSL files are plain-text files used by the Nimbus Batch Server to perform bulk operations (authorize, promote). Each line contains one DSLID.

### File Format
```
DSLID1
DSLID2
DSLID3
```

Plain text, one DSLID per line. No headers, no metadata.

### Five Category DSL Files (MCPT Main Generation)
Generated based on diagram status:

| Filename | Contents |
|---|---|
| `PromotionEngineeringApproved.dsl` | DSLIDs of diagrams with status = Engineering Approved |
| `PromotionClaimed.dsl` | DSLIDs of diagrams with status = Claimed |
| `PromotionUnclaimed.dsl` | DSLIDs of diagrams with status = Unclaimed |
| `PromotionNTBC.dsl` | DSLIDs of diagrams with status = Not To Be Claimed |
| `PromotionPromoOnly.dsl` | DSLIDs of diagrams flagged as Promo Only (no auth needed) |

### Per-Authorizer DSL Files (Authorization Dashboard Generation)
One file per authorizer containing DSLIDs of diagrams that authorizer needs to sign off:

| Filename | Contents |
|---|---|
| `AuthDSL_John_Smith.dsl` | DSLIDs pending John Smith's authorization |
| `AuthDSL_Jane_Doe.dsl` | DSLIDs pending Jane Doe's authorization |
| ... | ... |

### ZIP Download
All DSL files are packaged into a single ZIP archive for download:
```
mcpt_dsl_{promotion_date}.zip
├── PromotionEngineeringApproved.dsl
├── PromotionClaimed.dsl
├── PromotionUnclaimed.dsl
├── PromotionNTBC.dsl
├── PromotionPromoOnly.dsl
├── AuthDSL_Firstname_Lastname.dsl   (one per authorizer)
└── ...
```

---

## Nimbus REST API (Direct — NOT Used by MCPT)

The Nimbus application has an internal REST API, but MCPT does NOT call it directly. All diagram data comes from the backend team's SQLite database (which mirrors Nimbus data). This is by design — MCPT reads from the mirror DB, not from Nimbus itself.

The Nimbus web interface is still accessible via deep links for direct diagram viewing.

---

## TIBCO Nimbus Batch Server

The Batch Server is a separate Nimbus component that executes DSL files to perform bulk operations. The NAT team runs the Batch Server after each promotion cycle to:
1. Authorize all pending diagrams (using authorization DSL files)
2. Promote Draft → Master (using category DSL files)

MCPT generates the input DSL files. The Batch Server execution is done manually by the NAT team.

---

## Nimbus-Specific Fields in Diagrams Table

Confirmed fields from `Diagrams.sql`:
- `DraftLevel` / `MasterLevel` — level notation (e.g., `"1.3.8 Draft Copy"` / `"1.3.8"`)
- `DraftVersion` / `MasterVersion` — version numbers
- `DraftAuthorization` / `MasterAuthorization` — authorization status strings
- `DraftDSLID` / `MasterDSLID` — batch operation identifiers (separate from GUID)
- `DraftModified` / `MasterModified` — last modification timestamps
- `DraftMapPath` / `MasterMapPath` — internal Nimbus paths
- `Status` — current diagram status

---

## Known Nimbus Issues / Quirks

1. **SIPOCs and Storyboards FK bug**: Both tables define a composite FK referencing `Diagrams(GUID, Type)`, but `Diagrams` has no `Type` column — only `GUID` as primary key. This FK will fail if SQLite FK enforcement is enabled. Reported to dev team (Question #9 in developer_questions_email.md).

2. **`Attatchments` typo**: The Diagrams table column is `"Attatchments"` (with extra 't'). This is in the production schema — do not "fix" this typo in MCPT code or it won't match.

3. **Nimbus EOL**: Extended support means no new Nimbus API features. Build against current known behavior only.
