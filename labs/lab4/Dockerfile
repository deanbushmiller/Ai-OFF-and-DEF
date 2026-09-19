# SecLLM Bootcamp - Lab 4: Multimodal and vision-based exploits
# Consolidation contract: python:3.11-slim-bookworm, assets baked at build time,
# everything under /labs/lab4/. This lab does NOT serve - no port, no /etc/hosts entry.

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
LABEL org.opencontainers.image.description="Lab 4 - Multimodal and vision-based exploits"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

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
# Lab 4's own runtime: the OCR front-end.
#
# Kept in its own RUN, appended AFTER the line above rather than merged into it,
# so the two images differ in one obvious place.
#
# It does NOT save the student a download. Measured: BuildKit stamps added files
# with the build time, so every file-adding layer differs between builds and a
# student who already pulled lab 3 re-downloads the model anyway. See
# scripts/fetch_assets.py and INSTRUCTOR-TEST.md.
#
# osd.traineddata is orientation-and-script detection, used only by --psm 0.
# This lab pins --psm 6, so it is 10 MB of nothing. Deleted in the SAME RUN:
# a delete in a later layer makes the image BIGGER, not smaller.
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng fonts-dejavu-core \
 && rm -f /usr/share/tesseract-ocr/*/tessdata/osd.traineddata \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# ---------------------------------------------------------------------------
# Python dependencies, in ONE layer, from a wheel that was compiled once.
#
# llama-cpp-python ships no PyPI wheels, so labs used to compile it from source in
# a build stage and COPY the whole site-packages across. That cost a C++ compile per
# lab per architecture, and produced a DIFFERENT layer every time - the compiler is
# not deterministic - so every lab re-downloaded 43.6 MB of the same thing. It also
# dragged the build stage's own numpy along, which was never pinned: pip resolved
# whatever was newest, then requirements.txt installed 2.3.5 over the top, and both
# shipped.
#
# Now: build-wheels.sh compiles it once per arch into wheels/, and every lab installs
# that wheel alongside requirements.txt in a single pip layer. numpy resolves once.
#
# The wheels are NOT in this folder - they are passed in as a named build context, so
# one copy serves every lab:
#     docker build --build-context wheels=<Activity-Labs>/wheels .
# publish.sh does this for you. Build without it and pip fails loudly on a missing file.
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
# Model baked at build time. SHARED with labs 3 and 5-7 - keep this exact
# source ID and path so the merged image stores it once.
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
    LAB4_MODEL=/opt/lab-assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf

COPY scripts/pipeline.py           /labs/lab4/pipeline.py
COPY scripts/apply_perturbation.py /labs/lab4/apply_perturbation.py
COPY scripts/show_extraction.py    /labs/lab4/show_extraction.py
COPY scripts/craft.py              /labs/lab4/craft.py
COPY scripts/evidence.py           /labs/lab4/evidence.py
COPY scripts/check.py              /labs/lab4/check.py
COPY scripts/runner.py             /labs/lab4/runner.py
COPY scripts/make_invoices.py      /labs/lab4/make_invoices.py
COPY scripts/stamp_gate.py         /labs/lab4/stamp_gate.py
COPY scripts/gate.py               /labs/lab4/gate.py
COPY payload.txt                   /labs/lab4/payload.txt
COPY LAB.md                        /labs/lab4/LAB.md
COPY assets.json                   /labs/lab4/assets.json
COPY entrypoint.sh                 /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh

# ---------------------------------------------------------------------------
# Bake the lab's own assets: the clean invoice and the perturbation file.
#
# Neither ATTACK image is shipped. Each script renders one, saves only the
# difference as a compressed .npz, and drops it. The student reconstructs both,
# which is the "analyse an image with adversarial perturbations" exercise.
#
# stamp_gate.py also TRAINS the stage 1 classifier here, at build time: 800
# synthetic stamps, 300 epochs of gradient descent, about a minute. Nothing is
# downloaded and nothing is trained on the student's machine.
# ---------------------------------------------------------------------------
RUN python /labs/lab4/make_invoices.py --bake \
 && python /labs/lab4/stamp_gate.py --bake \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab4
ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "4"]
