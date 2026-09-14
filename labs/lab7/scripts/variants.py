"""Surface variants of one fixed record.

    python variants.py --formats json,csv,kv,xml,urlq    ask the MODEL
    python variants.py --encode base64,hex               do it in PYTHON
    python variants.py --show                             print what exists

The record is in record.txt. It never changes. Only its rendering does.

WHY THE PROMPT LOOKS LIKE THAT
------------------------------
The prompt below asks a model to re-encode a record into an ordinary data
format. That is all it asks. There is nothing offensive in it, it would not be
refused by any content filter, and lifting it out of this image gets you a
format converter.

That is the lesson, not an oversight. The offence in this lab is not in the
prompt - it is in what the variants are then used for, and in the fact that a
detector keyed on wording is beaten by a format converter. Keep the teaching in
LAB.md and in the detector results, which is where it belongs.

MEASURED, temperature 0, three trials each, on Qwen2.5-1.5B-Instruct Q4_K_M
(see lab-research/lab7/probe-transcripts/):

    json  csv  kv  xml  urlq  yaml      6/6 fields, byte-identical 3/3
    ini                                 0/6 fields - returns bare [section]
                                        headers and DROPS every value
    syslog                              6/6 fields but no syslog framing, and
                                        supplying a worked example made it WORSE
                                        (5/6, and not deterministic)
    base64  hex                         FAIL. Degenerate repeating loops, ~49 s,
                                        not deterministic. One phrasing returns
                                        SGVsbG8gd29ybGQ= - base64 for "Hello
                                        world", a memorised string, not the input.

That last row is why --encode exists and why it says PYTHON on screen. A model
is a paraphraser, not a computer: it cannot perform an exact transform on data
it has not memorised. Real AI-assisted malware knows this - LAMEHUG (APT28,
2025, ATLAS AML.CS0044) calls a Qwen model for command TEXT and uses ordinary
code for everything that has to be correct.

Do not add a format to FORMATS without measuring it three times first.
"""
import argparse
import base64
import json
import os
import pathlib
import re
import time

WORK = pathlib.Path("/labs/lab7")
RECORD = WORK / "record.txt"
VARIANTS = WORK / "variants.json"
MODEL = os.environ.get("LAB7_MODEL",
                       "/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf")

# The shipped prompt. Benign on its own, deliberately.
PROMPT = ("Re-encode this record as {desc}. Keep every field name and every value "
          "exactly as given. Output only the encoded record, nothing else.\n\n"
          "Record:\n{record}")

# Only formats that were measured at 6/6 fields and identical across three runs.
FORMATS = {
    "json": "a single-line JSON object",
    "csv":  "a two-line CSV: a header row and one data row",
    "kv":   "a single line of key=value pairs separated by semicolons",
    "xml":  "a single-line XML element with one attribute per field",
    "urlq": "a URL query string (key=value joined by &)",
    # Measured good but NOT in the guided list - the guided path uses five and
    # this is the spare, so an expert has somewhere to go. Keep it measured:
    # 6/6 fields, byte-identical across three runs.
    "yaml": "YAML, one key per line",
}

ENCODERS = {
    "base64": lambda s: base64.b64encode(s.encode()).decode(),
    "hex":    lambda s: s.encode().hex(),
}

FENCE = re.compile(r"```[a-zA-Z0-9]*\s*\n(.*?)```", re.S)


def usable_threads():
    """How many CPUs we may actually use, not how many the host has.

    MEASURED 2026-09-13: os.cpu_count() returns the HOST's count (24 here) even
    inside `docker run --cpus=2`, because --cpus is a CFS quota rather than a
    cpuset, and sched_getaffinity agrees with it. llama.cpp then starts 24
    threads to share 2 CPUs and thrashes: the lab took 541 s at --cpus=2 against
    189 s at --cpus=4, which is worse than linear and should not be.

    Reading the cgroup v2 quota instead fixes it. A student is not usually
    affected - Docker Desktop's CPU setting changes the VM's core count, which
    os.cpu_count() sees correctly - but anyone who sets a per-container limit is,
    and it makes our own floor measurement mean something.
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


def record_text():
    return RECORD.read_text().strip()


def field_values(rec):
    """The values a detector could key on, independent of rendering."""
    return [v.strip() for _, v in (p.split("=", 1) for p in rec.split(", "))]


def extract(raw):
    """Pull the payload out of what the model actually returned.

    MEASURED: six of ten cases wrapped the answer in a code fence or prefaced it
    with a sentence, despite being told "output only the encoded record, nothing
    else". Without this the detector would be measuring our parser.
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


def load():
    if VARIANTS.exists():
        try:
            return json.loads(VARIANTS.read_text())
        except ValueError:
            pass
    return {}


def save(store):
    VARIANTS.write_text(json.dumps(store, indent=2))


