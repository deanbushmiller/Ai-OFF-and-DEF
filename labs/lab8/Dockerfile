# SecLLM Bootcamp - Lab 8: Offensive recap and transition to defense
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab8/. No model, no pip packages, no port.

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
LABEL org.opencontainers.image.description="Lab 8 - Offensive recap and transition to defense"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# BYTE-IDENTICAL to labs 3, 4, 5, 6 and 7's first RUN. Do not tidy it.
#
# Lab 8 uses NEITHER libgomp1 NOR curl - it runs no model and fetches nothing at
# run time. Removing them would be tidier and would cost every student a fresh
# 28.1 MB download, because the layer digest would change and this layer would
# stop being the one they already have from labs 3-7. Measured on the published
# lab7-arm64 manifest. Same trade the shared requirements file makes with pillow:
# carry two packages you do not use, to keep a layer you do.
#
# The /var/log and /var/cache deletions are not tidiness. Those five files carry
# timestamps INSIDE their content, so the layer digest would change on every
# build and every lab would re-download it.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 nano less curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# ---------------------------------------------------------------------------
# NO PIP LAYER AT ALL. This is the only lab in the course with none.
#
# Labs 3-7 share a 49.8 MB pip layer for llama-cpp-python, numpy, hf-hub and
# pillow. Lab 8 runs no model and parses no YAML, so it imports nothing outside
# the standard library: json, argparse, pathlib, re, urllib.
#
# That is also why fetch_assets.py downloads the ATLAS STIX bundle rather than
# ATLAS.yaml - the YAML is friendlier but parsing it would mean PyYAML, and
# adding a pip layer to save one import is the wrong trade. VERIFIED: distilling
# from STIX reproduces the numbers taken from the YAML exactly.
#
# Do NOT "unify" this with the model tier's requirements.txt for consistency.
# The build prompt says so explicitly and it is right: it would cost every
# student 49.8 MB for a lab that imports none of it.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# ATLAS baked at build time, into the SHARED cache path. Lab 8 is the natural
# home for it in the merged 8-lab image. ~100 KB after distilling.
# ---------------------------------------------------------------------------
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

COPY scripts/lab8lib.py   /labs/lab8/lab8lib.py
COPY scripts/recap.py     /labs/lab8/recap.py
COPY scripts/mapping.py   /labs/lab8/mapping.py
COPY scripts/coverage.py  /labs/lab8/coverage.py
COPY scripts/defend.py    /labs/lab8/defend.py
COPY scripts/export.py    /labs/lab8/export.py
COPY scripts/check.py     /labs/lab8/check.py
COPY scripts/runner.py    /labs/lab8/runner.py
COPY course.json          /labs/lab8/course.json
COPY LAB.md               /labs/lab8/LAB.md
COPY assets.json          /labs/lab8/assets.json
COPY entrypoint.sh        /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

# course.json is this lab's answer key and it is GENERATED, not typed - see
# lab-research/lab8/gen_course.py, which reads every student-facing file of labs
# 1-7 and refuses to emit a key containing a technique the student was never
# shown. It caught two real problems on its first run.
#
# Nothing else to bake. The only files written at run time are answers.json,
# score.json, worksheet.txt and atlas-layer.json, all inside the lab folder and
# all disposable.
RUN find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

ENV PYTHONPATH=/labs/lab8
WORKDIR /labs/lab8
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "8"]
