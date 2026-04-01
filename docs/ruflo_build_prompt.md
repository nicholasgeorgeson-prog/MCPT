# MCPT — Ruflo Build Prompt

You are building **MCPT** (Model Change Package Tracker), a Flask web application that replaces a suite of Excel/VBA workbooks used by the NGAS (Northrop Grumman Aeronautics Systems) NAT team to manage TIBCO Nimbus process model diagram promotions.

**Build every module completely. No stubs, no TODOs, no placeholder functions.**

---

## Tech Stack

| Layer | Choice |
|---|---|
| Web server | Flask + Waitress WSGI (NOT Flask dev server) |
| Frontend | Vanilla JS, CSS, HTML — no frameworks, no npm, no build step |
| Auth | Windows NTLM via sspilib — users never type a password |
| Local DB | SQLite WAL mode — `data/notifications.db` (notifications only) |
| External API | Backend REST API at `http://127.0.0.1:8000` (dev) / `http://{nimbus-server-ip}:8000` (prod) |
| Excel export | openpyxl |
| Word export | python-docx |
| Email | smtplib → internal Exchange SMTP relay |
| Deployment | Windows, `C:\MCPT\`, port 5060 |

---

## CRITICAL RULES — Read Before Writing a Single Line

1. **All file `open()` calls**: `encoding='utf-8', errors='replace'`
2. **ALL backend API calls go through Flask proxy routes** — the browser NEVER calls the backend API directly
3. **`/get-mcpt` returns ALL rows** — filter promotion date client-side. No server-side filter exists.
4. **`"Promotion Date"` is Unix MILLISECONDS** — Python: `datetime.fromtimestamp(ts/1000)`. JS: `new Date(ts)`
5. **Booleans are THREE-STATE**: `null` (unknown/N/A), `true`, `false`. JS render: `val === null ? '—' : val ? '✓' : '✗'`
6. **JSON keys have spaces and special characters** — JS bracket notation: `row["SP Folder Created"]`, `row["DSL UUID"]`
7. **`"DSL UUID"` = DraftDSLID** (batch file identifier). `"GUID"` = concept-level DB key. They are NOT the same.
8. **Two Nimbus map GUIDs**: Draft map = `9820E23DD3204072819C50B7A2E57093`. Master map = `ED910D9C5F0C4F8491F8FD10A0C5695B`
9. **Draft URL** uses `DraftDSLID`. **Master URL** uses `MasterDSLID`. Neither uses `GUID`.
10. **Edit-entry field names** must match EXACT API JSON key: `"SP Folder Created"` not `"sp_folder_created"`
11. **Waitress** for production. `serve(app, host='0.0.0.0', port=5060, threads=8)`
12. **SQLite WAL**: `PRAGMA journal_mode=WAL` on `notifications.db` at startup
13. **No framework JS**: Every UI feature in vanilla JS. Module pattern = IIFE.
14. **Column detection by header name — ALWAYS**: Any module that processes an uploaded file (Excel, CSV, etc.) MUST detect columns by reading the header row and matching by name. NEVER access columns by position index (e.g., `row[22]`, `row[col_U]`), by Excel column letter, or by any hardcoded position. Different users may have different column orders in their SAP or other reports. This rule applies to ALL file inputs in the entire app — no exceptions.

---

## Project File Structure

```
C:\MCPT\
├── app.py
├── config.py
├── auth.py
├── nimbus_adapter.py
├── version.json                     {"version": "0.2.0", "date": "2026-04-01"}
├── Start_MCPT.bat
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── main_routes.py               (MCPT table + proxy)
│   ├── dsl_routes.py                (DSL generation + ZIP)
│   ├── tasking_routes.py            (weekly tasking)
│   ├── metrics_routes.py            (charging, BOE, DID)
│   ├── pal_routes.py                (PAL checklist + helper)
│   ├── admin_routes.py              (admin panel)
│   └── notification_routes.py       (notifications)
├── data/
│   └── notifications.db             (created at startup)
├── static/
│   ├── version.json
│   ├── css/
│   │   └── main.css
│   └── js/
│       ├── app.js                   (SPA controller, nav, auth display)
│       ├── mcpt-table.js
│       ├── auth-dashboard.js
│       ├── dsl-generator.js
│       ├── tasking.js
│       ├── metrics.js
│       ├── pal.js
│       ├── admin.js
│       └── notifications.js
└── templates/
    └── index.html
```

---

## app.py

```python
from flask import Flask
from waitress import serve
from routes import register_blueprints
from config import load_config
from data_init import init_db
import argparse

app = Flask(__name__)
app.secret_key = 'mcpt-dev-secret-change-in-production'

register_blueprints(app)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    init_db()
    config = load_config()
    if args.debug:
        app.run(host='0.0.0.0', port=config['PORT'], debug=True)
    else:
        print(f"MCPT v{config['VERSION']} starting on port {config['PORT']}")
        serve(app, host='0.0.0.0', port=config['PORT'], threads=8)

if __name__ == '__main__':
    main()
```

---

## config.py

```python
import json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = {
    'PORT': 5060,
    'API_BASE_URL': 'http://127.0.0.1:8000',
    'SMTP_HOST': '',
    'SMTP_PORT': 587,
    'SMTP_FROM': '',
    'SAP_CHARGE_ORDER': '9L99G054',
    'SAP_EXCLUDED_SUPP_CODES': ['PTO', 'HOL', 'UNP'],
    'TRB_CHAIR_NAME': 'Jamie Dunham',    # Admin-editable. See Admin Panel → System Settings.
    'DEV_ROLE': 'Admin',                 # ⚠️ STUB: Used until /get-user endpoint is live.
                                         # Set to 'IC', 'Admin', or 'Director' for dev testing.
}

_config_path = os.path.join(BASE_DIR, 'mcpt_config.json')

def load_config():
    cfg = dict(DEFAULTS)
    if os.path.exists(_config_path):
        with open(_config_path, encoding='utf-8', errors='replace') as f:
            cfg.update(json.load(f))
    with open(os.path.join(BASE_DIR, 'version.json'), encoding='utf-8') as f:
        cfg['VERSION'] = json.load(f)['version']
    return cfg

def save_config(updates: dict):
    cfg = load_config()
    cfg.update(updates)
    with open(_config_path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)
```

---

## auth.py

```python
from flask import request, session, g, abort, current_app
from functools import wraps
import requests as req

