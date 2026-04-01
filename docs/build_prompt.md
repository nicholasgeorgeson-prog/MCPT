# MCPT Build Specification

Complete build specification for all 13 modules.
**Status**: Pre-build. API contract pending. Build begins once dev team responds.

---

## Project Context

**MCPT** (Model Change Package Tracker) is a Flask-based multi-user web app replacing Excel/VBA workbooks used by the NGAS NAT team to manage TIBCO Nimbus diagram promotion cycles.

- **Backend**: Flask + Waitress, port 5060
- **Frontend**: Vanilla JS, CSS, HTML
- **Auth**: Windows NTLM/Kerberos (sspilib/pywin32)
- **Deploy**: `C:\MCPT\` on Windows network server
- **API**: Separate dev team REST API, all calls proxied through Flask

See `CLAUDE.md` for architecture rules, `docs/architecture_decisions.md` for rationale.

---

## Project Structure

```
C:\MCPT\
├── app.py                  -- Flask entry point, middleware, Waitress startup
├── config.py               -- Config: API URL, SMTP, SAP settings
├── nimbus_adapter.py       -- Nimbus abstraction layer (URLs, DSL files)
├── auth.py                 -- Windows NTLM auth + role decorator
├── version.json            -- Version tracking
├── Start_MCPT.bat          -- Double-click to start server
├── routes/
│   ├── __init__.py
│   ├── main_routes.py      -- MCPT table CRUD proxy
│   ├── auth_routes.py      -- Auth + user lookup
│   ├── dsl_routes.py       -- DSL file generation + ZIP
│   ├── tasking_routes.py   -- Weekly tasking entries
│   ├── metrics_routes.py   -- Charging, BOE, DID metrics
│   ├── pal_routes.py       -- PAL checklist + PAL helper
│   ├── admin_routes.py     -- Admin panel operations
│   ├── notification_routes.py -- Notification poll + mark-read
│   └── export_routes.py    -- Excel, Word, HTML, ZIP exports
├── data/
│   ├── notifications.db    -- SQLite WAL, local only
│   └── sql_schemas/        -- Backend team's schemas (reference only)
├── static/
│   ├── version.json
│   ├── css/
│   │   └── main.css
│   └── js/
│       ├── app.js          -- Main SPA controller
│       ├── mcpt-table.js   -- Module 1: MCPT main table
│       ├── auth-dashboard.js -- Module 2: Authorization dashboard
│       ├── dsl-generator.js  -- Module 3: DSL file generator
│       ├── tasking.js        -- Module 4: Weekly tasking
│       ├── metrics.js        -- Module 5-7: Metrics modules
│       ├── pal.js            -- Modules 8-9: PAL checklist + helper
│       ├── admin.js          -- Module 10: Admin panel
│       └── notifications.js  -- Module 11: Notification feed
└── templates/
    └── index.html          -- Single-page app HTML
```

---

## app.py

```python
from flask import Flask
from waitress import serve
from auth import ntlm_middleware
from routes import register_blueprints
from config import load_config

app = Flask(__name__)
app.secret_key = 'replace-with-secure-key'
app.wsgi_app = ntlm_middleware(app.wsgi_app)

register_blueprints(app)

def main():
    config = load_config()
    print(f"MCPT starting on port {config['PORT']}")
    serve(app, host='0.0.0.0', port=config['PORT'], threads=8)

if __name__ == '__main__':
    main()
