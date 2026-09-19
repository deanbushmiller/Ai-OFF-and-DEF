# SecLLM Bootcamp - Lab 9: Defending the model supply chain
# Consolidation contract: python:3.11-slim-bookworm, CPU-only torch, assets
# baked at build time, everything under /labs/lab9/, no ports bound.
#
# TIER: torch, with labs 1 and 2. No llama wheel - nothing here runs a
# generator. This lab buys NO new bytes: every dependency and the model itself
# were already paid for by lab 1.
# BASE PINNED BY DIGEST - do not replace with the bare tag.
#
# python:3.11-slim-bookworm is a MOVING tag. It moved between the labs 1-8
# publish and the lab 9 build, and measured on 2026-09-19 that single patch bump
# broke every layer above it: same Dockerfile, same pinned requirements, and
# 192,760,307 of 192,769,075 bytes stopped being shared - including the 128.8 MB
# pip layer and the 16.6 MB model layer. Only 8,768 bytes still matched.
#
# So the digest is the only thing that makes cross-lab layer sharing survive
# labs being built weeks apart, which is exactly how this course is built.
# This digest is the index (multi-arch), so buildx resolves the right platform.
# It was 3.11.16-slim-bookworm on 2026-09-19.
#
# Bump it deliberately, for security patching, and when you do, rebuild and
# republish EVERY lab that carries it in the same sitting. A lab left behind on
# the old pin shares nothing with the others.
FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 9 - Defending the model supply chain"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# BYTE-IDENTICAL to lab 2's apt line, deliberately. nano is required for expert
# mode (editing rules.json in the container). Lab 1 has no apt layer at all, so
# there was nothing to inherit from the lab this one defends; lab 2 is the only
# other torch-tier lab and its line is the one to match.
#
# Do NOT adopt labs 3-8's line (libgomp1 nano less curl ca-certificates). That
# belongs to the llama tier. Nothing in this lab links against OpenMP or fetches
# anything at run time, and coupling the two tiers to share one layer is the
# trade lab 2 already considered and declined.
#
# The /var/log and /var/cache deletions are not tidiness. Those files carry
# timestamps INSIDE their content, so without them this layer's digest changes
# on every build and every student re-downloads it.
RUN apt-get update && apt-get install -y --no-install-recommends nano less \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# ---------------------------------------------------------------------------
# Shared dependency layer. requirements.txt is BYTE-IDENTICAL to lab 1's and
# this RUN is character-for-character lab 1's, so the two share this layer and
# a student who has lab 1 downloads none of it again. If you edit either one,
# edit lab 1's too and rebuild the tier together - otherwise this lab silently
# costs every student another ~185 MB.
#
# fickling is installed and never invoked by lab 9. That is on purpose: it is
# in lab 1's requirements, and dropping it here would change the file, change
# the layer, and cost more than the ~12 MB it saves. Same trade labs 3-8 make
# carrying libgomp1.
#
# CPU-only torch. The default PyPI wheel is 554 MB on x86_64 and pulls in
# multi-GB nvidia-* packages we cannot use. Do not change.
#
# NOTE: do NOT delete torchgen. torch/utils/_python_dispatch.py imports it.
# ---------------------------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.9.1 \
 && pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && rm -rf /usr/local/lib/python3.11/site-packages/torch/include \
           /usr/local/lib/python3.11/site-packages/torch/test \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

# ---------------------------------------------------------------------------
# Assets baked at build time. Nothing downloads during class.
#
# fetch_assets.py is BYTE-IDENTICAL to lab 1's and bakes the same
# prajjwal1/bert-tiny into the same shared cache path, so the merged image
# stores that model once.
#
# The xet deletion is the same lesson as the __pycache__ purge, found
# 2026-09-19 while building this lab. huggingface_hub 1.31 writes a transfer
# log to /opt/lab-assets/hf/xet/logs/, and BOTH its filename and its contents
# carry the build timestamp. It is 40 KB. It was the ONLY difference between
# this lab's 16.5 MB asset layer and lab 1's - all 49 other files, the model
# included, were byte-identical - and those 40 KB cost every student a 16.5 MB
# re-download. The directory is download-time telemetry plus an empty staging
# folder; nothing reads it at run time, and this lab runs with HF_HUB_OFFLINE=1.
#
# LABS 1 AND 2 STILL SHIP IT. Until they get this same line, lab 9 cannot share
# their asset layer no matter what else matches. Add it at the tier rebuild.
#
# The __pycache__ purge is NOT housekeeping - it is what makes this layer
# reproducible. Running fetch_assets.py imports huggingface_hub, which writes
# .pyc files into the SAME layer as the baked model, and a .pyc header embeds
# the source file's mtime. rewrite-timestamp cannot help: it rewrites mtimes,
# not file CONTENTS.
# ---------------------------------------------------------------------------
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py \
 && rm -rf /opt/lab-assets/hf/xet \
 && find /usr/local/lib/python3.11/site-packages -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11/site-packages -name '*.pyc' -delete

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1

# ---------------------------------------------------------------------------
# Lab files, all in the working directory so the student's commands are short:
# `python gate.py bert_tiny_clean.pt`, not a long path.
#
# _sandbox_child.py is the only file a student is not expected to invoke
# directly; the underscore says so. It is readable on purpose - the whole
# control is 120 lines and reading it is half the lesson.
#
# rules.json ships with on_scanner_error already set to "block". The lab
# teaches the counterfactual rather than shipping the bug.
# ---------------------------------------------------------------------------
COPY scripts/make_model.py      /labs/lab9/make_model.py
COPY scripts/gate.py            /labs/lab9/gate.py
COPY scripts/sandboxed_load.py  /labs/lab9/sandboxed_load.py
COPY scripts/_sandbox_child.py  /labs/lab9/_sandbox_child.py
COPY scripts/quarantine.py      /labs/lab9/quarantine.py
COPY scripts/tune.py            /labs/lab9/tune.py
COPY scripts/check.py           /labs/lab9/check.py
COPY scripts/runner.py          /labs/lab9/runner.py
COPY rules.json                 /labs/lab9/rules.json
COPY LAB.md                     /labs/lab9/LAB.md
COPY assets.json                /labs/lab9/assets.json
COPY entrypoint.sh              /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh \
 && find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab9

ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "9"]
