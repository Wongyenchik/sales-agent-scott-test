from app.config import SAP_API_MODE
from app.sap_client import fetch_order_from_sap


def _source_name() -> str:
    return "mock-sap-api" if SAP_API_MODE == "mock" else "company-sap-api"


def _map_status(status_code: int, payload_status: str | None) -> str:
    if payload_status == "missing_parameters":
        return "missing_parameters"
    if payload_status == "unauthorized" or status_code == 401:
        return "unauthorized"
    if payload_status == "not_found" or status_code == 404:
        return "not_found"
    if payload_status == "api_error" or status_code >= 500:
        return "api_error"
    if 200 <= status_code < 300:
        return "success"
    return "api_error"


def retrieve_from_sap_adapter(parameters: dict, request_id: str) -> dict:
    status_code, payload = fetch_order_from_sap(parameters, request_id)
    status = _map_status(status_code, payload.get("status"))

    result = {
        "called": True,
        "status": status,
        "source": _source_name(),
        "correlationId": payload.get("correlationId") or f"corr-{request_id}",
    }

    if status == "success":
        result["data"] = payload.get("order") or payload.get("data") or payload
    else:
        result["errorMessage"] = payload.get("errorMessage") or "SAP API did not return a successful result"

    return result
