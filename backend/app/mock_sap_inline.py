"""In-process mock SAP lookup for serverless / single-service deploys."""

from __future__ import annotations

import json
import time
from pathlib import Path

_ORDERS_PATH = Path(__file__).resolve().parents[2] / "mock-api" / "mockOrders.json"
_ORDERS: list[dict] | None = None


def _orders() -> list[dict]:
    global _ORDERS
    if _ORDERS is None:
        _ORDERS = json.loads(_ORDERS_PATH.read_text(encoding="utf-8"))
    return _ORDERS


def _correlation_id() -> str:
    return f"mock-{int(time.time() * 1000)}"


def _normalize(order: dict) -> dict:
    return {"source": "mock-sap-api", "correlationId": _correlation_id(), "order": order}


def fetch_order_inline(parameters: dict) -> tuple[int, dict]:
    purchase_order_number = parameters.get("purchaseOrderNumber")
    customer_reference = parameters.get("customerReference")

    if purchase_order_number == "4500099999":
        return 500, {
            "source": "mock-sap-api",
            "correlationId": _correlation_id(),
            "status": "api_error",
            "errorMessage": "Forced api_error for integration testing",
        }

    if purchase_order_number:
        order = next((o for o in _orders() if o.get("orderNumber") == purchase_order_number), None)
        if not order:
            return 404, {
                "source": "mock-sap-api",
                "correlationId": _correlation_id(),
                "status": "not_found",
                "errorMessage": f"Order {purchase_order_number} was not found",
            }
        return 200, _normalize(order)

    if customer_reference:
        ref_lower = str(customer_reference).lower()
        order = next(
            (o for o in _orders() if str(o.get("customerReference", "")).lower() == ref_lower),
            None,
        )
        if not order:
            return 404, {
                "source": "mock-sap-api",
                "correlationId": _correlation_id(),
                "status": "not_found",
                "errorMessage": f"Customer reference {customer_reference} was not found",
            }
        return 200, _normalize(order)

    return 400, {
        "status": "missing_parameters",
        "errorMessage": "purchaseOrderNumber or customerReference is required",
    }
