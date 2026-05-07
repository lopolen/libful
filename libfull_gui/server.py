#!/usr/bin/env python3
"""Small static server with an API proxy for the libful GUI."""

from __future__ import annotations

import argparse
import mimetypes
import posixpath
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
}


class LibfulGuiHandler(BaseHTTPRequestHandler):
    api_target = "http://127.0.0.1:8000"

    def do_GET(self) -> None:
        self.route()

    def do_HEAD(self) -> None:
        self.route(head_only=True)

    def do_POST(self) -> None:
        self.route()

    def do_PATCH(self) -> None:
        self.route()

    def do_PUT(self) -> None:
        self.route()

    def do_DELETE(self) -> None:
        self.route()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def route(self, *, head_only: bool = False) -> None:
        if self.path.startswith("/api/"):
            self.proxy_api(head_only=head_only)
        else:
            self.serve_static(head_only=head_only)

    def serve_static(self, *, head_only: bool = False) -> None:
        url_path = self.path.split("?", 1)[0]
        clean_path = posixpath.normpath(url_path.lstrip("/"))
        if clean_path in {"", "."}:
            clean_path = "index.html"

        file_path = (ROOT / clean_path).resolve()
        if ROOT not in file_path.parents and file_path != ROOT:
            self.send_error(403)
            return
        if not file_path.is_file():
            self.send_error(404)
            return

        content = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

    def proxy_api(self, *, head_only: bool = False) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else None
        target_url = urljoin(self.api_target.rstrip("/") + "/", self.path.lstrip("/"))

        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
        }

        request = Request(target_url, data=body, headers=headers, method=self.command)

        try:
            with urlopen(request, timeout=30) as response:
                response_body = response.read()
                self.send_response(response.status)
                self.copy_response_headers(response.headers, len(response_body))
                self.end_headers()
                if not head_only:
                    self.wfile.write(response_body)
        except HTTPError as error:
            response_body = error.read()
            self.send_response(error.code)
            self.copy_response_headers(error.headers, len(response_body))
            self.end_headers()
            if not head_only:
                self.wfile.write(response_body)
        except URLError as error:
            message = f'{{"detail":"Cannot reach libful API: {error.reason}"}}'.encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            if not head_only:
                self.wfile.write(message)

    def copy_response_headers(self, headers, content_length: int) -> None:
        for key, value in headers.items():
            if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "content-length":
                self.send_header(key, value)
        self.send_header("Content-Length", str(content_length))

    def log_message(self, fmt: str, *args) -> None:
        print(f"[libful-gui] {self.address_string()} - {fmt % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve libful GUI and proxy /api to FastAPI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    LibfulGuiHandler.api_target = args.api
    server = ThreadingHTTPServer((args.host, args.port), LibfulGuiHandler)
    print(f"libful GUI: http://{args.host}:{args.port}")
    print(f"API proxy:  {args.api}")
    server.serve_forever()


if __name__ == "__main__":
    main()
