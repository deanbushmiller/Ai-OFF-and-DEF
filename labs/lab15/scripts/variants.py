"""Red-team your own detector: make it a variant it has never seen.

    python variants.py --live json      generate one, deliver it, test the limb
    python variants.py --live yaml
    python variants.py --formats        which ones were measured to work

ONE GENERATION, ONE PROCESS. That is the course rule and this file is the only
place in lab 15 that touches a model at all. Everything else - the estate, the
four limbs, the sweep, the tune, the evidence - is deterministic Python with
fixed seeds.

THAT ASYMMETRY IS THE LAB'S THESIS MADE LIVE
---------------------------------------------
The only nondeterministic thing in this lab is the ATTACKER'S SURFACE. The
detector does not read surface. So a variant that did not exist when the
detector was written, generated on your laptop, in wording nobody predicted, is
caught by a limb that was never updated - and the assertion on it keys on the
FIELD COUNT and the VERDICT, never on a sentence the model produced.

Lab 13 measured why that distinction matters: under a tightened policy the model
stated "I have verified that the admin box is readable" when it had verified
nothing. A model narrates the instruction it was given, not the outcome it got.
Assert on structure.

WHY THIS IS A DEFENDER'S COMMAND AND NOT AN ATTACKER'S
-------------------------------------------------------
You are testing your own control against an input you have not seen. That is
ATLAS AML.M0035, AI Red Team - "convert confirmed failures into regression
tests, evaluation datasets, detection logic" - and it is exactly what lab 16
picks up as a process. A control nobody has attacked is a control nobody has
tested.

THE PROMPT, AND WHY IT LOOKS LIKE THAT
---------------------------------------
It asks a model to re-encode a record into an ordinary data format. That is all
it asks. There is nothing offensive in it, no content filter would refuse it,
and lifting it out of this image gets you a format converter. That is the
lesson, not an oversight: a detector keyed on WORDING is beaten by a format
converter, so the defence cannot be keyed on wording.

MEASURED, temperature 0, three trials each, on Qwen2.5-1.5B-Instruct Q4_K_M
(lab-research/lab7/probe-transcripts/):

    json  csv  kv  xml  urlq  yaml    6/6 fields, byte-identical 3/3
    ini                               0/6 - returns bare [section] headers
    syslog                            6/6 but no syslog framing, and a worked
                                      example made it WORSE
    base64  hex                       FAIL. Degenerate loops, ~49 s, not
                                      deterministic. One phrasing returns
                                      SGVsbG8gd29ybGQ= - base64 for "Hello
                                      world", a memorised string, not the input

A model is a paraphraser, not a computer. Do not add a format here without
measuring it three times first.
"""
import argparse
import os
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab15lib as L

MODEL = os.environ.get(
    "LAB15_MODEL",
    "/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf")

CHANNEL = f"{L.BEACON_HOST}->{L.BEACON_DEST}"

PROMPT = ("Re-encode this record as {desc}. Keep every field name and every "
          "value exactly as given. Output only the encoded record, nothing "
          "else.\n\nRecord:\n{record}")

FORMATS = {
    "json": "a single-line JSON object",
    "csv":  "a two-line CSV: a header row and one data row",
    "kv":   "a single line of key=value pairs separated by semicolons",
    "xml":  "a single-line XML element with one attribute per field",
    "urlq": "a URL query string (key=value joined by &)",
    "yaml": "YAML, one key per line",
}

FENCE = re.compile(r"```[a-zA-Z0-9]*\s*\n(.*?)```", re.S)


