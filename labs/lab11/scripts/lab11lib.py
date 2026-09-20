"""Shared pieces for lab 11. Nothing in here decides anything - the scripts do.

Three ideas, and every script uses at least one:

  ocr_text()        the pipeline's OCR, exactly as lab 4 configured it: tesseract,
                    local adaptive binarisation (thresholding_method=1), --psm 4.
                    That setting is what reads a 1.2% mark on white paper.
  visible_render()  what a person sees. Erase every mark fainter than a contrast
                    threshold, leave everything else untouched, save the result.
                    The SAME OCR then runs on it. Two renderings, one engine.
  log_event()       one line of JSON per decision, appended to mismatch-log.jsonl.
                    A detector that does not write anything down is a feeling.
"""
import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image

WORK = pathlib.Path("/labs/lab11")
INVOICES = WORK / "invoices"
VIEWS = WORK / "views"
QUEUE = WORK / "review-queue"
RULES = WORK / "rules.json"
LOG = WORK / "mismatch-log.jsonl"

# --psm 4: a single column of text of variable sizes, which is what an invoice
# is. Lab 4 measured that psm 6 silently drops the 30pt letterhead.
PSM = "4"


def load_rules():
    return json.loads(RULES.read_text(encoding="utf-8"))


def save_rules(rules):
    RULES.write_text(json.dumps(rules, indent=2) + "\n", encoding="utf-8")


def resolve(arg, hint=None):
    """A path the student typed, relative to the lab folder. Missing file: say
    so in plain English and stop, never a stack trace."""
    path = pathlib.Path(arg)
    if not path.is_absolute():
        path = WORK / path
    if not path.exists():
        print(f"No such image: {arg}")
        if hint:
            print(hint)
        sys.exit(1)
    return path


def ocr_text(path, method=1):
    """The pipeline's OCR. method=1 is Leptonica's tile-local Otsu - the setting a
    shop turns on to read faded scans, and the setting that reads hidden text."""
    p = subprocess.run(
        ["tesseract", str(path), "stdout", "--psm", PSM,
         "-c", f"thresholding_method={method}"],
        capture_output=True, text=True)
    if p.returncode != 0:
        print("OCR failed: " + p.stderr.strip())
        sys.exit(1)
    return p.stdout.strip()


def norm(line):
    return " ".join(line.split())


def lines_of(text):
    return [norm(l) for l in text.splitlines() if l.strip()]


def visible_render(path, contrast_percent):
    """What a person sees.

    Every pixel fainter than contrast_percent of the brightness range is set to
    paper-white; every other pixel is left exactly as it was. Lab 4 measured the
    scale this sits on: a mark at 1.2% contrast is invisible on a screen, a mark
    at 29% is plainly visible. The threshold lives in rules.json so you can move
    it and watch what a stricter or looser eye costs.

    Returns the rendered file and how many non-white pixels were erased.
    """
    grey = np.array(Image.open(path).convert("L"))
    cutoff = 255.0 - (255.0 * float(contrast_percent) / 100.0)
    faint = (grey > cutoff) & (grey < 255)
    out = grey.copy()
    out[grey > cutoff] = 255
    VIEWS.mkdir(exist_ok=True)
    dest = VIEWS / (pathlib.Path(path).stem + "-visible.png")
    Image.fromarray(out.astype(np.uint8)).save(dest)
    return dest, int(faint.sum())


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def log_event(event):
    """Append one decision to the mismatch log. The sequence number is the order
    things happened in, which is the only clock a defender can trust later."""
    existing = read_log()
    event = {"seq": len(existing) + 1, **event}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    return event


def read_log():
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines()
            if l.strip()]
