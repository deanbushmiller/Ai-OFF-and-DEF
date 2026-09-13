"""Build-time asset baking. Runs during `docker build` only - never at run time.

Qwen2.5-1.5B-Instruct, Q4_K_M quantised, ~1.12 GB.

SHARED with labs 3, 4 and 6-7. Keep this exact repo ID, filename and destination
so the merged 8-lab image stores it once.

Why this model and this quantisation - all measured, not assumed:
  flan-t5-small (lab 2)  0/4 payload styles  - cannot follow injected commands
  Qwen2.5-0.5B           1/3                 - a coin flip is not a lab
  Qwen2.5-1.5B bf16      3/3 but 9.0 GB RAM  - will not run on a student laptop
  Qwen2.5-1.5B Q4_K_M    3/3 and 1.19 GB RAM - this one

WHY THIS FILE IS FUSSY ABOUT TIMESTAMPS
---------------------------------------
A Docker layer is a tar, and a tar records mtimes. Two builds that download the
same 1.12 GB produce two DIFFERENT layers if the timestamps differ - so a
student who already has lab 3 downloads the same model again for lab 4.

Copying to a fixed path, deleting the hub cache metadata (which carries etags
and timestamps) and stamping the mtimes to the epoch removes the variance this
script controls.

MEASURED, so nobody repeats the experiment: it is NOT sufficient on its own.
Two no-cache builds of this exact Dockerfile still produce different diffIDs
for every layer that adds a file - including plain COPY layers of unchanged
files - because BuildKit stamps added files with the build time. Sharing the
model layer across labs needs a decision above this file: SOURCE_DATE_EPOCH
with rewrite-timestamp, a published base image holding the model, or simply
waiting for the 8-lab consolidation, which stores it once anyway.

Keep this recipe regardless: it costs nothing, it removes the variance that IS
in our control, and any of those three fixes needs it in place.
"""
import os
import pathlib
import shutil

from huggingface_hub import hf_hub_download

REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
DEST = pathlib.Path("/opt/lab-assets/models")
HF_CACHE = pathlib.Path(os.environ.get("HF_HOME", "/opt/lab-assets/hf"))

DEST.mkdir(parents=True, exist_ok=True)

# Download into the hub cache, then place a plain copy at the fixed path.
# A copy, not a symlink: a symlink into a cache we are about to delete is a
# broken symlink, and the failure would only show up at run time.
src = hf_hub_download(repo_id=REPO, filename=FILE)
final = DEST / FILE
shutil.copyfile(src, final)

# The hub cache is build-time scaffolding. It also holds the metadata that
# would make this layer non-reproducible.
shutil.rmtree(HF_CACHE, ignore_errors=True)

os.chmod(final, 0o644)
for path in (final, DEST, DEST.parent):
    os.utime(path, (0, 0))

size = final.stat().st_size
print(f"  baked {FILE}  {size/1e9:.2f} GB")
print(f"  -> {final}  (mtime pinned to the epoch for a reproducible layer)")
