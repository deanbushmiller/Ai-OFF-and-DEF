# SecLLM Bootcamp - Lab 1: Data and model supply chain poisoning
# Consolidation contract: python:3.11-slim-bookworm, CPU-only torch, assets
# baked at build time, everything under /labs/lab1/, no ports bound.
FROM python:3.11-slim-bookworm

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
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py

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