def get_windows_username():
    """Extract Windows username from NTLM auth context or dev override."""
    # Production: sspilib sets REMOTE_USER or similar header via IIS
    # For now: check X-Auth-User header (set by IIS Windows Auth) or session
    username = request.headers.get('X-Auth-User') or session.get('windows_username')
    if not username:
        # Fallback for development: use a test username
        username = 'dev_user'
        session['windows_username'] = username
    return username

def get_current_user():
    if 'user' not in g:
        from config import load_config
        config = load_config()
        username = get_windows_username()
        # ⚠️ STUB: /get-user endpoint is backlog. Use DEV_ROLE from config until live.
        # When /get-user is implemented, replace this block:
        # resp = req.get(f"{config['API_BASE_URL']}/get-user?username={username}")
        # if resp.status_code == 403: abort(403)
        # g.user = resp.json()
        g.user = {
            'username': username,
            'display_name': username,
            'role': config.get('DEV_ROLE', 'IC'),
            'email': f'{username}@as.northgrum.com'
        }
    return g.user

def require_role(*roles):
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

## nimbus_adapter.py

```python
class NimbusAdapter:
    BASE_URL = "https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0"
    DRAFT_MAP_GUID  = "9820E23DD3204072819C50B7A2E57093"
    MASTER_MAP_GUID = "ED910D9C5F0C4F8491F8FD10A0C5695B"

    def draft_url(self, draft_dslid: str) -> str:
        return f"{self.BASE_URL}:{self.DRAFT_MAP_GUID}.{draft_dslid}"

    def master_url(self, master_dslid: str) -> str:
        return f"{self.BASE_URL}:{self.MASTER_MAP_GUID}.{master_dslid}"

    def generate_dsl_content(self, dslid_list: list) -> str:
        return '\n'.join(str(d) for d in dslid_list if d)

    def level_number(self, level_str: str) -> int:
        if not level_str:
            return 0
        return len(level_str.replace(' Draft Copy', '').strip().split('.'))

    def is_draft(self, level_str: str) -> bool:
        return 'Draft Copy' in (level_str or '')

    def promotion_date_from_ms(self, ts_ms) -> str:
        from datetime import datetime
        if not ts_ms:
            return ''
        return datetime.fromtimestamp(ts_ms / 1000).strftime('%m/%d/%Y')

    def promotion_date_display(self, ts_ms) -> str:
        from datetime import datetime
        if not ts_ms:
            return 'Unknown'
        return datetime.fromtimestamp(ts_ms / 1000).strftime('%B %d, %Y')

nimbus = NimbusAdapter()
```

---

## data_init.py

```python
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'notifications.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            target_guid TEXT,
            read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasking_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            week_ending DATE NOT NULL,
            diagram_guid TEXT,
            diagram_title TEXT,
            diagram_level TEXT,
            activity_type TEXT,
            hours REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT (datetime('now')),
            updated_at TIMESTAMP DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pal_checklist_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            promotion_date TEXT NOT NULL,
            item_number INTEGER NOT NULL,
            checked INTEGER DEFAULT 0,
            item_notes TEXT,
            updated_at TIMESTAMP DEFAULT (datetime('now')),
            UNIQUE(username, promotion_date, item_number)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS did_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            did_number TEXT NOT NULL,
            title TEXT NOT NULL,
            contract_cdrl TEXT,
            status TEXT DEFAULT 'In Work',
            due_date DATE,
            owner TEXT,
            notes TEXT,
            revision TEXT,
            updated_at TIMESTAMP DEFAULT (datetime('now')),
            updated_by TEXT
        )
    """)
    conn.commit()
    conn.close()
```

---

## /get-mcpt API Response — Complete Field Reference

The backend returns a JSON array. Every field name below is the EXACT key returned. All are `Optional` except `GUID`.

```
"Promotion Date"          → Unix ms int  (datetime.fromtimestamp(v/1000))
"Level"                   → str          e.g. "1.11.2.1"
"Diagram Category (Identify Primary & Verify Selection)" → str
"Model Change Package Title" → str
"PEACE Portal TRB Change Package Title OR Info Only" → str
"PEACE Portal TRB Change Package Description" → str
"NAT Contact"             → str
"SP Folder Created"       → bool|null    THREE STATES
"Tool Entry Created"      → bool|null    THREE STATES
"Related Files Posted"    → bool|null    THREE STATES
"CR Package Ready"        → bool|null    THREE STATES
"Doc Registry Item Attatched" → bool|null  (intentional typo — do not fix)
"Updated Doc Registry URL"   → bool|null  THREE STATES
"All Diagrams Included In Tracker" → bool|null
"Peer Review Complete"    → bool|null    THREE STATES
"Notes"                   → str|null
"DSL UUID"                → str          = DraftDSLID. USE FOR DSL FILES AND DRAFT URL.
"Diagram Level"           → str          e.g. "1.11.2.1 Draft Copy"
"Draft Diagram Hyperlink" → str          pre-built, use directly
"Master Diagram Hyperlink"→ str          pre-built, use directly
"Diagram Title"           → str
"Diagram Ownership by Function / CoP" → str
"Draft Status"            → str          e.g. "Engineering Approved"
"Master Status"           → str
"Draft Template"          → str
"Master Template"         → str
"Owner"                   → str
"Version"                 → str          (draft version number as string)
"Master Version"          → str
"Authorization"           → str          e.g. "Update Pending"
"Authorizer"              → str          current authorizer display name
"Overlap Disposition"     → bool|null
"Multiple Occurrences"    → str          "Yes" or "No"
"AuthorizationSent"       → int
"AuthorizationAccepted"   → int
"TotalAuthorizations"     → int
"Authorized by POC"       → str          "Yes" or "No"
"Authorized by Eng Process TRB Chair" → str  "Yes", "No", or "N/A"
"Last Promotion Date"     → str          "12/16/2025" (MM/DD/YYYY string)
"Post-Promotion Template Changed in Draft (Not In-work)" → str "Yes"/"No"
"Post-Promotion Template Changed in Master (Not In-work)"→ str "Yes"/"No"
"Non-engineering Approved Diagram Templates" → str "Good"/"Warning"
"Links from Draft to Archive" → int
"Links from Draft to Master"  → int
"Links from Master to Draft"  → int
"Links from Sandbox"          → int
"Diagram Links Errors"        → int
"Document Links Errors"       → int
"Broken FLL"                  → int
"Total Errors"                → int      sum of all error counts
"URL"                         → str|null e.g. "AW-0100"
"Storyboard Impact"           → str      comma-separated
"Changes Since Last Promotion"→ int
"Change Log Entries"          → str      bullet-point string with • characters
"Master DSLID"                → str      = MasterDSLID. USE FOR MASTER URL.
"GUID"                        → str      NON-NULL. Primary key for all API operations.
```

