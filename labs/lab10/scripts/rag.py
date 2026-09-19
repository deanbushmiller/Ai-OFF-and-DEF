"""
The same toy RAG pipeline you attacked in lab 2, with three things added.

    python rag.py build            embed corpus/ into a searchable index
    python rag.py ask "question"   retrieve, then answer from what was retrieved
    python rag.py ingest FILE      add one document - VALIDATED FIRST
    python rag.py log              show the retrieval log

WHAT IS NEW SINCE LAB 2, and it is only these three things:

  1. PROVENANCE. Every chunk carries the tag of the document it came from -
     source, ingestion time, trust tier. Lab 2 stored the filename and nothing
     else. A chunk you cannot attribute is a chunk you cannot purge.

  2. A RETRIEVAL LOG. Every question writes down which chunks came back, their
     scores, and which one drove the answer. OWASP LLM09:2026 prevention 6:
     "Keep immutable logs of retrieval activity (... query, returned IDs,
     similarity scores)." Without it, "why did it say that?" has no answer.

  3. INGEST GOES THROUGH THE VALIDATOR. `ingest` calls validate.py and refuses
     a document that fails. You can override with --force, and in this lab you
     will have to - on purpose, so you see what you are overriding.

WHAT IS STILL DELIBERATELY VULNERABLE: look at build_prompt(). Retrieved text is
still pasted straight into the prompt with no marker saying where it came from.
That is unchanged from lab 2 and it is unchanged on purpose. This lab defends the
INGESTION path, not the prompt boundary - lab 12 is the prompt boundary. A lab
that fixed everything at once would teach which control did the work: none of them
distinguishably.
"""
import json
import os
import pathlib
import subprocess
import sys
import time

import numpy as np
import torch
from transformers import AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer

LAB = pathlib.Path("/labs/lab10")
INDEX = LAB / "index.npz"
RETRIEVAL_LOG = LAB / "retrieval-log.jsonl"
CORPUS = LAB / "corpus"
PROVENANCE = CORPUS / "PROVENANCE.json"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ANSWER_MODEL = "google/flan-t5-small"

UNTAGGED = "UNTAGGED"

# The index is saved as .npz, not pickle. Lab 1 showed why that matters.

_embed_cache = {}


def _embedder():
    if "e" not in _embed_cache:
        tok = AutoTokenizer.from_pretrained(EMBED_MODEL)
        mdl = AutoModel.from_pretrained(EMBED_MODEL)
        mdl.eval()
        _embed_cache["e"] = (tok, mdl)
    return _embed_cache["e"]


def embed(texts):
    tok, mdl = _embedder()
    out = []
    for t in texts:
        enc = tok(t, return_tensors="pt", truncation=True, max_length=256, padding=True)
        with torch.no_grad():
            h = mdl(**enc).last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).float()
        v = (h * mask).sum(1) / mask.sum(1)          # mean pooling
        v = torch.nn.functional.normalize(v, dim=-1)  # cosine == dot product
        out.append(v[0].numpy())
    return np.vstack(out).astype("float32")


def chunk(text):
    """Split a document into retrievable chunks. Identical to lab 2's."""
    parts = []
    for block in text.split("\n"):
        block = block.strip()
        if not block:
            continue
        if len(block) > 240:
            buf = ""
            for s in block.replace("? ", "?|").replace(". ", ".|").split("|"):
                if len(buf) + len(s) > 240 and buf:
                    parts.append(buf.strip()); buf = ""
                buf += s + " "
            if buf.strip():
                parts.append(buf.strip())
        else:
            parts.append(block)
    return [p for p in parts if len(p) > 15]


def read_any(path):
    """Read a .txt or a .pdf. For a PDF this reads the TEXT LAYER - which is
    not the same thing as what a human sees on the page."""
    p = pathlib.Path(path)
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    return p.read_text(encoding="utf-8")


def provenance():
    if not PROVENANCE.exists():
        return {}
    try:
        return json.loads(PROVENANCE.read_text(encoding="utf-8")).get("documents", {})
    except ValueError:
        return {}


def tag_for(name):
    """The provenance tag a chunk carries into the index."""
    entry = provenance().get(name)
    if not entry:
        return UNTAGGED
    return f"{entry.get('source', '?')}/{entry.get('trust', '?')}"


def load():
    d = np.load(INDEX, allow_pickle=False)
    tags = list(d["tags"]) if "tags" in d else [UNTAGGED] * len(d["texts"])
    return d["vectors"], list(d["texts"]), list(d["sources"]), tags


def save(vectors, texts, sources, tags):
    np.savez(INDEX, vectors=vectors,
             texts=np.array(texts, dtype=object).astype(str),
             sources=np.array(sources, dtype=object).astype(str),
             tags=np.array(tags, dtype=object).astype(str))


