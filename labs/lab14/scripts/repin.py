"""RECOVERY, move 2 of 2: re-pin the known-good descriptor and restore service.

    python repin.py

You have read the diff. The change was not a legitimate update - it was an
instruction hidden in help text - so you do NOT pin what the server is
advertising now. You re-pin the copy you reviewed and approved, and you tell the
host to serve that copy rather than whatever the server says next time.

    CSA, 2026-07-11: "require explicit human review of the diff before the new
    description takes effect, exactly as a pull request to production code
    would be reviewed."

That is the whole loop, and it is what Cursor 1.3 shipped in response to
CVE-2025-54136: any change to an MCP configuration, "including something as
small as adding a space", triggers a mandatory approval prompt.

Note what re-pinning does NOT do. It restores the tool. It does not make the
server honest, and it does not help against a well-formed lie - you will see
that beat fail on purpose.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab14lib as L

t = L.load_trust()
entry = t.setdefault("servers", {}).setdefault(L.SERVER, {})

entry["trusted"] = True
entry["serve_pinned"] = True          # use OUR copy, not the advertised one
# Re-derive every pin from the known-good copies on file. The pin is a function
# of the approved bytes, never of what the server just sent.
entry["pinned"] = {name: L.fingerprint(tool)
                   for name, tool in (entry.get("known_good") or {}).items()}
L.save_trust(t)

print(f"Trust list: {L.SERVER}")
print("  trusted:      False -> True")
print("  serve_pinned: True   (the host uses OUR approved copy of each descriptor)")
for name, sha in entry["pinned"].items():
    print(f"  re-pinned {name}  sha256:{sha[:16]}...")
print()
print("  ^ Service restored on the descriptor YOU approved, not the one the")
print("    server is advertising. Run it again:")
print()
print("    python ask.py")