---

## Module 1 — MCPT Main Table (routes/main_routes.py + static/js/mcpt-table.js)

### Flask Routes
```
GET  /api/mcpt/data         → proxy GET /get-mcpt; cache result for 30s
POST /api/mcpt/edit         → body: {"guid":"...","field":"exact API key name","value":"..."}
                              → proxy POST /edit-entry
POST /api/mcpt/add          → JSON body → proxy POST /add-entry
POST /api/mcpt/archive      → {"guid":"..."} → proxy POST /archive-entry (Admin/Director only)
POST /api/mcpt/remove       → {"guid":"..."} → proxy POST /remove-entry (Admin/Director only)
GET  /api/mcpt/diagram/<g>  → proxy GET /get-diagram?guid=g
```

### UI Behavior
- Sticky-header data grid, alternating row colors
- **Promotion date dropdown** in page header — populated from unique `"Promotion Date"` values in the fetched data, sorted descending. Persisted in `localStorage`. Filters rows client-side.
- **Primary visible columns** (default): Level | Diagram Title | Draft Status | NAT Contact | SP Folder | Tool Entry | CR Package | Authorizer | Total Errors | Notes | Actions
- **Error rows**: rows where `Total Errors > 0` get a red left border
- **Boolean cells**: `null → "—" (grey)`, `true → "✓" (green)`, `false → "✗" (red)`
- **Inline edit**: click editable cell → input/select appears → blur/Enter saves → POST /api/mcpt/edit
  - Editable fields: all boolean tracking columns, Notes, NAT Contact, Diagram Category, Model Change Package Title, PEACE Portal fields
  - Non-editable (read-only from Nimbus): Diagram Title, Level, Owner, Authorization status, error counts
- **Row expand**: click row → detail panel shows all 49 fields including Change Log Entries, Storyboard Impact, all error breakdowns
- **Filter bar**: Status chips (All / Unclaimed / Claimed / Engineering Approved / NTBC / Conceptual) + search input (matches Title, Level, Notes, NAT Contact)
- **"+ Add"** button (Admin only): modal form → GUID required, optional tracking fields
- **"Archive"** (Admin only): row action → confirm dialog
- **"Generate DSL"** button: navigates to DSL Generator tab with current promotion date pre-filled

### JavaScript Pattern
```javascript
const MCPTTable = (() => {
    let allRows = [];
    let currentPromoDate = null;
    // fetch, filter, render, edit handlers
    return { init, refresh };
})();
```

---

## Module 2 — Authorization Dashboard (routes/main_routes.py + static/js/auth-dashboard.js)

Built from data already in `/get-mcpt` response (AuthorizationSent, AuthorizationAccepted, TotalAuthorizations, Authorizer, "Authorized by POC", "Authorized by Eng Process TRB Chair").

Note: `/get-trb` detailed endpoint is backlog. This module uses the embedded authorization counts from `/get-mcpt`.

### UI
- Table: Level | Diagram Title | Authorizer | Auth Sent | Auth Accepted | Total Required | POC Auth | TRB Chair Auth | Progress Bar
- Progress bar per row: `AuthorizationAccepted / TotalAuthorizations` (green fill)
- Filter: "Pending Only" toggle hides fully authorized rows (`AuthorizationAccepted === TotalAuthorizations`)
- Color coding: fully authorized = green, partially = yellow, none sent = red
- "Send Reminder Emails" button (Admin): triggers POST /api/email/auth-reminders
- "Send Auth Request Emails" button (Admin): triggers POST /api/email/auth-requests

---

## Module 3 — DSL File Generator (routes/dsl_routes.py + static/js/dsl-generator.js)

### Generation Logic
```python
import zipfile, io
from flask import send_file

STATUS_TO_DSL = {
    'Engineering Approved': 'PromotionEngineeringApproved',
    'Claimed':              'PromotionClaimed',
    'Unclaimed':            'PromotionUnclaimed',
    'Not To Be Claimed':    'PromotionNTBC',
}

def generate_dsl_zip(rows, promotion_date_str):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Category files — use "DSL UUID" field (= DraftDSLID)
        categories = {name: [] for name in STATUS_TO_DSL.values()}
        categories['PromotionPromoOnly'] = []
        by_authorizer = {}  # display_name → [dslid, ...]

        for row in rows:
            dslid = row.get('DSL UUID', '') or ''
            if not dslid:
                continue
            status = row.get('Draft Status', '')
            cat = STATUS_TO_DSL.get(status)
            if cat:
                categories[cat].append(dslid)

            # Per-authorizer files
            authorizer = row.get('Authorizer', '') or ''
            sent = row.get('AuthorizationSent', 0) or 0
            accepted = row.get('AuthorizationAccepted', 0) or 0
            if authorizer and sent > 0 and accepted < (row.get('TotalAuthorizations') or 1):
                by_authorizer.setdefault(authorizer, []).append(dslid)

        for cat_name, dslids in categories.items():
            zf.writestr(f'{cat_name}.dsl', '\n'.join(dslids))

        for name, dslids in by_authorizer.items():
            safe = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            zf.writestr(f'AuthDSL_{safe}.dsl', '\n'.join(dslids))

    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name=f'mcpt_dsl_{promotion_date_str}.zip',
                     mimetype='application/zip')
```

### Flask Route
```
POST /api/dsl/generate   → body: {"promotion_date": "2026-04-04"}
                          → fetches /get-mcpt, filters by date, generates ZIP
```

### UI
- Promotion date pre-filled from current selection
- Preview table: one row per DSL file showing filename + count of DSLIDs
- "Download ZIP" button — uses iframe download (not window.open — popup blockers)

---

## Module 4 — Weekly Tasking Report (routes/tasking_routes.py + static/js/tasking.js)

### Flask Routes
```
GET    /api/tasking/entries              → IC: own; Director/Admin: all
POST   /api/tasking/entries              → add entry (all roles)
PUT    /api/tasking/entries/<id>         → edit own entry
DELETE /api/tasking/entries/<id>         → delete own (Admin can delete any)
GET    /api/tasking/weeks                → list of available week-ending dates
GET    /api/tasking/export/word          → Word .docx download (Director/Admin)
```

