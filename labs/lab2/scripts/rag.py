"""
A toy RAG pipeline, built the way real ones are built.

    python rag.py build            embed corpus/ into a searchable index
    python rag.py ask "question"   retrieve, then answer from what was retrieved
    python rag.py ingest FILE      add one document (.txt or .pdf) to the index
    python rag.py evidence         show the first and latest answer to each question

THE VULNERABLE CONFIGURATION IS DELIBERATE.

Look at build_prompt() below. Retrieved text is pasted straight into the prompt
with no marker saying where it came from and no separation between instructions
and data. OWASP LLM01:2026 calls this context-window pooling: the model sees
system prompt, question and retrieved documents as one flat stream of tokens,
with no enforced trust boundary.

Whatever is in the index is treated as true. That is the whole vulnerability.
"""
import json
import os
import pathlib
import sys

import numpy as np
import torch
from transformers import AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer

LAB = pathlib.Path("/labs/lab2")
INDEX = LAB / "index.npz"
LOG = LAB / "answers.json"
CORPUS = LAB / "corpus"

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ANSWER_MODEL = "google/flan-t5-small"

# Note for the security-minded: the index is saved as .npz, not pickle.
# Lab 1 showed why that matters.


def _embedder():
    tok = AutoTokenizer.from_pretrained(EMBED_MODEL)
    mdl = AutoModel.from_pretrained(EMBED_MODEL)
    mdl.eval()
    return tok, mdl


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
    """Split a document into retrievable chunks.

    Real pipelines do this - you retrieve passages, not whole files. It also
    matters for the attack: a poisoned sentence buried in a long document gets
    diluted, but as its own chunk it competes directly with the true one.
    """
    parts = []
    for block in text.split("\n"):
        block = block.strip()
        if not block:
            continue
        # split long blocks on sentence ends, keep short ones whole
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


def load():
    d = np.load(INDEX, allow_pickle=False)
    return d["vectors"], list(d["texts"]), list(d["sources"])


def save(vectors, texts, sources):
    np.savez(INDEX, vectors=vectors, texts=np.array(texts, dtype=object).astype(str),
             sources=np.array(sources, dtype=object).astype(str))


def cmd_build():
    files = sorted(CORPUS.glob("*.txt"))
    texts, sources = [], []
    for f in files:
        for c in chunk(f.read_text(encoding="utf-8")):
            texts.append(c); sources.append(f.name)
    print(f"Embedding {len(files)} documents from corpus/ -> {len(texts)} chunks ...")
    save(embed(texts), texts, sources)
    print(f"Index built: {len(texts)} chunks from {len(files)} documents")


def cmd_ingest(path):
    vectors, texts, sources = load()
    raw = read_any(path).strip()
    chunks = chunk(raw)
    name = os.path.basename(path)
    print(f"Ingesting {path}")
    print(f"  extracted {len(raw)} characters -> {len(chunks)} chunks")
    v = embed(chunks)
    save(np.vstack([vectors, v]), texts + chunks, sources + [name] * len(chunks))
    print(f"  index now holds {len(texts)+len(chunks)} chunks")
    print("\nNo review. No approval. No provenance check. That is the point.")


def build_prompt(question, chunks):
    # THE VULNERABLE BIT. Retrieved text goes straight in, unlabelled and
    # untrusted, mixed with the instruction. No trust boundary anywhere.
    context = "\n".join(chunks)
    return (f"Answer the question using only the context.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:")


def cmd_ask(question, k=3, quiet=False):
    vectors, texts, sources = load()
    qv = embed([question])[0]
    scores = vectors @ qv
    top = np.argsort(-scores)[:k]

    if not quiet:
        print(f"Question: {question}\n")
        print("Retrieved (highest similarity first):")
        for rank, i in enumerate(top, 1):
            print(f"  {rank}. {sources[i]:<28} score {scores[i]:.3f}")
        print()

    tok = AutoTokenizer.from_pretrained(ANSWER_MODEL)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(ANSWER_MODEL)
    mdl.eval()
    prompt = build_prompt(question, [texts[i] for i in top])
    ids = tok(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        out = mdl.generate(**ids, max_new_tokens=32)
    answer = tok.decode(out[0], skip_special_tokens=True)

    print(f"ANSWER: {answer}")

    log = json.loads(LOG.read_text()) if LOG.exists() else {}
    log.setdefault(question, []).append(
        {"answer": answer, "top_source": sources[top[0]], "score": float(scores[top[0]])})
    LOG.write_text(json.dumps(log, indent=2))
    return answer


def cmd_evidence():
    if not LOG.exists():
        print("No answers recorded yet. Ask a question first.")
        return
    log = json.loads(LOG.read_text())
    print("=" * 70)
    print(" EVIDENCE - same question, same pipeline, before and after")
    print("=" * 70)
    for q, runs in log.items():
        first, last = runs[0], runs[-1]
        print(f"\n  {q}")
        if len(runs) > 1:
            print(f"     BEFORE      {first['answer']:<24} <- {first['top_source']} ({first['score']:.3f})")
            print(f"     AFTER       {last['answer']:<24} <- {last['top_source']} ({last['score']:.3f})")
            if first["answer"] != last["answer"]:
                print("     CHANGED. The poisoned document outranked the true one.")
            else:
                print("     unchanged.")
        else:
            # Asked only once - do not mislabel a post-ingestion answer as "before".
            print(f"     AFTER ONLY  {last['answer']:<24} <- {last['top_source']} ({last['score']:.3f})")
            print("     Asked only after ingestion. The true document is still in")
            print("     the index - it was simply outranked.")
    print("\n" + "=" * 70)
    print(" Nothing about the model changed. Nothing about the code changed.")
    print(" One document entered the index.")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(64)
    c = sys.argv[1]
    if c == "build":      cmd_build()
    elif c == "ask":      cmd_ask(" ".join(sys.argv[2:]))
    elif c == "ingest":   cmd_ingest(sys.argv[2])
    elif c == "evidence": cmd_evidence()
    else:
        print(f"unknown command: {c}"); sys.exit(64)
