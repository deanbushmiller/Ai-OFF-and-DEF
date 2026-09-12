# SecLLM Bootcamp - Lab 3: Advanced prompt injection
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab3/, serves the mock site on 127.0.0.1:8003 only.

# ---------------------------------------------------------------------------
# Build stage: compile llama-cpp-python. It ships NO wheels on PyPI, so this is
# a source build needing cmake and a C++ toolchain. Multi-stage keeps ~400 MB of
# build tooling out of the image students pull.
#
# GGML_NATIVE=OFF is load-bearing: the default bakes in the BUILD machine's
# instruction set, which crashes on older student CPUs.
# ---------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git \
 && rm -rf /var/lib/apt/lists/*
ENV CMAKE_ARGS="-DGGML_NATIVE=OFF"
RUN pip install --no-cache-dir llama-cpp-python==0.3.35

# ---------------------------------------------------------------------------
FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 3 - Advanced prompt injection"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# libgomp1: the compiled libllama.so links against OpenMP, which ships with gcc
# in the build stage and is NOT in slim. Without it the import dies at run time
# with "libgomp.so.1: cannot open shared object file".
# nano/less: expert mode. curl: students fetch the page the way the assistant does.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 nano less curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

# ---------------------------------------------------------------------------
# Model baked at build time. SHARED with labs 5-7 - keep this exact source ID
# and path so the merged image stores it once.
# ---------------------------------------------------------------------------
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1 \
    LAB3_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf

# NOTE: the news.acme.com -> 127.0.0.1 mapping CANNOT be baked here. Docker
# regenerates /etc/hosts when the container starts, discarding anything written
# at build time. The entrypoint adds it at run time instead.

COPY site/                       /labs/lab3/site/
COPY scripts/serve.py            /labs/lab3/serve.py
COPY scripts/assistant.py        /labs/lab3/assistant.py
COPY scripts/show_injection.py   /labs/lab3/show_injection.py
COPY scripts/evidence.py         /labs/lab3/evidence.py
COPY scripts/check.py            /labs/lab3/check.py
COPY scripts/runner.py           /labs/lab3/runner.py
COPY LAB.md                      /labs/lab3/LAB.md
COPY assets.json                 /labs/lab3/assets.json
COPY entrypoint.sh               /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

WORKDIR /labs/lab3
EXPOSE 8003
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "3"]
