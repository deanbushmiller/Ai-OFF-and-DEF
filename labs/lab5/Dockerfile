# SecLLM Bootcamp - Lab 5: Exploiting AI agents and excessive agency
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab5/. This lab does NOT serve - no port, no /etc/hosts entry.

# BASE PINNED BY DIGEST - do not replace with the bare tag.
#
# python:3.11-slim-bookworm is a MOVING tag. Measured 2026-09-19: one patch bump of
# the base broke every layer above it - same Dockerfile, same pinned requirements,
# 192,760,307 of 192,769,075 bytes stopped being shared. The digest is the only thing
# that lets labs built weeks apart share layers. It is the multi-arch index, so buildx
# resolves the right platform. It was 3.11.16-slim-bookworm on 2026-09-19.
#
# Bump it deliberately, for security patching, and rebuild EVERY lab in one sitting
# when you do. See Activity-Labs/lab-build-prompts/REBUILD-PLAN.md.
# ---------------------------------------------------------------------------
# MODEL STAGE - fetch Qwen2.5-1.5B-Instruct Q4_K_M and split it into six shards.
#
# Why (2026-09-23): GHCR serves a layer through a signed CDN link that expires
# about 6.5-10 minutes after it is issued, and the CDN cuts a download that is
# still running at that moment (measured: stream reset at 472 MB, exactly at
# expiry). Docker then restarts the layer from zero. A single 1.09 GB layer
# therefore needs ~2.8 MB/s sustained or it never finishes. Six shards of at
# most ~197 MB need ~0.5 MB/s, and a failure repeats one shard, not the model.
#
# 197 MB is the floor: llama.cpp splits on tensor boundaries and output.weight
# alone is 191,439,360 bytes. llama-gguf-split is built from the llama.cpp
# source vendored in llama-cpp-python 0.3.35 - the exact version the image runs.
# Runs on the build host's platform: shards are data, identical for both arches.
# ---------------------------------------------------------------------------
FROM --platform=$BUILDPLATFORM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b AS model
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 HF_HOME=/opt/lab-assets/hf
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake \
 && rm -rf /var/lib/apt/lists/*
RUN pip download --no-deps --no-binary :all: llama-cpp-python==0.3.35 -d /src \
 && tar xzf /src/llama_cpp_python-0.3.35.tar.gz -C /src \
 && cmake -S /src/llama_cpp_python-0.3.35/vendor/llama.cpp -B /build \
      -DGGML_NATIVE=OFF -DLLAMA_CURL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_SERVER=OFF \
 && cmake --build /build --target llama-gguf-split -j4 \
 && cp /build/bin/llama-gguf-split /usr/local/bin/
RUN pip install huggingface-hub==1.31.0
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py \
 && mkdir /shards \
 && llama-gguf-split --split --split-max-size 192M \
      /opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf /shards/qwen2.5-1.5b-instruct-q4_k_m \
 && test "$(ls /shards | wc -l)" -eq 6 \
 && chmod 644 /shards/*.gguf && touch -d @0 /shards/*.gguf

FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b

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
      -c /wheels/constraints-llama.txt \
 && rm /tmp/requirements.txt \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

# Qwen2.5-1.5B-Instruct Q4_K_M, 1.09 GB, as SIX layers (see the model stage above).
# Byte-identical across labs 3-7 and 12-15, so a student downloads each shard once.
COPY --from=model /shards/qwen2.5-1.5b-instruct-q4_k_m-00001-of-00006.gguf /opt/lab-assets/models/
COPY --from=model /shards/qwen2.5-1.5b-instruct-q4_k_m-00002-of-00006.gguf /opt/lab-assets/models/
COPY --from=model /shards/qwen2.5-1.5b-instruct-q4_k_m-00003-of-00006.gguf /opt/lab-assets/models/
COPY --from=model /shards/qwen2.5-1.5b-instruct-q4_k_m-00004-of-00006.gguf /opt/lab-assets/models/
COPY --from=model /shards/qwen2.5-1.5b-instruct-q4_k_m-00005-of-00006.gguf /opt/lab-assets/models/
COPY --from=model /shards/qwen2.5-1.5b-instruct-q4_k_m-00006-of-00006.gguf /opt/lab-assets/models/

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1 \
    LAB5_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m-00001-of-00006.gguf

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
