"""Shared vocabulary for lab 15. Every script reads the rules from HERE.

Lab 13 learned this the expensive way: a verdict label lived in four files and
changing it was a four-file edit. Lab 14 learned the sharper version: assertions
that key on OUR OWN PROSE break the moment somebody rewords a message. So every
verdict here carries a RULE TOKEN, the token is what the log stores, and the
token is what runner.py, check.py and evidence.py assert on. The prose next to
it is free to change.

    ESTATE     the telemetry file - one record per host->destination channel
    COLLECTOR  what actually arrived, one JSON line per POST
    DETECTOR   the student's tunable: weights, threshold, window
    RULES      the verdict vocabulary
    limbs()    the four orthogonal tests
    score()    the weighted sum

WHY THE ESTATE IS A FILE AND THE PAYLOADS ARE A LOG
---------------------------------------------------
A SOC does not replay a day of packets. It reads flow records - NetFlow, Zeek
conn.log - which carry who talked to whom, when, and how much, and it reads
whatever payload inspection it has separately. So the cadence limbs read
estate.json and the content limb reads collector.log, and the two are different
files on purpose. That split IS the realistic asymmetry, and it is also why the
detector can be run on a laptop in milliseconds.
"""
import json
import os
import pathlib
import random
import statistics
import time

# /labs/lab15 in the image. LAB15_WORK exists ONLY so the build can run these
# same modules on the host while probing - it is never set inside the container
# and every student path resolves to the default. Lab 7 hardcoded this and the
# consequence was that its detector logic could only be tested by building an
# image, which is why its probes had to re-implement it and could drift from it.
WORK = pathlib.Path(os.environ.get("LAB15_WORK", "/labs/lab15"))
ESTATE = WORK / "estate.json"
COLLECTOR_LOG = WORK / "collector.log"
DETECT_LOG = WORK / "detect-log.jsonl"
DETECTOR = WORK / "detector.json"
DETECTOR_DEFAULT = WORK / "detector.default.json"
VARIANTS = WORK / "variants.json"
RECORD = WORK / "record.txt"

PORT = 8015                       # 127.0.0.1 only. See the README.
ENDPOINT = f"http://127.0.0.1:{PORT}/checkin"
HOURS = 24
HOSTS = 24
BEACON_HOST = "WKSTN-14"
BEACON_DEST = "198.51.100.37"
MARKER = "LAB-BEACON-7742"

# The four limbs, and the verdict vocabulary. A record's `rule` is always one of
# these. `gate` is only used for ordering the display.
RULES = {
    # limb hits
    "rare_dest":        (1, "limb 1  destination rarity"),
    "machine_cadence":  (2, "limb 2  machine cadence"),
    "high_volume":      (3, "limb 3  volume"),
    "record_values":    (4, "limb 4  record values survive"),
    # verdicts
    "above_threshold":  (5, "ALERT    score >= threshold"),
    "below_threshold":  (5, "clean    score <  threshold"),
    # the other two detectors, for comparison
    "signature_match":  (0, "D1       signature"),
    "lab7_behaviour":   (0, "lab 7    volume OR regularity"),
    # the prevent stub
    "volume_cap":       (0, "limit    rate and volume cap"),
    # the window setting, recorded so the tune is visible in the log
    "window_per_message": (6, "window   per message"),
    "window_per_channel": (6, "window   per channel-day"),
}


def label_of(rule):
    return RULES.get(rule, (0, rule))[1]


# --------------------------------------------------------------------- config
def load_detector():
    return json.loads(DETECTOR.read_text())


def save_detector(d):
    DETECTOR.write_text(json.dumps(d, indent=2) + "\n")


def reset_detector():
    """Restore the shipped configuration. runner.py calls this at every start.

    Without it a second run would begin with the threshold already tuned and
    the window already widened, so the lab would silently skip its own lesson.
    Lab 12 hit this with its rule file, lab 13 with its policy file and lab 14
    with its trust list. It is cheap to prevent and expensive to debug on
    thirty remote laptops.
    """
    DETECTOR.write_text(DETECTOR_DEFAULT.read_text())


# --------------------------------------------------------------------- record
def record_text():
    return RECORD.read_text().strip()