```

---

## Module 1 — MCPT Main Table

**Purpose**: The primary view. Shows all diagrams for the current promotion cycle with their tracking status. Supports inline editing, adding entries, and archiving.

### UI

- Full-width data grid, sortable columns, sticky header
- Promotion date selector in page header. **`/get-mcpt` returns ALL rows** — filter client-side by `row["Promotion Date"]` (Unix ms timestamp). Store available dates from the full dataset.
- Primary columns: Level | Diagram Title | Draft Status | Diagram Category | NAT Contact | SP Folder | Tool Entry | CR Package | Auth Status | Authorizer | Total Errors | Notes | Actions
- Extended columns (collapsible/hidden by default): Authorization sent/accepted counts, template checks, link error counts, Change Log, Storyboard Impact
- **Boolean cells render three states**: `null` → `—` (grey dash), `true` → `✓` (green), `false` → `✗` (red)
- **Hyperlinks**: Use pre-built `row["Draft Diagram Hyperlink"]` and `row["Master Diagram Hyperlink"]` directly — no URL construction needed
- **Inline edit**: Click any editable cell → text input or dropdown → Tab/Enter to save → calls `POST /edit-entry` via Flask proxy
  - Note: JSON field names in edit-entry `"field"` parameter must match exact API key names (e.g., `"SP Folder Created"`, NOT `"sp_folder_created"`)
- **Add entry**: "+ Add Diagram" button → modal form → GUID lookup → fill fields → save
- **Archive**: Row action button (Admin only) → confirm → `POST /archive-entry`
- **Filter chips**: All | Unclaimed | Claimed | Engineering Approved | NTBC + promotion date dropdown
- **Search**: Full-text search across Diagram Title, Owner, Level, Notes, Change Log Entries
- **DSL Generate**: "Generate DSL Files" button → triggers Module 3
- **Error highlighting**: Rows where `Total Errors > 0` get a red left border / warning indicator

### Flask Routes

```
GET  /api/mcpt/data              → proxy GET /get-mcpt (+ filter params)
POST /api/mcpt/edit              → proxy POST /edit-entry
POST /api/mcpt/add               → proxy POST /add-entry
POST /api/mcpt/archive           → proxy POST /archive-entry (Admin only)
POST /api/mcpt/remove            → proxy POST /remove-entry (Admin only)
GET  /api/mcpt/diagram/<guid>    → proxy GET /get-diagram?guid=GUID
```

### Edit-Entry Request
```json
{ "guid": "ACDF1AE9385543888E91381F30D3F806", "field": "Status", "value": "Claimed" }
```

### Business Rules
- IC can only edit rows where `IC_Assigned == current_user.username`
- Admin can edit any row
- Archived rows hidden by default, revealed by "Include Archived" toggle (Admin only)
- Status changes trigger a notification to the row's IC
- `SP_Folder_Created` and `Tool_Entry_Created` are boolean checkboxes

---

## Module 2 — Authorization Dashboard

**Purpose**: Tracks authorization sign-off progress for the current promotion cycle. Shows which diagrams are awaiting authorization, who needs to sign off, and generates authorization emails.

### UI

- Table: Diagram | Level | Auth Status | Authorizer 1 | Authorizer 2 | ... | Authorizer N
- Color coding: Green = signed, Yellow = pending, Red = overdue
- Per-authorizer column shows: ✓ Approved | ⏳ Pending | ✗ Overdue
- Filter by: authorizer, status, overdue only
- "Send Auth Reminder" button → sends Email Type 2 to overdue authorizers
- "Send Auth Requests" button → sends Email Type 3 to authorizers with new pending items
- "Generate Auth DSL" button → generates per-authorizer DSL files → redirects to Module 3

### Flask Routes

```
GET  /api/auth-dashboard/data           → proxy GET /get-trb
POST /api/auth-dashboard/send-reminders → Admin: trigger missing auth emails
POST /api/auth-dashboard/send-requests  → Admin: trigger auth request emails
```

### Data Requirements
- Authorization data from `GET /get-trb` (structure TBD from dev team)
- Must show per-authorizer sign-off status for every diagram in current cycle
- Must identify overdue authorizations (DueDate < today AND not signed)

---

## Module 3 — DSL File Generator

**Purpose**: Generates all DSL files for the Nimbus Batch Server and serves them as a ZIP download.

### UI

- Simple page: promotion date (auto-filled from current cycle), statistics summary
- Shows preview table: one row per DSL file, with count of DSLIDs it will contain
- "Download DSL ZIP" button → generates and downloads ZIP

### DSL Generation Logic

**Category DSL files** (from MCPT main table data, `DraftDSLID` column):
```python
categories = {
    'PromotionEngineeringApproved': [r for r in rows if r['Status'] == 'Engineering Approved'],
    'PromotionClaimed':             [r for r in rows if r['Status'] == 'Claimed'],
    'PromotionUnclaimed':           [r for r in rows if r['Status'] == 'Unclaimed'],
    'PromotionNTBC':                [r for r in rows if r['Status'] == 'Not To Be Claimed'],
    'PromotionPromoOnly':           [r for r in rows if r.get('PromoOnly')],
}
for name, rows in categories.items():
    content = '\n'.join(r['DraftDSLID'] for r in rows)
    zip_file.writestr(f'{name}.dsl', content)
