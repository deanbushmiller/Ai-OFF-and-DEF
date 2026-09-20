"""The firewall itself: the scanners, the severity gate and the log writer.

Shared by firewall.py, log.py, tune.py and check.py so there is exactly one
copy of the rules logic. Nothing in here loads the model.

THE SHAPE, in one paragraph. A request goes out to a page, comes back as HTML,
and is scraped into text. The INBOUND scan runs on that text (plus the raw HTML
for the concealment checks) and returns a set of detector families; the severity
is the number of families that matched; the gate blocks if that severity is at
or above rules.json's block_at. If the gate allows it, the text reaches the
model. The OUTBOUND scan runs on the model's answer and looks for a seeded fake
secret. Both directions write a record to firewall-log.jsonl with the verdict.

WHY 'detected' AND 'filtered' ARE TWO SEPARATE FIELDS
-----------------------------------------------------
Because they are two different things, and the gap between them is this lab.
Azure AI Content Safety's Prompt Shields returns exactly this pair in its own
annotations, and its documentation tells you to "adjust from block to annotate
mode to log without filtering" when you are tuning. A rule can match and the
firewall can still wave the request through - which is not a bug, it is a
threshold decision someone made. detected:true with filtered:false is the
signature of that decision, and it is what the student goes looking for.
"""
import json
import pathlib
import re
import time
import unicodedata

LAB = pathlib.Path("/labs/lab12")
RULES = LAB / "rules.json"
LOG = LAB / "firewall-log.jsonl"

# Severity is the family count. Deliberately crude, and deliberately the same
# crude thing CVE-2026-60086 did.
ORDER = ["NONE", "MEDIUM", "HIGH", "CRITICAL"]


def severity_for(n_families):
    return ORDER[min(n_families, 3)]


def at_or_above(sev, floor):
    return ORDER.index(sev) >= ORDER.index(floor)


# Characters that render as nothing in a browser and as content to a tokenizer.
# Unicode Tags block, zero-width family, variation selectors. This is OWASP
# LLM01:2026 prevention 5's list.
INVISIBLE = re.compile(r"[\U000E0000-\U000E007F​‌‍⁠︀-️]")


def load_rules():
    return json.loads(RULES.read_text())


def to_text(html):
    """Strip tags the way a naive scraper does - lab 3's function, unchanged.

    It keeps text inside display:none and text inside HTML comments. A browser
    paints neither. This is not a bug we are fixing; it is the behaviour the
    firewall exists to compensate for, so it stays exactly as lab 3 shipped it.
    """
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--(.*?)-->", r" \1 ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def normalize(text):
    """Microsoft's rule, four words: "normalize before you match" (2026-09-03).

    NFKC folds lookalike forms together; the strip removes the invisible
    characters outright. Without this, one TAG SPACE inside a word is enough to
    miss every phrase rule, which is precisely what the 2026 campaign did to
    keyword filters.
    """
    return INVISIBLE.sub("", unicodedata.normalize("NFKC", text))


def scan_inbound(html, rules):
    """Return (extracted_text, {family: [what matched]}, severity).

    ORDER MATTERS HERE, and it is the subtle part of the whole lab.

    Concealment is scored on the RAW html, BEFORE normalising. Normalising
    strips the invisible characters, which destroys the evidence that anything
    was concealed - measured 2026-09-19: the smuggled page scores HIGH on raw
    bytes and MEDIUM if you sanitise first. So: find the concealment first, then
    match the phrase families on normalised text.

    "Normalize before you match" is about matching. It is not about scoring.
    """
    raw_text = to_text(html)
    clean_text = normalize(raw_text)

    hits = {}
    for family, patterns in rules["inbound_families"].items():
        matched = [p for p in patterns if re.search(p, clean_text, re.I)]
        if matched:
            hits[family] = matched

    concealment = [p for p in rules["concealment_css"] if re.search(p, html, re.I)]
    if rules.get("concealment_invisible_chars") and INVISIBLE.search(html):
        concealment.append("invisible-unicode")
    if concealment:
        hits["concealment"] = concealment

    return raw_text, hits, severity_for(len(hits))


def scan_outbound(answer, rules):
    """Return {rule_name: redacted_match} for every sensitive pattern in the answer.

    Patterns, not values. rules.json carries the SHAPE of the credential, so the
    rule file can be read, diffed and pasted into a ticket without being a copy
    of the thing it protects. Real DLP rules are written this way for exactly
    that reason.

    The match is redacted here, in the only function that ever holds it, so
    there is no path by which the whole value reaches a caller, the log, or the
    student's transcript.

    The honest limit, in OWASP LLM02:2026's own words (Tier 1, prevention 5):
    "Sanitize with classifiers, not regex alone: pattern matching plus NER plus
    trained classifiers, because regex fails on encoded and cross-lingual
    output." This is regex alone. Base64 the key and it walks straight out.
    """
    found = {}
    for name, pattern in rules["outbound_patterns"].items():
        m = re.search(pattern, answer)
        if m:
            found[name] = m.group(0)[:12] + "...REDACTED"
    return found


def log_write(record):
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    return record


def log_read():
    if not LOG.exists():
        return []
    out = []
    for line in LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out
