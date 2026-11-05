"""Local-only, static Projection Studio server. No uploads or remote execution."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
import webbrowser

_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/studio.css": ("studio.css", "text/css; charset=utf-8"),
    "/studio.js": ("studio.js", "text/javascript; charset=utf-8"),
}


class StudioHandler(BaseHTTPRequestHandler):
    """Explicit allowlist: never serve arbitrary paths or caller-provided files."""

    def do_GET(self) -> None:  # noqa: N802 - stdlib HTTP API
        resource = _FILES.get(self.path)
        if resource is None:
            self.send_error(404, "Not found")
            return
        name, content_type = resource
        try:
            content = resources.files("projection_mapping").joinpath(
                "studio_static", name
            ).read_bytes()
        except (FileNotFoundError, OSError):
            self.send_error(500, "Studio asset unavailable")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(self), microphone=(self)")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "img-src 'self' blob: data:; media-src 'self' blob:; "
            "connect-src 'none'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'none'",
        )
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:  # noqa: N802
        self.send_error(405, "Read-only local viewer")

    def log_message(self, fmt: str, *args: object) -> None:
        # Avoid exposing local URL paths in console logs.
        pass


def start_server(*, port: int = 0) -> tuple[ThreadingHTTPServer, str]:
    """Bind to loopback only, even for packaged distributions."""
    if not 0 <= port <= 65535:
        raise ValueError("Invalid port")
    server = ThreadingHTTPServer(("127.0.0.1", port), StudioHandler)
    server.daemon_threads = True
    url = f"http://127.0.0.1:{server.server_port}/"
    return server, url


def main() -> None:
    parser = argparse.ArgumentParser(description="Local-first Projection Studio")
    parser.add_argument("--port", type=int, default=0, help="Loopback port (0: select free port)")
    parser.add_argument("--no-open", action="store_true", help="Don't open the browser")
    args = parser.parse_args()
    server, url = start_server(port=args.port)
    print(f"Projection Studio: {url}  (local only; Ctrl+C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
