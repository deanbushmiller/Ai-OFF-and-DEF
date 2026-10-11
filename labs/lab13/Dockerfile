# SecLLM Bootcamp - Lab 13: Defending AI agents
# Defends attack lab 5. Llama tier: the preamble below is
# Activity-Labs/tier-templates/llama.Dockerfile copied VERBATIM - only the LABEL
# description is changed. Do not tidy it, do not reorder it. The tier's layers are
# shared only if this text is identical, and that is worth 1.09 GB per student.
#
# This lab does NOT serve: no port, no /etc/hosts entry, no background process.
# It runs under --network none, which is part of what it teaches.

# ===== LLAMA TIER PREAMBLE — labs 3, 4, 5, 6, 7, 8, 12, 13, 14, 15. Copy verbatim. =====
# See tier-templates/README.md.
#   lab 4 and lab 11 insert the tesseract RUN from ocr-light.Dockerfile right after the apt RUN.
#   lab 8 has NO pip layer and fetches ATLAS instead of Qwen; it keeps the apt line and the purge.
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
LABEL org.opencontainers.image.description="Lab 13 - Defending AI agents"

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

ENV LAB13_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m-00001-of-00006.gguf

COPY scripts/lab13lib.py  /labs/lab13/lab13lib.py
COPY scripts/tools.py     /labs/lab13/tools.py
COPY scripts/agent.py     /labs/lab13/agent.py
COPY scripts/audit.py     /labs/lab13/audit.py
COPY scripts/revoke.py    /labs/lab13/revoke.py
COPY scripts/tighten.py   /labs/lab13/tighten.py
COPY scripts/evidence.py  /labs/lab13/evidence.py
COPY scripts/plant.py     /labs/lab13/plant.py
COPY scripts/check.py     /labs/lab13/check.py
COPY scripts/runner.py    /labs/lab13/runner.py
COPY payload.txt          /labs/lab13/payload.txt
COPY LAB.md               /labs/lab13/LAB.md
COPY assets.json          /labs/lab13/assets.json
COPY entrypoint.sh        /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

# The policy file, baked TWICE on purpose - the same trick lab 12 uses for its
# rule file, and for the same reason.
#
#   policy.json          the working copy the student revokes and tightens
#   policy.default.json  the shipped LOOSE state, never edited at run time
#
# runner.py restores one from the other at the start of every run. Without it, a
# second run of the lab starts with the credential already revoked and set_role
# already off the allow-list - so step 4 would block at gate 1 and the lab would
# silently skip its own lesson. Measured as a real failure mode in lab 12.
COPY policy.json /labs/lab13/policy.json
COPY policy.json /labs/lab13/policy.default.json

# The notes boxes. Baked TWICE on purpose, exactly as lab 5 does:
#   notes-pristine/  the read-only source of truth, never touched at run time
#   notes/           the working copy the agent reads and the student poisons
# plant.py --reset restores one from the other.
COPY notes-src/ /labs/lab13/notes-pristine/
RUN cp -r /labs/lab13/notes-pristine /labs/lab13/notes \
 && find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab13
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "13"]
