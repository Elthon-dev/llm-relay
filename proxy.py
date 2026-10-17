#!/usr/bin/env python3
"""Tiny auth gate in front of the local Ollama server.

Cloudflared quick tunnels are public, and Ollama's /v1 API ignores the
Authorization header. So we put this in the middle: it demands
`Authorization: Bearer $RELAY_TOKEN`, then relays the request to Ollama.
The userscript already sends that header when you set an API key.

Stdlib only, so it runs on a bare GitHub runner with zero pip installs.
"""
import http.server
import json
import os
import socketserver
import urllib.error
import urllib.request

TOKEN = os.environ.get("RELAY_TOKEN", "")
UPSTREAM = "http://127.0.0.1:11434"
PORT = int(os.environ.get("PORT", "8081"))


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _unauthorized(self):
        body = b'{"error":{"message":"unauthorized: bad or missing RELAY_TOKEN"}}'
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _relay(self, method):
        if TOKEN and self.headers.get("Authorization", "") != "Bearer " + TOKEN:
            return self._unauthorized()

        length = int(self.headers.get("Content-Length", 0) or 0)
        data = self.rfile.read(length) if length else None

        req = urllib.request.Request(UPSTREAM + self.path, data=data, method=method)
        req.add_header("Content-Type", self.headers.get("Content-Type", "application/json"))
        req.add_header("Accept", self.headers.get("Accept", "application/json"))

        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                payload = resp.read()
                status = resp.status
                ctype = resp.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            payload = e.read()
            status = e.code
            ctype = "application/json"
        except Exception as e:  # upstream down, timeout, etc.
            payload = json.dumps({"error": {"message": str(e)}}).encode()
            status = 502
            ctype = "application/json"

        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._relay("GET")

    def do_POST(self):
        self._relay("POST")

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print(f"auth proxy on 127.0.0.1:{PORT} -> {UPSTREAM} (token {'set' if TOKEN else 'UNSET!'})", flush=True)
    Server(("127.0.0.1", PORT), Handler).serve_forever()
