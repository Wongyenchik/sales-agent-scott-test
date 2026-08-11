Backend MVP (Web First)

This backend exposes a web endpoint that:
1) Reads email context payload
2) Extracts required SAP parameters
3) Calls SAP retrieval tool (mock mode by default)
4) Validates SAP call result with mandatory gate
5) Returns a reply draft

Run

Python 3.x only (no extra packages required).

Terminal 1 (mock API):

```powershell
cd <repo-root>\mock-api
py server.py
```

Terminal 2 (backend API):

```powershell
cd <repo-root>\backend
py server.py
```

Terminal 3 (frontend):

```powershell
cd <repo-root>\frontend
py server.py
```

If `py` is unavailable, try `python` instead.

Backend URL

- API base: `http://localhost:8080`
- Health: `GET /health`
- Generate draft: `POST /api/agent/generate-reply`

Frontend

- Standalone frontend is in `../frontend`
- Start it separately with `python server.py` and open `http://localhost:5173`

Endpoint

POST /api/agent/generate-reply

Health

GET /health

Example request body

{
  "messageId": "abc123",
  "subject": "Order 4500012345 status",
  "sender": {
    "name": "Customer Name",
    "email": "customer@example.com"
  },
  "recipients": [],
  "bodyText": "Can you update me on order 4500012345?",
  "conversationId": "conv-1",
  "userAction": "generate_reply"
}
