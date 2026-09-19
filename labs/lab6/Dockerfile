# SecLLM Bootcamp - Lab 6: MCP and interface hijacking
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab6/. It serves on 127.0.0.1 ONLY and publishes no port.

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
FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 6 - MCP and interface hijacking"

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
# NO NEW PACKAGE, and none is needed.
#
# The MCP server and the proxy are stdlib only - http.server, socketserver,
# json, hmac - the same approach lab 3 used to serve HTML. An MCP server is
# JSON-RPC 2.0 over a transport; none of that needs a framework, and adding one
# would break the shared pip layer for the whole 3-7 tier to save nothing.
#
# Lab 6 therefore buys nothing at all: no model, no apt package, no pip package.
# Same as lab 5, and for the same reason - the attack is in the wiring, not in
# anything that has to be downloaded.
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
# shared with labs 3, 4, 5 and 7. Never edit this lab's copy - the layer is only
# shared if the file is byte-identical. pillow is in it and lab 6 never imports
# it; that is the price of the shared layer and it is the right trade.
# ---------------------------------------------------------------------------
ARG TARGETARCH
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=bind,from=wheels,target=/wheels \
    pip install --no-cache-dir \
      "$(ls /wheels/${TARGETARCH}/llama_cpp_python-*.whl)" \
      -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

# ---------------------------------------------------------------------------
# Model baked at build time. SHARED with labs 3, 4, 6 and 7 - keep this exact
# source ID and path so the merged image stores it once. Lab 6 buys no model.
# ---------------------------------------------------------------------------
# Two things in this RUN are what make the baked-asset layer identical across builds
# AND across base versions (measured 2026-09-19, see REBUILD-PLAN.md):
#   - rm -rf /opt/lab-assets/hf/xet: huggingface_hub 1.31 writes a transfer log whose
#     filename and contents carry the build time. 40 KB that forced a full re-download.
#   - the __pycache__ purge covers the WHOLE python3.11 tree, not just site-packages:
#     running fetch_assets.py byte-compiles stdlib modules, and a .pyc header embeds
#     the source mtime, which differs between base builds. Seven such files tied this
#     layer to the base. The base ships no .pyc, so this whiteouts nothing.
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py \
 && rm -rf /opt/lab-assets/hf/xet \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1 \
    LAB6_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf

COPY scripts/mcp_server.py /labs/lab6/mcp_server.py
COPY scripts/proxy.py      /labs/lab6/proxy.py
COPY scripts/mitm.py       /labs/lab6/mitm.py
COPY scripts/mcp_client.py /labs/lab6/mcp_client.py
COPY scripts/evidence.py   /labs/lab6/evidence.py
COPY scripts/check.py      /labs/lab6/check.py
COPY scripts/runner.py     /labs/lab6/runner.py
COPY payload.txt           /labs/lab6/payload.txt
COPY LAB.md                /labs/lab6/LAB.md
COPY assets.json           /labs/lab6/assets.json
COPY entrypoint.sh        /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

# ---------------------------------------------------------------------------
# Nothing to bake. Lab 6 has no dataset, no rendered asset and no trained
# model: the accounts live in mcp_server.py and the payload is one line of
# text. The only files written at run time are wire.log, ledger.json and
# runs.json, all inside the lab folder and all disposable.
# ---------------------------------------------------------------------------
RUN find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab6
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "6"]
