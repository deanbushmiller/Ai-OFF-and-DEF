"""The evidence: what the AI bought you, and what it cost.

    python evidence.py

The finding in this lab is not one artefact. It is three numbers next to each
other:

    how many variants the model produced         - what you spent
    how many the signature rule missed           - what you got
    how much slower you had to run to go clean   - what it cost

The first two are almost always disappointing, and that is the point. The third
is the one to put in a report, because it is the only one a defender can price.
"""
import json
import pathlib
import sys

WORK = pathlib.Path("/labs/lab7")
VARIANTS = WORK / "variants.json"
RESULTS = WORK / "results.json"
LOG = WORK / "collector.log"


def main():
    if not RESULTS.exists():
        print("Nothing recorded yet. Run the lab first.")
        return 1
    res = json.loads(RESULTS.read_text())
    store = json.loads(VARIANTS.read_text()) if VARIANTS.exists() else {}

    model = {k: v for k, v in store.items() if v["source"] == "model"}
    py = {k: v for k, v in store.items() if v["source"] == "python"}
    gen_seconds = sum(v["seconds"] for v in model.values())

    print("=" * 68)
    print(" WHAT YOU GENERATED")
    print("=" * 68)
    print()
    print(f"   {len(model)} variants from the model, {gen_seconds:.1f}s of CPU")
    print(f"   {len(py)} variants from two lines of Python, "
          f"{sum(v['seconds'] for v in py.values()):.3f}s")
    print()
    lost = {k: v for k, v in store.items() if v["missing"]}
    print(f"   every field survived in {len(store) - len(lost)} of {len(store)}"
          + (f"   (lost fields in: {', '.join(lost)})" if lost else ""))
    print()

    sig = res.get("signature")
    struct = res.get("structural")
    beh = res.get("behaviour")

    print("=" * 68)
    print(" WHAT THE DETECTORS DID")
    print("=" * 68)
    print()
    if sig:
        print(f"   D1 signature    caught {sig['caught']}/{sig['total']}"
              + (f"   missed: {', '.join(sig['missed'])}" if sig["missed"] else ""))
    if struct:
        print(f"   D2 structural   caught {struct['caught']}/{struct['total']}"
              + (f"   missed: {', '.join(struct['missed'])}"
                 if struct["missed"] else "   missed: nothing"))
    if beh:
        print(f"   D3 behavioural  {'FLAGGED' if beh['flagged'] else 'CLEAN'}"
              f"   at interval={beh['interval']:g}s jitter={beh['jitter']:.0%}"
              f"   ({beh['records_per_hour']:.2f} records/h)")
    print()

    if sig and struct:
        missed = sig["missed"]
        from_model = [m for m in missed
                      if store.get(m, {}).get("source") == "model"]
        from_py = [m for m in missed
                   if store.get(m, {}).get("source") == "python"]
        print("=" * 68)
        print(" THE FINDING")
        print("=" * 68)
        print()
        print(f"   The model spent {gen_seconds:.0f} seconds producing "
              f"{len(model)} renderings of one record.")
        if from_model:
            print(f"   The signature rule missed {len(from_model)} of them: "
                  f"{', '.join(from_model)}. That did not")
            print("   happen in any measured run - tell the instructor.")
        else:
            print("   The signature rule caught every single one of them.")
        if from_py:
            print()
            print(f"   The {len(from_py)} variants that DID get past it - "
                  f"{', '.join(from_py)} - came from")
            print("   base64.b64encode and .hex(). Two lines of standard library,")
            print("   no model, no CPU time, and they are the only evasion that")
            print("   worked.")
        print()
        print("   Then a twenty-line detector that ignores the format entirely")
        print(f"   caught {struct['caught']} of {struct['total']}.")
        print()
        print("   Varying the surface is cheap, and it beats rules that key on")
        print("   the surface. It does nothing to a rule that keys on the record.")
        print("   Polymorphic is not the same word as undetectable.")
        print()

    if beh and not beh["flagged"]:
        rate = beh["records_per_hour"]
        print("=" * 68)
        print(" THE BILL")
        print("=" * 68)
        print()
        print(f"   clean, at {rate:.2f} records/h instead of 60.00")
        print(f"   500 records: 0.35 days becomes {500 / rate / 24:.1f} days")
        print(f"   slowdown: {60.0 / rate:.0f}x")
        print()
        print("   You beat the content detectors for free. You beat the")
        print("   behavioural one by paying, and the defender set the price.")
        print("   That is the whole lab, and it is why detection engineering is")
        print("   measured in what it costs an attacker rather than in what it")
        print("   catches.")
        print()

    print("=" * 68)
    print(" MAPPING")
    print("=" * 68)
    print()
    print("   MITRE ATLAS leads here, because OWASP's Top 10 describes risks in")
    print("   an application you BUILD, and this lab is about an attacker using")
    print("   an LLM as a tool. That is a threat-landscape fact, not an")
    print("   application vulnerability. Say so rather than forcing a fit.")
    print()
    print("   AML.T0016.002  Obtain Capabilities: Generative AI")
    print("                  'obtain generative AI models ... to assist them in")
    print("                   various steps of their operation ... serve them")
    print("                   locally using frameworks such as Ollama or vLLM'")
    print("   AML.T0043.003  Craft Adversarial Data: Manual Modification")
    print("   AML.T0015      Evade AI Model   <- the core technique")
    print()
    print("   AML.CS0000     Palo Alto evaded a deep-learning C2-traffic")
    print("                  detector by varying HTTP header fields. The crafted")
    print("                  packets were called benign with >80% confidence.")
    print("   AML.CS0044     LAMEHUG, APT28, 2025: real malware that called a")
    print("                  Qwen 2.5 model to generate its commands. Same model")
    print("                  family you just used, three sizes up.")
    print()
    print("   OWASP LLM10:2026 Improper Output Handling, Scenario #2 - 'the LLM")
    print("         can encode the sensitive data and send it, without any output")
    print("         validation or filtering, to an attacker-controlled server'")
    print()
    if LOG.exists():
        n = len([l for l in LOG.read_text().splitlines() if l.strip()])
        print(f"   collector.log holds {n} entries. It is the defender's whole")
        print("   view of this incident.")
        print()
    print("=" * 68)
    print()
    print("Paste these three numbers into the class chat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
