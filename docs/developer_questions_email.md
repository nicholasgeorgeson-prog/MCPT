# Developer Questions Email

**Status**: DRAFT — ready to send. Paste this into an email to the backend dev team.

---

**Subject: MCPT Web App — Frontend Integration Questions**

Hi [Dev Team],

As we begin architecting the MCPT frontend, we have the following questions that need answers before the first line of code is written. Some are architectural decisions that affect both sides.

---

**1. GET /get-mcpt — Response Format**
Please provide a sample JSON response for `GET /get-mcpt` showing at minimum 2 rows. Specifically need:
- The exact JSON field names for all columns returned
- Data types (string, boolean, number, timestamp format)
- Whether boolean tracking columns (SP Folder Created, Tool Entry Created, etc.) return `true/false`, `"Yes"/"No"`, or `1/0`
- Whether this endpoint returns ALL records or only current (non-archived) records by default
- Is there a filter parameter (e.g., `?promotion_date=2026-04-04`) or does it always return everything?

**2. MCPT Table Schema**
The Reports GitHub repo contains `Diagrams.sql`, `Authorizations.sql`, `Changes.sql`, etc. — but there is no `ModelChangePackageTracker` table definition. Can you share the SQL schema for the MCPT tracking table? Specifically, which columns are stored in the MCPT table vs. derived/joined from the Diagrams table?

**3. User Management / Authentication**
The frontend will use Windows Integrated Authentication (NTLM/Kerberos) so users never type a password — the Windows username is known automatically. We need:
- An endpoint `GET /get-user?username={windows_username}` (or similar) that returns the user's role (IC / Admin / Director) and display name
- A `users` table in the database: `(windows_username, display_name, role, email, active)` managed by admin
- If no user record exists, the API should return `403 Unauthorized`

Is this something you can add to the API, or should the frontend maintain its own separate user table?

**4. POST /edit-entry — Request Format**
The email described `POST /edit-entry?{diagram:GUID,key:new-value}`. Some MCPT fields (Change Log Entries, Notes) can contain hundreds of characters. URL query strings have a ~2,000 character limit which may be insufficient.

Question: Should `edit-entry` use a JSON request body instead of URL query parameters? Suggested format:
```json
{ "guid": "ACDF1AE9385543888E91381F30D3F806", "field": "Notes", "value": "Updated text here..." }
```

**5. API Base URL and Port**
What hostname and port will the API run on? (e.g., `localhost:8080`, `mcpt-api.as.northgrum.com:5000`). This is needed for CORS configuration and the Flask proxy layer. Will the API and frontend be on the same server (same origin) or different hosts?

**6. API Authentication**
When the frontend calls `GET /get-mcpt`, how does the API verify the caller is authorized? Options:
- Open on the internal network (trusted by IP/subnet)
- Bearer token returned from a login/session endpoint
- API key in a request header

Which approach are you implementing?

**7. POST /add-entry and POST /remove-entry — Request Bodies**
What fields are required vs. optional in `POST /add-entry`? What does `POST /remove-entry` expect — just the GUID?

**8. Pagination**
Does `GET /get-mcpt` return all records or is there pagination? With the current 194-row dataset this is fine either way, but we want to confirm for scalability.

**9. Schema Bug in SIPOCs and Storyboards**
Both `SIPOCs.sql` and `Storyboards.sql` define a composite FK:
```sql
FOREIGN KEY("DiagramGUID","Type") REFERENCES "Diagrams"("GUID","Type")
```
But the `Diagrams` table has no `Type` column — only `GUID` as primary key. This FK will fail if SQLite FK enforcement is enabled. Should the FK reference only `GUID`?

**10. GET /get-trb — What Does It Return?**
Does this endpoint return the full Authorizations table filtered for a specific promotion date? What parameters does it accept?

**11. GET /get-diagram Parameters**
What parameters does `GET /get-diagram` accept? Just GUID? Does it return full diagram detail including change log entries?

---

Thank you — once these are answered the frontend architecture will be finalized and build can begin immediately.

---

## Answers Log

| # | Question | Status | Answer | Date |
|---|---|---|---|---|
| 1 | GET /get-mcpt JSON format | ⏳ Pending | | |
| 2 | MCPT table SQL schema | ⏳ Pending | | |
| 3 | User auth endpoint | ⏳ Pending | | |
| 4 | POST /edit-entry format | ⏳ Pending | | |
| 5 | API base URL and port | ⏳ Pending | | |
| 6 | API authentication method | ⏳ Pending | | |
| 7 | add-entry / remove-entry bodies | ⏳ Pending | | |
| 8 | Pagination | ⏳ Pending | | |
| 9 | SIPOCs/Storyboards FK bug | ⏳ Pending | | |
| 10 | GET /get-trb details | ⏳ Pending | | |
| 11 | GET /get-diagram params | ⏳ Pending | | |
