# MCPT Architecture Decisions

All architectural decisions made during pre-flight planning (2026-03-31).
Each decision includes rationale and any alternatives considered.

---

## AD-1: Flask + Waitress (Not Flask Dev Server)

**Decision**: Production server uses Waitress WSGI. Flask dev server is never used in deployment.

**Rationale**:
- Flask's built-in server is single-threaded and explicitly not production-ready
- Waitress is pure Python (no C compiler required), production-grade, and handles concurrent requests
- Critical for MCPT: multiple ICs editing rows simultaneously requires thread safety
- Same pattern proven in AEGIS (sister app)

**Configuration**:
```python
from waitress import serve
serve(app, host='0.0.0.0', port=5060, threads=8)
```

---

## AD-2: Vanilla JS / CSS / HTML — No Framework

**Decision**: Frontend uses pure JavaScript, CSS, and HTML. No React, Vue, Angular, or any JS framework.

**Rationale**:
- Deployed on air-gapped classified network — no CDN access, no npm, no build pipeline
- Zero external runtime dependencies = zero supply chain risk
- AEGIS proved this pattern works well at this scale
- Maintenance: anyone familiar with basic web dev can read the code

**Pattern**: Single-page app (SPA) with one `templates/index.html`. JavaScript organized as module IIFEs in `static/js/`.

---

## AD-3: Windows NTLM/Kerberos Authentication

**Decision**: Use Windows Integrated Authentication (sspilib/pywin32). No login screen.

**Rationale**:
- All users are on the Windows domain already
- NTLM/Kerberos auto-sends credentials from browser → server
- Zero friction: users never type a password
- Role lookup via `GET /get-user?username={windows_username}` → returns IC/Admin/Director
- If no user record exists → 403 Forbidden

**Implementation**:
- `sspilib` for NTLM token exchange
- Flask middleware extracts `windows_username` from auth context
- Role cached in Flask session for duration of session
- `@require_role('Admin')` decorator on protected routes

**Alternative considered**: Basic auth or API key — rejected, no domain integration.

---

## AD-4: Flask Proxy Pattern for All API Calls

**Decision**: ALL calls to the backend REST API go through Flask routes. The browser NEVER calls the backend API directly.

**Rationale**:
- CORS: browser cannot call cross-origin APIs without CORS headers. The backend team may not implement these.
- Auth injection: Flask proxy can inject API auth headers without exposing credentials to browser
- Abstraction: if the API URL/port changes, only one Flask route needs updating
- Error handling: Flask can normalize error responses before they reach the browser
- Rate limiting and logging can be centralized

**Pattern**:
```python
# Browser → Flask → Backend API
@app.route('/api/mcpt/data')
def proxy_get_mcpt():
    resp = requests.get(f"{BACKEND_API_URL}/get-mcpt", headers=auth_headers())
    return jsonify(resp.json())
```

---

## AD-5: Local SQLite Only for Notifications

**Decision**: The local Flask app has its own SQLite database (`data/notifications.db`) for notifications only. All MCPT tracking data lives in the backend API's database.

**Rationale**:
- Single source of truth: MCPT data belongs to the backend team's database
- Notifications are app-local state (read/unread, timestamps, user preferences)
- WAL mode for concurrent reads without blocking writes

**Schema (notifications.db)**:
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    type TEXT NOT NULL,          -- 'row_edit', 'auth_request', 'promo_ready', etc.
    message TEXT NOT NULL,
    target_guid TEXT,            -- related diagram GUID if applicable
    read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT (datetime('now'))
);
```

---

## AD-6: Nimbus Abstraction Layer

**Decision**: All Nimbus-specific code (URLs, GUID format, deep link construction, DSL file format) is isolated behind an abstraction layer (`nimbus_adapter.py`).

**Rationale**:
- Nimbus reached End of Life September 1, 2025. NGAS is on extended legacy support.
- When Nimbus is replaced (likely within 2-3 years), the adapter is the only file that changes
- All URL construction, DSLID handling, and DSL file generation routes through the adapter

**Interface**:
```python
class NimbusAdapter:
    BASE_URL = "https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0"
    MAP_GUID = "9820E23DD3204072819C50B7A2E57093"

    def diagram_url(self, guid: str) -> str: ...
    def generate_dsl_file(self, dsid_list: list, category: str) -> str: ...
    def parse_authorization_string(self, auth_str: str) -> dict: ...
