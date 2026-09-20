# ===== LLAMA TIER PREAMBLE — labs 3, 4, 5, 6, 7, 8, 12, 13, 14, 15. Copy verbatim. =====
# See tier-templates/README.md.
#   lab 4 and lab 11 insert the tesseract RUN from ocr-light.Dockerfile right after the apt RUN.
#   lab 8 has NO pip layer and fetches ATLAS instead of Qwen; it keeps the apt line and the purge.
FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 14 - Defending MCP tool calls"

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
 && rm /tmp/requirements.txt \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

# Qwen2.5-1.5B-Instruct Q4_K_M baked at build, 1.09 GB, shared by the whole tier.
# fetch_assets.py byte-identical to lab 7's. The whole-tree purge is what makes this
# layer survive a base pin bump - without it, seven stdlib .pyc files tie it to the base.
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py \
 && rm -rf /opt/lab-assets/hf/xet \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1

# --- lab files: everything below here is the lab's own ---

WORKDIR /labs/lab14

# The trust list is COPIED TWICE on purpose: once as itself, and once as the
# pristine copy runner.py restores at the start of every run. Without the second
# copy a re-run would begin with the server already dropped and serve_pinned
# already true, and the lab would silently skip its own lesson. Lab 12 hit this
# with its rule file and lab 13 with its policy file.
COPY trust.json /labs/lab14/trust.json
COPY trust.json /labs/lab14/trust.default.json

COPY scripts/ /labs/lab14/
COPY LAB.md assets.json /labs/lab14/

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

# 8014, loopback only, started by ask.py as a child process - never published.
# EXPOSE is documentation; it opens nothing. The lab runs under --network none
# and a loopback bind inside the container cannot be reached from the host
# anyway, which lab 12 measured. Do not add -p.
EXPOSE 8014

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
