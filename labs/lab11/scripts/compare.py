"""DETECT - what a person sees against what the model reads. The core of the lab.

    python compare.py invoices/invoice-clean.png invoices/invoice-attack.png

Two renderings of the same image go through the SAME OCR:

  what the model reads   the image as it is, through the pipeline's OCR
  what a person sees     the image with every mark fainter than the contrast
                         threshold in rules.json erased to paper-white, then
                         the same OCR

Every line in the first that is not in the second is a mismatch: text the
machine will act on that no reviewer would have seen. It is logged, whatever it
says. This check has no opinion about the words. That is its strength - it
catches a payload the rule check has never heard of - and it is why detect
leads in this lab.

Lab 4's contrast table anchors the default threshold of 15%: a mark at 1.2% is
invisible on a screen, a mark at 29% is plainly visible.
"""
import sys

from lab11lib import (LOG, lines_of, load_rules, log_event, ocr_text, resolve,
                      visible_render)

if len(sys.argv) < 2:
    print("usage: python compare.py <image> [<image> ...]")
    sys.exit(64)

rules = load_rules()
contrast = rules["visible_contrast_percent"]

for arg in sys.argv[1:]:
    path = resolve(arg)
    read = lines_of(ocr_text(path))
    visible_path, erased = visible_render(path, contrast)
    seen = lines_of(ocr_text(visible_path))
    extra = [l for l in read if l not in seen]
    missing = [l for l in seen if l not in read]

    print(f"COMPARE: {path.name}")
    print(f"  what a person sees    {len(seen):>2} lines   (marks under {contrast}% contrast erased: "
          f"{erased:,} pixels, then the same OCR)")
    print(f"  what the model reads  {len(read):>2} lines   (the pipeline's OCR, untouched)")
    if not extra and not missing:
        verdict = "MATCH"
        print("  MATCH - the model read nothing a person could not see.")
    elif extra:
        verdict = "MISMATCH"
        print(f"  MISMATCH - {len(extra)} line{'s' if len(extra) > 1 else ''} the model read "
              f"that a person would not see:")
        for l in extra:
            print(f"     >>> {l}")
        if missing:
            print(f"  (and {len(missing)} line(s) OCR read differently in the two views - "
                  f"kept in the log, not counted as hidden text)")
    else:
        verdict = "NOISE"
        print(f"  NOISE - the two views differ by {len(missing)} line(s) but the model read")
        print("  nothing extra. Recorded; not a hidden-text finding.")
    log_event({"kind": "compare", "image": path.name, "verdict": verdict,
               "contrast_percent": contrast, "erased_pixels": erased,
               "lines_seen": len(seen), "lines_read": len(read),
               "extra": extra, "missing": missing})
    print(f"  logged to {LOG.name}")
    print()
