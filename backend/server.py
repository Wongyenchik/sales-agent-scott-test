from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

from app.controller import handle_generate_reply
from app.config import APP_PORT, SAP_API_MODE


class BackendHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        if self.path == "/health":
            self._set_headers(200)
            self.wfile.write(
                json.dumps(
                    {
                        "status": "ok",
                        "service": "sales-agent-backend",
                        "sapApiMode": SAP_API_MODE,
                    }
                ).encode("utf-8")
            )
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"status": "error", "message": "Not found"}).encode("utf-8"))

    def do_POST(self):
        if self.path != "/api/agent/generate-reply":
            self._set_headers(404)
            self.wfile.write(json.dumps({"status": "error", "message": "Not found"}).encode("utf-8"))
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))

            status_code, response = handle_generate_reply(payload)
            self._set_headers(status_code)
            self.wfile.write(json.dumps(response).encode("utf-8"))
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(
                json.dumps({"status": "bad_request", "error": "Invalid JSON request body"}).encode("utf-8")
            )
        except Exception as exc:  # noqa: BLE001
            self._set_headers(500)
            self.wfile.write(
                json.dumps({"status": "error", "message": str(exc) or "Unexpected server error"}).encode("utf-8")
            )


if __name__ == "__main__":
    server = ThreadingHTTPServer(("", APP_PORT), BackendHandler)
    print(f"Backend listening on http://localhost:{APP_PORT}")
    server.serve_forever()
