from pathlib import Path
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

from app.config import MOCK_SAP_INLINE, SAP_API_MODE  # noqa: E402
from app.controller import handle_generate_reply  # noqa: E402

app = FastAPI(title="Sales Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "sales-agent-backend",
        "sapApiMode": SAP_API_MODE,
        "mockSapInline": MOCK_SAP_INLINE,
    }


@app.post("/api/agent/generate-reply")
async def generate_reply(request: Request):
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse(
            {"status": "bad_request", "error": "Invalid JSON request body"},
            status_code=400,
        )

    try:
        status_code, response = handle_generate_reply(payload)
        return JSONResponse(response, status_code=status_code)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            {"status": "error", "message": str(exc) or "Unexpected server error"},
            status_code=500,
        )


# Serve Outlook taskpane + standalone frontend (must be last).
app.mount("/", StaticFiles(directory=str(ROOT / "frontend"), html=True), name="frontend")