def add(store, name, source, text, seconds, values, probe=None):
    """probe is the text the field count is measured against.

    For a re-encoding it is the output itself. For base64 and hex it is the
    DECODED form, because the values are all still in there - that is the whole
    reason D2 catches them. Counting against the encoded text would report
    "fields lost" for the two variants that lose nothing.
    """
    probe = text if probe is None else probe
    kept = [v for v in values if v in probe]
    store[name] = {"source": source, "text": text, "seconds": seconds,
                   "fields_kept": len(kept), "fields_total": len(values),
                   "missing": [v for v in values if v not in probe]}
    return store[name]


def do_formats(names):
    rec = record_text()
    values = field_values(rec)
    store = load()

    # The plain record is variant zero. A detector has to see the thing it is
    # supposed to be good at before the variants mean anything.
    add(store, "plain", "none", rec, 0.0, values)

    print("=" * 68)
    print(" THE PROMPT THAT IS ABOUT TO BE SENT, IN FULL")
    print("=" * 68)
    print()
    for line in PROMPT.format(desc="<the format>", record=rec).splitlines():
        print("   " + line)
    print()
    print("   Read it again. It is a format converter. There is no jailbreak")
    print("   here, no roleplay, no 'you are DAN', nothing a safety filter on")
    print("   the model would refuse - and nothing a prompt-inspection tool")
    print("   would flag. That is the point.")
    print()

    from llama_cpp import Llama
    threads = usable_threads()
    print(f"   loading the model ({pathlib.Path(MODEL).name}) ...")
    t0 = time.time()
    llm = Llama(model_path=MODEL, n_ctx=2048, n_threads=threads, verbose=False)
    print(f"   loaded in {time.time() - t0:.1f}s on {threads} thread(s). "
          f"{len(names)} generations to go, a few seconds each.")
    print()

    print("=" * 68)
    print(f" {len(names)} VARIANTS, GENERATED BY THE MODEL")
    print("=" * 68)
    for name in names:
        desc = FORMATS[name]
        t0 = time.time()
        out = llm.create_chat_completion(
            messages=[{"role": "user",
                       "content": PROMPT.format(desc=desc, record=rec)}],
            max_tokens=200, temperature=0.0)
        secs = round(time.time() - t0, 2)
        text = extract(out["choices"][0]["message"]["content"])
        v = add(store, name, "model", text, secs, values)
        print()
        print(f"--- {name}   {secs}s   fields kept {v['fields_kept']}/"
              f"{v['fields_total']}"
              + ("   <-- FIELDS LOST" if v["missing"] else ""))
        for line in text.splitlines():
            print("    " + line)
    save(store)
    print()
    print(f"   {len(names)} variants written to variants.json.")


def do_encode(names):
    rec = record_text()
    values = field_values(rec)
    store = load()
    add(store, "plain", "none", rec, 0.0, values)

    print("=" * 68)
    print(" TWO MORE VARIANTS - AND THE MODEL IS NOT INVOLVED")
    print("=" * 68)
    print()
    print("   These two come from Python's standard library:")
    print()
    print("       base64.b64encode(record.encode()).decode()")
    print("       record.encode().hex()")
    print()
    print("   Two lines, no model, no GPU, instant, and correct every time.")
    print("   Remember these two. They are about to be the only variants that")
    print("   get anywhere.")
    print()
    for name in names:
        t0 = time.time()
        text = ENCODERS[name](rec)
        v = add(store, name, "python", text, round(time.time() - t0, 4), values,
                probe=rec)
        print(f"--- {name}   {v['seconds']}s   (python)")
        print("    " + text)
        print()
    save(store)
    print(f"   variants.json now holds {len(store)} variants.")


def do_show():
    store = load()
    if not store:
        print("Nothing generated yet. Run:")
        print("    python variants.py --formats json,csv,kv,xml,urlq")
        return
    print(f"{'variant':<10} {'source':<8} {'fields':<8} bytes")
    for name, v in store.items():
        print(f"{name:<10} {v['source']:<8} "
              f"{v['fields_kept']}/{v['fields_total']:<6} {len(v['text'])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--formats", default="",
                    help="comma list: " + ",".join(FORMATS))
    ap.add_argument("--encode", default="",
                    help="comma list: " + ",".join(ENCODERS))
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    if args.show:
        do_show()
        return
    if args.formats:
        names = [n.strip() for n in args.formats.split(",") if n.strip()]
        bad = [n for n in names if n not in FORMATS]
        if bad:
            print(f"Unknown format(s): {', '.join(bad)}")
            print("Measured and available: " + ", ".join(FORMATS))
            print("ini, syslog, base64 and hex were measured and FAIL on this")
            print("model. See the comment at the top of this file.")
            raise SystemExit(2)
        do_formats(names)
        return
    if args.encode:
        names = [n.strip() for n in args.encode.split(",") if n.strip()]
        bad = [n for n in names if n not in ENCODERS]
        if bad:
            print(f"Unknown encoder(s): {', '.join(bad)}")
            raise SystemExit(2)
        do_encode(names)
        return
    print(__doc__.split("WHY THE PROMPT")[0].strip())


if __name__ == "__main__":
    main()
