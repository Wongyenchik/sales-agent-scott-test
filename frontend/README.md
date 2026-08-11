Frontend (Standalone Test Chat)

This is a simple standalone web frontend for testing the backend flow.

Default URLs

- Frontend: http://localhost:5173
- Backend: http://localhost:8080
- Mock SAP API: http://localhost:7071

Run order

1. Start mock SAP API
   cd <repo-root>\mock-api
   py server.py

2. Start backend API
   cd <repo-root>\backend
   py server.py

3. Start frontend
   cd <repo-root>\frontend
   py server.py

If `py` is unavailable, use `python`.

4. Open browser
   http://localhost:5173

Notes

- The page has a Backend URL field, defaulted to http://localhost:8080.
- Use Ctrl+Enter in the message box to send quickly.
- This frontend sends requests to POST /api/agent/generate-reply and displays status, draft, and metadata.