### Tasking Entry Form Fields
- Week Ending Date (Monday-anchored week calculation)
- Diagram GUID (autocomplete from MCPT data → shows Level + Title)
- Activity Type (dropdown: Modeling, Review, Authorization, Administration, Meeting, Other)
- Hours (number, 0.5 increments)
- Notes (textarea)

### Word Export (python-docx)
- Title: "Weekly Tasking Report — Week Ending {date}"
- One section per IC (Director/Admin view) or single section (IC view)
- Table per section: Level | Diagram Title | Activity | Hours | Notes
- Summary row: Total hours for IC
- Document-level summary: all ICs, total hours by activity type

### Director Consolidated View
- Grouped by IC, then by diagram
- Total hours per IC this week
- Trend arrow vs. previous week (stored in tasking DB)

---

## Module 5 — Metrics: Charging (routes/metrics_routes.py)

### Design Rule — NO HARDCODED COLUMN POSITIONS
**Never reference columns by letter (A, B, C...) or index (0, 1, 2...).** Always detect columns
by reading row 1 headers from the uploaded file. This makes the module work on any SAP export
regardless of how the user configured the report. Use case-insensitive, stripped header matching.

### Known Column Names — CONFIRMED FROM Charging.xlsm (for reference only, not for hard-coding)
These are the actual column names in the real SAP export. Document them so the header detector
knows what to look for, but all access must go through the dynamic `col` index map:
```
Fiscal Year | Fiscal Month | Pay Period | Week Ending Date | Pay Period Week Ending
Work Date | Employee ID | Employee ID2 | Employee Full Name | Employee Email
Employee Cost Center | Sender Cost Center | Att/Absence Type | Att/Absence Type3
Charge Number | Network | Order | Ship | Supplemental 2 | Supplemental 3 | Hours | Clean Hours
```
Key business rules from the VBA:
- **Order** column: filter rows where value == charge_order (admin-configurable, default `9L99G054`)
- **Att/Absence Type** column: exclude rows containing "PTO", "HOL", or "UNP"
- **Pay Period** column: SAP exports are cumulative — use ONLY the rows with the highest Pay Period value to avoid double-counting YTD hours
- **Hours** column: raw value may be formatted as `"8.0 H"` — strip " H" suffix and convert to float
- **Clean Hours** column: if present, prefer it over Hours (it is pre-cleaned by a prior macro step)
- **Employee Full Name**: primary display name for pivot rows

### Processing Logic
```python
from collections import defaultdict
import openpyxl

EXCLUDED_ATT_TYPES = {'PTO', 'HOL', 'UNP'}

def _detect_col(headers, *candidates):
    """Return column index for the first matching candidate name (case-insensitive)."""
    norm = [h.lower().strip() for h in headers]
    for c in candidates:
        try:
            return norm.index(c.lower().strip())
        except ValueError:
            pass
    return None

def _parse_hours(val):
    """Parse SAP hours value: strips ' H' suffix, converts to float."""
    if val is None or val == '':
        return 0.0
    return float(str(val).replace(' H', '').strip() or 0)

def process_charging(filepath, charge_order='9L99G054'):
    """
    Build pivot: Employee Full Name × Fiscal Month → hours.
    - Reads header row dynamically; no column positions assumed.
    - Filters to charge_order, excludes PTO/HOL/UNP, uses max Pay Period only.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb['Data'] if 'Data' in wb.sheetnames else wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = [str(h).strip() if h else '' for h in rows[0]]

    # Detect all needed columns by name — no position assumptions
    c_payperiod = _detect_col(headers, 'Pay Period')
    c_order     = _detect_col(headers, 'Order')
    c_att       = _detect_col(headers, 'Att/Absence Type', 'Att/Absence Type3')
    c_emp       = _detect_col(headers, 'Employee Full Name', 'Employee ID')
    c_month     = _detect_col(headers, 'Fiscal Month')
    c_hours_clean = _detect_col(headers, 'Clean Hours')
    c_hours_raw   = _detect_col(headers, 'Hours')

    # Find max Pay Period to scope to most-recent pay period only
    max_pp = 0
    if c_payperiod is not None:
        for row in rows[1:]:
            pp = row[c_payperiod]
            if isinstance(pp, (int, float)) and pp > max_pp:
                max_pp = float(pp)

    pivot = defaultdict(lambda: defaultdict(float))
    months_seen = set()

    for row in rows[1:]:
        # Filter: max pay period only
        if c_payperiod is not None and float(row[c_payperiod] or 0) != max_pp:
            continue
        # Filter: matching charge order
        if c_order is not None and str(row[c_order] or '').strip() != charge_order:
            continue
        # Filter: exclude PTO/HOL/UNP
        if c_att is not None:
            att = str(row[c_att] or '').strip()
            if any(excl in att for excl in EXCLUDED_ATT_TYPES):
                continue
        emp = str(row[c_emp] or 'Unknown') if c_emp is not None else 'Unknown'
        month = row[c_month] if c_month is not None else None
        if month is not None:
            months_seen.add(month)
        # Prefer Clean Hours; fall back to Hours
        if c_hours_clean is not None and row[c_hours_clean] not in (None, ''):
            hours = _parse_hours(row[c_hours_clean])
        elif c_hours_raw is not None:
            hours = _parse_hours(row[c_hours_raw])
        else:
            hours = 0.0
        pivot[emp][month] = pivot[emp].get(month, 0.0) + hours

    wb.close()
    return {
        'pivot': {k: dict(v) for k, v in pivot.items()},
        'months': sorted(m for m in months_seen if m is not None),
        'max_pay_period': max_pp,
        'charge_order': charge_order,
        'detected_headers': headers,   # Return for UI preview/debugging
    }
```

### UI
- Upload button: accepts .xlsx or .xlsm SAP export
- After process: show pivot table — rows = Employee Full Name, columns = Fiscal Month (1–12), values = hours
- Grand Total column (right) + Grand Total row (bottom)
- Charge order filter at top (pre-filled from config `SAP_CHARGE_ORDER`)
- "Export to Excel" button — styled pivot table with auto-fit columns

