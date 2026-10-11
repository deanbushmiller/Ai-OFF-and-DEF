# SecLLM Bootcamp - Lab 3: Advanced prompt injection
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab3/, serves the mock site on 127.0.0.1:8003 only.
#
# REALIGNED 2026-09-14. Lab 3 was the last lab still on the pre-wheel recipe: it
# compiled llama-cpp-python in a build stage, carried its own requirements.txt,
# ran an old fetch_assets.py with no mtime pinning, and purged no __pycache__
# after running Python. The result, measured on the live registry, was that it
# shared NOTHING with labs 4-7 - not the apt layer, not the pip layer, not the
# 1.09 GB model layer - and a student paid for the model twice.

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
LABEL org.opencontainers.image.description="Lab 3 - Advanced prompt injection"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# BYTE-IDENTICAL to labs 4, 5, 6, 7 and 8's first RUN. Do not tidy it, do not
# reorder it, do not "improve" the package list: the layer is only shared across
# the tier if this line matches exactly, and it is worth more than it looks.
#
# Lab 3 is the FIRST lab in the tier a student pulls, so this is the pull that
# buys the layer for labs 4-8. Before the realignment lab 3's version of this
# line lacked the /var/log and /var/cache deletions, so it hashed differently
# and lab 4 paid for the apt layer a second time.
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
# Python dependencies, in ONE layer, from a wheel that was compiled once.
#
# llama-cpp-python ships no PyPI wheels. Lab 3 used to compile it here in a
# multi-stage build and COPY the whole site-packages across - 43.6 MB that could
# never be shared, because the compiler is not deterministic, plus a second
# unpinned numpy dragged in from the build stage. It is now compiled ONCE per
# architecture by Activity-Labs/wheels/build-wheels.sh and installed from that
# wheel, exactly as labs 4-7 do. No lab carries a C++ build stage any more.
#
# The wheels are NOT in this folder - they arrive as a named build context, so
# one copy serves every lab:
#     docker build --build-context wheels=<Activity-Labs>/wheels .
# publish.sh does this for you. Build without it and pip fails loudly rather
# than silently producing a different image.
#
# requirements.txt is a VERBATIM copy of Activity-Labs/requirements-llama.txt,
# shared with labs 4, 5, 6 and 7. Never edit this lab's copy - the layer is only
# shared if the file is byte-identical. pillow is in it and lab 3 never imports
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
    LAB3_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m-00001-of-00006.gguf

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

# ---------------------------------------------------------------------------
# Nothing to bake. Lab 3's site is static HTML copied in above; the only files
# written at run time are runs.json and lab3-results.txt, both inside the lab
# folder and both disposable.
# ---------------------------------------------------------------------------
RUN find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab3
EXPOSE 8003
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "3"]