```

**Per-authorizer DSL files** (from authorization data):
```python
# Group by authorizer where SignOffStatus != 'Approved'
by_auth = defaultdict(list)
for auth_row in auth_data:
    if auth_row['SignOffStatus'] != 'Approved':
        by_auth[auth_row['User']].append(auth_row['DraftDSLID'])
for username, dslids in by_auth.items():
    safe_name = username.replace(' ', '_').replace('/', '_')
    zip_file.writestr(f'AuthDSL_{safe_name}.dsl', '\n'.join(dslids))
```

### Flask Route

```
POST /api/dsl/generate    → body: { "promotion_date": "2026-04-04" }
                           → response: ZIP file download
```

### ZIP Contents

```
mcpt_dsl_2026-04-04.zip
├── PromotionEngineeringApproved.dsl
├── PromotionClaimed.dsl
├── PromotionUnclaimed.dsl
├── PromotionNTBC.dsl
├── PromotionPromoOnly.dsl
├── AuthDSL_{Username1}.dsl
├── AuthDSL_{Username2}.dsl
└── ...
```

---

## Module 4 — Weekly Tasking Report

**Purpose**: Each IC enters their weekly task entries. Director sees consolidated view across all ICs. Export to Word.

### UI

**IC View**:
- Form: Week ending date | Diagram GUID (with autocomplete from MCPT data) | Activity type | Hours | Notes
- Save entry → appears in their tasking list for this week
- Edit/delete own entries

**Director View**:
- Consolidated table: IC Name | Diagrams worked | Hours | Activity types
- Expandable rows to see per-IC detail
- "Export to Word" button

### Data Storage

Tasking entries stored locally in `notifications.db` (or separate `tasking.db`):
```sql
CREATE TABLE tasking_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    week_ending DATE NOT NULL,
    diagram_guid TEXT,
    activity_type TEXT,
    hours REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT (datetime('now'))
);
```

### Flask Routes

```
GET  /api/tasking/entries         → IC: own entries; Director: all entries
POST /api/tasking/entries         → IC: add entry
PUT  /api/tasking/entries/<id>    → IC: edit own entry
DELETE /api/tasking/entries/<id>  → IC: delete own entry
GET  /api/tasking/export/word     → Director: download Word report
```

### Word Export (python-docx)

- Document title: "Weekly Tasking Report — Week Ending {date}"
- Section per IC with table: Diagram Level | Title | Activity | Hours | Notes
- Summary section: total hours by activity type across all ICs
- Director signature line

---

## Module 5 — Metrics: Charging

**Purpose**: Process SAP charging export files to produce a pivot table of hours by employee and fiscal month.

### UI

- File upload area: drag-and-drop or click to upload Excel (.xlsx or .xls)
- Smart column detection: auto-detects which column contains hours, employee names, fiscal months
- Preview: first 5 rows of detected data
- "Process" button → generates pivot table
- Pivot table displayed: rows = employees, columns = fiscal months, values = hours
- "Export to Excel" button → downloads styled pivot table

### Processing Logic

```python
import openpyxl

def process_charging(filepath):
    # Step 1: Load Excel
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    # Step 2: Smart column detection
    headers = [cell.value for cell in next(ws.rows)]
    hours_col = detect_hours_column(headers)    # Look for "Hours", "Hrs", "Actual Hours"
    emp_col = detect_employee_column(headers)   # Look for "Employee", "Name", "User"
    month_col = detect_month_column(headers)    # Look for "FiscalMonth", "Month", "Period"

    # Step 3: Parse rows
    data = []
    for row in ws.rows:
        hours_raw = row[hours_col].value
        hours = float(str(hours_raw).replace(' H', '').strip()) if hours_raw else 0.0
        data.append({
            'employee': row[emp_col].value,
            'month': row[month_col].value,
            'hours': hours
        })

    # Step 4: Pivot with MAX aggregation
    # SAP data is cumulative within pay period — use MAX not SUM
    pivot = {}
    for row in data:
        key = (row['employee'], row['month'])
        pivot[key] = max(pivot.get(key, 0), row['hours'])

    return pivot
