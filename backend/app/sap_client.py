import json
import urllib.error
import urllib.parse
import urllib.request

from app.config import (
    COMPANY_SAP_BASE_URL,
    MOCK_SAP_BASE_URL,
    MOCK_SAP_INLINE,
    SAP_API_MODE,
    SAP_API_TIMEOUT_MS,
)
from app.mock_sap_inline import fetch_order_inline


def _request_json(url: str, request_id: str) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Content-Type": "application/json",
            "x-request-id": request_id,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=SAP_API_TIMEOUT_MS / 1000) as response:
            status_code = response.getcode()
            payload = json.loads(response.read().decode("utf-8") or "{}")
            return status_code, payload
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:  # noqa: BLE001
            payload = {}
        return exc.code, payload
    except TimeoutError:
        return 504, {"status": "api_error", "errorMessage": "SAP API timeout"}
    except Exception as exc:  # noqa: BLE001
        return 500, {"status": "api_error", "errorMessage": str(exc) or "SAP API request failed"}


def fetch_order_from_sap(parameters: dict, request_id: str) -> tuple[int, dict]:
    purchase_order_number = parameters.get("purchaseOrderNumber")
    customer_reference = parameters.get("customerReference")

    if not purchase_order_number and not customer_reference:
        return 400, {
            "status": "missing_parameters",
            "errorMessage": "purchaseOrderNumber or customerReference is required",
        }

    if SAP_API_MODE == "mock":
        if MOCK_SAP_INLINE:
            return fetch_order_inline(parameters)

        if purchase_order_number:
            url = f"{MOCK_SAP_BASE_URL}/api/mock-sap/orders/{urllib.parse.quote(purchase_order_number)}"
            return _request_json(url, request_id)

        ref = urllib.parse.quote(customer_reference)
        url = f"{MOCK_SAP_BASE_URL}/api/mock-sap/orders?customerReference={ref}"
        return _request_json(url, request_id)

    if SAP_API_MODE == "company":
        query = {}
        if purchase_order_number:
            query["orderNumber"] = purchase_order_number
        if customer_reference:
            query["customerReference"] = customer_reference

        separator = "&" if "?" in COMPANY_SAP_BASE_URL else "?"
        query_string = urllib.parse.urlencode(query)
        url = f"{COMPANY_SAP_BASE_URL}{separator}{query_string}"
        return _request_json(url, request_id)

    return 500, {"status": "api_error", "errorMessage": f"Unsupported SAP_API_MODE: {SAP_API_MODE}"}
