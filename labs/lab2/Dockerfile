# SecLLM Bootcamp - Lab 2: RAG and semantic ingestion attacks
# Consolidation contract: python:3.11-slim-bookworm, CPU-only torch, assets
# baked at build time, everything under /labs/lab2/, no ports bound.
FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 2 - RAG and semantic ingestion attacks"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# nano is required for expert mode (editing poison_source.txt in the container).
RUN apt-get update && apt-get install -y --no-install-recommends nano less \
 && rm -rf /var/lib/apt/lists/*

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
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py

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