```

### Flask Routes

```
POST /api/metrics/charging/upload    → upload SAP file, return preview
POST /api/metrics/charging/process   → process uploaded file, return pivot data
GET  /api/metrics/charging/export    → download Excel pivot table
```

---

## Module 6 — Metrics: NimbusBOE

**Purpose**: Process SAP BOE (Basis of Estimate) export files filtered to the NAT team charge order.

### UI

- File upload (same pattern as Charging)
- Order number display (from admin config, `9L99G054`)
- "Process" button → BOE summary table
- Table: Employee | SuppCode1 | SuppCode2 | ... | Total
- "Export to Excel" button

### Processing Logic

```python
EXCLUDED_SUPP_CODES = {'PTO', 'HOL', 'UNP'}

def process_boe(filepath, charge_order):
    # Load and filter
    rows = [r for r in load_excel(filepath)
            if r['Order'] == charge_order
            and r['SuppCode'] not in EXCLUDED_SUPP_CODES]

    # Group by Employee × SuppCode, sum hours
    pivot = defaultdict(lambda: defaultdict(float))
    for row in rows:
        pivot[row['Employee']][row['SuppCode']] += row['Hours']

    return pivot
```

### Flask Routes

```
POST /api/metrics/boe/upload     → upload SAP BOE file
POST /api/metrics/boe/process    → process + return BOE table
GET  /api/metrics/boe/export     → download Excel BOE table
```

---

## Module 7 — Metrics: DID Working

**Purpose**: Track government DID (Data Item Description) working documents.

### UI

- Table: DID Number | Title | Responsible Party | Status | Due Date | Notes
- Add/edit/delete entries (Admin)
- Filter by status, responsible party
- Export to Excel

### Data Storage

Local SQLite table:
```sql
CREATE TABLE did_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    did_number TEXT NOT NULL,
    title TEXT NOT NULL,
    responsible_party TEXT,
    status TEXT DEFAULT 'In Work',
    due_date DATE,
    notes TEXT,
    updated_at TIMESTAMP DEFAULT (datetime('now')),
    updated_by TEXT
);
```

### Flask Routes

```
GET    /api/metrics/did          → list all DID entries
POST   /api/metrics/did          → add entry (Admin)
PUT    /api/metrics/did/<id>     → edit entry (Admin)
DELETE /api/metrics/did/<id>     → delete entry (Admin)
GET    /api/metrics/did/export   → Excel export
```

---

## Module 8 — PAL Checklist

**Purpose**: 25-item interactive review checklist for the PAL (Promotion Authorization List) review process.

### UI

- Checklist with 25 items grouped by category (e.g., "Documentation", "Technical Review", "Authorization")
- Each item: checkbox + item text + optional notes field
- Progress bar: N/25 items complete
- "Save Progress" persists state per-user per-promotion-cycle
- "Export" → PDF-friendly HTML print view

### Checklist Items — CONFIRMED from PAL Checklist.xlsx (Reports repo)

All 25 items confirmed. All belong to the **"Clerical"** category (document review items for PAL manuals):

| # | Item |
|---|---|
| 1 | Document number formally reserved |
| 2 | Check front page is filled out properly (date = TRB date, doc number is good with no brackets, doc owner is spelled like email incl [US] (AS) afterward, PA element is correct/hyperlinked correctly) |
| 3 | Are the report title, document number, and revision letter included in the header |
| 4 | Check the Table of Contents – when there are lowercase letters that are supposed to be uppercase, go to that section of the doc/update with caps/refresh the table of contents |
| 5 | Is the revision letter correct |
| 6 | Correct TRB date included |
| 7 | Is the TOC correct |
| 8 | Roman Numerals used for Table of Contents, up until page 1 |
| 9 | Are all the figures and tables numbered and referenced correctly |
| 10 | Are the margins, paragraph indentations and bullets/numbering correct |
| 11 | Are all sheets numbered correctly |
| 12 | Are the Contract, Line Item Number, and Data Item correct |
| 13 | Is the Distribution Statement correct |
| 14 | Make sure Nimbus is spelled Nimbus and not NIMBUS |
| 15 | Make sure hyperlinks to Nimbus are correct – and to the MASTER version, not DRAFT |
| 16 | Take out everywhere they are calling PAL manuals "process documents" |
| 17 | Make sure NGAS is Aeronautics sector, not Aerospace sector |
| 18 | For old PAL manuals, ensure there are no ref to old orgs, e.g. "ISWR", DPTO, etc. |
| 19 | There should be no "shalls". State as fact — "Need", "will", "should", "do/does", "are/is" |
| 20 | Has spell check passed? Also review blue wavy underlined grammar suggestions |
| 21 | Check all references are in reference section – and check they are correct |
| 22 | Check all docs called out in reference section are actually in the doc |
| 23 | Ensure all hyperlinks work |
| 24 | Check the first time an acronym is used, that it is spelled out |
| 25 | Check all acronyms in the acronym list are used |

### Data Storage

```sql
CREATE TABLE pal_checklist_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    promotion_date DATE NOT NULL,
    item_number INTEGER NOT NULL,
    checked INTEGER DEFAULT 0,
    notes TEXT,
    updated_at TIMESTAMP DEFAULT (datetime('now')),
    UNIQUE(username, promotion_date, item_number)
);
```

### Flask Routes

```
GET  /api/pal/checklist/<promotion_date>   → get checklist state for current user
POST /api/pal/checklist                    → save item state
GET  /api/pal/checklist/export             → HTML print view
```

---

## Module 9 — PAL Helper

**Purpose**: SharePoint PAL document browser. Provides quick access to the correct PAL document by discipline.

### UI

- Discipline selector (dropdown or grid of tiles): Systems Engineering | Manufacturing | Quality | ...
- Selected discipline → list of PAL documents from SharePoint with links
- Read-only browser — no edit operations
- "Open in SharePoint" link for each document

### Implementation — CONFIRMED from PALHelperFile.xlsx (Reports repo)

**12 disciplines confirmed** (one sheet per discipline in source Excel):

| Discipline Code | Description |
|---|---|
| `VE` | Vehicle Engineering |
| `T&E` | Test & Evaluation |
| `SW` | Software |
| `SRV` | Survivability |
| `SE` | Systems Engineering |
| `PS` | Product Support |
| `PM&P` | Program Management & Planning |
| `FS` | Flight Sciences |
| `EP&T` | Engineering Processes & Tools |
| `Engineering` | General Engineering |
| `AWWSC` | AW & WSC |
| `AvI` | Avionics & Integration |

**SharePoint base path**: `sites/AS-ENG/PAL/{discipline_code}/`

**Document columns**: Name, Title, Revision, Release Date, Owner, Author, Doc Type, TD (Technical Discipline), File Size, Item Type, Path

**Item Types**: Folder (for subfolders like Checklists, Formal Docs, Manuals, Templates), Item (actual files)

**Implementation**:
- Source data from PALHelperFile.xlsx embedded in the app (static data, not live SharePoint query for initial build)
- Each row has a `Path` field (relative SharePoint path, e.g. `sites/AS-ENG/PAL/VE/Manuals`)
- Construct SharePoint URL as `https://{sharepoint_host}/{path}/{filename}`
- Document type icons: Checklist 📋, PAL Manual 📖, Formal Doc 📄, Template 📝
- Filter by discipline → filter by Doc Type within discipline

