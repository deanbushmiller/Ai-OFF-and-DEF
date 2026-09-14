"""A mock MCP server for Velocity Corp's finance tools.

    python mcp_server.py            serve on 127.0.0.1:8007
    python mcp_server.py --sign     also sign every response (the beat-5 defence)

It speaks real MCP shape over JSON-RPC 2.0:

    initialize              handshake
    tools/list              advertise the tools, their descriptions and schemas
    tools/call              run one tool, return its result

Real MCP runs this over stdio or Streamable HTTP. This uses HTTP on loopback so
the student can put a proxy in the middle and watch the messages go past - which
is the entire point of the lab.

NOTHING HERE IS THE VULNERABILITY. This server is honest: it returns the correct
balance for the account it is asked about, and it records payments it is told to
make. The vulnerability is that its answers reach the client across a channel
with no integrity protection, and anything sitting on that channel can rewrite
them. That is why the attack in this lab needs no bug in this file.

Stdlib only - http.server and socketserver, the same approach lab 3 used. No new
dependency enters the shared image for this lab.
"""
import argparse
import hashlib
import hmac
import http.server
import json
import pathlib
import socketserver
import sys

WORK = pathlib.Path("/labs/lab6")
LEDGER = WORK / "ledger.json"

HOST, PORT = "127.0.0.1", 8007

# The shared secret the beat-5 defence uses. In a real deployment this would be
# a TLS channel or a signed transport, not a hardcoded string - but the failure
# it prevents is exactly the one the student is about to cause.
SECRET = b"lab6-demo-shared-secret-not-a-real-key"

ACCOUNTS = {
    "chk-001": {"owner": "Velocity Corp operating account", "balance": "4820.55"},
    "chk-002": {"owner": "Velocity Corp petty cash",        "balance": "17.02"},
}

# The tool descriptions and schemas. THE USER NEVER SEES THESE - the model does.
# OWASP LLM08:2026 Hidden Context Exposure, risk #1 (tool and function schemas)
# and risk #4, whose worked example is literally a tool description served by an
# MCP server. Beat 1 of the lab is just reading them.
TOOLS = [
    {
        "name": "get_balance",
        "description": "Return the current balance of one Velocity Corp account.",
        "inputSchema": {
            "type": "object",
            "properties": {"account": {"type": "string",
                                       "description": "Account number, e.g. chk-001"}},
            "required": ["account"],
        },
    },
    {
        "name": "send_payment",
        "description": "Send a payment from the operating account to a payee.",
        "inputSchema": {
            "type": "object",
            "properties": {"to": {"type": "string", "description": "Payee reference"},
                           "amount": {"type": "number", "description": "Amount in USD"}},
            "required": ["to", "amount"],
        },
    },
]


def sign(body: str) -> str:
    """HMAC-SHA256 over the exact bytes of the result. The beat-5 defence."""
    return hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()


def call_tool(name, args):
    if name == "get_balance":
        acct = str(args.get("account", "")).strip()
        if acct not in ACCOUNTS:
            return f"ERROR: no account {acct!r}."
        return f"balance is {ACCOUNTS[acct]['balance']} USD"

    if name == "send_payment":
        to, amount = args.get("to"), args.get("amount")
        # Recorded, never performed. No money exists in this lab.
        entries = json.loads(LEDGER.read_text()) if LEDGER.exists() else []
        entries.append({"to": to, "amount": amount})
        LEDGER.write_text(json.dumps(entries, indent=2))
        return f"payment of {amount} sent to {to}"

    return f"ERROR: no tool named {name!r}."


def handle(req, signing):
    """One JSON-RPC request in, one response out."""
    method, rid = req.get("method"), req.get("id")
    params = req.get("params") or {}

    if method == "ping":
        # mitm.py's readiness probe. Answered, not logged, never part of MCP.
        return {"jsonrpc": "2.0", "id": rid, "result": {"ready": True}}

    if method == "initialize":
        result = {"protocolVersion": "2024-11-05",
                  "serverInfo": {"name": "velocity-finance-tools", "version": "1.0.0"},
                  "capabilities": {"tools": {}}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        text = call_tool(params.get("name"), params.get("arguments") or {})
        result = {"content": [{"type": "text", "text": text}]}
    else:
        return {"jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"no method {method!r}"}}

    resp = {"jsonrpc": "2.0", "id": rid, "result": result}
    if signing:
        # Sign the result exactly as it will be serialised, so any edit in
        # transit - one digit, one character - invalidates it.
        resp["_signature"] = sign(json.dumps(result, sort_keys=True))
    return resp


class Handler(http.server.BaseHTTPRequestHandler):
    signing = False

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            self.send_error(400, "bad JSON")
            return
        body = json.dumps(handle(req, self.signing)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass  # the proxy is what logs; a second log would just be noise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sign", action="store_true",
                    help="sign every response (the beat-5 defence)")
    args = ap.parse_args()
    Handler.signing = args.sign

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        mode = "signing responses" if args.sign else "unsigned"
        print(f"MCP server listening on {HOST}:{PORT} ({mode})", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