def cmd_build():
    files = sorted(CORPUS.glob("*.txt"))
    texts, sources, tags = [], [], []
    for f in files:
        t = tag_for(f.name)
        for c in chunk(f.read_text(encoding="utf-8")):
            texts.append(c); sources.append(f.name); tags.append(t)
    print(f"Embedding {len(files)} documents from corpus/ -> {len(texts)} chunks ...")
    save(embed(texts), texts, sources, tags)
    tagged = sum(1 for t in tags if t != UNTAGGED)
    print(f"Index built: {len(texts)} chunks from {len(files)} documents")
    print(f"  {tagged} of {len(tags)} chunks carry a provenance tag")


def cmd_ingest(path, force=False):
    name = os.path.basename(path)
    print(f"Ingesting {path}")

    proc = subprocess.run([sys.executable, str(LAB / "validate.py"), path],
                          capture_output=True, text=True)
    passed = proc.returncode == 0
    print(f"  validator: {'PASS' if passed else 'REFUSED'}")
    if not passed:
        for line in (proc.stdout or "").rstrip("\n").split("\n"):
            # only the rule names - the validator's own closing verdict would
            # read "does not enter the index", which is about to be untrue
            if line.strip().startswith("RULE"):
                print("    " + line.strip())
        if not force:
            print()
            print("  Not ingested. The validator refused it and nothing overrode that.")
            print("  To ingest it anyway:  python rag.py ingest " + name + " --force")
            return 1
        print()
        print("  --force given. Ingesting a document your own validator refused.")
        print("  Somebody does this in every organisation, usually to unblock a demo.")

    vectors, texts, sources, tags = load()
    raw = read_any(path).strip()
    chunks = chunk(raw)
    t = tag_for(name)
    print(f"  extracted {len(raw)} characters -> {len(chunks)} chunks")
    print(f"  provenance tag: {t}")
    v = embed(chunks)
    save(np.vstack([vectors, v]), texts + chunks, sources + [name] * len(chunks),
         tags + [t] * len(chunks))
    print(f"  index now holds {len(texts)+len(chunks)} chunks")
    if t == UNTAGGED:
        print()
        print("  Those chunks went in UNTAGGED. Remember that - it is what makes")
        print("  the purge possible later, and what would make it impossible if")
        print("  every document arrived this way.")
    return 0


def build_prompt(question, chunks):
    # UNCHANGED FROM LAB 2, on purpose. Retrieved text goes straight in,
    # unlabelled, mixed with the instruction. This lab defends ingestion.
    # The prompt boundary is lab 12's subject.
    context = "\n".join(chunks)
    return (f"Answer the question using only the context.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:")


def retrieve(question, k=3):
    vectors, texts, sources, tags = load()
    qv = embed([question])[0]
    scores = vectors @ qv
    top = np.argsort(-scores)[:k]
    return [(int(i), texts[i], sources[i], tags[i], float(scores[i])) for i in top]


def answer_from(question, hits):
    tok = AutoTokenizer.from_pretrained(ANSWER_MODEL)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(ANSWER_MODEL)
    mdl.eval()
    prompt = build_prompt(question, [h[1] for h in hits])
    ids = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        out = mdl.generate(**ids, max_new_tokens=32, do_sample=False)  # greedy: temperature 0
    return tok.decode(out[0], skip_special_tokens=True)


def log_retrieval(question, hits, answer):
    """OWASP LLM09:2026 prevention 6. Append-only, one JSON object per line."""
    rec = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "question": question,
        "answer": answer,
        "drove_the_answer": {"source": hits[0][2], "tag": hits[0][3],
                             "score": round(hits[0][4], 4)},
        "retrieved": [{"source": h[2], "tag": h[3], "score": round(h[4], 4)} for h in hits],
    }
    with open(RETRIEVAL_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def cmd_ask(question, k=3):
    hits = retrieve(question, k)
    print(f"Question: {question}\n")
    print("Retrieved (highest similarity first):")
    for rank, h in enumerate(hits, 1):
        print(f"  {rank}. {h[2]:<26} {h[3]:<24} score {h[4]:.3f}")
    print()
    answer = answer_from(question, hits)
    print(f"ANSWER: {answer}")
    log_retrieval(question, hits, answer)
    print(f"\n  logged to retrieval-log.jsonl")
    return answer


def cmd_log():
    if not RETRIEVAL_LOG.exists():
        print("No retrievals logged yet. Ask a question first.")
        return
    print("=" * 68)
    print(" RETRIEVAL LOG - which chunk drove each answer")
    print("=" * 68)
    for line in RETRIEVAL_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        d = r["drove_the_answer"]
        print(f"\n  {r['at']}  {r['question']}")
        print(f"    answer  {r['answer']}")
        print(f"    from    {d['source']}  [{d['tag']}]  {d['score']}")
    print()
    print("=" * 68)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(64)
    c = sys.argv[1]
    if c == "build":
        cmd_build()
    elif c == "ask":
        cmd_ask(" ".join(a for a in sys.argv[2:] if not a.startswith("--")))
    elif c == "ingest":
        sys.exit(cmd_ingest(sys.argv[2], force="--force" in sys.argv))
    elif c == "log":
        cmd_log()
    else:
        print(f"unknown command: {c}"); sys.exit(64)