### Flask Routes

```
GET  /api/pal/documents                → list all PAL documents (all disciplines)
GET  /api/pal/documents/<discipline>   → documents for specific discipline
```

**Note**: For initial build, serve PALHelperFile data statically (embed as JSON). Live SharePoint queries are a future enhancement.

---

## Module 10 — Admin Panel

**Purpose**: Admin-only management console for all configurable aspects of MCPT.

### Sections

#### Users
- Table: Username | Display Name | Role | Email | Active
- Add user: Windows username + role + email
- Edit user: change role, email, active status
- Deactivate (not delete) — inactive users get 403

#### Dropdown Management
- Edit the valid options for Status, Organization, Activity Type, etc.
- Add/remove options from each dropdown list

#### Email Configuration
- SMTP Host, Port, From Address
- "Test Email" button → sends a test email to the currently logged-in admin

#### SAP Settings
- Default SAP charge order number (default: `9L99G054`)
- Excluded supp codes list (default: PTO, HOL, UNP)
- Fiscal month format

#### Promotion Dates
- List of all promotion cycles with start/end dates
- Add new cycle (requires Admin)
- Mark cycle as closed (archived)

#### System Settings
- Current version display
- "Check for updates" (future: GitHub-based update pull)
- Database health status
- **TRB Chair name** — display name of the Engineering Process TRB Chair (default: `"Jamie Dunham"`). Used to determine `"Authorized by Eng Process TRB Chair"` column logic. When changed, MCPT must notify the dev team to update the `<TRB_chair>` parameter in the backend SQL config. Stored in MCPT local config. A pending dev team request: support a `trb_chair` parameter on `/get-mcpt` so MCPT can pass this value dynamically instead of requiring a backend redeploy when the chair changes.

