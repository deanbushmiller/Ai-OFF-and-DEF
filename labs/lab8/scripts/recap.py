"""Beat 1 - the seven attacks, one line each.

    python recap.py

Nothing to type. This is the frame for everything that follows, and it is the point of
the lab: eight hours of work, on one screen.
"""
import lab8lib as L


def main():
    c = L.course()
    L.head("WHAT YOU DID IN THIS COURSE")
    print("   Seven labs. Seven ways in. One screen.\n")
    for n in sorted(c, key=int):
        lab = c[n]
        print(f"   LAB {n}  {lab['title']}")
        print(f"          {lab['oneline']}")
        print(f"          OWASP {' + '.join(lab['owasp'])}")
        print()
    print("   Every one of those was you attacking a model, a pipeline, or the")
    print("   wire between them. None of it was theory and none of it was a")
    print("   simulation - the attacks worked, on your own machine, every time.")
    print()
    print("   For the rest of this lab you are the defender.")
    print()
    L.save_score("recap", {"labs": len(c)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
