# SecLLM Bootcamp - Lab 12: Defending against prompt injection
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab12/. It serves on 127.0.0.1 ONLY and publishes no port.
#
# ===== LLAMA TIER PREAMBLE - copied VERBATIM from tier-templates/llama.Dockerfile.
# Only the LABEL description below differs. Everything from the FROM line down to
# the "lab files" marker must stay byte-identical to labs 3-8 and 13-15, or this
# lab stops sharing the 1.09 GB Qwen layer and costs every student a fresh 1.2 GB.

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
LABEL org.opencontainers.image.description="Lab 12 - Defending against prompt injection"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# Byte-identical across the llama tier. libgomp1 is required (libllama.so links OpenMP);
# nano for expert mode; curl and ca-certificates are carried, not used, to keep the layer
# identical across labs that do use them.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 nano less curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# One pip layer: the prebuilt llama-cpp-python wheel (named build context, see publish.sh)
# plus Activity-Labs/requirements-llama.txt copied VERBATIM as this lab's requirements.txt.
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
    HF_HUB_OFFLINE=1

# --- lab files: everything below here is the lab's own ---

ENV LAB12_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m-00001-of-00006.gguf

# ---------------------------------------------------------------------------
# Lab 12 buys NOTHING. No model, no apt package, no pip package.
#
# The firewall is re, json, unicodedata and pathlib. The site is stdlib
# http.server. The model, the wheel and the whole dependency set are already
# on the student's disk from labs 3 to 8. This lab is its own source files
# and nothing else, which is why its download is measured in kilobytes.
# ---------------------------------------------------------------------------

COPY scripts/lab12lib.py  /labs/lab12/lab12lib.py
COPY scripts/firewall.py  /labs/lab12/firewall.py
COPY scripts/log.py       /labs/lab12/log.py
COPY scripts/tune.py      /labs/lab12/tune.py
COPY scripts/serve.py     /labs/lab12/serve.py
COPY scripts/evidence.py  /labs/lab12/evidence.py
COPY scripts/check.py     /labs/lab12/check.py
COPY scripts/runner.py    /labs/lab12/runner.py
COPY site/                /labs/lab12/site/
COPY LAB.md               /labs/lab12/LAB.md
COPY assets.json          /labs/lab12/assets.json

# rules.json ships TWICE on purpose. The student edits rules.json; the runner
# restores it from rules.default.json at the start of every run, so a second
# run of the lab starts from the vulnerable threshold with an empty log and
# still has a leak to teach from. Without this, re-running the lab silently
# skips its own lesson.
COPY rules.json           /labs/lab12/rules.json
COPY rules.json           /labs/lab12/rules.default.json

COPY entrypoint.sh        /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

RUN find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab12
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "12"]