def field_values(rec=None):
    """The values a detector can key on, independent of rendering."""
    rec = record_text() if rec is None else rec
    return {v.strip() for _, v in (p.split("=", 1) for p in rec.split(", "))}


# --------------------------------------------------------------------- estate
def load_estate():
    return json.loads(ESTATE.read_text())


def cadence(times, min_events):
    """Coefficient of variation of the inter-arrival gaps, or None."""
    if len(times) < min_events:
        return None
    gaps = [b - a for a, b in zip(times, times[1:])]
    m = statistics.mean(gaps)
    return statistics.pstdev(gaps) / m if m else None


def schedule_times(interval_s, jitter_frac, seed, hours=HOURS):
    """A fixed seed, so every student on every machine sees the same numbers.

    Same shape as lab 7's schedule_times(). Determinism is a feature: thirty
    remote students with no shared screen is the wrong place to discover that
    the estate came out differently on somebody's laptop.
    """
    rng = random.Random(seed)
    t, out = 0.0, []
    while t < hours * 3600:
        out.append(t)
        t += interval_s * (1 + rng.uniform(-jitter_frac, jitter_frac))
    return out


def dest_host_counts(channels):
    d = {}
    for c in channels:
        d.setdefault(c["dest"], set()).add(c["host"])
    return {k: len(v) for k, v in d.items()}


# ------------------------------------------------------------------ collector
def collector_entries():
    if not COLLECTOR_LOG.exists() or not COLLECTOR_LOG.read_text().strip():
        return []
    return [json.loads(l) for l in COLLECTOR_LOG.read_text().splitlines()
            if l.strip()]


def delivered_values():
    """How many of the record's values ACTUALLY reached the collector.

    THIS IS THE PROTECTED ASSET, and it is measured at the collector's own
    store rather than inferred from any verdict. Lab 14's rule: a detect-and-log
    control will happily log a clean bill of health for a configuration that
    protects nothing, so at least one assertion has to measure the thing being
    protected. Here that thing is the record, and this is the number.
    """
    vals = field_values()
    seen = set()
    for e in collector_entries():
        _, hits = content_hits(e["body"], vals)
        seen |= hits
    return seen


# ------------------------------------------------------------- the four limbs
import base64   # noqa: E402  - kept next to the limb that uses it
import re       # noqa: E402


def content_hits(text, values=None):
    """Peel the surface off, then return which of the record's VALUES survive.

    This is lab 7's D2, unchanged, because lab 7 already measured it at 10/10
    across every variant that model produces. It never asks what format the body
    is in: it decodes anything that looks like base64 or hex, percent-decodes,
    splits on everything that is not part of a value, and counts.

    The point worth keeping in front of a student: this limb cannot be moved by
    rewording, because the record is the thing the attacker NEEDED to send.
    """
    values = field_values() if values is None else values
    t = text
    for tok in re.findall(r"[A-Za-z0-9+/=]{24,}", t):
        try:
            dec = base64.b64decode(tok + "===").decode("utf-8")
            if dec.isprintable():
                t += "\n" + dec
        except Exception:
            pass
    for tok in re.findall(r"\b[0-9a-fA-F]{24,}\b", t):
        try:
            dec = bytes.fromhex(tok).decode("utf-8")
            if dec.isprintable():
                t += "\n" + dec
        except Exception:
            pass
    t = re.sub(r"%3A", ":", t, flags=re.I)
    toks = set(re.split(r"[^A-Za-z0-9:.\-]+", t))
    hits = values & toks
    return len(hits), hits


def signature_limb(text):
    """The whole of D1. One line, and it is what most deployed rules are."""
    return MARKER.lower() in text.lower()


