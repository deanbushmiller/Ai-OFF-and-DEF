# ===== TORCH TIER PREAMBLE — labs 1, 2, 9, 10. Copy verbatim; edit only the LABEL description. =====
# See tier-templates/README.md. Two requirement sets live in this tier and must not be mixed:
#   scan set       labs 1, 9    requirements.txt byte-identical to lab 1's
#   embedding set  labs 2, 10   requirements.txt byte-identical to lab 2's
FROM python:3.11-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b

LABEL org.opencontainers.image.source="https://github.com/deanbushmiller/Ai-OFF-and-DEF"
LABEL org.opencontainers.image.title="SecLLM Bootcamp Labs"
LABEL org.opencontainers.image.description="Lab 10 - Defending RAG ingestion"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/lab-assets/hf

# Byte-identical across the torch tier. Lab 1 uses neither package; it carries them so
# the pip layer below has the same parent-directory entries as the rest of the tier
# (measured: 200 bytes of difference on amd64 stopped a 184 MB layer being shared).
RUN apt-get update && apt-get install -y --no-install-recommends nano less \
 && rm -rf /var/lib/apt/lists/* /var/log/apt /var/log/dpkg.log /var/log/alternatives.log \
           /var/cache/fontconfig/* /var/cache/ldconfig/aux-cache

# One pip layer. Install and trim in the SAME RUN. Do not delete torchgen.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.9.1 \
 && pip install --no-cache-dir -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt \
 && rm -rf /usr/local/lib/python3.11/site-packages/torch/include \
           /usr/local/lib/python3.11/site-packages/torch/test \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

# Assets baked at build. fetch_assets.py byte-identical to the lab that first baked
# the asset (lab 1 for bert-tiny, lab 2 for MiniLM + flan-t5). The xet deletion and
# the whole-tree purge are what make this layer identical across builds AND bases.
COPY scripts/fetch_assets.py /tmp/fetch_assets.py
RUN python /tmp/fetch_assets.py && rm /tmp/fetch_assets.py \
 && rm -rf /opt/lab-assets/hf/xet \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete

ENV TRANSFORMERS_OFFLINE=1 \
    HF_HUB_OFFLINE=1

# --- lab files: everything below here is the lab's own ---

# Lab files. Scripts sit in the working directory so student commands are short.
#
# corpus/ and make_poison.py are lab 2's, unchanged. This lab does not re-teach
# the attack; it defends the pipeline that attack already broke. PROVENANCE.json
# is new and is the whole of rule 2: the 15 corpus documents have an entry, the
# poisoned PDF never will.
#
# The student builds poisoned_handbook.pdf themselves rather than it being baked.
# It is 2 KB, it costs one command, and it visibly connects this lab to lab 2 -
# "this is the file you made". Baking it would add a COPY layer and hide the link.
COPY corpus/                     /labs/lab10/corpus/
COPY scripts/rag.py              /labs/lab10/rag.py
COPY scripts/make_poison.py      /labs/lab10/make_poison.py
COPY scripts/poison_source.txt   /labs/lab10/poison_source.txt
COPY scripts/validate.py         /labs/lab10/validate.py
COPY scripts/canary.py           /labs/lab10/canary.py
COPY scripts/purge.py            /labs/lab10/purge.py
COPY scripts/tune.py             /labs/lab10/tune.py
COPY scripts/check.py            /labs/lab10/check.py
COPY scripts/runner.py           /labs/lab10/runner.py
COPY rules.json                  /labs/lab10/rules.json
COPY LAB.md                      /labs/lab10/LAB.md
COPY assets.json                 /labs/lab10/assets.json
COPY entrypoint.sh               /labs/entrypoint.sh
RUN chmod +x /labs/entrypoint.sh \
 && find /labs -name '__pycache__' -type d -prune -exec rm -rf {} +

WORKDIR /labs/lab10

ENTRYPOINT ["/labs/entrypoint.sh"]
CMD ["lab", "10"]
