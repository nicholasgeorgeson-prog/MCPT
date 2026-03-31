# MCPT Pre-Flight Q&A

All 43 pre-flight questions and answers gathered before build began.
Recorded 2026-03-31.

---

## Q1 — What is the purpose of MCPT?

**A**: MCPT (Model Change Package Tracker) replaces a suite of Excel/VBA workbooks used by the NAT (Nimbus Admin Team) at NGAS to manage TIBCO Nimbus process model diagrams through a bi-weekly promotion cycle. The team promotes diagrams from Draft state through Authorization and into Master. MCPT tracks every diagram's status, automates DSL file generation, manages authorization workflows, and produces reporting for directors.

---

## Q2 — How many users will use MCPT simultaneously?

**A**: Approximately 10-20 concurrent users. Small team. This drove the decision to use polling (not WebSockets) for notifications and Waitress with 8 threads for the web server.

---

## Q3 — What is the promotion cycle cadence?

**A**: Bi-weekly (every two weeks). Each cycle has a specific promotion date. All MCPT views are filtered by promotion date as a top-level filter.

---

## Q4 — What are the three user roles and their permissions?

**A**:
- **IC (Individual Contributor)**: View all data; edit only their own assigned rows; manage their own tasking entries.
- **Admin**: Edit any row; manage users/dropdowns; send emails; delegate authority; full MCPT management.
- **Director**: Everything Admin can do + access to charging view; consolidated tasking across all ICs; executive export formats.

---

## Q5 — How is authentication handled?

**A**: Windows Integrated Authentication (NTLM/Kerberos). The browser automatically sends the user's Windows domain credentials. No login screen, no password entry. The Flask app uses `sspilib`/`pywin32` to verify the NTLM token and extract the Windows username. Role is looked up via `GET /get-user?username={windows_username}` from the backend API.

---

## Q6 — What happens if a user is not in the user table?

**A**: The API returns 403 Forbidden. The Flask app shows an "Access Denied — contact your MCPT administrator" page. The user cannot proceed until an Admin adds them.

---

## Q7 — What is a GUID vs a DSLID?

**A**: Two completely different identifiers for the same diagram:
- **GUID**: Primary key in the database; used in Nimbus deep-link URLs; used in all API calls. Format: 32 uppercase hex chars, no dashes (e.g., `ACDF1AE9385543888E91381F30D3F806`).
- **DSLID**: Used in `.dsl` batch operation files for Nimbus Batch Server. Format TBD from dev team response.
- They are NOT interchangeable. The Diagrams table has both: `DraftDSLID` and `MasterDSLID` separate from `GUID`.

---

## Q8 — What is the Nimbus deep link URL format?

**A**:
```
https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:9820E23DD3204072819C50B7A2E57093.{DIAGRAM_GUID}
```
The map GUID `9820E23DD3204072819C50B7A2E57093` is hardcoded — all NGAS diagrams live in one map.

---

## Q9 — Is Nimbus still active?

**A**: TIBCO Nimbus reached End of Life September 1, 2025. NGAS is on extended legacy support. The tool still runs but receives no updates. A replacement is expected within 2-3 years. All Nimbus-specific code in MCPT is behind a `nimbus_adapter.py` abstraction layer — when the tool changes, only the adapter changes.

---

## Q10 — What is the diagram lifecycle?

**A**: Draft Created → Claimed (IC takes ownership) → Engineering Approved (IC marks complete) → Authorization Requested → Authorization Pending (authorizers sign off sequentially) → Promotion Ready → Promoted to Master.

---

## Q11 — What are the valid diagram statuses in MCPT?

**A**:
- `Unclaimed` — no IC has taken this diagram
- `Claimed` — an IC has claimed it and is working it
- `Engineering Approved` — IC marked it ready for authorization
- `Conceptual Image` — special type, no change required
- `Not To Be Claimed` (NTBC) — excluded from this promotion cycle

---

## Q12 — What is the authorization workflow?

**A**: Sequential + unanimous. Authorizers are listed in order (by `Sequence` column in Authorizations table). Each must sign off before the next is notified. All must approve. When all sign off, the diagram status becomes `"Promotion Ready - {date}"`. The authorization status is stored as a string with the date embedded (e.g., `"Authorization Pending - 2/13/2026"`).

---

## Q13 — What is a DSL file?

**A**: A plain-text file, one DSLID per line, used by the Nimbus Batch Server to perform bulk authorize/promote operations. MCPT generates them. The Batch Server consumes them. Two types: (1) five category DSL files based on diagram status; (2) per-authorizer DSL files for the authorization step.