### Flask Routes
```
POST /api/metrics/charging/upload    → multipart form; save to temp dir; return {"preview": [...first 5 rows...]}
POST /api/metrics/charging/process   → {"filename": "...", "charge_order": "9L99G054"} → pivot data
GET  /api/metrics/charging/export    → download styled Excel pivot table (must have processed data in session)
```

---

## Module 6 — Metrics: NimbusBOE (routes/metrics_routes.py)

### Design Rule — NO HARDCODED COLUMN POSITIONS
Same as Module 5: detect all columns by reading header row 1. Never reference by position.
The NimbusBOE workbook produces a "CleanData" sheet — the MCPT app accepts this OR the raw
SAP export and detects whichever columns are present.

### Known Column Names — CONFIRMED FROM NimbusBOE.xlsm (for reference, not for hardcoding)
CleanData sheet columns (11 confirmed): `Fiscal Year`, `Fiscal Quarter`, `Fiscal Month`,
`Pay Period Week Ending`, `Week Ending Date`, `Employee ID`, `Att/Absence Type`,
`Supplemental 1`, `Supplemental 2`, `Supplemental 3`, `Hours`

Raw SAP export also has: `Order` column (filter by charge_order), `Att/Absence Type` (exclude PTO/HOL/UNP)

Key business rules from the VBA:
- Filter: `Order` == charge_order (admin-configurable, default `9L99G054`)
- Exclude: `Att/Absence Type` containing "PTO", "HOL", or "UNP"
- Scope: current fiscal year only (`Fiscal Year` == current year AND `Fiscal Month` <= current month)
- `Hours` in CleanData is already cleaned (no " H" suffix); in raw SAP may have " H" suffix — strip it
- `Employee ID` is the display key for BOE table rows (NimbusBOE uses Employee ID, not full name)
- Group by: Employee ID × Fiscal Month → sum hours
- Also group by: Employee ID × Supplemental 2 → sum hours (second tab)

### Processing Logic
```python
from datetime import date as _date
from collections import defaultdict
import openpyxl

BOE_EXCLUDED_ATT = {'PTO', 'HOL', 'UNP'}

def process_boe(filepath, charge_order='9L99G054'):
    """
    Accept CleanData export or raw SAP file. Detect columns dynamically from header row.
    Returns YTD monthly totals and per-supplemental breakdown.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    # Prefer CleanData sheet (pre-processed); fall back to Data or active
    target = next((s for s in ['CleanData', 'Data'] if s in wb.sheetnames), None)
    ws = wb[target] if target else wb.active

    today = _date.today()
    current_year, current_month = today.year, today.month

    rows = list(ws.iter_rows(values_only=True))
    headers = [str(h).strip() if h else '' for h in rows[0]]

    # Detect columns by name — no positions assumed
    c = {name: headers.index(name) for name in headers if name in [
        'Fiscal Year', 'Fiscal Month', 'Employee ID', 'Att/Absence Type',
        'Supplemental 1', 'Supplemental 2', 'Supplemental 3', 'Hours', 'Order'
    ] if name in headers}
    # Also check for duplicated column names (Employee ID appears twice in raw SAP — pick last occurrence)
    for idx, h in enumerate(headers):
        if h in c:
            c[h] = idx   # will naturally keep last occurrence

    monthly = defaultdict(lambda: defaultdict(float))
    by_supp = defaultdict(lambda: defaultdict(float))
    months_seen = set()

    for row in rows[1:]:
        if not any(row):
            continue
        # Filter by charge order if present
        if 'Order' in c and str(row[c['Order']] or '').strip() != charge_order:
            continue
        # Exclude PTO/HOL/UNP
        if 'Att/Absence Type' in c:
            att = str(row[c['Att/Absence Type']] or '').strip()
            if any(excl in att for excl in BOE_EXCLUDED_ATT):
                continue
        # Scope to current year/month
        fy  = row[c['Fiscal Year']]  if 'Fiscal Year'  in c else None
        fm  = row[c['Fiscal Month']] if 'Fiscal Month' in c else None
        if fy is not None and fy != current_year:
            continue
        if fm is None or int(fm) > current_month:
            continue
        emp   = str(row[c.get('Employee ID', -1)] or 'Unknown') if 'Employee ID' in c else 'Unknown'
        supp2 = str(row[c.get('Supplemental 2', -1)] or '').strip() if 'Supplemental 2' in c else ''
        hrs_raw = row[c['Hours']] if 'Hours' in c else None
        hrs = float(str(hrs_raw).replace(' H', '').strip() or 0) if hrs_raw not in (None, '') else 0.0
        months_seen.add(int(fm))
        monthly[emp][int(fm)] += hrs
        if supp2:
            by_supp[emp][supp2] += hrs

    wb.close()
    return {
        'monthly': {k: dict(v) for k, v in monthly.items()},
        'by_supp':  {k: dict(v) for k, v in by_supp.items()},
        'months':   sorted(months_seen),
        'fiscal_year': current_year,
        'charge_order': charge_order,
        'detected_headers': headers,
    }
```

### UI
- Upload button: accepts .xlsx, .xlsm (CleanData sheet or raw SAP export)
- Charge Order field (pre-filled from config `SAP_CHARGE_ORDER`, e.g. `9L99G054`)
- Two tabs after processing:
  - **Monthly Summary**: Employee × Fiscal Month grid (hours), row totals, column totals
  - **By Supplemental Code**: Employee × Supp2/Supp3 breakdown
- "Export to Excel" button

### Flask Routes
```
POST /api/metrics/boe/upload     → multipart; save to temp; return {"preview": [...]}
POST /api/metrics/boe/process    → {"filename":"...", "charge_order":"9L99G054"} → BOE data
GET  /api/metrics/boe/export     → Excel download of BOE table
```

---

## Module 7 — Metrics: DID Working (routes/metrics_routes.py + static/js/metrics.js)

### Design Rule — NO HARDCODED COLUMN POSITIONS
Same as Modules 5 and 6: detect all columns by header name from the uploaded file.
The column name lists below are documentation of the confirmed column names — use them for
header matching, never for position indexing.

### What This Module Is — CONFIRMED FROM DID Working.xlsm VBA + Sheet Analysis
DID Working is a **government Data Item Description (DID) gap analysis tool**. It tracks which
DI-coded CDRLs (Contract Data Requirements List items) appear in which contracts, matches them
against the DLA (Defense Logistics Agency) DID database, and shows whether DIDs are current
and in use in Nimbus process diagrams.