```

---

## AD-7: SMTP Relay for Email (Not Azure AD / Graph API)

**Decision**: Use Python `smtplib` → internal Exchange SMTP relay. No OAuth, no Azure AD.

**Rationale**:
- Simplest approach for an internal corporate network
- IT can whitelist the server's IP at the SMTP relay (no credentials required)
- No tokens to manage, no auth expiry, no API registration
- Works entirely on internal network — no internet dependency

**Configuration** (admin-managed in Admin Panel):
- SMTP host (e.g., `smtp-relay.as.northgrum.com`)
- SMTP port (typically 25 or 587)
- From address (e.g., `mcpt-noreply@as.northgrum.com`)
- IT whitelists the server IP

---

## AD-8: In-App Notifications via 60-Second Poll

**Decision**: Notification feed uses client-side polling (60-second interval). No WebSockets.

**Rationale**:
- WebSockets require persistent connection management and add complexity
- At MCPT's scale (~10-20 concurrent users), polling is entirely sufficient
- 60 seconds is appropriate latency for "someone edited your row" notifications
- Simpler to implement, simpler to debug, zero extra dependencies

**Pattern**: Bell icon in header. Red badge count. Click → notification feed panel. Mark-as-read per item.

---

## AD-9: API Proxy for GET /edit-entry — JSON Body (Not Query String)

**Decision**: `POST /edit-entry` should use a JSON request body, not URL query parameters.

**Rationale**:
- URL query strings have a ~2,000 character limit
- Notes and Change Log entries can easily exceed this
- JSON body has no practical length limit
- More standard REST design

**Recommended format**:
```json
{ "guid": "ACDF1AE9385543888E91381F30D3F806", "field": "Notes", "value": "Updated text here..." }
```

This was raised with the dev team as Question #4 in `developer_questions_email.md`.

---

## AD-10: DSL Files — ZIP Download

**Decision**: DSL file generation produces a ZIP archive containing multiple `.dsl` files, served as a browser download.

**Rationale**:
- Multiple DSL files generated per promotion cycle (5 category files + N per-authorizer files)
- ZIP is standard and users can extract to wherever Nimbus Batch Server expects them
- Alternative (individual file downloads) creates too many browser prompts

**ZIP contents**:
```
mcpt_dsl_2026-04-04.zip
├── PromotionEngineeringApproved.dsl
├── PromotionClaimed.dsl
├── PromotionUnclaimed.dsl
├── PromotionNTBC.dsl
├── PromotionPromoOnly.dsl
├── AuthDSL_John_Smith.dsl
├── AuthDSL_Jane_Doe.dsl
└── ...
```

---

## AD-11: Windows Deployment — C:\MCPT\ Path

**Decision**: Deploy to `C:\MCPT\` (never OneDrive, never paths with spaces).

**Rationale**:
- AEGIS lesson learned (Lesson #195): OneDrive-synced paths cause I/O locking during SQLite WAL operations
- Paths with spaces break batch Python `-c` commands on Windows
- `C:\MCPT\` is clean, predictable, no sync interference

**Start method**: `Start_MCPT.bat` (double-click) or Windows Service via pywin32. Port 5060 (avoids conflict with AEGIS on 5050).

---

## AD-12: Role-Based Access Control (RBAC) via Middleware

**Decision**: Enforce RBAC via Flask decorator, not frontend visibility only.

**Rationale**:
- Frontend-only access control is not real security
- Every route that modifies data must check the user's role server-side
- Three roles: IC (view + edit own), Admin (edit any + manage), Director (Admin + charging + executive export)

**Pattern**:
```python
@require_role('Admin')
def admin_only_route():
    ...

@require_role('IC', 'Admin', 'Director')
def any_authenticated_route():
    ...
```

---

## AD-13: Promotion Date as First-Class Filter

**Decision**: Promotion date is a top-level filter applied to every MCPT view. Users select the active two-week cycle.

**Rationale**:
- All work is organized by promotion cycle (bi-weekly)
- Filtering by date is the first thing every user does
- Baking this into the UI as a persistent filter (not a search) reduces friction

**UI pattern**: Dropdown of available promotion dates in the header bar, persisted in `localStorage`.

---

## AD-14: All `open()` Calls Use UTF-8

**Decision**: Every file read/write operation includes `encoding='utf-8', errors='replace'`.

**Rationale**:
- Windows default encoding is cp1252 (Windows-1252)
- Any file containing non-ASCII characters will crash with `UnicodeDecodeError` on Windows without explicit encoding
- `errors='replace'` prevents crashes from malformed characters (e.g., special characters in diagram titles)

---

## AD-15: Export Uses `io.BytesIO` (Not Temp Files)

**Decision**: Excel, Word, and ZIP exports are generated in-memory using `io.BytesIO` and returned as Flask responses.

**Rationale**:
- No temp file cleanup needed
- No file permission issues on Windows
- Faster — no disk I/O
- Pattern proven in AEGIS

**Pattern**:
```python
buf = io.BytesIO()
wb.save(buf)
buf.seek(0)
return send_file(buf, as_attachment=True, download_name='mcpt_export.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
```
