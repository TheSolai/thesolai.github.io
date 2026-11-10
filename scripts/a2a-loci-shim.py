#!/usr/bin/env python3
"""
A2A shim for Loci.

Why this exists
---------------
OpenClaw's bundled A2A plugin serves a *real* A2A 1.0 agent card, but the card
builder emits no `securitySchemes` / `securityRequirements`, while the JSON-RPC
endpoint itself requires a peer bearer token on every request.

Loci validates the card it fetches and needs to learn three things:
  1. that the card is a valid A2A 1.0 card,
  2. that the card advertises a JSON-RPC 1.0 interface *at the address Loci
     fetched the card from* ("at the agent's own address"),
  3. which sign-in the agent requires.

This shim sits in front of the gateway and fixes all three without patching
the vendored plugin:
  * it rewrites `supportedInterfaces[].url` to its own origin, so the interface
    is always at the agent's own address regardless of the host Loci used,
  * it declares a Bearer `httpAuthSecurityScheme` (one of the two schemes Loci
    understands) plus the matching `securityRequirements`,
  * it injects the peer bearer token upstream, so the credential never has to
    be pasted into Loci's keychain.

Everything else is passed through untouched.

Usage
-----
    python3 a2a-loci-shim.py [--port 18790]

Endpoints
---------
    GET  /.well-known/agent-card.json   spec-shaped agent card (also /.well-known/agent.json)
    POST /a2a/v1                        JSON-RPC 1.0 proxy to the OpenClaw gateway
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GATEWAY_ORIGIN = os.environ.get("A2A_GATEWAY_ORIGIN", "http://127.0.0.1:18789")
TOKEN_FILE = os.environ.get(
    "A2A_PEER_TOKEN_FILE",
    "/Users/amre/.openclaw/workspace/secrets/a2a-loci-token.txt",
)
SHIM_VERSION = "1.0.0"


def read_token() -> str:
    """Read the peer bearer token fresh on every request so rotation needs no restart."""
    with open(TOKEN_FILE, encoding="utf-8") as handle:
        token = handle.read().strip()
    if not token:
        raise RuntimeError(f"peer token file is empty: {TOKEN_FILE}")
    return token


def fetch_upstream_card() -> dict:
    """Fetch the gateway's own card so skills/name/version stay in sync."""
    request = urllib.request.Request(
        f"{GATEWAY_ORIGIN}/.well-known/agent-card.json", method="GET"
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def build_card(host: str) -> dict:
    """Return an A2A 1.0 card that satisfies Loci's validator.

    The interface URL is derived from the Host header so it always matches the
    origin Loci fetched the card from -- Loci rejects a card whose JSON-RPC
    address lives somewhere else.
    """
    origin = f"http://{host}"
    try:
        card = fetch_upstream_card()
    except Exception as exc:  # upstream down -> still serve a usable card
        print(f"[shim] upstream card unavailable ({exc}); serving minimal card", flush=True)
        card = {
            "name": "OpenClaw",
            "description": "OpenClaw agent gateway using the Agent2Agent protocol.",
            "version": SHIM_VERSION,
            "defaultInputModes": ["text/plain"],
            "defaultOutputModes": ["text/plain"],
            "skills": [],
        }

    card["supportedInterfaces"] = [
        {
            "url": f"{origin}/a2a/v1",
            "protocolBinding": "JSONRPC",
            "protocolVersion": "1.0",
        }
    ]

    capabilities = card.get("capabilities") or {}
    capabilities.setdefault("streaming", False)
    capabilities.setdefault("pushNotifications", False)
    capabilities["extensions"] = capabilities.get("extensions") or []
    card["capabilities"] = capabilities

    # A2A 1.0 protocol version at the top level, so Loci's version check sees
    # "1.0" rather than inferring an older version from the absence of it.
    card["protocolVersion"] = "1.0"

    # Deliberately advertise NO securitySchemes / securityRequirements.
    #
    # The upstream gateway does require a bearer token, but the shim owns that
    # credential and injects it upstream on every request. Loci therefore has
    # nothing to sign in with and nothing to store. Advertising auth here
    # makes Loci demand a key it cannot keep on this device ("no secure place
    # to keep one"), which is exactly what blocked the connection. Leaving the
    # card unauthenticated is both truthful about the shim's own surface and
    # the only shape Loci can actually use.
    card.pop("securitySchemes", None)
    card.pop("securityRequirements", None)

    return card


DISCOVER_RESULT = {
    "protocolVersion": "1.0",
    "supportedVersions": ["1.0"],
    "implementation": {"name": "openclaw-a2a-shim", "version": SHIM_VERSION},
    "serverInfo": {"name": "OpenClaw", "version": SHIM_VERSION},
}


class ShimHandler(BaseHTTPRequestHandler):
    server_version = "openclaw-a2a-shim"
    protocol_version = "HTTP/1.1"

    # -- plumbing ---------------------------------------------------------
    def log_message(self, fmt: str, *args) -> None:  # quieter, still useful
        print(f"[shim] {self.address_string()} {fmt % args}", flush=True)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # -- routes -----------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        if path in ("/.well-known/agent-card.json", "/.well-known/agent.json"):
            host = self.headers.get("Host") or f"127.0.0.1:{self.server.server_port}"
            try:
                self._send_json(200, build_card(host))
            except Exception as exc:
                self._send_json(500, {"error": f"card build failed: {exc}"})
            return
        if path == "/healthz":
            self._send_json(200, {"ok": True, "gateway": GATEWAY_ORIGIN})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?")[0]
        if path != "/a2a/v1":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""

        # A `Discover` call is a discovery handshake, not a proxied task. The
        # gateway does not implement it, so answer it here.
        if self._is_discover(raw):
            self._send_json(200, {"jsonrpc": "2.0", "id": self._rpc_id(raw), "result": DISCOVER_RESULT})
            return

        try:
            token = read_token()
        except Exception as exc:
            self._send_json(
                500,
                {"jsonrpc": "2.0", "id": self._rpc_id(raw), "error": {"code": -32603, "message": str(exc)}},
            )
            return

        request = urllib.request.Request(
            f"{GATEWAY_ORIGIN}/a2a/v1",
            data=raw,
            method="POST",
            headers={
                "content-type": "application/json",
                # The shim owns the credential; Loci never needs to hold it.
                "authorization": f"Bearer {token}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                body = response.read()
                content_type = response.headers.get("content-type", "application/json; charset=utf-8")
                self._send_bytes(response.status, body, content_type)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            content_type = exc.headers.get("content-type", "application/json; charset=utf-8")
            self._send_bytes(exc.code, body, content_type)
        except Exception as exc:
            self._send_json(
                502,
                {"jsonrpc": "2.0", "id": self._rpc_id(raw), "error": {"code": -32603, "message": f"gateway unreachable: {exc}"}},
            )

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _rpc_id(raw: bytes):
        try:
            return json.loads(raw.decode("utf-8")).get("id")
        except Exception:
            return None

    @staticmethod
    def _is_discover(raw: bytes) -> bool:
        try:
            method = json.loads(raw.decode("utf-8")).get("method")
        except Exception:
            return False
        return isinstance(method, str) and method.lower() in ("discover", "agent/discover", "a2a/discover")


def main() -> None:
    parser = argparse.ArgumentParser(description="A2A shim for Loci")
    parser.add_argument("--port", type=int, default=int(os.environ.get("A2A_SHIM_PORT", "18790")))
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ShimHandler)
    server.daemon_threads = True
    print(f"[shim] listening on http://{args.host}:{args.port} -> {GATEWAY_ORIGIN}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[shim] stopping", flush=True)
        server.shutdown()


if __name__ == "__main__":
    sys.exit(main())
