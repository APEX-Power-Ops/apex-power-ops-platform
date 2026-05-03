"""HTTP runtime shell for the bounded forms-engine contract."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from apex_forms_engine.contract import get_runtime_status


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, get_runtime_status())
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    port = int(os.getenv("APEX_FORMS_RUNTIME_PORT") or os.getenv("PORT") or "8080")
    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
