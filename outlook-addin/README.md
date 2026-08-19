# Outlook Add-in Integration

This folder contains a minimal Outlook Add-in manifest that opens the Sales Agent task pane.
The task pane reads the currently selected email via Office.js and calls the main FastAPI workflow:

```http
POST http://localhost:8000/api/v1/run
```

The Outlook UI maps the selected message to the existing `EmailRequest` contract:

```json
{
   "sender_email": "buyer@contoso.example",
   "subject": "Order status request",
   "body": "Could you provide the status of PO-2026-08001?"
}
```

Files

- manifest.xml
- frontend/taskpane.html
- frontend/taskpane.js
- frontend/taskpane.css
- frontend/commands.html

## Run local services first

Terminal 1 (FastAPI workflow):

```powershell
cd <repo-root>
C:\Users\062359\source\repos\SalesAgent\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Terminal 2 (frontend host for add-in pages):

```powershell
cd <repo-root>\frontend
C:\Users\062359\source\repos\SalesAgent\.venv\Scripts\python.exe server.py
```

If `py` or `python` is preferred and dependencies are already available, those can be used instead of the full virtual environment path.

## URLs

- FastAPI health: http://localhost:8000/health
- Workflow API: http://localhost:8000/api/v1/run
- Task pane: http://localhost:5173/taskpane.html
- Commands file: http://localhost:5173/commands.html

## Manifest URLs

The checked-in manifest may point to a hosted test URL or to localhost depending on the branch state. For local testing, these entries must resolve to the frontend host or an HTTPS tunnel that forwards to it:

```xml
<SourceLocation DefaultValue="http://localhost:5173/taskpane.html"/>
<bt:Url id="Commands.Url" DefaultValue="http://localhost:5173/commands.html"/>
<bt:Url id="Taskpane.Url" DefaultValue="http://localhost:5173/taskpane.html"/>
```

If Outlook blocks `http://localhost`, expose the frontend through an HTTPS tunnel and replace the manifest URLs with that HTTPS origin. If the frontend origin changes, set `OUTLOOK_ORIGIN` in `.env` to the same origin so FastAPI CORS allows the request.

## Sideload in Outlook on Web

1. Open Outlook on Web with your account.
2. Go to Settings > Manage add-ins (or Get Add-ins).
3. Open My add-ins.
4. Choose Add a custom add-in > Add from file.
5. Select this file:
   <repo-root>\outlook-addin\manifest.xml
6. Open any email in read mode.
7. Click the add-in button "Generate SAP Draft" under the add-in group.
8. In the task pane, wait for the selected email details to load.
9. Type a short prompt such as `Generate draft` and click `Send`.
10. Review the workflow status, understanding result, draft reply, and correlation ID returned by FastAPI.

## Sideload in New Outlook for Windows

1. Open New Outlook.
2. Go to Get Add-ins > My add-ins.
3. Add custom add-in from file.
4. Select manifest.xml from this folder.
5. Open a message and click the add-in button.

## Test email

Use a message body similar to:

```text
Could you provide the status of PO-2026-08001?
```

If the sender is not present in `app/data/customers.json`, the workflow should return `needs_review` after understanding and customer validation. That is expected behavior.

## Troubleshooting

1. If task pane does not load, verify frontend server is running on port 5173.
2. If draft generation fails, verify FastAPI is running on port 8000.
3. If the browser console shows a CORS error, verify `OUTLOOK_ORIGIN` matches the task pane origin.
4. If your tenant blocks custom add-ins, ask the M365 admin to allow sideloading.
5. Some Outlook environments require HTTPS add-in URLs. If HTTP localhost is blocked, use an HTTPS tunnel URL and update manifest URLs accordingly.
