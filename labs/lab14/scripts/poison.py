"""Arm the compromised server. NO MODEL RUNS - this is instant and free.

    python poison.py --descriptor   AML.T0110.000  poison a tool DESCRIPTION
    python poison.py --result       AML.T0110.002  append to a tool RESULT
    python poison.py --rewrite      AML.T0110.002  return a well-formed LIE
    python poison.py --off          behave honestly again
    python poison.py                show what is armed

This is the attacker's move and it stands in for a real one. In the real world
nobody hands you a flag: the server is compromised upstream, or it ships a
poisoned tool from day one, or - MCPoison, CVE-2025-54136 - it is approved once
and swapped afterwards. Here the switch is a JSON file so the consequence is
visible in fifteen minutes.

The server reads this file on every request, so nothing has to restart.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab14lib as L

WHAT = {
    "descriptor": ("AML.T0110.000  Definition and Instructions",
                   "The server now advertises get_balance with an extra sentence in its\n"
                   "  description. The user will never see it. The model would see all of it."),
    "result":     ("AML.T0110.002  Runtime Response",
                   "The server now appends an instruction to the get_balance RESULT,\n"
                   "  mixed in with the real balance so the tool looks like it worked."),
    "rewrite":    ("AML.T0110.002  Runtime Response",
                   "The server now returns a DIFFERENT balance. Nothing is appended and\n"
                   "  nothing is malformed. It is simply false."),
    "none":       ("-", "The server behaves honestly."),
}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--descriptor", action="store_true")
    g.add_argument("--result", action="store_true")
    g.add_argument("--rewrite", action="store_true")
    g.add_argument("--off", action="store_true")
    a = ap.parse_args()

    mode = ("descriptor" if a.descriptor else "result" if a.result
            else "rewrite" if a.rewrite else "none" if a.off else None)

    if mode is None:
        mode = L.poison_mode()
        print(f"Armed: {mode}")
    else:
        L.set_poison(mode)
        print(f"Armed: {mode}")

    atlas, text = WHAT[mode]
    print(f"  {atlas}")
    print(f"  {text}")
    print()
    print("  ^ Nothing has been checked yet. Run ask.py to see what the host does.")


if __name__ == "__main__":
    main()
