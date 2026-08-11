from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
import os
import time

PORT = int(os.getenv("MOCK_SAP_PORT", "7071"))
ORDERS_PATH = Path(__file__).with_name("mockOrders.json")
ORDERS = json.loads(ORDERS_PATH.read_text(encoding="utf-8"))


def build_correlation_id() -> str:
    return f"mock-{int(time.time() * 1000)}"


def json_response(handler: BaseHTTPRequestHandler, status_code: int, payload: dict):
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET,OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type,x-mock-sap-scenario")
    handler.end_headers()
    handler.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))


def normalize_order(order: dict) -> dict:
    return {"source": "mock-sap-api", "correlationId": build_correlation_id(), "order": order}


def find_by_order_number(order_number: str):
    return next((o for o in ORDERS if o.get("orderNumber") == order_number), None)


def find_by_customer_reference(reference: str):
    ref_lower = reference.lower()
    return next((o for o in ORDERS if str(o.get("customerReference", "")).lower() == ref_lower), None)


def handle_scenario(handler: BaseHTTPRequestHandler, scenario: str) -> bool:
    if scenario == "unauthorized":
        json_response(
            handler,
            401,
            {
                "source": "mock-sap-api",
                "correlationId": build_correlation_id(),
                "status": "unauthorized",
                "errorMessage": "Mock unauthorized scenario",
            },
        )
        return True

    if scenario == "api_error":
        json_response(
            handler,
            500,
            {
                "source": "mock-sap-api",
                "correlationId": build_correlation_id(),
                "status": "api_error",
                "errorMessage": "Mock API error scenario",
            },
        )
        return True

    if scenario == "timeout":
        time.sleep(6)
        json_response(
            handler,
            504,
            {
                "source": "mock-sap-api",
                "correlationId": build_correlation_id(),
                "status": "api_error",
                "errorMessage": "Mock timeout scenario",
            },
        )
        return True

    return False


class MockSapHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,x-mock-sap-scenario")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        scenario = (
            (query.get("scenario") or [""])[0].strip().lower()
            or str(self.headers.get("x-mock-sap-scenario") or "").strip().lower()
        )

        if handle_scenario(self, scenario):
            return

        if parsed.path == "/health":
            json_response(self, 200, {"status": "ok", "service": "mock-sap-api", "port": PORT})
            return

        if parsed.path.startswith("/api/mock-sap/orders/"):
            order_number = parsed.path.split("/")[-1]

            if order_number == "4500099999":
                json_response(
                    self,
                    500,
                    {
                        "source": "mock-sap-api",
                        "correlationId": build_correlation_id(),
                        "status": "api_error",
                        "errorMessage": "Forced api_error for integration testing",
                    },
                )
                return

            order = find_by_order_number(order_number)
            if not order:
                json_response(
                    self,
                    404,
                    {
                        "source": "mock-sap-api",
                        "correlationId": build_correlation_id(),
                        "status": "not_found",
                        "errorMessage": f"Order {order_number} was not found",
                    },
                )
                return

            json_response(self, 200, normalize_order(order))
            return

        if parsed.path == "/api/mock-sap/orders":
            customer_reference = (query.get("customerReference") or [None])[0]
            if not customer_reference:
                json_response(
                    self,
                    400,
                    {
                        "source": "mock-sap-api",
                        "correlationId": build_correlation_id(),
                        "status": "missing_parameters",
                        "errorMessage": "customerReference query parameter is required",
                    },
                )
                return

            order = find_by_customer_reference(customer_reference)
            if not order:
                json_response(
                    self,
                    404,
                    {
                        "source": "mock-sap-api",
                        "correlationId": build_correlation_id(),
                        "status": "not_found",
                        "errorMessage": f"Customer reference {customer_reference} was not found",
                    },
                )
                return

            json_response(self, 200, normalize_order(order))
            return

        json_response(self, 404, {"error": "Route not found"})


if __name__ == "__main__":
    server = ThreadingHTTPServer(("", PORT), MockSapHandler)
    print(f"Mock SAP API running on http://localhost:{PORT}")
    server.serve_forever()
