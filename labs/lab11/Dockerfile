# ===== OCR-LIGHT TIER PREAMBLE — lab 11 (and the tesseract RUN lab 4 inserts). =====
# See tier-templates/README.md.
#
# Lab 11 carries the llama tier's apt line even though it runs no model: that layer is
# 1.95 MB and already on every student's disk from labs 3-8, and the tesseract layer below
# only matches lab 4's if what precedes it matches lab 4's. No llama wheel, no torch.
FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 11 - Defending multimodal input"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 nano less curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# Byte-identical to lab 4's tesseract RUN. 30.9 MB compressed, shared with lab 4.
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng fonts-dejavu-core \
 && rm -f /usr/share/tesseract-ocr/*/tessdata/osd.traineddata \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# Lab 11's own small pip layer: numpy==2.3.5 and pillow==11.3.0 only. No wheel.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

# Any build-time Python (rendering sample images, training the numpy classifier) gets the
# same whole-tree purge in the same RUN.

# --- lab files: everything below here is the lab's own ---

# Lab 4's files, reused so the two labs line up on the same document and the same
# gate: make_invoices.py, stamp_gate.py, craft.py and payload.txt are byte-identical
# to lab 4's except one hint line in make_invoices.py (see assets.json).
COPY scripts/make_invoices.py  /labs/lab11/make_invoices.py
COPY scripts/stamp_gate.py     /labs/lab11/stamp_gate.py
COPY scripts/craft.py          /labs/lab11/craft.py
COPY scripts/bake_attacks.py   /labs/lab11/bake_attacks.py
COPY payload.txt               /labs/lab11/payload.txt

# The defence: OCR, check, compare, log, gate, route, tune, check.
COPY scripts/lab11lib.py       /labs/lab11/lab11lib.py
COPY scripts/ocr.py            /labs/lab11/ocr.py
COPY scripts/inspect.py        /labs/lab11/inspect.py
COPY scripts/compare.py        /labs/lab11/compare.py
COPY scripts/log.py            /labs/lab11/log.py
COPY scripts/gate.py           /labs/lab11/gate.py
COPY scripts/route.py          /labs/lab11/route.py
COPY scripts/tune.py           /labs/lab11/tune.py
COPY scripts/check.py          /labs/lab11/check.py
COPY scripts/runner.py         /labs/lab11/runner.py
COPY rules.json                /labs/lab11/rules.json
COPY LAB.md                    /labs/lab11/LAB.md
COPY assets.json               /labs/lab11/assets.json
COPY entrypoint.sh             /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

# ---------------------------------------------------------------------------
# Bake the lab's assets, all of them rendered or trained here, nothing downloaded:
#   make_invoices.py --bake   the clean invoice and the invoice perturbation (lab 4's)
#   stamp_gate.py --bake      800 synthetic stamps, 300 epochs of logistic regression,
#                             ~36 s; the clean stamp, its FGSM perturbation, the weights
#   bake_attacks.py           BOTH attack images, reconstructed from the perturbations.
#                             Lab 4 made the student do this; here the student is the
#                             defender and receives the document already doctored.
# Same RUN, so the whole-tree __pycache__ purge covers what these imports compiled.
# ---------------------------------------------------------------------------
RUN cd /labs/lab11 \
 && python make_invoices.py --bake \
 && python stamp_gate.py --bake \
 && python bake_attacks.py \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete \
 && find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab11
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "11"]
