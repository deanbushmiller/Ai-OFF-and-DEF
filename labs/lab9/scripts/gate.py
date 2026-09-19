"""PREVENT - the ingest gate.

    python gate.py <artifact.pt>

Nothing reaches a build without passing through here. The gate:

  1. checks the file's SHA-256 against blocklist.json - anything quarantined
     before is refused without further thought
  2. runs picklescan, the same scanner you used in lab 1
  3. applies its own rules from rules.json

Exit 0 means allowed into the build. Exit 1 means blocked.

This is a stub, and it is honest about that. A production gate runs in CI
against every artifact, prefers a format that cannot execute code at all
(safetensors), and verifies a signature bound to a publisher identity
(OpenSSF Model Signing, Sigstore) before it even gets to scanning. Here it is
one tool and one small rule file.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "rules.json")
BLOCKLIST = os.path.join(HERE, "blocklist.json")
WIDTH = 64


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        return json.loads(open(path, encoding="utf-8").read())
    except (OSError, ValueError):
        return default


def scan(path):
    """Run picklescan and turn its output into a verdict.

    Returns (verdict, globals_found, note) where verdict is one of
    'clean', 'infected', 'no-verdict'.

    picklescan's exit codes: 0 nothing found, 1 something found, anything
    else is trouble. It can also exit 0 having printed a warning that it
    could not parse the file - which is NOT the same as clean, and is the
    single most important line in this function.
    """
    proc = subprocess.run(
        ["picklescan", "-p", path, "-g"],
        capture_output=True, text=True, timeout=120,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    found = re.findall(r"^\s+\*\s+(\S+)\s+-\s+(\w+)", out, re.M)

    unparsed = ("could not parse" in out) or ("Invalid PyTorch magic number" in out)

    if proc.returncode == 1:
        return "infected", found, "the scanner found something"
    if proc.returncode == 0 and not unparsed:
        return "clean", found, "the scanner read the whole file and found nothing"
    if proc.returncode == 0 and unparsed:
        return "no-verdict", found, "the scanner could not parse the file - it reported nothing because it read nothing"
    return "no-verdict", found, f"the scanner exited {proc.returncode}, which is neither clean nor infected"


def main():
    if len(sys.argv) != 2:
        print("usage: python gate.py <artifact.pt>")
        return 64
    path = sys.argv[1]
    if not os.path.exists(path):
        print("No such file: " + path)
        return 66

    rules = load_json(RULES, {"on_scanner_error": "block", "blocked_globals": []})
    blocked_hashes = load_json(BLOCKLIST, {}).get("blocked", {})
    digest = sha256(path)

    print("=" * WIDTH)
    print(" INGEST GATE  " + os.path.basename(path))
    print("=" * WIDTH)
    print()
    print("  sha256  " + digest)
    print()

    # --- 1. the block list, checked first and cheapest ---------------------
    if digest in blocked_hashes:
        entry = blocked_hashes[digest]
        print("  BLOCKED by the block list.")
        print("    quarantined " + entry.get("when", "earlier") + " as " + entry.get("name", "unknown"))
        print("    reason: " + entry.get("reason", "no reason recorded"))
        print()
        print("  The gate never had to run the scanner. That is the point of")
        print("  recording a hash: the second time is free.")
        print("=" * WIDTH)
        return 1

    # --- 2. the scanner ----------------------------------------------------
    try:
        verdict, found, note = scan(path)
    except (OSError, subprocess.SubprocessError) as exc:
        verdict, found, note = "no-verdict", [], "the scanner would not run: " + type(exc).__name__

    print("  scanner: " + note)
    if found:
        for name, judgement in found:
            mark = "  <-- dangerous" if judgement != "innocuous" else ""
            print("    " + name + mark)
    print()

    # --- 3. no verdict is decided FIRST -----------------------------------
    # Deliberate ordering. When the scanner could not finish, whatever it
    # managed to print before it stopped is a partial read, and a partial
    # read is not evidence of anything - including of the file being clean.
    # Decide on the fact that it failed, not on what it half-said.
    if verdict == "no-verdict":
        policy = rules.get("on_scanner_error", "block")
        print("  The scanner gave NO VERDICT on this file.")
        print("  rules.json says on_scanner_error = \"" + policy + "\"")
        print()
        if policy == "block":
            print("  BLOCKED. No verdict is not a clean verdict.")
            print()
            print("  If that line said \"pass\", this file would be in your build")
            print("  right now, and the gate would have reported nothing wrong -")
            print("  because nothing was read. That is how two malicious models")
            print("  sat on a public hub for eight months in 2025.")
            print("=" * WIDTH)
            return 1
        print("  ALLOWED. Nothing was found, because nothing was read.")
        print("  Read that sentence again before you move on.")
        print("=" * WIDTH)
        return 0

    # --- 4. the gate's own rules, then the scanner's opinion ---------------
    own = [n for n, _ in found if n in rules.get("blocked_globals", [])]
    if own:
        print("  BLOCKED by rules.json: " + ", ".join(own))
        print("  Your own rule, not the scanner's. This one you control.")
        print("=" * WIDTH)
        return 1

    if verdict == "infected":
        dangerous = [n for n, j in found if j != "innocuous"]
        print("  BLOCKED by the scanner: " + ", ".join(dangerous))
        print()
        print("  Note what did NOT happen: none of those names is in your own")
        print("  rules.json. This block is the vendor's opinion, and you are")
        print("  trusting their list stays current. Hold that thought.")
        print("=" * WIDTH)
        return 1

    print("  ALLOWED into the build.")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