---

## Q14 — What are the five DSL file categories?

**A**:
- `PromotionEngineeringApproved.dsl` — Status = Engineering Approved
- `PromotionClaimed.dsl` — Status = Claimed
- `PromotionUnclaimed.dsl` — Status = Unclaimed
- `PromotionNTBC.dsl` — Status = Not To Be Claimed
- `PromotionPromoOnly.dsl` — Promo-only flag set

---

## Q15 — What is the DSL ZIP download?

**A**: All DSL files (5 category + N per-authorizer) are packaged into a single ZIP file (`mcpt_dsl_{date}.zip`) served as a browser download. The user extracts it and feeds the files to the Nimbus Batch Server.

---

## Q16 — What backend API endpoints exist?

**A** (from developer email):
- `GET /get-mcpt` — full MCPT tracking table
- `GET /get-trb` — authorization/TRB progress data
- `GET /get-diagram?guid={GUID}` — single diagram details
- `POST /add-entry` — add new MCPT tracking row
- `POST /remove-entry` — remove by GUID
- `POST /edit-entry` — edit single field
- `POST /archive-entry` — archive by GUID

---

## Q17 — How are ALL backend API calls handled in MCPT?

**A**: Via Flask proxy. The browser calls Flask routes. Flask routes call the backend API and relay the response. The browser never calls the backend API directly. This handles CORS, auth injection, error normalization, and future URL changes.

---

## Q18 — How many diagrams are in the current dataset?

**A**: 194 rows confirmed from `Team_Dashboard-Diagrams.xlsx` in the Reports repo.

---

## Q19 — What email types does MCPT send?

**A**: Three email types:
1. **Status Summary Email** — Director-level overview of the promotion cycle (Engineering Approved count, Claimed count, Unclaimed count, NTBC count). Was `JamieEmail.bas` in VBA.
2. **Missing Authorization Reminder** — Per-authorizer email listing diagrams with overdue pending sign-offs. Was `MissingAuthorizations.bas` in VBA.
3. **Per-Authorizer Authorization Request** — Sent to each authorizer when a diagram enters the authorization queue.

---

## Q20 — How is email sent?

**A**: `smtplib` → internal Exchange SMTP relay. No OAuth, no Azure AD. IT whitelists the server's IP at the relay. Configurable in Admin Panel: SMTP host, port, from address.

---

## Q21 — What does the Weekly Tasking Report module do?

**A**: Each IC enters their weekly task entries (diagram GUIDs, hours, activity type). The director sees a consolidated view across all ICs. Export to Word (.docx) using `python-docx`.

---

## Q22 — What does Metrics: Charging do?

**A**: Ingests SAP export Excel files. Smart column detection (finds the hours column by header name). Strips `" H"` suffix from hours values (SAP format `"8.0 H"` → `8.0`). Builds Employee × FiscalMonth pivot table using MAX aggregation (not sum — SAP data is cumulative within pay period). Export via openpyxl.

---

## Q23 — What does Metrics: NimbusBOE do?

**A**: Ingests SAP BOE (Basis of Estimate) Excel files. Filters to charge order `9L99G054` (admin-configurable) and excludes PTO/HOL/UNP supp codes. Builds BOE summary table grouped by Employee × SuppCode. Export via openpyxl.

---

## Q24 — What does Metrics: DID Working do?

**A**: Government document tracker. Tracks DID (Data Item Description) working documents, their status, responsible parties, and due dates. Details TBD — this module needs more specification input from the user once build begins.

---

## Q25 — What is the PAL Checklist?

**A**: 25-item interactive review checklist for the PAL (Promotion Authorization List) review process. Each item can be checked off. The checklist state is saved per promotion cycle. Export to PDF or print.

---

## Q26 — What is the PAL Helper?

**A**: Browses SharePoint for PAL documents organized by discipline. Provides quick links to the correct PAL document for each team/discipline. Read-only browser — no edit operations.

---

## Q27 — What is the Admin Panel?

**A**: Admin-only module for managing:
- User accounts (windows_username, display_name, role, email, active)
- Dropdown option lists (e.g., valid organization names, diagram types)
- Email configuration (SMTP host/port/from address)
- SAP settings (charge order number, default filters)
- Promotion date management (add/close cycles)

---

## Q28 — How does the In-App Notification system work?

**A**: Bell icon in the app header with a badge count. Clicking opens a notification feed panel. New notifications are generated when: someone edits a row you own; a diagram you claimed moves to a new status; an authorization request is made on a diagram you IC'd. 60-second polling via `GET /api/notifications/unread`. Mark-as-read per item or all-at-once.

