"""RECOVERY, move 1 of 2: drop the server from the trust list.

    python drop.py

The log showed a descriptor that changed after we approved it. That is an
incident, not a bad day: a server that ships one poisoned descriptor is not a
server you keep three-quarters of.

Dropping it flips one field. On the next run the refusal happens at GATE 1,
before a single descriptor is read - earlier than the block you just saw, and
for a different reason. That movement is the point: a control that only ever
fails in the same place is not being tuned.

In production this is a change to a tool registry with an owner and a target
time to close. Here it is `"trusted": false`.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab14lib as L

t = L.load_trust()
entry = t.setdefault("servers", {}).setdefault(L.SERVER, {})
was = entry.get("trusted")
entry["trusted"] = False
L.save_trust(t)

print(f"Trust list: {L.SERVER}")
print(f"  trusted: {was}  ->  False")
print()
print("  ^ The server is off the trust list. Nothing from it will be read.")
print()
print("Run it again and watch WHERE the refusal happens now:")
print()
print("    python ask.py --wire-only")
