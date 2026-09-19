# SecLLM Bootcamp - Lab 1: Data and model supply chain poisoning
# Consolidation contract: python:3.11-slim-bookworm, CPU-only torch, assets
# baked at build time, everything under /labs/lab1/, no ports bound.
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
LABEL org.opencontainers.image.description="Lab 1 - Data and model supply chain poisoning"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# ---------------------------------------------------------------------------
# Shared dependency layer. All 8 labs reuse this - keep it identical everywhere
# so the merged image stores it once.
#
# ONE layer, per the consolidation contract. This also matters for size: a trim
# in a LATER layer does not shrink the image, it only adds a whiteout. Install
# and trim must happen together.
#
# CPU-only torch from the PyTorch index. The default PyPI wheel is 554 MB on
# x86_64 and pulls in multi-GB nvidia-* packages we cannot use. Do not change.
#
# NOTE: do NOT delete torchgen. It looks like build tooling, but
# torch/utils/_python_dispatch.py imports it at run time.
# ---------------------------------------------------------------------------
# BYTE-IDENTICAL to labs 2 and 9's apt line, and lab 1 uses NEITHER package.
#
# That is deliberate, and it is the same trade labs 3-8 make carrying libgomp1
# and curl they never call. Measured on amd64, 2026-09-19: whether an apt layer
# sits between the base and the pip layer changes the PIP layer's tar by 200
# bytes - parent directory entries - and 200 bytes is enough to stop a
# 183,934,794-byte layer being shared. Without this line lab 1 and lab 9 do not
# share the torch install on amd64, and an Intel student pays 184 MB for lab 9
# instead of 28 KB.
#
# arm64 happened to share it anyway. amd64 did not. Do not "tidy" this away
# because the lab has no editor step - the layer is the point, not the editor.
RUN apt-get update && apt-get install -y --no-install-recommends nano less \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

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
# Lab files. make_model.py sits in the working directory so the student's
# commands are short: `cat make_model.py`, not a long path.
# ---------------------------------------------------------------------------
COPY scripts/make_model.py /labs/lab1/make_model.py
COPY scripts/unpack.py     /labs/lab1/unpack.py
COPY scripts/runner.py     /labs/lab1/runner.py
COPY assets.json           /labs/lab1/assets.json
COPY entrypoint.sh         /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

WORKDIR /labs/lab1

ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "1"]