This is a **read/display** module — no local DB needed. Users upload the "Raw Data" sheet export
from the DID Working.xlsm workbook and the app renders the analysis.

### Raw Data Sheet — 24 CONFIRMED COLUMNS (from openpyxl header read)
```python
DID_RAW_COLUMNS = [
    'Platform',                       # Col A — e.g. "E-2D", "RQ-4", "Triton"
    'Contract Title',                 # Col B — contract name (used as pivot column header)
    'DID #',                          # Col C — raw DID number as submitted (may be dirty)
    'DID Title',                      # Col D — raw title
    'Clean DID #',                    # Col E — normalized DI code, e.g. "DI-ADMN-81250"
    'Matched Title',                  # Col F — title from DLA DI database (or "Not Found")
    'Title Comparison Result',        # Col G — "Match", "OK As-is (same meaning)", "No Match"
    'Title Comparison Result Human',  # Col H — manual human override for G
    'Final Comparison',               # Col I — H if present, else G
    'CDRL Title',                     # Col J — title of the CDRL as in the contract
    'CDRL Sub-Title',                 # Col K
    'Function',                       # Col L — raw function label
    'Translated Function',            # Col M — mapped org function (e.g. "Systems Engineering (SE)")
    'Manual / Verified Function',     # Col N — human override for M
    'Final Translated Function',      # Col O — N if present, else M
    'POC',                            # Col P — point of contact
    'Actual CDRL Delivery',           # Col Q
    'Status Notes',                   # Col R
    'Approval / Info Item',           # Col S — e.g. "Approval", "Info"
    'CDRL Type',                      # Col T
    'Program Areas',                  # Col U
    'FSC/Area',                       # Col V — Federal Supply Classification grouping code
    'Status',                         # Col W — "A" = Active (filter for analysis)
    'In Doc Reg',                     # Col X — numeric if in Document Registry (truthy = Yes)
]
```

### DLA DI Search Results Sheet — 6 CONFIRMED COLUMNS
```python
DID_DLA_COLUMNS = [
    'Img / File Available',   # "Y" or "N"
    'Document ID',            # DI code, e.g. "DI-STDZ-80000C NOT 1"
    'Status',                 # "A" = Active
    'FSC/Area',               # Federal Supply Classification
    'Doc Date',               # datetime
    'Title',                  # Full DID title
]
```

### Analysis Pivot — CONFIRMED OUTPUT STRUCTURE
The workbook produces 4 pivot views. MCPT renders all 4 as tabs:

**Tab 1: By Function** — columns: FSC/Area or Clean DID # | Airworthiness (AW) | Avionics Integration (AvI) | Business Management (BM) | Contracts | Global Supply Chain (GSC) | Mission Assurance (MA) | Product Support (PS) | Production | Program Management (PM) | Security | Software (SW) | Systems Engineering (SE) | Test & Evaluation (T&E) | Grand Total (Function)

**Tab 2: By Platform** — columns: FSC/Area or Clean DID # | E-2D | RQ-4 | Strike | Triton | Grand Total (Platform)

**Tab 3: By Contract** — columns: FSC/Area or Clean DID # | [dynamic contract names from Raw Data "Contract Title" column] | Grand Total (Contract) | # of Contracts Using the DID | Primary Org | In Nimbus

**Tab 4: Raw Data** — full 24-column table, filterable/sortable

