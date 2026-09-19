"""DETECT - the canary.

    python canary.py ask       ask the canary question and record the answer
    python canary.py check     ask it, and say whether the answer still holds

One document with a question whose correct answer you already know, asked after
every ingest. If the answer ever changes, something entered your index that
outranks the truth.

This is the deterministic heart of the lab. It is not clever. That is the point:
it fires the same way on every machine, every run, and it needs no model of what
an attack looks like - only a fact you are certain of.

What a production version is: a canary SUITE, tens or hundreds of questions
across every topic the corpus covers, run in CI after every ingest batch, with
the diff posted to the owning team. Here it is one question. The shape is real;
the scale is not - and the gap is the lesson, because a canary only ever proves
the questions you thought of.
"""
import json
import pathlib
import sys

LAB = pathlib.Path("/labs/lab10")
CANARY_LOG = LAB / "canary-log.jsonl"
WIDTH = 68

QUESTION = "Who invented the telephone?"
EXPECT = "Bell"
EXPECT_SOURCE = "bell.txt"

# The canary you did NOT configure. Same poisoned document, a different subject.
# Expert mode asks this one to show that the gap is real rather than theoretical:
# the monitored question was restored, and this one was never watched at all.
SECOND_QUESTION = "Who painted the Mona Lisa?"
SECOND_EXPECT = "Leonardo"
SECOND_EXPECT_SOURCE = "davinci.txt"

sys.path.insert(0, str(LAB))


def run(question=None, expect=None):
    import rag
    question = question or QUESTION
    expect = expect or EXPECT
    hits = rag.retrieve(question, k=3)
    answer = rag.answer_from(question, hits)
    rag.log_retrieval(question, hits, answer)
    rec = {"question": question, "answer": answer,
           "top_source": hits[0][2], "top_tag": hits[0][3],
           "top_score": round(hits[0][4], 4),
           "holds": expect.lower() in answer.lower(),
           "ranked": [(h[2], round(h[4], 4)) for h in hits]}
    with open(CANARY_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def history():
    """Only the CONFIGURED canary. The second question is a demonstration, not
    part of the monitored record, and counting it would overstate coverage -
    which is the exact error this lab is warning about."""
    if not CANARY_LOG.exists():
        return []
    return [json.loads(l) for l in CANARY_LOG.read_text(encoding="utf-8").splitlines()
            if l.strip() and json.loads(l).get("question") == QUESTION]


def show(rec, expect=None, source=None):
    print("  question       " + rec["question"])
    print("  expected       an answer naming " + (expect or EXPECT)
          + ", from " + (source or EXPECT_SOURCE))
    print("  answer         " + rec["answer"])
    print("  driven by      " + rec["top_source"] + "  [" + rec["top_tag"] + "]  "
          + str(rec["top_score"]))
    print()
    for rank, (src, score) in enumerate(rec["ranked"], 1):
        print(f"    {rank}. {src:<28} {score}")


def cmd_ask():
    print("=" * WIDTH)
    print(" CANARY")
    print("=" * WIDTH)
    print()
    rec = run()
    show(rec)
    print()
    if rec["holds"]:
        print("  CANARY HOLDS. The answer is the one you know to be true.")
    else:
        print("  *** CANARY CHANGED ***")
        print()
        print("  The pipeline did not break. No error was raised, no exception")
        print("  logged, no alert fired anywhere else. It retrieved a document")
        print("  and answered from it, exactly as designed.")
        print()
        print("  The document that drove it: " + rec["top_source"])
        print("  Its provenance tag:         " + rec["top_tag"])
        print()
        print("  Run  python rag.py log  to see every chunk that came back.")
    print("=" * WIDTH)
    return 0


def cmd_check():
    print("=" * WIDTH)
    print(" CANARY CHECK - is the answer restored?")
    print("=" * WIDTH)
    print()
    rec = run()
    show(rec)
    past = history()
    changed = [h for h in past if not h["holds"]]
    print()
    print(f"  asked {len(past)} time(s); {len(changed)} of those answered wrongly")
    print()
    if rec["holds"] and changed:
        print("  RESTORED. The canary answered wrongly earlier in this lab and")
        print("  answers correctly now. That pair is your evidence: something")
        print("  was detected, and something was done about it.")
        print("=" * WIDTH)
        return 0
    if rec["holds"]:
        print("  Holding - but it has never failed, so nothing has been proven")
        print("  about recovery yet.")
        print("=" * WIDTH)
        return 0
    print("  STILL WRONG. The poisoned chunks are still being retrieved.")
    print("  Purge them and rebuild the index before re-checking.")
    print("=" * WIDTH)
    return 1


def cmd_second():
    """The question nobody was watching."""
    print("=" * WIDTH)
    print(" THE CANARY YOU DID NOT CONFIGURE")
    print("=" * WIDTH)
    print()
    past = history()
    monitored_holds = bool(past) and past[-1]["holds"]
    if monitored_holds:
        print("  Your canary covers the telephone, and it is answering")
        print("  correctly. Here is a question from the same corpus, poisoned")
        print("  by the same document, that nobody was watching.")
    else:
        print("  Your canary covers the telephone, and it is currently wrong.")
        print("  Here is a question from the same corpus, poisoned by the same")
        print("  document, that nobody was watching at all.")
    print()
    rec = run(SECOND_QUESTION, SECOND_EXPECT)
    show(rec, SECOND_EXPECT, SECOND_EXPECT_SOURCE)
    print()
    if rec["holds"]:
        print("  This one is correct too - you purged by TAG, not by question,")
        print("  so the recovery covered every subject that document touched.")
        print()
        print("  That is the argument for provenance over monitoring. The purge")
        print("  fixed answers you were never watching, because it removed the")
        print("  document rather than correcting an answer.")
    elif monitored_holds:
        print("  *** STILL WRONG ***")
        print()
        print("  Your monitored canary says the incident is over. This question")
        print("  says it is not. Both are true: you restored what you measured.")
        print()
        print("  A canary only ever proves the questions you thought of.")
    else:
        print("  *** ALSO WRONG ***")
        print()
        print("  Both questions are wrong, and only one of them is being")
        print("  watched. That is the shape of the problem: one document, five")
        print("  false answers, one alert.")
        print()
        print("  Purge by tag and ask both again. The purge removes the")
        print("  DOCUMENT, so it will fix the four answers you never measured")
        print("  as well as the one you did.")
    print("=" * WIDTH)
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ask"
    if cmd == "ask":
        sys.exit(cmd_ask())
    if cmd == "check":
        sys.exit(cmd_check())
    if cmd == "second":
        sys.exit(cmd_second())
    print("usage: python canary.py [ask|check|second]")
    sys.exit(64)
