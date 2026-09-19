# SecLLM Bootcamp - Lab 2: RAG and semantic ingestion attacks
# Consolidation contract: python:3.11-slim-bookworm, CPU-only torch, assets
# baked at build time, everything under /labs/lab2/, no ports bound.
# BASE PINNED BY DIGEST - do not replace with the bare tag.
#
# python:3.11-slim-bookworm is a MOVING tag. It moved between the labs 1-8
# publish and the lab 9 build, and measured on 2026-09-19 that single patch bump
# broke every layer above it: same Dockerfile, same pinned requirements, and
# 192,760,307 of 192,769,075 bytes stopped being shared - including the 128.8 MB
# pip layer and the 16.6 MB model layer. Only 8,768 bytes still matched.
#
# So the digest is the only thing that makes cross-lab layer sharing survive
# labs being built weeks apart, which is exactly how this course is built.
# This digest is the index (multi-arch), so buildx resolves the right platform.
# It was 3.11.16-slim-bookworm on 2026-09-19.
#
# Bump it deliberately, for security patching, and when you do, rebuild and
# republish EVERY lab that carries it in the same sitting. A lab left behind on
# the old pin shares nothing with the others.
FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 2 - RAG and semantic ingestion attacks"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# nano is required for expert mode (editing poison_source.txt in the container).
#
# The /var/log and /var/cache deletions are not tidiness. Those five files
# (dpkg.log, apt/history.log, alternatives.log, the fontconfig caches and
# ldconfig's aux-cache) carry timestamps INSIDE their content, so without them
# this layer's digest changes on every build. Added 2026-09-15.
#
# This line is deliberately NOT the one labs 3-8 share. Lab 2 needs neither
# libgomp1 nor curl, and adopting their line to share a 1.95 MB layer would add
# ~1.6 MB to lab 2's own pull to save lab 3 the same amount - a net course saving
# of about 366 KB, in exchange for coupling the torch tier to the model tier.
# Two tiers is correct; see "Do NOT unify with labs 1-2".
RUN apt-get update && apt-get install -y --no-install-recommends nano less \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# ---------------------------------------------------------------------------
# Shared dependency layer. ONE layer, per the consolidation contract - a trim in
# a later layer does not shrink the image, it only adds a whiteout.
#
# CPU-only torch. The default PyPI wheel is 554 MB on x86_64 and pulls in
# multi-GB nvidia-* packages we cannot use. Do not change.
#
# NOTE: do NOT delete torchgen. torch/utils/_python_dispatch.py imports it.
# ---------------------------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.9.1 \
 && pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && rm -rf /usr/local/lib/python3.11/site-packages/torch/include \
           /usr/local/lib/python3.11/site-packages/torch/test \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

# ---------------------------------------------------------------------------
# Assets baked at build time. Nothing downloads during class.
# ---------------------------------------------------------------------------
# The __pycache__ purge is NOT housekeeping - it is what makes this layer
# reproducible. Running fetch_assets.py imports huggingface_hub (and, in lab 2,
# transformers and torch), which writes .pyc files into the SAME layer as the
# baked model. A .pyc header embeds the source file's mtime, so the layer differs
# on every build and every student re-downloads it whole for a rebuild that
# changed nothing. rewrite-timestamp cannot help: it rewrites mtimes, not file
# CONTENTS. Added 2026-09-15; labs 3-8 have had it since 2026-09-13.
#
# The xet deletion, added 2026-09-19 at lab 9. huggingface_hub 1.31 writes a
# transfer log to /opt/lab-assets/hf/xet/logs/ whose FILENAME and CONTENTS both
# carry the build time. It was the only difference between lab 9's 16.5 MB asset
# layer and lab 1's - all 49 other files, the model included, were already
# byte-identical - and those 40 KB cost every student a 16.5 MB re-download.
# Download-time telemetry; nothing reads it at run time and these labs run with
# HF_HUB_OFFLINE=1.
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py \
 && rm -rf /opt/lab-assets/hf/xet \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1

# ---------------------------------------------------------------------------
# Lab files. Scripts sit in the working directory so student commands are short.
# ---------------------------------------------------------------------------
COPY corpus/                   /labs/lab2/corpus/
COPY scripts/rag.py            /labs/lab2/rag.py
COPY scripts/make_poison.py    /labs/lab2/make_poison.py
COPY scripts/peek_pdf.py       /labs/lab2/peek_pdf.py
COPY scripts/check.py          /labs/lab2/check.py
COPY scripts/poison_source.txt /labs/lab2/poison_source.txt
COPY scripts/runner.py         /labs/lab2/runner.py
COPY LAB.md                    /labs/lab2/LAB.md
COPY assets.json               /labs/lab2/assets.json
COPY entrypoint.sh             /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

WORKDIR /labs/lab2

ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "2"]
