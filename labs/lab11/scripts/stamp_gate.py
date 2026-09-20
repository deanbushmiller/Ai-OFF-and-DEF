"""Stage 1 of the pipeline: the stamp gate, and the attack against it.

Runs at BUILD time (--bake). Trains a small image classifier, renders the two
stamps, and crafts the perturbation that defeats it.

WHAT THE GATE IS FOR
Accounts payable has a real control against duplicate-payment fraud: a scan
stamped DUPLICATE must never reach the payment queue. Automating that check
means a classifier looks at the stamp box and decides.

WHY IT IS A LINEAR MODEL, AND WHY THAT IS THE POINT
This gate is logistic regression over the pixels - no hidden layers, no deep
learning. Adversarial examples are usually explained as a quirk of deep nets.
They are not. For a linear model the maths is visible in one line: FGSM moves
the score by

    eps * sum(|w|)

so an attacker needs only

    eps  >  |score of the clean image| / sum(|w|)

Every pixel adds to sum(|w|). The more pixels the model looks at, the cheaper
the attack - which is Goodfellow's linear explanation of adversarial examples
(2014), and it is why more capable models did not make this go away.

TRAINING SETTINGS, ALL MEASURED with --tune (the table is in LAB.md)
  400 samples per class, +/-8 px jitter, +/-8 deg rotation, sigma=20 noise
  -> 95.0% accuracy on held-out stamps, and 7/255 flips it.
The trade-off is real and worth showing students: training on tighter crops
gives a better gate that costs more to fool (97.5% and 20/255 at +/-6 px);
training on looser ones gives a cheaper attack against a gate too weak to
ship (92.5% at +/-10 px). We took the middle.
"""
import argparse
import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HERE = pathlib.Path(__file__).resolve().parent
INVOICES = HERE / "invoices"
WEIGHTS = HERE / "gate-weights.npz"

SIZE = 160          # the stamp box the pipeline crops out of the scan
FONT_SIZE = 15      # big enough to read, small enough that the whole word fits
CLASSES = ("DUPLICATE", "ORIGINAL")     # index 0 blocked, index 1 allowed
JITTER, ROTATE, NOISE = 8, 8.0, 20.0
SAMPLES, EPOCHS, LR = 400, 300, 0.3
SEED = 20260913


