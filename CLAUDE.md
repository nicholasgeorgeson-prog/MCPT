# MCPT — Claude Session Notes

## Project Overview
**MCPT** (Model Change Package Tracker) is a Flask-based multi-user web application replacing a suite of Excel/VBA workbooks used by the NGAS (Northrop Grumman Aeronautics Systems) NAT team. The team manages TIBCO Nimbus process model diagrams through a two-week promotion cycle (Draft → authorized → promoted to Master). Created by Nicholas Georgeson. Will deploy on a Windows network server at TBD hostname, port 5060.

**Current phase**: Pre-build. Awaiting backend dev team API response (see `docs/developer_questions_email.md`). Build begins once API contract is confirmed.

## Architecture
- **Backend**: Flask (Python 3), Waitress WSGI (NOT Flask dev server)
- **Frontend**: Vanilla JS, CSS, HTML (no framework)
- **Auth**: Windows NTLM/Kerberos — `sspilib`/`pywin32`; users never type a password
- **Email**: `smtplib` → internal Exchange SMTP relay (IT whitelists server IP)
- **External API**: Backend REST API (separate dev team builds this)
- **Local DB**: SQLite WAL mode — notifications only (`data/notifications.db`)
- **Export**: `openpyxl` (Excel), `python-docx` (Word), HTML string templates

## Backend API (Separate Dev Team)
- **Base URL**: TBD — awaiting dev team response
- **Auth mechanism**: TBD — awaiting dev team response
- **Known endpoints**:
  - `GET /get-mcpt` — full MCPT table (main data load)
  - `GET /get-trb` — authorization progress data
  - `GET /get-diagram?guid={GUID}` — single diagram details
  - `POST /add-entry` — add new MCPT tracking row
  - `POST /remove-entry` — remove row by GUID
  - `POST /edit-entry` — edit single field {guid, field, value}
  - `POST /archive-entry` — archive row by GUID
- **Source of truth**: `nicholasgeorgeson-prog/Reports` GitHub repo — SQL schemas in `data/sql_schemas/`

## Key Data Facts
- **Nimbus base URL**: `https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:9820E23DD3204072819C50B7A2E57093.{GUID}`
- **Map GUID** (hardcoded in URL): `9820E23DD3204072819C50B7A2E57093`
- **DSLID ≠ GUID**: GUID is for URLs and DB lookups; DSLID is for `.dsl` batch operation files
- **Authorization field format**: `"Authorization Pending - 2/13/2026"` or `"Promotion Ready - 2/6/2026"` — date embedded in string
- **Level format**: `"1.3.8 Draft Copy"` or `"1.3.8"` (Master) — Level number = dots + 1
- **Diagram statuses**: Unclaimed / Claimed / Engineering Approved / Conceptual Image / Not To Be Claimed
- **SAP charge order**: `9L99G054` (NAT team, admin-editable)
- **Nimbus EOL**: September 1, 2025 — build Nimbus integration behind abstraction layer for future tool swap

## User Roles
| Role | Key Permissions |
|---|---|
| `IC` (Individual Contributor) | View all; edit own rows only; own tasking entries |
| `Admin` | Edit any row; manage users/dropdowns; send emails; delegate |
| `Director` | All Admin + charging view; consolidated tasking; executive export |

## Modules to Build (All Required — No Stubs)
1. MCPT Main Table — data grid, inline edit, add/archive, DSL generation
2. Authorization Dashboard — sign-off tracking, authorization email automation
3. DSL File Generator — 5-category + per-authorizer `.dsl` files, ZIP download
4. Weekly Tasking Report — per-user entry + director consolidated view + Word export
5. Metrics: Charging — SAP ingest, smart column detection, pivot table
6. Metrics: NimbusBOE — SAP BOE ingest, filter by order#, BOE table
7. Metrics: DID Working — government document tracker
8. PAL Checklist — 25-item interactive review checklist
9. PAL Helper — SharePoint PAL document browser by discipline
10. Admin Panel — users, dropdowns, email config, SAP settings
11. In-App Notifications — bell icon, feed, 60-second poll
12. Email Automation — SMTP; 3 email types (status, missing auth, per-authorizer)
13. Export — Excel, Word, HTML, DSL ZIP

## Key Files
| File | Purpose |
|---|---|
| `docs/build_prompt.md` | Complete build specification — full detail on every module |
| `docs/architecture_decisions.md` | All architectural decisions with rationale |
| `docs/developer_questions_email.md` | Email to send to backend dev team |
| `docs/preflight_qa.md` | All 43 pre-flight Q&A pairs (complete record) |
| `docs/nimbus_research.md` | Full TIBCO Nimbus research findings |
| `docs/vba_analysis.md` | All VBA logic extracted and documented |
| `docs/data_model.md` | SQL schemas, Excel field mappings, data formats |
| `data/sql_schemas/*.sql` | Backend DB table definitions (from Reports repo) |
| `project_knowledge.db` | SQLite FTS5 searchable knowledge base |
| `search_knowledge.py` | Search the knowledge base |
| `build_knowledge_db.py` | Rebuild DB from CLAUDE.md.backup |

## GitHub
- **Repo**: `nicholasgeorgeson-prog/MCPT`, branch `main`
- **Git index LOCKED** — MUST use GitHub REST API for all pushes (same pattern as AEGIS)
- **PAT**: `[REDACTED — stored locally only, not in repo]`
- **Workflow**: GET refs → GET commits → POST blobs → POST trees → POST commits → PATCH refs
- **Batch size**: 25-30 files per commit

## Version Management
- **Current version**: 0.1.0 (pre-build, spec phase)
- **Source of truth**: `version.json` in project root
- **Always sync**: `cp version.json static/version.json`

## Windows Deployment
- **Path**: `C:\MCPT\` (never OneDrive, never paths with spaces)
- **Port**: 5060 (avoid conflict with AEGIS on 5050)
- **Start**: `Start_MCPT.bat` (double-click) or Windows Service via `pywin32`
- **All `open()` calls**: `encoding='utf-8', errors='replace'`
- **SQLite**: WAL mode for all local databases

## MANDATORY RULES
1. **Discovery-first**: Research → hypothesis → validate → implement. Never shotgun fixes.
2. **No stubs**: Every module must be fully implemented and integration-tested.
3. **Every deliverable**: Update version.json + static/version.json.
4. **Nimbus abstraction**: All Nimbus-specific code behind an adapter — future tool swap = adapter change only.
5. **API proxy pattern**: ALL backend API calls go through Flask routes — never direct browser-to-API calls.
6. **Windows-first**: Test on Windows. UTF-8 encoding everywhere. Waitress, not Flask dev server.
7. **DB questions → developer email**: Any question about API response format → add to `docs/developer_questions_email.md`.

## Knowledge Base — Searchable
All project knowledge is stored in `project_knowledge.db` (SQLite FTS5).

**To search**:
```bash
python3 search_knowledge.py "DSL file generation"      # Full-text search
python3 search_knowledge.py --category api-contract     # By category
python3 search_knowledge.py --category nimbus           # Nimbus research
python3 search_knowledge.py --recent 10                 # Last 10 entries
python3 search_knowledge.py --categories                # List all categories
```

**Categories**: api-contract, architecture, ui-modules, data-model, business-rules,
nimbus, vba-logic, notifications, deployment-windows, dev-questions, preflight-qa

**To add entries**: Edit `CLAUDE.md.backup`, then run `python3 build_knowledge_db.py`
