# SecLLM Bootcamp - Lab 5: Exploiting AI agents and excessive agency
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab5/. This lab does NOT serve - no port, no /etc/hosts entry.

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 5 - Exploiting AI agents and excessive agency"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# BYTE-IDENTICAL to labs 3 and 4's first RUN. Do not tidy it, do not reorder it,
# do not "improve" the package list: the layer is only shared across the tier if
# this line matches exactly, and it is worth more than it looks.
#
# The /var/log and /var/cache deletions are not tidiness. Those five files
# (dpkg.log, apt/history.log, alternatives.log, the fontconfig caches and
# ldconfig's aux-cache) carry timestamps INSIDE their content, so the layer
# digest changes on every build and every lab re-downloads it. Measured: with
# them gone, two independent builds produce a byte-identical apt layer.
#
# libgomp1: libllama.so links against OpenMP, which is NOT in slim. Still required
# now that the wheel is prebuilt - the wheel carries the .so, not its system
# dependency. Without it the IMPORT dies at run time with
# "libgomp.so.1: cannot open shared object file", long after a green build.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 nano less curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# ---------------------------------------------------------------------------
# NO TESSERACT LAYER, and that is a deliberate divergence from lab 4.
#
# Lab 5 does no OCR. Carrying lab 4's tesseract RUN anyway would keep the two
# images sharing one more 78.6 MB layer, at the cost of 78.6 MB of dead weight
# in a lab that never calls it. Raised with the instructor in
# lab-research/lab5/review.md; the decision was to drop it.
#
# Consequence, so nobody is surprised at the republish: lab 5's layer stack
# diverges from lab 4's immediately after the pip layer below. Everything up to
# and including pip is shared; nothing after it is.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Python dependencies, in ONE layer, from a wheel that was compiled once.
#
# llama-cpp-python ships no PyPI wheels. It is compiled ONCE per architecture by
# Activity-Labs/wheels/build-wheels.sh and installed from that wheel here, so no
# lab carries a C++ build stage. The wheels are NOT in this folder - they arrive
# as a named build context, so one copy serves every lab:
#     docker build --build-context wheels=<Activity-Labs>/wheels .
# publish.sh does this for you. Build without it and pip fails loudly rather
# than silently producing a different image.
#
# requirements.txt is a VERBATIM copy of Activity-Labs/requirements-llama.txt,
# shared with labs 3, 4, 6 and 7. Never edit this lab's copy - the layer is only
# shared if the file is byte-identical. pillow is in it and lab 5 never imports
# it; that is the price of the shared layer and it is the right trade.
# ---------------------------------------------------------------------------
ARG TARGETARCH
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=bind,from=wheels,target=/wheels \
    pip install --no-cache-dir \
      "$(ls /wheels/${TARGETARCH}/llama_cpp_python-*.whl)" \
      -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

# ---------------------------------------------------------------------------
# Model baked at build time. SHARED with labs 3, 4, 6 and 7 - keep this exact
# source ID and path so the merged image stores it once. Lab 5 buys no model.
# ---------------------------------------------------------------------------
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1 \
    LAB5_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf

COPY scripts/agent.py     /labs/lab5/agent.py
COPY scripts/tools.py     /labs/lab5/tools.py
COPY scripts/plant.py     /labs/lab5/plant.py
COPY scripts/evidence.py  /labs/lab5/evidence.py
COPY scripts/check.py     /labs/lab5/check.py
COPY scripts/runner.py    /labs/lab5/runner.py
COPY payload.txt          /labs/lab5/payload.txt
COPY LAB.md               /labs/lab5/LAB.md
COPY assets.json          /labs/lab5/assets.json
COPY entrypoint.sh        /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

# ---------------------------------------------------------------------------
# The notes boxes. Baked TWICE on purpose:
#   notes-pristine/  the read-only source of truth, never touched at run time
#   notes/           the working copy the agent reads and the student poisons
# plant.py --reset restores one from the other, so a student who makes a mess
# (or an expert who rewrites payload.txt) can always get back to a clean run
# without pulling the image again.
# ---------------------------------------------------------------------------
COPY notes-src/ /labs/lab5/notes-pristine/
RUN cp -r /labs/lab5/notes-pristine /labs/lab5/notes \
 && find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab5
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "5"]
