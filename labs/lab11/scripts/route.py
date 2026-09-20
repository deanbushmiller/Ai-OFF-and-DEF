"""RECOVER, first half - send what the detectors flagged to a person.

    python route.py

Reads the mismatch log. Any invoice whose latest content check was FLAG, or
whose latest comparison was MISMATCH, is moved out of invoices/ - the pipeline's
inbox - into review-queue/, with a JSON record beside it: what was found, the
lines that were found, and the file's hash so nobody can quietly swap it.

OWASP LLM01:2026 prevention 7: "Require explicit human confirmation before any
privileged, irreversible, or externally visible action." Paying an invoice is
all three. A flagged document does not get a worse score. It gets a person.
"""
import json
import shutil

from lab11lib import INVOICES, QUEUE, log_event, read_log, sha256

events = read_log()
latest = {}
for e in events:
    if e["kind"] in ("content-check", "compare"):
        latest.setdefault(e["image"], {})[e["kind"]] = e

print("ROUTE TO REVIEW")
print()
routed = 0
already = 0
for image, by_kind in latest.items():
    reasons, evidence = [], []
    cc = by_kind.get("content-check")
    if cc and cc["verdict"] == "FLAG":
        reasons.append(f"content check: {len(cc['rules'])} rule(s) fired")
        evidence += cc["lines"]
    cp = by_kind.get("compare")
    if cp and cp["verdict"] == "MISMATCH":
        reasons.append(f"visible-vs-read: {len(cp['extra'])} line(s) a person would not see")
        evidence += [l for l in cp["extra"] if l not in evidence]
    if not reasons:
        continue

    src, dest, record = INVOICES / image, QUEUE / image, QUEUE / (image.rsplit(".", 1)[0] + ".json")
    if record.exists():
        print(f"  already queued   {image}   (record: review-queue/{record.name})")
        already += 1
        continue
    if not src.exists():
        print(f"  not in the inbox {image}   (nothing to move)")
        continue
    QUEUE.mkdir(exist_ok=True)
    digest = sha256(src)
    shutil.move(str(src), str(dest))
    record.write_text(json.dumps({"image": image, "sha256": digest, "routed_by": "route.py",
                                  "reasons": reasons, "evidence": evidence}, indent=2) + "\n")
    log_event({"kind": "route", "image": image, "verdict": "QUEUED", "reasons": reasons})
    routed += 1
    print(f"  ROUTED   invoices/{image}  ->  review-queue/{image}")
    for r in reasons:
        print(f"             {r}")
    for l in evidence:
        print(f"             >>> {l}")
    print(f"             record: review-queue/{record.name}   sha256 {digest[:16]}...")
    print()

if routed == 0 and already == 0:
    print("  Nothing flagged in the log. Run inspect.py or compare.py first.")
elif routed == 0:
    print("  Nothing new to route.")
else:
    print(f"  {routed} item{'s' if routed > 1 else ''} out of the pipeline's inbox.")
    print("  Nothing downstream can act on it now, and a person has the")
    print("  evidence in one place instead of scattered across a terminal.")
