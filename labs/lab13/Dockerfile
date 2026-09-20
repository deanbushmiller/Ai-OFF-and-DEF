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

ENV LAB13_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf

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
