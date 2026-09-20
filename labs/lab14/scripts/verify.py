"""THE CONTROL. Three gates, in order, and a record for every one of them.

This is the whole defence and it is about 80 lines. Read it - `cat verify.py`
is in the command list for exactly that reason.

    tools/list  ─►  gate 1  is this server on the trust list?
                    gate 2  does sha256(descriptor) match what we pinned?
                            ─► on a mismatch: BLOCK, and log the DIFF
    tools/call  ─►  gate 3  does the result match the shape its own schema declares?

Every gate logs whether it passed or blocked. A log that only records blocks
cannot tell you the check ran at all, which is why the clean run writes three
PASS records and the lab opens by reading them.

WHAT THIS CATCHES
  AML.T0110.000  a poisoned tool DEFINITION      - gate 2, by hash
  AML.T0110.002  a poisoned tool RESPONSE        - gate 3, by shape
  AML.T0109      a rug pull after approval       - gate 2, because the hash moves

WHAT THIS DOES NOT CATCH, AND THE LAB SHOWS IT ON PURPOSE
  A well-formed lie. `balance is 999999.00 USD` matches the declared shape
  perfectly, so gate 3 has nothing to object to. You checked the shape; nobody
  checked the source. The production answer is a SIGNED tool call - ATLAS
  AML.M0013, OWASP LLM04 prevention 5 - which binds a message to the identity
  that produced it rather than to its form. Lab 6 built exactly that HMAC and
  watched it work; this lab declines to rebuild it and names it instead.

Gate 2 is deliberately NOT a version check. OWASP LLM01:2026 prevention 10 says
why in its own caveat: "pinning does not stop a payload shipped in the pinned
version or tool-description poisoning that leaves the version unchanged." A
version number does not move when a description does. A hash does.
"""
import difflib
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab14lib as L

# Gate 3's shape rules. One regex per tool, keyed by name. In production this is
# full JSON Schema validation over a structured result plus a scan for imperative
# language; here it is the smallest thing that is honestly a shape check.
SHAPES = {
    "get_balance": re.compile(r"^balance is \d+\.\d{2} USD$"),
    "send_payment": re.compile(r"^payment of \S+ sent to \S+$"),
}


def check_descriptors(advertised, run):
    """Gates 1 and 2. Returns (tools_the_model_may_see, blocked, server_dropped).

    On a descriptor mismatch the WHOLE SERVER is dropped for this run, not just
    the one tool. That is not tidiness, it is a measurement: withholding one
    descriptor and keeping its siblings left the assistant holding only
    send_payment, and it offered to use it. A server that shipped one poisoned
    descriptor is not a server you keep three-quarters of.
    """
    trust = L.load_trust()
    entry = trust.get("servers", {}).get(L.SERVER)

    # ---- gate 1: is this server trusted at all?
    if not entry or not entry.get("trusted"):
        L.log(run=run, kind="server", tool=L.SERVER, verdict="BLOCK",
              rule="not_in_trust_list", detail="the server is not on the trust list")
        return [], list(advertised), True
    L.log(run=run, kind="server", tool=L.SERVER, verdict="PASS",
          rule="server_trusted", detail=entry.get("owner", ""))

    # ---- gate 2: does every descriptor match its pin?
    pins = entry.get("pinned", {})
    serve_pinned = bool(entry.get("serve_pinned"))
    kept, blocked = [], []
    for tool in advertised:
        name = tool.get("name")
        got = L.fingerprint(tool)
        want = pins.get(name)

        if want is None:
            L.log(run=run, kind="descriptor", tool=name, verdict="BLOCK",
                  rule="not_pinned", sha256=got,
                  detail="this server advertised a tool we never approved")
            blocked.append(tool)
        elif got != want:
            L.log(run=run, kind="descriptor", tool=name, verdict="BLOCK",
                  rule="descriptor_changed", sha256=got, pinned=want,
                  diff=descriptor_diff(entry, tool))
            blocked.append(tool)
            if serve_pinned:
                # After a re-pin the host stops asking the server what its tools
                # look like. It serves the copy a human reviewed and approved.
                # The poisoned text never reaches the model - it is not withheld
                # from the model so much as never offered to it.
                good = (entry.get("known_good") or {}).get(name)
                if good is not None:
                    kept.append(json.loads(json.dumps(good)))
                    L.log(run=run, kind="descriptor", tool=name, verdict="REPIN",
                          rule="served_pinned_copy", sha256=L.fingerprint(good))
        else:
            L.log(run=run, kind="descriptor", tool=name, verdict="PASS",
                  rule="matches_pin", sha256=got)
            kept.append(tool)

    if blocked and not serve_pinned:
        # Drop the server. The model sees no tools from it at all.
        return [], blocked, True
    return kept, blocked, False


def descriptor_diff(entry, tool):
    """The unified diff a human reviews before re-pinning.

    CSA, 2026-07-11: "require explicit human review of the diff before the new
    description takes effect, exactly as a pull request to production code would
    be reviewed." This is that diff.
    """
    known = entry.get("known_good", {}).get(tool.get("name"))
    if known is None:
        return "(no known-good copy on file for this tool)"
    return "\n".join(difflib.unified_diff(
        json.dumps(known, indent=2, sort_keys=True).splitlines(),
        json.dumps(tool, indent=2, sort_keys=True).splitlines(),
        "pinned", "advertised", lineterm="", n=1))


def check_result(run, name, text):
    """Gate 3. Returns the text the model may see, and whether it was blocked."""
    shape = SHAPES.get(name)
    if shape is not None and not shape.match(text.strip()):
        L.log(run=run, kind="result", tool=name, verdict="BLOCK",
              rule="result_off_schema", text=text[:300])
        return ("TOOL RESULT REJECTED: the server's answer did not match the shape "
                "its own schema declares. It was not passed on."), True
    L.log(run=run, kind="result", tool=name, verdict="PASS",
          rule="matches_declared_shape", text=text[:300])
    return text, False


def server_trusted():
    """Gate 1 alone, for callers that need to phrase the refusal correctly."""
    entry = L.load_trust().get("servers", {}).get(L.SERVER)
    return bool(entry and entry.get("trusted"))


def known_good(name):
    """The pinned copy, for the host to serve after a re-pin."""
    entry = L.load_trust().get("servers", {}).get(L.SERVER) or {}
    return (entry.get("known_good") or {}).get(name)


if __name__ == "__main__":
    print(__doc__)