### DID Gap Criteria (from DID Reporting Table sheet)
A DID is flagged as a **gap** when: it appears in 2 or more contracts (# of Contracts Using the DID ≥ 2).
Highlight these rows in yellow in the Contract pivot tab.

### Processing Logic
```python
def process_did_working(filepath):
    """
    Read 'Raw Data' sheet. Build 3 pivot summaries and return raw row data.
    Rows grouped by FSC/Area, then by Clean DID # within each group.
    Only include rows where Status == 'A' (Active).
    'In Nimbus' = True if 'In Doc Reg' column is non-empty and numeric.
    'Primary Org' = contract column with the highest count for that DID.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb['Raw Data'] if 'Raw Data' in wb.sheetnames else wb.active
    headers = [str(h).strip() if h else '' for h in
               next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
    # Detect all columns dynamically — no position hardcoding. Works on any Raw Data export.
    col = {h: idx for idx, h in enumerate(headers) if h}

    raw_rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        status = str(row[col.get('Status', -1)] or '').strip() if 'Status' in col else ''
        if status != 'A':
            continue
        record = {name: row[col[name]] for name in col}
        record['in_nimbus'] = bool(record.get('In Doc Reg'))
        raw_rows.append(record)

    wb.close()

    # Build contract pivot: fsc → did → contract → count
    contract_set = sorted({str(r.get('Contract Title') or '').strip()
                           for r in raw_rows if r.get('Contract Title')})
    fsc_groups = {}
    for r in raw_rows:
        fsc = str(r.get('FSC/Area') or '').strip() or 'Unknown'
        did = str(r.get('Clean DID #') or '').strip()
        contract = str(r.get('Contract Title') or '').strip()
        fsc_groups.setdefault(fsc, {}).setdefault(did, {'contracts': {}, 'in_nimbus': False})
        if contract:
            fsc_groups[fsc][did]['contracts'][contract] = fsc_groups[fsc][did]['contracts'].get(contract, 0) + 1
        if r.get('in_nimbus'):
            fsc_groups[fsc][did]['in_nimbus'] = True

    # Add gap flag and primary org
    for fsc in fsc_groups:
        for did in fsc_groups[fsc]:
            contracts = fsc_groups[fsc][did]['contracts']
            total = sum(contracts.values())
            num_contracts = len([v for v in contracts.values() if v > 0])
            fsc_groups[fsc][did]['grand_total'] = total
            fsc_groups[fsc][did]['num_contracts'] = num_contracts
            fsc_groups[fsc][did]['is_gap'] = (num_contracts >= 2)  # DID gap criteria
            fsc_groups[fsc][did]['primary_org'] = max(contracts, key=contracts.get) if contracts else ''

    return {
        'raw_rows': raw_rows,
        'fsc_pivot': fsc_groups,
        'contract_columns': contract_set,
    }
```

### Flask Routes
```
POST /api/metrics/did/upload     → multipart; save to temp; return {"preview": [...first 5 raw rows...]}
POST /api/metrics/did/process    → {"filename":"..."} → pivot data (all 4 tab payloads)
GET  /api/metrics/did/export     → Excel download with 4 sheets matching the 4 UI tabs
```

### Export (Excel — 4 Sheets)
- Sheet 1: "By Contract" — FSC/Area header rows (grey) + DID rows, contract columns, gap rows yellow
- Sheet 2: "By Function" — FSC/Area + DID rows × function columns
- Sheet 3: "By Platform" — FSC/Area + DID rows × platform columns
- Sheet 4: "Raw Data" — all 24 columns, auto-fit

---

## Module 8 — PAL Checklist (routes/pal_routes.py + static/js/pal.js)

### 25 Checklist Items (ALL confirmed — Category: Clerical)

Store these as a hardcoded list in `pal_routes.py`:

```python
PAL_ITEMS = [
    (1,  "Document number formally reserved"),
    (2,  "Check front page is filled out properly (date = TRB date, doc number is good with no brackets, doc owner is spelled like email incl [US] (AS) afterward, PA element is correct/hyperlinked correctly)"),
    (3,  "Are the report title, document number, and revision letter included in the header"),
    (4,  "Check the Table of Contents – when there are lowercase letters that are supposed to be uppercase, go to that section of the doc/update with caps/refresh the table of contents"),
    (5,  "Is the revision letter correct"),
    (6,  "Correct TRB date included"),
    (7,  "Is the TOC correct"),
    (8,  "Roman Numerals used for Table of Contents, up until page 1"),
    (9,  "Are all the figures and tables numbered and referenced correctly"),
    (10, "Are the margins, paragraph indentations and bullets/numbering correct"),
    (11, "Are all sheets numbered correctly"),
    (12, "Are the Contract, Line Item Number, and Data Item correct"),
    (13, "Is the Distribution Statement correct"),
    (14, "Make sure Nimbus is spelled Nimbus and not NIMBUS"),
    (15, "Make sure hyperlinks to Nimbus are correct – and to the MASTER version, not DRAFT"),
    (16, "Take out everywhere they are calling PAL manuals \"process documents\""),
    (17, "Make sure NGAS is Aeronautics sector, not Aerospace sector"),
    (18, "For old PAL manuals, ensure there are no ref to old orgs, e.g. \"ISWR\" (Integrated Systems Western Region), DPTO, etc. [Integrated Systems should be replaced with Aeronautics Systems]"),
    (19, "There should be no \"shalls\". State as fact – something happens. \"Need\", \"will\", \"should\", \"do/does\", \"are/is\", etc."),
    (20, "Has spell check passed? Also review blue wavy underlined grammar suggestions (usually for semi-colon usage, \"that\" vs \"which\", correct words)"),
    (21, "Check all references are in reference section (search on common doc prefixes to find any hiding) – and check they are correct"),
    (22, "Check all docs called out in reference section are actually in the doc"),
    (23, "Ensure all hyperlinks work"),
    (24, "Check the first time an acronym is used, that it is spelled out"),
    (25, "Check all acronyms in the acronym list are used"),
]
```

### UI
- 25 checkboxes with item text, grouped under "Clerical" header
- Progress bar: N/25 complete
- Optional notes field per item (expand on click)
- State saved per-user per-promotion-date in `pal_checklist_state` table
- "Export" button → print-friendly HTML page

### Flask Routes
```
GET  /api/pal/checklist/<promo_date>   → checklist state for current user
POST /api/pal/checklist/save           → {"promotion_date":"...","item":N,"checked":true,"notes":"..."}
GET  /api/pal/checklist/export         → HTML print view
GET  /api/pal/items                    → list of all 25 items
```

---

## Module 9 — PAL Helper (routes/pal_routes.py + static/js/pal.js)

### 12 Disciplines (confirmed)
```python
PAL_DISCIPLINES = ['VE', 'T&E', 'SW', 'SRV', 'SE', 'PS', 'PM&P', 'FS', 'EP&T', 'Engineering', 'AWWSC', 'AvI']

DISCIPLINE_NAMES = {
    'VE': 'Vehicle Engineering',
    'T&E': 'Test & Evaluation',
    'SW': 'Software',
    'SRV': 'Survivability',
    'SE': 'Systems Engineering',
    'PS': 'Product Support',
    'PM&P': 'Program Management & Planning',
    'FS': 'Flight Sciences',
    'EP&T': 'Engineering Processes & Tools',
    'Engineering': 'General Engineering',
    'AWWSC': 'AW & WSC',
    'AvI': 'Avionics & Integration',
}
```

Embed the full PALHelperFile data as a JSON file at `static/data/pal_helper_data.json`. Each document has: `name, title, revision, release_date, owner, doc_type, path, discipline`.

SharePoint URL construction: `https://as.northgrum.com/{path}/{name}` (base URL configurable in admin settings).

### UI
- Discipline selector grid (12 tiles with icons)
- Click discipline → document list with columns: Name | Title | Revision | Release Date | Owner | Doc Type
- Each row has "Open in SharePoint" link (constructed from path + name)
- Filter by Doc Type within discipline (Checklist, PAL Manual, Formal Doc, Template)

### Flask Routes
```
GET /api/pal/helper                      → all documents (all disciplines)
GET /api/pal/helper/<discipline_code>    → documents for one discipline
```

---

## Module 10 — Admin Panel (routes/admin_routes.py + static/js/admin.js)

All routes require `require_role('Admin', 'Director')`.

### Sections and Routes
```
GET  /api/admin/config              → all config values
POST /api/admin/config              → save config updates (writes mcpt_config.json)

GET  /api/admin/users               → stub until /get-user endpoint live; returns [{username, role, email}]
POST /api/admin/users               → add user to local override table
PUT  /api/admin/users/<username>    → edit user

GET  /api/admin/promotion-dates     → unique promotion dates from /get-mcpt data
```

### Config Fields Exposed in UI
| Field | Label | Default |
|---|---|---|
| `API_BASE_URL` | Backend API URL | `http://127.0.0.1:8000` |
| `SMTP_HOST` | SMTP Relay Host | (empty) |
| `SMTP_PORT` | SMTP Port | 587 |
| `SMTP_FROM` | From Address | (empty) |
| `SAP_CHARGE_ORDER` | SAP Charge Order | `9L99G054` |
| `SAP_EXCLUDED_SUPP_CODES` | Excluded SAP Codes | `PTO, HOL, UNP` |
| `TRB_CHAIR_NAME` | TRB Chair Name | `Jamie Dunham` |
| `DEV_ROLE` | Dev Auth Override | `Admin` |
| `SHAREPOINT_BASE_URL` | SharePoint Base URL | (empty) |

"Test Email" button → POST /api/email/test → sends test email to current user's address.

---

## Module 11 — Notifications (routes/notification_routes.py + static/js/notifications.js)

### Flask Routes
```
GET  /api/notifications/count      → {"count": N}  — polled every 60 seconds
GET  /api/notifications/feed       → last 50 for current user, newest first
POST /api/notifications/read/<id>  → mark one read
POST /api/notifications/read-all   → mark all read for current user
```

### Notification Types
`row_edit`, `auth_request`, `promo_ready`, `system`

### Bell UI
- Bell icon in app header
- Red badge with count (hidden when 0)
- Click → slide-out panel from right
- Each item: type icon + message + time-ago + mark-read button
- "Mark all read" at top of panel
- Auto-poll: `setInterval(() => fetchCount(), 60000)`

### Creating Notifications (internal, called by other route handlers)
```python
def create_notification(username, type_, message, target_guid=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO notifications (username, type, message, target_guid) VALUES (?,?,?,?)",
        (username, type_, message, target_guid)
    )
    conn.commit()
    conn.close()
```

---

## Module 12 — Email Automation (routes/admin_routes.py)

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(config, to: list, subject: str, html_body: str):
    if not config.get('SMTP_HOST'):
        raise ValueError("SMTP not configured. Set SMTP_HOST in Admin Panel.")
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = config['SMTP_FROM']
    msg['To'] = ', '.join(to)
    msg.attach(MIMEText(html_body, 'html'))
    with smtplib.SMTP(config['SMTP_HOST'], config['SMTP_PORT']) as server:
        server.sendmail(config['SMTP_FROM'], to, msg.as_string())
```

### Email Type 1: Status Summary
- **Route**: `POST /api/email/status-summary`
- **Trigger**: Admin manually
- Fetches /get-mcpt, groups by status, builds HTML table per status group
- Subject: `MCPT Promotion Cycle Status — {promotion_date}`

### Email Type 2: Missing Authorization Reminder
- **Route**: `POST /api/email/auth-reminders`
- Groups rows where `AuthorizationSent > 0` AND `AuthorizationAccepted < TotalAuthorizations`
- One email per authorizer (from `Authorizer` field) listing their pending diagrams

### Email Type 3: Authorization Request
- **Route**: `POST /api/email/auth-requests`
- Body: `{"guids": ["...", "..."]}`
- Sends per-diagram email to the listed Authorizer with diagram link

### Test Email
- **Route**: `POST /api/email/test`
- Sends test message to current user

---

## Module 13 — Export

### Excel Export (openpyxl)
```
GET /api/export/mcpt-excel    → MCPT table for current promotion date
GET /api/export/did-excel     → DID Working table
GET /api/export/charging      → delegates to metrics module
GET /api/export/boe           → delegates to metrics module
```

All exports:
- `io.BytesIO()` buffer — no temp files
- Frozen first row (header)
- Auto-sized columns
- `send_file(buf, as_attachment=True, download_name='...xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')`

### Word Export (python-docx)
```
GET /api/export/tasking-word    → delegates to tasking module
```

---

## Single-Page App — templates/index.html

Standard HTML5 boilerplate. Navigation tabs map to module JS files:

Tabs: MCPT Table | Authorization | DSL Generator | Tasking | Metrics | PAL | Admin (admin/director only)

Notification bell in header. Promotion date selector in header (persisted in localStorage).

Each module section: `<section id="module-{name}" class="module">` — active class shows it.

---

## CSS Key Rules (static/css/main.css)

- Module visibility: `.module { display: none; } .module.active { display: block; }`
- **NEVER set `style.display` directly on modules** — always `classList.add/remove('active')`
- Three-state boolean cells: `.bool-null { color: #999; }`, `.bool-true { color: #22c55e; }`, `.bool-false { color: #ef4444; }`
- Error row highlight: `tr.has-errors { border-left: 3px solid #ef4444; }`
- Notification badge: `.badge { background: red; color: white; border-radius: 50%; ... }`

---

## requirements.txt

```
flask>=3.0.0
waitress>=3.0.0
requests>=2.31.0
openpyxl>=3.1.0
python-docx>=1.1.0
sspilib>=0.1.0
```

---

## Start_MCPT.bat

```bat
@echo off
cd /d C:\MCPT
python app.py
pause
```

---

## Build Order

Build in this exact sequence — each layer depends on the one before:

1. `config.py`, `data_init.py`, `nimbus_adapter.py`, `auth.py` — foundation
2. `app.py`, `routes/__init__.py`, `templates/index.html`, `static/css/main.css`, `static/js/app.js` — shell
3. `routes/main_routes.py` + `static/js/mcpt-table.js` — Module 1 (highest value, confirms API works)
4. `routes/dsl_routes.py` + `static/js/dsl-generator.js` — Module 3 (DSL generation, critical)
5. `static/js/auth-dashboard.js` — Module 2 (uses data already loaded in Module 1)
6. `routes/notification_routes.py` + `static/js/notifications.js` — Module 11
7. `routes/admin_routes.py` + `static/js/admin.js` — Module 10 (email config needed for Module 12)
8. `routes/admin_routes.py` email handlers — Module 12
9. `routes/tasking_routes.py` + `static/js/tasking.js` — Module 4
10. `routes/metrics_routes.py` (charging + BOE + DID) + `static/js/metrics.js` — Modules 5, 6, 7
11. `routes/pal_routes.py` + `static/js/pal.js` — Modules 8, 9
12. Export handlers woven into relevant routes — Module 13

---

## Final Checklist Before Declaring Done

- [ ] `/api/mcpt/data` returns data (confirm against `127.0.0.1:8000/get-mcpt`)
- [ ] Promotion date filter works client-side
- [ ] Boolean three-state rendering correct (null/true/false)
- [ ] Inline edit sends exact API field name as `"field"` param
- [ ] DSL ZIP downloads with correct filename and file contents
- [ ] Notification bell polls every 60s and badge updates
- [ ] Admin config saves to `mcpt_config.json`
- [ ] TRB Chair field visible and editable in Admin Panel → System Settings
- [ ] All `open()` calls have `encoding='utf-8', errors='replace'`
- [ ] Waitress server starts on port 5060
- [ ] `Start_MCPT.bat` works from `C:\MCPT\`