---

## Q29 — What export formats does MCPT support?

**A**:
- **Excel (.xlsx)**: MCPT main table export, charging pivot, BOE table
- **Word (.docx)**: Weekly tasking report
- **HTML**: Status summary view for email/printing
- **DSL ZIP**: Batch operation files for Nimbus

---

## Q30 — What is the SAP charge order number?

**A**: `9L99G054` — NAT team's SAP charge number. Used to filter SAP data in the Charging and BOE modules. Stored as an admin-configurable setting (default: `9L99G054`).

---

## Q31 — How many diagrams typically appear in each DSL category?

**A**: Unknown until API contract is confirmed. With 194 total diagrams, distribution varies by cycle. Engineering Approved is typically the largest category near promotion date.

---

## Q32 — What is the `Attatchments` typo in the schema?

**A**: The column is literally named `"Attatchments"` (with an extra 't') in the production Diagrams schema. This is NOT a typo to fix — it's the actual column name in the backend database. MCPT code must use the same spelling or the column won't match.

---

## Q33 — What is the deployment path and port?

**A**: `C:\MCPT\` on a Windows network server. Port 5060 (avoids conflict with AEGIS on 5050). Started via `Start_MCPT.bat` or Windows Service. All `open()` calls use `encoding='utf-8', errors='replace'`.

---

## Q34 — What Python packages are required?

**A** (expected):
- `flask` — web framework
- `waitress` — production WSGI server
- `requests` — HTTP client for proxying API calls
- `sspilib` or `pywin32` — Windows NTLM auth
- `openpyxl` — Excel read/write
- `python-docx` — Word document generation
- `sqlite3` — standard library, no install needed

---

## Q35 — Does MCPT need to handle concurrent edits to the same row?

**A**: The backend API handles concurrent edit conflicts. MCPT's Flask proxy just calls the API endpoints. If the API returns an error for a concurrent conflict, MCPT displays it to the user. MCPT does not implement optimistic locking itself — that's the backend team's concern.

---

## Q36 — How are deleted/archived entries handled?

**A**: `POST /archive-entry` moves a row to archived state (not deleted). Archived rows are hidden from the main table by default. An "Include Archived" toggle in the Admin Panel reveals them. `POST /remove-entry` is a hard delete — only available to Admins, used for data cleanup.

---

## Q37 — What is the Promotion Date cycle management?

**A**: Promotion dates are bi-weekly. They are managed in the Admin Panel (add new cycle, close current cycle). The active promotion date is the top-level filter in all MCPT views. Stored in the admin config table in the backend DB (TBD structure from dev team).

---

## Q38 — Does MCPT integrate directly with Nimbus?

**A**: No. MCPT does not call Nimbus APIs directly. All diagram data comes from the backend team's SQLite database (which syncs with Nimbus). MCPT provides deep links to Nimbus for direct diagram viewing, but all data operations go through the backend API.

---

## Q39 — What is the `GET /get-trb` endpoint?

**A**: Awaiting dev team response (Question #10 in developer_questions_email.md). Expected to return the Authorizations table data filtered by promotion date. Used by the Authorization Dashboard and DSL generation.

---

## Q40 — What format does `POST /edit-entry` use?

**A**: Recommended JSON body format (Question #4 in developer_questions_email.md):
```json
{ "guid": "ACDF1AE9385543888E91381F30D3F806", "field": "Notes", "value": "Updated text..." }
```
URL query parameters rejected — 2,000 char limit insufficient for Notes/Change Log fields.

---

## Q41 — What is the API base URL?

**A**: TBD — awaiting dev team response (Question #5 in developer_questions_email.md). Expected format: `http://mcpt-api.as.northgrum.com:XXXX`. Until confirmed, use an environment variable / config value.

---

## Q42 — How does the API authenticate MCPT's Flask proxy?

**A**: TBD — awaiting dev team response (Question #6 in developer_questions_email.md). Options: open on internal network (trusted by IP/subnet), bearer token, or API key header. The Flask proxy will inject whichever auth mechanism the dev team implements.

---

## Q43 — What is the MCPT table SQL schema (dev team's tracking table)?

**A**: TBD — awaiting dev team response (Question #2 in developer_questions_email.md). The Reports repo contains `Diagrams.sql` and related tables, but the MCPT-specific tracking table definition is not published. This is the most critical question — it determines the exact fields available in `GET /get-mcpt` responses.
