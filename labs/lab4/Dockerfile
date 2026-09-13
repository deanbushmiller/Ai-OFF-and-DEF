# SecLLM Bootcamp - Lab 4: Multimodal and vision-based exploits
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab4/. This lab does NOT serve - no port, no /etc/hosts entry.

# ---------------------------------------------------------------------------
# Build stage: compile llama-cpp-python. It ships NO wheels on PyPI, so this is
# a source build needing cmake and a C++ toolchain. Multi-stage keeps ~400 MB of
# build tooling out of the image students pull.
#
# GGML_NATIVE=OFF is load-bearing: the default bakes in the BUILD machine's
# instruction set, which crashes on older student CPUs.
#
# These four lines are IDENTICAL to lab 3's on purpose. Do not "tidy" them.
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
LABEL org.opencontainers.image.description="Lab 4 - Multimodal and vision-based exploits"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# The /var/log and /var/cache deletions are not tidiness. Those five files
# (dpkg.log, apt/history.log, alternatives.log, the fontconfig caches and
# ldconfig's aux-cache) carry timestamps INSIDE their content, so the layer
# digest changes on every build and every lab re-downloads it. Measured: with
# them gone, two independent builds produce a byte-identical apt layer.
#
# libgomp1: the compiled libllama.so links against OpenMP, which ships with gcc
# in the build stage and is NOT in slim. Without it the import dies at run time
# with "libgomp.so.1: cannot open shared object file".
# Kept identical to lab 3's line so the two images stay easy to diff.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 nano less curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# ---------------------------------------------------------------------------
# Lab 4's own runtime: the OCR front-end.
#
# Kept in its own RUN, appended AFTER the line above rather than merged into it,
# so the two images differ in one obvious place.
#
# It does NOT save the student a download. Measured: BuildKit stamps added files
# with the build time, so every file-adding layer differs between builds and a
# student who already pulled lab 3 re-downloads the model anyway. See
# scripts/fetch_assets.py and INSTRUCTOR-TEST.md.
#
# osd.traineddata is orientation-and-script detection, used only by --psm 0.
# This lab pins --psm 6, so it is 10 MB of nothing. Deleted in the SAME RUN:
# a delete in a later layer makes the image BIGGER, not smaller.
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng fonts-dejavu-core \
 && rm -f /usr/share/tesseract-ocr/*/tessdata/osd.traineddata \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

# ---------------------------------------------------------------------------
# Model baked at build time. SHARED with labs 3 and 5-7 - keep this exact
# source ID and path so the merged image stores it once.
# ---------------------------------------------------------------------------
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1 \
    LAB4_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf

COPY scripts/pipeline.py           /labs/lab4/pipeline.py
COPY scripts/apply_perturbation.py /labs/lab4/apply_perturbation.py
COPY scripts/show_extraction.py    /labs/lab4/show_extraction.py
COPY scripts/craft.py              /labs/lab4/craft.py
COPY scripts/evidence.py           /labs/lab4/evidence.py
COPY scripts/check.py              /labs/lab4/check.py
COPY scripts/runner.py             /labs/lab4/runner.py
COPY scripts/make_invoices.py      /labs/lab4/make_invoices.py
COPY scripts/stamp_gate.py         /labs/lab4/stamp_gate.py
COPY scripts/gate.py               /labs/lab4/gate.py
COPY payload.txt                   /labs/lab4/payload.txt
COPY LAB.md                        /labs/lab4/LAB.md
COPY assets.json                   /labs/lab4/assets.json
COPY entrypoint.sh                 /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

# ---------------------------------------------------------------------------
# Bake the lab's own assets: the clean invoice and the perturbation file.
#
# Neither ATTACK image is shipped. Each script renders one, saves only the
# difference as a compressed .npz, and drops it. The student reconstructs both,
# which is the "analyse an image with adversarial perturbations" exercise.
#
# stamp_gate.py also TRAINS the stage 1 classifier here, at build time: 800
# synthetic stamps, 300 epochs of gradient descent, about a minute. Nothing is
# downloaded and nothing is trained on the student's machine.
# ---------------------------------------------------------------------------
RUN python /labs/lab4/make_invoices.py --bake \
 && python /labs/lab4/stamp_gate.py --bake \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab4
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "4"]
