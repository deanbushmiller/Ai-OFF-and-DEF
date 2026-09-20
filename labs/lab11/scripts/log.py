"""Read the mismatch log.

    python log.py

One line per decision, in the order they happened. This is the question a
detector has to be able to answer afterwards: WHICH document said that, and
what exactly did it say? If nobody wrote it down, there is no answer.
"""
from lab11lib import LOG, read_log

events = read_log()
print(f"MISMATCH LOG   {LOG.name}   {len(events)} entr{'y' if len(events) == 1 else 'ies'}")
print()
if not events:
    print("  Nothing recorded yet. Run inspect.py, compare.py or gate.py first.")
    raise SystemExit(0)

print(f"  {'#':>2}  {'kind':<14} {'image':<20} {'verdict':<9} detail")
print("  " + "-" * 64)
for e in events:
    kind = e["kind"]
    if kind == "content-check":
        detail = f"{len(e['rules'])} rule(s) fired" if e["rules"] else "no rule fired"
    elif kind == "compare":
        detail = (f"{len(e['extra'])} hidden line(s), {e['erased_pixels']:,} faint px erased"
                  if e["verdict"] == "MISMATCH" else
                  f"{e['lines_seen']} lines both ways")
    elif kind == "gate":
        detail = (f"{e['label']} at {e['confidence']:.3f}, threshold {e['threshold']:.2f}, "
                  f"noise control {e['noise_flips']}/{e['noise_tries']}")
    elif kind == "route":
        detail = "moved to review-queue/"
    elif kind == "tune":
        detail = e.get("detail", "")
    else:
        detail = ""
    print(f"  {e['seq']:>2}  {kind:<14} {e['image']:<20} {e['verdict']:<9} {detail}")
    if kind == "compare" and e["verdict"] == "MISMATCH":
        for l in e["extra"]:
            print(f"      >>> {l}")
    if kind == "content-check" and e["verdict"] == "FLAG":
        for label in e["rules"]:
            print(f"      RULE {label}")
print()
