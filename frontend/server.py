from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os

PORT = int(os.getenv("FRONTEND_PORT", "5173"))
BASE_DIR = Path(__file__).resolve().parent


class FrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("", PORT), FrontendHandler)
    print(f"Frontend running on http://localhost:{PORT}")
    server.serve_forever()