def usable_threads():
    """How many CPUs we may actually use, not how many the host has.

    MEASURED at lab 7, 2026-09-13: os.cpu_count() returns the HOST's count even
    inside `docker run --cpus=2`, because --cpus is a CFS quota rather than a
    cpuset, and sched_getaffinity agrees with it. llama.cpp then starts 24
    threads to share 2 CPUs and thrashes - 541 s against 89 s, worse than
    linear. Reading the cgroup quota instead fixes it.
    """
    n = os.cpu_count() or 4
    try:
        quota, period = (pathlib.Path("/sys/fs/cgroup/cpu.max")
                         .read_text().split())          # cgroup v2
        if quota != "max":
            n = max(1, min(n, int(int(quota) // int(period))))
    except (OSError, ValueError):
        try:
            q = int(pathlib.Path(                        # cgroup v1 fallback
                "/sys/fs/cgroup/cpu/cpu.cfs_quota_us").read_text())
            p = int(pathlib.Path(
                "/sys/fs/cgroup/cpu/cpu.cfs_period_us").read_text())
            if q > 0:
                n = max(1, min(n, q // p))
        except (OSError, ValueError, ZeroDivisionError):
            pass
    return n


def extract(raw):
    """Pull the payload out of what the model actually returned.

    MEASURED at lab 7: six of ten cases wrapped the answer in a code fence or
    prefaced it with a sentence, despite being told "output only the encoded
    record, nothing else". Without this the detector would be measuring our
    parser rather than the model.
    """
    t = raw.strip()
    m = FENCE.search(t)
    if m:
        return m.group(1).strip()
    lines = t.splitlines()
    while lines and lines[0].rstrip().endswith(":"):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", default="", help="one of: " + ",".join(FORMATS))
    ap.add_argument("--formats", action="store_true")
    args = ap.parse_args()

    if args.formats or not args.live:
        print("Measured good on this model, 6/6 fields, identical 3/3:")
        for k, v in FORMATS.items():
            print(f"   {k:<8} {v}")
        print()
        print("Measured and FAIL: ini (0/6), syslog (no framing), base64, hex.")
        print("See the comment at the top of this file.")
        return 0

    name = args.live.strip()
    if name not in FORMATS:
        print(f"Unknown format: {name}")
        print("Measured and available: " + ", ".join(FORMATS))
        return 2

    cfg = L.load_detector()
    rec = L.record_text()
    vals = L.field_values()

    print(L.BAR)
    print(" RED-TEAM YOUR OWN DETECTOR")
    print(L.BAR)
    print()
    print("   Your detector was written before this variant existed. Nobody")
    print("   has updated it. Let us make it one and see.")
    print()
    print("   THE PROMPT THAT IS ABOUT TO BE SENT, IN FULL:")
    print()
    for line in PROMPT.format(desc=FORMATS[name], record=rec).splitlines():
        print("      " + line)
    print()
    print("   Read it again. It is a format converter. No jailbreak, no")
    print("   roleplay, nothing a safety filter would refuse and nothing a")
    print("   prompt scanner would flag. A detector keyed on WORDING loses to")
    print("   this. That is why yours is not.")
    print()

    from llama_cpp import Llama
    threads = usable_threads()
    print(f"   loading {pathlib.Path(MODEL).name} ...")
    t0 = time.time()
    llm = Llama(model_path=MODEL, n_ctx=2048, n_threads=threads, verbose=False)
    print(f"   loaded in {time.time() - t0:.1f}s on {threads} thread(s). "
          f"One generation, a few seconds.")
    print()

    t0 = time.time()
    out = llm.create_chat_completion(
        messages=[{"role": "user",
                   "content": PROMPT.format(desc=FORMATS[name], record=rec)}],
        max_tokens=200, temperature=0.0)
    secs = time.time() - t0
    text = extract(out["choices"][0]["message"]["content"])

    print(f"   --- {name}   {secs:.1f}s   generated just now ---")
    for line in text.splitlines():
        print("       " + line)
    print()

    hits, which = L.content_hits(text, vals)
    sig = L.signature_limb(text)
    caught = hits >= cfg["limits"]["min_fields"]

    print(L.BAR)
    print(" THE TEST")
    print(L.BAR)
    print()
    print(f"   signature rule (D1)      {'CAUGHT' if sig else 'miss'}")
    print(f"   record_values limb       {hits}/6 values survive  ->  "
          f"{'CAUGHT' if caught else 'MISS'}")
    print()
    if caught:
        print("   Caught, by a limb nobody updated, on wording nobody")
        print("   predicted. The record is the thing the attacker needed to")
        print("   send, so the record is what survives every rendering - and")
        print("   that is what your limb asks about.")
        print()
        print("   Note which number this lab checks. Not the model's sentence")
        print("   - the FIELD COUNT and the verdict. Lab 13 measured a model")
        print("   confidently narrating something that never happened, so no")
        print("   assertion in this course keys on prose. Yours should not")
        print("   either.")
    else:
        print("   It got through. That is a real finding, not a lab failure:")
        print("   write it down and widen the limb.")
    print()

    # Deliver it, so it is in the log with everything else.
    proc, reused = L.start_collector()
    if proc is None and not reused:
        print("   (could not reach the collector to deliver it - the limb")
        print("    result above still stands)")
    else:
        try:
            L.post(text, CHANNEL, f"live-{name}", "model", hour=23)
        finally:
            L.stop_collector(proc)
        print(f"   Delivered to the collector as 'live-{name}'. It is now in")
        print("   the same log as the other ten.")
        print()

    L.log(run="live", kind="regression", detector="score",
          rule="record_values" if caught else "below_threshold",
          variant=f"live-{name}", fields=hits, total=len(vals),
          signature=sig, seconds=round(secs, 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