def limbs(chan, counts, cfg, payloads=None):
    """The four orthogonal tests. None of them can be turned off by rewording.

    LIMB 2 IS THE ONE DESIGN CHANGE FROM LAB 7 AND IT IS LOAD-BEARING.
    Lab 7 asked `cv < 0.35` - *is this a timer* - which 95% jitter beats for
    free, measured, at no cost to the attacker's throughput. This asks
    `cv < 1.0` - *is this not a human* - which does not break, because bounded
    jitter is still bounded: a beacon at 95% jitter sits at cv 0.543 while human
    browsing sits at 4.482. Free jitter moves a beacon from 0.000 to 0.543 and
    never gets it anywhere near a person.
    """
    lim = cfg["limits"]
    times = chan["times"]
    cv = cadence(times, lim["min_events"])

    rare = counts.get(chan["dest"], 99) <= lim["rare_max_hosts"]
    machine = cv is not None and cv < lim["burst_cv_max"]
    volume = len(times) > lim["volume_max"]

    content = False
    if payloads:
        if cfg["window"] == "channel":
            # Reassemble the channel's whole day, THEN match. This is lab 7's
            # own defence #2 - "normalise before you match" - extended from
            # format to time, and it is the recovery move.
            content = content_hits("\n".join(payloads))[0] >= lim["min_fields"]
        else:
            content = any(content_hits(p)[0] >= lim["min_fields"]
                          for p in payloads)

    return {"rare_dest": rare, "machine_cadence": machine,
            "high_volume": volume, "record_values": content}


def score(l, cfg):
    w = cfg["weights"]
    return sum(w[k] for k, v in l.items() if v)


def verdict(l, cfg):
    s = score(l, cfg)
    return s, s >= cfg["threshold"]


# ------------------------------------------------------------------------ log
def log(**rec):
    rec.setdefault("ts", round(time.time(), 3))
    rec.setdefault("run", "-")
    with DETECT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def read_log():
    if not DETECT_LOG.exists():
        return []
    return [json.loads(l) for l in DETECT_LOG.read_text().splitlines()
            if l.strip()]


# ---------------------------------------------------------------- presentation
BAR = "=" * 70
THIN = "-" * 70


def precision(tp, fp):
    return tp / (tp + fp) if (tp + fp) else 0.0


def confusion(channels, counts, cfg, payload_for):
    """Score every channel. Returns (tp, fp, fn, rows)."""
    tp = fp = fn = 0
    rows = []
    for c in channels:
        l = limbs(c, counts, cfg, payload_for(c))
        s, alert = verdict(l, cfg)
        if c["malicious"] and alert:
            tp += 1
        elif c["malicious"]:
            fn += 1
        elif alert:
            fp += 1
        rows.append((c, l, s, alert))
    return tp, fp, fn, rows


# ------------------------------------------------------- talking to the collector
import socket        # noqa: E402
import subprocess    # noqa: E402
import sys           # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402


def wait_for_port(host="127.0.0.1", port=PORT, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            s.settimeout(0.4)
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.05)
    return False


def start_collector(cap=None):
    """Start collector.py as a child, or reuse one already listening.

    A collector may ALREADY be running - expert mode starts one by hand. Without
    this check we would start a second one, it would fail to bind silently, and
    wait_for_port would see the FIRST one: everything appears to work, which is
    worse than failing. Lab 7 hit exactly this on 2026-09-13.

    Returns (proc_or_None, reused_bool). Only ever stop a process you started.
    """
    if wait_for_port(timeout=0.4):
        return None, True
    cmd = [sys.executable, str(WORK / "collector.py")]
    if cap is not None:
        cmd += ["--cap", str(cap)]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    if not wait_for_port():
        proc.terminate()
        return None, False
    return proc, False


def stop_collector(proc):
    if not proc:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def post(text, channel, variant, source, hour=0):
    """One check-in. Returns the HTTP status, or 0 if the endpoint refused."""
    req = urllib.request.Request(
        ENDPOINT, data=text.encode(),
        headers={"Content-Type": "text/plain",
                 "X-Lab-Channel": channel,
                 "X-Lab-Variant": variant,
                 "X-Lab-Source": source,
                 "X-Lab-Hour": str(hour)})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError):
        return 0


def load_variants():
    return json.loads(VARIANTS.read_text())["variants"]


def beacon_payloads():
    """What the compromised channel actually sent, read from collector.log.

    The detector never reads variants.json. A defender does not get the
    attacker's working files - only what arrived.
    """
    return [e["body"] for e in collector_entries()
            if e.get("channel") == f"{BEACON_HOST}->{BEACON_DEST}"]


def payload_for(chan):
    """Payloads visible to the detector for a channel. Only the beacon has any.

    Every other channel in the estate is a flow record with no payload
    inspection attached, which is realistic and is also why the content limb
    can never produce a false positive here. Said out loud in LAB.md.
    """
    if chan["dest"] == BEACON_DEST:
        return beacon_payloads()
    return []
