Outlook Add-in Integration (Python Backend)

This folder contains a minimal Outlook Add-in manifest that opens a task pane UI.
The task pane reads the currently selected email via Office.js and calls:

POST /api/agent/generate-reply

## Deployed test URLs (Vercel)

Production app (frontend + backend + inline mock SAP):

- App: https://sales-agent-scott-test.vercel.app
- Health: https://sales-agent-scott-test.vercel.app/health
- Task pane: https://sales-agent-scott-test.vercel.app/outlook/taskpane.html
- Commands: https://sales-agent-scott-test.vercel.app/outlook/commands.html

`manifest.xml` already points at these HTTPS URLs.

Redeploy after code changes:

```powershell
cd <repo-root>
npx vercel@latest deploy --prod
```

Files

- manifest.xml
- frontend/outlook/taskpane.html
- frontend/outlook/taskpane.js
- frontend/outlook/taskpane.css
- frontend/outlook/commands.html

Run local services first (optional for local-only testing)

Terminal 1 (mock API):

cd <repo-root>\mock-api
py server.py

Terminal 2 (backend):

cd <repo-root>\backend
py server.py

Terminal 3 (frontend host for add-in pages):

cd <repo-root>\frontend
py server.py

Sideload in Outlook on Web (recommended)

1. Open Outlook on Web with your account.
2. Go to Settings > Manage add-ins (or Get Add-ins).
3. Open My add-ins.
4. Choose Add a custom add-in > Add from file.
5. Select this file:
   <repo-root>\outlook-addin\manifest.xml
6. Open any email in read mode.
7. Click the add-in button "Generate SAP Draft".
8. In task pane:
   - Leave Backend URL blank (uses the Vercel host automatically)
   - Click Generate Draft
   - Click Open Reply Draft to open reply compose with generated text

If you previously sideloaded the localhost manifest, remove that add-in first, then add this updated manifest again.

Troubleshooting

1. If task pane does not load, open the task pane URL in a browser and confirm HTTPS works.
2. If draft generation fails, open /health and confirm `"status":"ok"`.
3. If your tenant blocks custom add-ins, ask M365 admin to allow sideloading.
4. Vercel free tier can cold-start slowly on the first request after idle time.