### Flask Routes

```
GET    /api/admin/users              → list users (Admin only)
POST   /api/admin/users              → add user
PUT    /api/admin/users/<username>   → edit user
DELETE /api/admin/users/<username>   → deactivate user

GET    /api/admin/config             → get all config values
POST   /api/admin/config             → save config values

GET    /api/admin/dropdowns          → get all dropdown lists
POST   /api/admin/dropdowns          → update dropdown list

GET    /api/admin/promotion-dates    → list all cycles
POST   /api/admin/promotion-dates    → add cycle
PUT    /api/admin/promotion-dates/<id> → update cycle status
```

---

## Module 11 — In-App Notifications

**Purpose**: Real-time-ish notification feed for events relevant to each user.

### UI

- Bell icon in app header with badge count (red dot with number)
- Click → slide-out notification panel (right side)
- Each notification: type icon + message + time ago + mark-read button
- "Mark all read" button
- Unread count badge on bell icon

### Events That Generate Notifications

| Event | Who Gets Notified |
|---|---|
| Someone edits a row you IC'd | The IC assigned to that row |
| A diagram you IC'd changes status | The IC assigned |
| An authorization is requested for a diagram | The listed authorizer |
| A diagram's authorization is complete | The IC who requested it |
| An Admin sends a note to a user | The target user |

### Implementation

- 60-second poll: `GET /api/notifications/unread-count` → returns `{"count": N}`
- On badge click: `GET /api/notifications/feed` → returns last 50 notifications
- `POST /api/notifications/read/<id>` → mark one as read
- `POST /api/notifications/read-all` → mark all as read
- Notifications written by Flask route handlers when events occur

### Flask Routes

```
GET  /api/notifications/unread-count   → {"count": N} — polled every 60s
GET  /api/notifications/feed           → last 50 notifications for current user
POST /api/notifications/read/<id>      → mark one notification read
POST /api/notifications/read-all       → mark all notifications read
POST /api/notifications/internal       → (internal only) create notification
```

---

## Module 12 — Email Automation

**Purpose**: Send three types of automated emails via SMTP relay.

### Email Type 1: Status Summary Email

**Trigger**: Admin manually triggers from Authorization Dashboard or Admin Panel.
**Recipients**: Director(s) + configurable recipient list.

**Subject**: `MCPT Promotion Cycle Status — {promotion_date}`

**Body structure**:
```
Engineering Approved: N diagrams
  Level | Title | Owner | IC Assigned

Claimed: N diagrams
  Level | Title | Owner | IC Assigned

Unclaimed: N diagrams
  Level | Title | Owner

Not To Be Claimed: N diagrams
  Level | Title

Conceptual Image: N diagrams
  Level | Title
```

### Email Type 2: Missing Authorization Reminder

**Trigger**: Admin manually triggers OR scheduled (configurable).
**Recipients**: One email per authorizer who has overdue pending authorizations.

**Subject**: `Reminder: Authorization Pending for {N} Diagrams — Due {date}`

**Body**: Table of diagrams awaiting their sign-off, with due dates highlighted.

### Email Type 3: Per-Authorizer Authorization Request

**Trigger**: Admin initiates authorization process for a diagram or batch.
**Recipients**: Each required authorizer.

**Subject**: `Authorization Required — {diagram_title} [{level}]`

**Body**: Diagram details, link to Nimbus diagram, sign-off instructions, due date.

### SMTP Implementation

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to: list, subject: str, html_body: str):
    config = load_config()
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = config['SMTP_FROM']
    msg['To'] = ', '.join(to)
    msg.attach(MIMEText(html_body, 'html'))

    with smtplib.SMTP(config['SMTP_HOST'], config['SMTP_PORT']) as server:
        server.sendmail(config['SMTP_FROM'], to, msg.as_string())
