"""PREVENT - the ingestion validator.

    python validate.py corpus/                 validate every document in a folder
    python validate.py poisoned_handbook.pdf   validate one

Nothing is embedded without passing through here. Three rules, all of them from
OWASP LLM09:2026's prevention list, all of them measured against the real
poisoned document before they were written:

  RULE 1  invisible text      refuse ink a human cannot read
  RULE 2  provenance          refuse a document with no recorded origin
  RULE 3  topic claim         refuse a document that claims too many answers

Exit 0 means it may be embedded. Exit 1 means refused.

THIS IS A STUB AND IT IS HONEST ABOUT THAT. A production pipeline runs content
inspection on ingest AND on retrieved context, carries signed provenance rather
than a JSON file, and validates thousands of documents in CI. The named
production answer for the content half is Azure AI Content Safety. It costs money
per call, it adds latency to every ingest, and your documents leave your boundary
to be inspected. A bought control is still yours to run, monitor and recover.
"""
import json
import os
import pathlib
import sys

HERE = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
RULES = HERE / "rules.json"
PROVENANCE = HERE / "corpus" / "PROVENANCE.json"
WIDTH = 68

CANARY_QUESTIONS = [
    "Who invented the telephone?",
    "Who painted the Mona Lisa?",
    "Who invented the light bulb?",
    "Who discovered penicillin?",
    "Who invented the World Wide Web?",
    "Who was the first computer programmer?",
    "Who developed the theory of evolution?",
    "Who discovered radioactivity?",
]


def load_json(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------------------
# RULE 1 - invisible text, by content-stream inspection
# ---------------------------------------------------------------------------
def invisible_text(path, max_lum, min_pt):
    """Walk the PDF content stream tracking fill colour and font size, and
    attribute every text-showing operator to the state in force when it ran.

    extract_text() cannot do this. It returns characters and throws away how
    they were drawn - which is exactly why the attack works on the pipeline and
    on the human who opens the file to check it. Colour is a rendering
    instruction, and the rendering instruction is the evidence.
    """
    if pathlib.Path(path).suffix.lower() != ".pdf":
        return []          # a .txt has no rendering, so nothing can be hidden in one
    from pypdf import PdfReader
    from pypdf.generic import ContentStream

    reader = PdfReader(str(path))
    hidden = []
    for pageno, page in enumerate(reader.pages, 1):
        cs = ContentStream(page.get_contents(), reader)
        fill = (0.0, 0.0, 0.0)
        size = None
        for operands, operator in cs.operations:
            if operator == b"rg":
                fill = tuple(float(x) for x in operands[:3])
            elif operator == b"g":
                v = float(operands[0]); fill = (v, v, v)
            elif operator == b"Tf":
                try:
                    size = float(operands[1])
                except (IndexError, ValueError, TypeError):
                    pass
            elif operator in (b"Tj", b"TJ", b"'", b'"'):
                if operator == b"TJ":
                    text = "".join(str(x) for x in operands[0]
                                   if not isinstance(x, (int, float)))
                else:
                    text = str(operands[0])
                text = text.strip()
                if not text:
                    continue
                lum = 0.299 * fill[0] + 0.587 * fill[1] + 0.114 * fill[2]
                why = []
                if lum > max_lum:
                    why.append(f"luminance {lum:.2f} on a white page")
                if size is not None and size < min_pt:
                    why.append(f"{size:g}pt type")
                if why:
                    hidden.append((pageno, text, ", ".join(why)))
    return hidden


# ---------------------------------------------------------------------------
# RULE 3 - how many distinct canary topics does one document claim?
# ---------------------------------------------------------------------------
def topic_claims(path, threshold):
    """A reference document answers one question. Count how many DISTINCT
    canary questions any chunk of this document answers above the threshold.

    Measured on lab 2's corpus: every clean document covers 1 (or 0); the
    poisoned PDF covers 5. Counted per CHUNK instead, poison and clean are
    indistinguishable - each individual poisoned sentence imitates exactly one
    reference document, because that is what it is pretending to be. The tell is
    not any single chunk. It is one document pretending to be five.
    """
    sys.path.insert(0, str(HERE))
    import rag                                   # noqa: E402

    chunks = rag.chunk(rag.read_any(path))
    if not chunks:
        return 0, []
    cv = rag.embed(chunks)
    qv = rag.embed(CANARY_QUESTIONS)
    sims = qv @ cv.T                             # (questions, chunks)
    best = sims.max(axis=1)
    return (sum(1 for b in best if b > threshold),
            [(CANARY_QUESTIONS[i], float(b)) for i, b in enumerate(best) if b > threshold])


def validate_one(path, rules, quiet=False):
    name = os.path.basename(path)
    failures = []

    # RULE 1
    if rules.get("flag_invisible_text", True):
        hidden = invisible_text(path, rules.get("invisible_luminance", 0.9),
                                rules.get("min_font_pt", 7.0))
        if hidden:
            failures.append(("RULE 1  invisible text",
                             [f"{t[:56]!r} - {why}" for _, t, why in hidden]))

    # RULE 2
    if rules.get("require_provenance", True):
        docs = load_json(PROVENANCE, {}).get("documents", {})
        if name not in docs:
            failures.append(("RULE 2  no provenance",
                             ["no entry in corpus/PROVENANCE.json - "
                              "no source, no trust tier, nobody accountable"]))

    # RULE 3
    limit = rules.get("max_canary_topics", 2)
    n, which = topic_claims(path, rules.get("canary_similarity", 0.6))
    if n >= limit:
        failures.append((f"RULE 3  claims {n} topics (limit {limit})",
                         [f"{q!r} at {s:.3f}" for q, s in which]))

    # the student's own rule
    blocked = rules.get("blocked_indicators", [])
    if blocked:
        hit = [b for b in blocked
               if b == "invisible-text" and rules.get("flag_invisible_text", True)
               and invisible_text(path, rules.get("invisible_luminance", 0.9),
                                  rules.get("min_font_pt", 7.0))]
        if hit:
            failures.append(("YOUR RULE  " + ", ".join(hit),
                             ["the indicator your own detector produced"]))

    if not quiet:
        status = "REFUSED" if failures else "pass"
        print(f"  {status:<8} {name:<28} topics={n}")
        for label, details in failures:
            print(f"      {label}")
            for d in details:
                print(f"        - {d}")
    return failures


def main():
    if len(sys.argv) != 2:
        print("usage: python validate.py <file-or-folder>")
        return 64
    target = pathlib.Path(sys.argv[1])
    if not target.exists():
        print("No such file: " + str(target))
        return 66

    rules = load_json(RULES, {})
    print("=" * WIDTH)
    print(" INGESTION VALIDATOR  " + target.name)
    print("=" * WIDTH)
    print()

    if target.is_dir():
        files = sorted(list(target.glob("*.txt")) + list(target.glob("*.pdf")))
        refused = 0
        for f in files:
            if validate_one(f, rules):
                refused += 1
        print()
        print(f"  {len(files) - refused} of {len(files)} documents may be embedded.")
        if refused:
            print(f"  {refused} REFUSED.")
        print("=" * WIDTH)
        return 1 if refused else 0

    failures = validate_one(target, rules)
    print()
    if failures:
        print("  REFUSED. This document does not enter the index.")
        print()
        print("  Read which rule fired. Rule 1 is the one a human reviewer")
        print("  cannot reproduce by opening the file - the payload is drawn in")
        print("  white on a white page, and it is perfectly legible to the")
        print("  extractor that feeds your index.")
        print("=" * WIDTH)
        return 1
    print("  PASS. May be embedded.")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
