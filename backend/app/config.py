import os


def parse_int(value: str, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


APP_PORT = parse_int(os.getenv("PORT", "8080"), 8080)
SAP_API_MODE = os.getenv("SAP_API_MODE", "mock").strip().lower()
# On Vercel, default to in-process mock so no separate mock-api service is required.
_DEFAULT_INLINE = "1" if os.getenv("VERCEL") else "0"
MOCK_SAP_INLINE = os.getenv("MOCK_SAP_INLINE", _DEFAULT_INLINE).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
MOCK_SAP_BASE_URL = os.getenv("MOCK_SAP_BASE_URL", "http://localhost:7071").rstrip("/")
COMPANY_SAP_BASE_URL = os.getenv("COMPANY_SAP_BASE_URL", "").strip().rstrip("/")
SAP_API_TIMEOUT_MS = parse_int(os.getenv("SAP_API_TIMEOUT_MS", "5000"), 5000)