```

### Flask Routes

```
POST /api/email/status-summary        → Admin: send status summary email
POST /api/email/auth-reminders        → Admin: send missing auth reminders
POST /api/email/auth-requests         → Admin: send auth request emails
POST /api/email/test                  → Admin: send test email to self
```

---

## Module 13 — Export

**Purpose**: Multiple export formats for MCPT data.

### Excel Export (openpyxl)

- MCPT main table → styled Excel with all columns
- Column widths auto-sized
- Frozen first row (header)
- Alternating row colors
- Status cells color-coded (green = Engineering Approved, yellow = Claimed, red = Unclaimed)

### Word Export (python-docx)

- Weekly tasking report format (see Module 4)
- Table styles matching NGAS standards

### HTML Export

- Status summary as standalone HTML file
- Styled for printing / saving as PDF via browser print

### DSL ZIP Export

- Handled by Module 3 (DSL File Generator)

### Flask Routes

```
GET /api/export/mcpt-excel           → download MCPT table as Excel
GET /api/export/tasking-word         → download tasking report as Word
GET /api/export/status-html          → download status summary as HTML
GET /api/export/dsl-zip              → download DSL ZIP (delegates to Module 3)
```

---

## auth.py — NTLM Authentication

```python
import sspilib
from flask import request, session, abort, g
from functools import wraps

def ntlm_middleware(wsgi_app):
    """Wrap WSGI app with NTLM auth negotiation."""
    # Exchange NTLM tokens with browser
    # Extract Windows username from authenticated context
    # Store in session
    ...

def get_current_user():
    """Get the current user's info (cached in Flask g)."""
    if 'user' not in g:
        username = session.get('windows_username')
        # Look up role from backend API
        resp = requests.get(f"{API_URL}/get-user?username={username}")
        if resp.status_code == 403:
            abort(403)
        g.user = resp.json()  # { username, display_name, role, email }
    return g.user

