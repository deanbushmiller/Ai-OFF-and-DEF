"""RECOVER - purge the poisoned vectors, by provenance tag.

    python purge.py --untagged            remove every chunk with no provenance
    python purge.py --source FILE.pdf     remove every chunk from one document

Deletes the vectors from the index and writes down what it removed. Then you
rebuild from the reviewed corpus and re-ask the canary.

WHY --untagged IS THE DEFAULT MOVE, and it is the payoff for rule 2:

You do not have to know which document was poisoned. You have to know which
documents you can account for. Everything else goes. That is a decision you can
make in an incident at 2am with no analysis, and it is only available because
every chunk carried a tag on the way in.

If the pipeline had stored filenames and nothing else - which is what lab 2 did -
the only safe recovery would be to rebuild the entire index from scratch and hope
the source of the poison was not in the corpus folder. On 26 chunks that is
instant. On a corpus of millions it is days, and the business does not get to
stop retrieving while you do it.

What a production version is: bounded-time deletion reconciled by audit (OWASP
LLM09:2026 prevention 5), a quarantine copy kept for investigation, a ticket, and
a revocation wherever those embeddings were replicated. Here it is a local delete
and a JSON file.
"""
import argparse
import json
import pathlib
import sys
import time

LAB = pathlib.Path("/labs/lab10")
PURGE_LOG = LAB / "purge-log.json"
WIDTH = 68

sys.path.insert(0, str(LAB))


def main():
    ap = argparse.ArgumentParser(description="Purge vectors from the index.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--untagged", action="store_true",
                   help="remove every chunk with no provenance tag")
    g.add_argument("--source", metavar="NAME",
                   help="remove every chunk from this document")
    args = ap.parse_args()

    import numpy as np
    import rag

    if not rag.INDEX.exists():
        print("No index. Run: python rag.py build")
        return 66

    vectors, texts, sources, tags = rag.load()
    before = len(texts)

    if args.untagged:
        keep = [i for i in range(before) if tags[i] != rag.UNTAGGED]
        criterion = "provenance tag is missing"
    else:
        keep = [i for i in range(before) if sources[i] != args.source]
        criterion = "source is " + args.source

    removed = [(sources[i], tags[i], texts[i][:60])
               for i in range(before) if i not in set(keep)]

    print("=" * WIDTH)
    print(" PURGE")
    print("=" * WIDTH)
    print()
    print("  criterion   " + criterion)
    print(f"  index held  {before} chunks")
    print(f"  removing    {len(removed)}")
    print()

    if not removed:
        print("  Nothing matched. The index is unchanged.")
        print("=" * WIDTH)
        return 0

    by_source = {}
    for s, t, _ in removed:
        by_source[(s, t)] = by_source.get((s, t), 0) + 1
    for (s, t), n in by_source.items():
        print(f"    {n:>3} chunk(s)  {s}  [{t}]")
    print()
    for _, _, preview in removed[:3]:
        print(f"      {preview!r}")
    if len(removed) > 3:
        print(f"      ... and {len(removed) - 3} more")

    rag.save(vectors[keep], [texts[i] for i in keep],
             [sources[i] for i in keep], [tags[i] for i in keep])

    record = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "criterion": criterion,
        "chunks_before": before,
        "chunks_removed": len(removed),
        "chunks_after": len(keep),
        "documents": [{"source": s, "tag": t, "chunks": n}
                      for (s, t), n in by_source.items()],
    }
    PURGE_LOG.write_text(json.dumps(record, indent=2) + "\n")

    print()
    print(f"  index now holds {len(keep)} chunks")
    print("  recorded in purge-log.json")
    print()
    print("  The index is consistent again - those vectors are gone, not")
    print("  merely hidden, and the reviewed chunks were never touched.")
    print()
    print("  Now VERIFY it. A purge you have not verified is a hope, not a")
    print("  recovery:  python canary.py check")
    print()
    print("  (A production recovery does more than delete: it re-embeds from")
    print("  the reviewed corpus, reconciles the deletion by audit, and")
    print("  revokes those embeddings wherever they were replicated. OWASP")
    print("  LLM09:2026 prevention 5. Here the corpus is 15 documents and the")
    print("  delete is exact, so there is nothing left to rebuild.)")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
