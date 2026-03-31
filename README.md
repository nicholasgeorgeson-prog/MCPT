# MCPT — Model Change Package Tracker

**Status**: Pre-build | Awaiting backend dev team API contract
**Version**: 0.1.0 (2026-03-31)
**Author**: Nicholas Georgeson

---

## What Is MCPT?

MCPT replaces a suite of Excel/VBA workbooks used by the NGAS (Northrop Grumman Aeronautics Systems) NAT team to manage TIBCO Nimbus process model diagrams through a bi-weekly promotion cycle.

The team promotes diagrams through a lifecycle: **Draft → Authorized → Promoted to Master**. MCPT tracks every diagram's status, automates authorization workflows, generates DSL batch files for Nimbus, and produces tasking/charging reports for directors.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend web server | Flask (Python 3) + Waitress WSGI |
| Frontend | Vanilla JS / CSS / HTML (no framework) |
| Auth | Windows NTLM/Kerberos (sspilib/pywin32) |
| Local DB | SQLite WAL (notifications only) |
| External API | Separate dev team REST API (Flask-proxied) |
| Email | smtplib → internal Exchange SMTP relay |
| Export | openpyxl (Excel), python-docx (Word), HTML templates |
| Deployment | Windows server, port 5060, C:\MCPT\ |

---

## Architecture

```
Browser
  └── Flask app (port 5060, Waitress)
        ├── Routes (blueprints)
        │     ├── /api/mcpt/*        → proxy to backend REST API
        │     ├── /api/auth/*        → Windows NTLM auth
        │     ├── /api/notifications/* → local SQLite
        │     └── /api/export/*      → file generation
        ├── Local SQLite (notifications.db) — WAL mode
        └── Backend REST API (separate dev team)
              ├── GET  /get-mcpt      → all tracking rows
              ├── GET  /get-trb       → authorization data
              ├── GET  /get-diagram   → single diagram detail
              ├── POST /add-entry     → add tracking row
              ├── POST /remove-entry  → remove by GUID
              ├── POST /edit-entry    → edit single field
              └── POST /archive-entry → archive by GUID
```

**Critical**: ALL backend API calls go through Flask routes. The browser never calls the backend API directly.

---

## Key Data Facts

- **Nimbus base URL**: `https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:9820E23DD3204072819C50B7A2E57093.{GUID}`
- **Map GUID** (hardcoded): `9820E23DD3204072819C50B7A2E57093`
- **DSLID ≠ GUID**: GUID = URL/DB key; DSLID = used in `.dsl` batch operation files
- **Authorization string format**: `"Authorization Pending - 2/13/2026"` (date embedded in string)
- **Level format**: `"1.3.8 Draft Copy"` (Draft) or `"1.3.8"` (Master)
- **Diagram statuses**: Unclaimed / Claimed / Engineering Approved / Conceptual Image / Not To Be Claimed
- **SAP charge order**: `9L99G054` (NAT team default, admin-editable)
- **Nimbus EOL**: September 1, 2025 — all Nimbus-specific code is behind an abstraction layer

---

## Modules

| # | Module | Description |
|---|---|---|
| 1 | MCPT Main Table | Data grid, inline edit, add/archive, DSL generation |
| 2 | Authorization Dashboard | Sign-off tracking, authorization email automation |
| 3 | DSL File Generator | 5-category + per-authorizer `.dsl` files, ZIP download |
| 4 | Weekly Tasking Report | Per-user entry + director consolidated view + Word export |
| 5 | Metrics: Charging | SAP ingest, smart column detection, pivot table |
| 6 | Metrics: NimbusBOE | SAP BOE ingest, filter by order#, BOE table |
| 7 | Metrics: DID Working | Government document tracker |
| 8 | PAL Checklist | 25-item interactive review checklist |
| 9 | PAL Helper | SharePoint PAL document browser by discipline |
| 10 | Admin Panel | Users, dropdowns, email config, SAP settings |
| 11 | In-App Notifications | Bell icon, feed, 60-second poll |
| 12 | Email Automation | SMTP; 3 email types (status, missing auth, per-authorizer) |
| 13 | Export | Excel, Word, HTML, DSL ZIP |

---

## User Roles

| Role | Key Permissions |
|---|---|
| `IC` | View all; edit own rows only; own tasking entries |
| `Admin` | Edit any row; manage users/dropdowns; send emails; delegate |
| `Director` | All Admin + charging view; consolidated tasking; executive export |

---

## Development Status

| Phase | Status |
|---|---|
| Pre-flight research (43 Q&A) | ✅ Complete |
| SQL schema analysis | ✅ Complete |
| VBA analysis (4 workbooks) | ✅ Complete |
| TIBCO Nimbus research | ✅ Complete |
| Architecture decisions | ✅ Complete |
| Build specification | ✅ Complete |
| Developer questions email | ✅ Sent — awaiting responses |
| API contract finalized | ⏳ Awaiting dev team |
| Build | ⏳ Begins after API contract |

---

## Project Files

| File | Purpose |
|---|---|
| `CLAUDE.md` | Claude session instructions (project state, rules) |
| `docs/build_prompt.md` | Complete build specification |
| `docs/architecture_decisions.md` | All architectural decisions with rationale |
| `docs/developer_questions_email.md` | Email sent to backend dev team + answers log |
| `docs/preflight_qa.md` | All 43 pre-flight Q&A pairs |
| `docs/nimbus_research.md` | Full TIBCO Nimbus research findings |
| `docs/vba_analysis.md` | All VBA logic extracted and documented |
| `docs/data_model.md` | SQL schemas, Excel field mappings, data formats |
| `data/sql_schemas/*.sql` | Backend DB table definitions (from Reports repo) |
| `project_knowledge.db` | SQLite FTS5 searchable knowledge base |
| `search_knowledge.py` | Search the knowledge base |
| `build_knowledge_db.py` | Rebuild DB from CLAUDE.md.backup |

---

## GitHub

- **Repo**: `nicholasgeorgeson-prog/MCPT`
- **Branch**: `main`
- **Push method**: GitHub REST API (git index locked on dev machine)

---

## Related Repos

- `nicholasgeorgeson-prog/Reports` — SQL schemas + Excel source data (backend team's repo)
- `nicholasgeorgeson-prog/AEGIS` — Sister app, same Flask/Vanilla JS architecture pattern