def require_role(*roles):
    """Decorator to enforce role-based access."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user['role'] not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
```

---

## nimbus_adapter.py — Nimbus Abstraction Layer

**CRITICAL: Draft and Master use DIFFERENT map GUIDs.** Confirmed from actual API response.

```python
class NimbusAdapter:
    BASE_URL = "https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0"
    DRAFT_MAP_GUID  = "9820E23DD3204072819C50B7A2E57093"   # Draft diagrams
    MASTER_MAP_GUID = "ED910D9C5F0C4F8491F8FD10A0C5695B"  # Master diagrams — DIFFERENT!

    def draft_url(self, draft_dslid: str) -> str:
        """Generate Nimbus deep link for a Draft diagram (uses DraftDSLID, not GUID)."""
        return f"{self.BASE_URL}:{self.DRAFT_MAP_GUID}.{draft_dslid}"

    def master_url(self, master_dslid: str) -> str:
        """Generate Nimbus deep link for a Master diagram (uses MasterDSLID, not GUID)."""
        return f"{self.BASE_URL}:{self.MASTER_MAP_GUID}.{master_dslid}"

    def generate_dsl_content(self, dslid_list: list) -> str:
        """Generate DSL file content (one DSLID per line)."""
        return '\n'.join(str(d) for d in dslid_list if d)

    def level_number(self, level_str: str) -> int:
        """Extract numeric level from '1.3.8 Draft Copy' → 3."""
        if not level_str:
            return 0
        clean = level_str.replace(' Draft Copy', '').strip()
        return len(clean.split('.'))

    def is_draft(self, level_str: str) -> bool:
        return 'Draft Copy' in (level_str or '')

    def promotion_date_from_ms(self, ts_ms) -> str:
        """Convert Unix milliseconds timestamp to display string."""
        from datetime import datetime
        if not ts_ms:
            return ''
        return datetime.fromtimestamp(ts_ms / 1000).strftime('%m/%d/%Y')

# Global instance
nimbus = NimbusAdapter()

# NOTE: The /get-mcpt response already includes pre-built "Draft Diagram Hyperlink"
# and "Master Diagram Hyperlink" fields. Use those directly in the UI.
# Only use nimbus_adapter URL methods when building DSL-related features or
# when working with data that doesn't already have the hyperlink.
```

---

## Single-Page App Structure (index.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MCPT — Model Change Package Tracker</title>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <!-- App header -->
    <header id="app-header">
        <div class="header-left">
            <span class="app-title">MCPT</span>
            <span class="app-subtitle">Model Change Package Tracker</span>
        </div>
        <div class="header-center">
            <!-- Promotion date selector -->
            <select id="promotion-date-selector"></select>
        </div>
        <div class="header-right">
            <!-- Notification bell -->
            <button id="notif-bell" class="bell-btn">
                🔔 <span id="notif-badge" class="badge hidden">0</span>
            </button>
            <!-- Current user display -->
            <span id="user-display"></span>
        </div>
    </header>

    <!-- Navigation tabs -->
    <nav id="main-nav">
        <button class="nav-tab active" data-module="mcpt-table">MCPT Table</button>
        <button class="nav-tab" data-module="auth-dashboard">Authorization</button>
        <button class="nav-tab" data-module="dsl-generator">DSL Generator</button>
        <button class="nav-tab" data-module="tasking">Tasking</button>
        <button class="nav-tab" data-module="metrics">Metrics</button>
        <button class="nav-tab" data-module="pal">PAL</button>
        <button class="nav-tab admin-only" data-module="admin">Admin</button>
    </nav>

    <!-- Module containers -->
    <main id="app-main">
        <section id="module-mcpt-table" class="module active"></section>
        <section id="module-auth-dashboard" class="module"></section>
        <section id="module-dsl-generator" class="module"></section>
        <section id="module-tasking" class="module"></section>
        <section id="module-metrics" class="module"></section>
        <section id="module-pal" class="module"></section>
        <section id="module-admin" class="module admin-only"></section>
    </main>

    <!-- Notification panel (slide-out) -->
    <aside id="notif-panel" class="panel hidden"></aside>

    <script src="/static/js/app.js"></script>
    <script src="/static/js/mcpt-table.js"></script>
    <script src="/static/js/auth-dashboard.js"></script>
    <script src="/static/js/dsl-generator.js"></script>
    <script src="/static/js/tasking.js"></script>
    <script src="/static/js/metrics.js"></script>
    <script src="/static/js/pal.js"></script>
    <script src="/static/js/admin.js"></script>
    <script src="/static/js/notifications.js"></script>
</body>
</html>
```

---

## Build Order

When build begins (after API contract confirmed):

1. **Foundation**: `app.py`, `config.py`, `auth.py`, `nimbus_adapter.py`
2. **Database**: `data/notifications.db` schema init
3. **Module 1**: MCPT Main Table (core data grid) — highest priority
4. **Module 2**: Authorization Dashboard
5. **Module 3**: DSL File Generator
6. **Module 10**: Admin Panel (needed for user management)
7. **Module 11**: Notifications (needed for real-time feel)
8. **Module 12**: Email Automation
9. **Module 4**: Weekly Tasking Report
10. **Module 5**: Metrics: Charging
11. **Module 6**: Metrics: NimbusBOE
12. **Module 7**: Metrics: DID Working
13. **Modules 8-9**: PAL Checklist + Helper
14. **Module 13**: Export (weave in as each module is built)

---

## Pre-Build Checklist

- [x] Architecture decisions documented
- [x] SQL schemas analyzed (Reports repo)
- [x] VBA logic extracted and documented (4 workbooks)
- [x] Nimbus research complete
- [x] 43 pre-flight Q&A complete
- [x] Developer questions email sent (11 questions)
- [x] API contract confirmed ✅ 2026-04-01
- [x] `/get-mcpt` JSON response sample received ✅ (49 fields, full Pydantic model)
- [x] MCPT tracking table — no table, compiled SQL JOIN query ✅
- [x] API base URL confirmed ✅ `127.0.0.1:8000` dev / nimbus server IP:8000 prod
- [x] API auth mechanism confirmed ✅ open on internal network
- [x] BUILD CAN BEGIN

---

## Notes on API Contract

When the dev team responds, update:
1. `CLAUDE.md` — Backend API section
2. `docs/developer_questions_email.md` — Answers Log table
3. `config.py` — API_BASE_URL
4. `routes/main_routes.py` — field name mappings
5. `docs/data_model.md` — MCPT tracking table section
6. Re-run `python3 build_knowledge_db.py` to update knowledge DB