def render_stamp(word, dx=0, dy=0, angle=0.0, scale=1.0, noise=0.0, rng=None):
    """A rubber stamp: a rounded box with a word in it."""
    big = Image.new("L", (SIZE * 2, SIZE * 2), 255)
    d = ImageDraw.Draw(big)
    f = ImageFont.truetype(FONT, max(8, int(round(FONT_SIZE * scale))))
    # Place from the glyph box rather than by hand, so changing FONT_SIZE or
    # the words does not silently push the text outside the crop.
    left, top, right, bottom = d.textbbox((0, 0), word, font=f)
    tw, th = right - left, bottom - top
    x, y = SIZE - tw / 2 - left, SIZE - th / 2 - top
    d.rounded_rectangle((SIZE - tw / 2 - 13, SIZE - th / 2 - 9,
                         SIZE + tw / 2 + 13, SIZE + th / 2 + 9),
                        radius=7, outline=40, width=3)
    d.text((x, y), word, fill=40, font=f)
    big = big.rotate(angle, resample=Image.BILINEAR, fillcolor=255,
                     center=(SIZE, SIZE))
    a = np.asarray(big.crop((SIZE // 2 + dx, SIZE // 2 + dy,
                             SIZE // 2 + SIZE + dx, SIZE // 2 + SIZE + dy)),
                   dtype=np.float32)
    if noise and rng is not None:
        a = np.clip(a + rng.normal(0, noise, a.shape), 0, 255)
    return a


def to_input(grey):
    """Pixels as the model sees them: 0 is blank paper, 1 is solid ink."""
    return (255.0 - np.asarray(grey, dtype=np.float32).ravel()) / 255.0


def to_image(x):
    return Image.fromarray(
        np.clip(255.0 - x.reshape(SIZE, SIZE) * 255.0, 0, 255).astype(np.uint8))


def score(x, w, b):
    """Positive score means ORIGINAL, so the document is allowed through."""
    return float(np.asarray(x) @ w + b)


def probability(z):
    return float(1.0 / (1.0 + np.exp(-np.clip(z, -60, 60))))


def training_set(rng):
    X, y = [], []
    for _ in range(SAMPLES):
        for label, word in enumerate(CLASSES):
            X.append(to_input(render_stamp(
                word,
                dx=int(rng.integers(-JITTER, JITTER + 1)),
                dy=int(rng.integers(-JITTER, JITTER + 1)),
                angle=float(rng.uniform(-ROTATE, ROTATE)),
                scale=float(rng.uniform(0.9, 1.1)),
                noise=NOISE, rng=rng)))
            y.append(label)
    return np.array(X, np.float32), np.array(y)


def train(X, y):
    """Plain gradient descent on logistic loss. Convex, so no seeds to babysit."""
    w = np.zeros(X.shape[1], np.float32)
    b = np.float32(0.0)
    for _ in range(EPOCHS):
        p = 1.0 / (1.0 + np.exp(-np.clip(X @ w + b, -60, 60)))
        g = (p - y) / len(X)
        w = (w - LR * (X.T @ g)).astype(np.float32)
        b = np.float32(b - LR * g.sum())
    return w, b


def craft(clean, w, b):
    """FGSM, respecting the pixel box.

    sign(w) is the direction that raises the ORIGINAL score fastest. The clip
    matters: on blank paper you can only ADD ink, so roughly half the
    theoretical step is unavailable and the honest epsilon is found by search,
    not by the formula.
    """
    for eps255 in range(1, 65):
        adv = np.clip(clean + (eps255 / 255.0) * np.sign(w), 0.0, 1.0)
        if score(adv, w, b) > 0:
            return eps255, adv
    raise SystemExit("No perturbation under 64/255 flips this gate - retrain.")


def random_control(clean, w, b, eps255, tries=30, seed=5):
    """The control that separates an adversarial example from a fragile model:
    the same magnitude of change, in random directions."""
    rng = np.random.default_rng(seed)
    flips = 0
    for _ in range(tries):
        r = np.clip(clean + (eps255 / 255.0) * rng.choice([-1.0, 1.0], size=clean.shape),
                    0.0, 1.0)
        flips += score(r, w, b) > 0
    return int(flips), tries


def bake():
    INVOICES.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    X, y = training_set(rng)
    w, b = train(X, y)

    held = np.random.default_rng(SEED + 1)
    Xh, yh = [], []
    for _ in range(60):
        for label, word in enumerate(CLASSES):
            Xh.append(to_input(render_stamp(
                word, dx=int(held.integers(-JITTER, JITTER + 1)),
                dy=int(held.integers(-JITTER, JITTER + 1)),
                angle=float(held.uniform(-ROTATE, ROTATE)),
                scale=float(held.uniform(0.9, 1.1)), noise=NOISE, rng=held)))
            yh.append(label)
    Xh, yh = np.array(Xh, np.float32), np.array(yh)
    held_acc = float((((Xh @ w + b) > 0) == yh).mean())

    clean = to_input(render_stamp(CLASSES[0]))
    to_image(clean).save(INVOICES / "stamp.png")
    to_image(to_input(render_stamp(CLASSES[1]))).save(INVOICES / "stamp-original-example.png")

    eps255, adv = craft(clean, w, b)
    delta = (adv - clean).astype(np.float32)
    np.savez_compressed(INVOICES / "stamp-perturbation.npz", delta=delta, eps255=eps255)
    np.savez_compressed(WEIGHTS, w=w, b=np.float32(b), classes=np.array(CLASSES))

    flips, tries = random_control(clean, w, b, eps255)
    print(f"  gate trained: held-out accuracy {held_acc:.3f}, "
          f"clean stamp scored {CLASSES[0]} at p={1 - probability(score(clean, w, b)):.4f}")
    print(f"  perturbation: {eps255}/255 flips it to {CLASSES[1]} "
          f"(p={probability(score(adv, w, b)):.3f}); random control {flips}/{tries}")
    print(f"  baked stamp.png, stamp-perturbation.npz, gate-weights.npz")


def tune():
    """Sweep the jitter/noise trade-off. A gate that generalises better needs a
    bigger perturbation; one that is cheap to fool is too weak to ship."""
    global JITTER, NOISE
    print(f"{'jitter':>7} {'noise':>6} {'held-out':>9} {'min eps':>9} {'random control':>15}")
    for jitter in (6, 8, 10, 12):
        for noise in (12, 20):
            JITTER, NOISE = jitter, noise
            rng = np.random.default_rng(SEED)
            X, y = training_set(rng)
            w, b = train(X, y)
            held = np.random.default_rng(SEED + 1)
            Xh, yh = [], []
            for _ in range(60):
                for label, word in enumerate(CLASSES):
                    Xh.append(to_input(render_stamp(
                        word, dx=int(held.integers(-JITTER, JITTER + 1)),
                        dy=int(held.integers(-JITTER, JITTER + 1)),
                        angle=float(held.uniform(-ROTATE, ROTATE)),
                        scale=float(held.uniform(0.9, 1.1)), noise=NOISE, rng=held)))
                    yh.append(label)
            Xh, yh = np.array(Xh, np.float32), np.array(yh)
            acc = float((((Xh @ w + b) > 0) == yh).mean())
            clean = to_input(render_stamp(CLASSES[0]))
            eps255, _ = craft(clean, w, b)
            flips, tries = random_control(clean, w, b, eps255)
            print(f"{jitter:>7} {noise:>6} {acc:>9.3f} {eps255:>6}/255 {f'{flips}/{tries}':>15}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bake", action="store_true")
    ap.add_argument("--tune", action="store_true")
    args = ap.parse_args()
    tune() if args.tune else bake()
