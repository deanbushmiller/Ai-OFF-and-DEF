"""Build-time asset baking. Runs during `docker build` only - never at run time.

Qwen2.5-1.5B-Instruct, Q4_K_M quantised, ~1.12 GB.

SHARED with labs 5-7. Keep this exact repo ID, filename and destination so the
merged 8-lab image stores it once.

Why this model and this quantisation - all measured, not assumed:
  flan-t5-small (lab 2)  0/4 payload styles  - cannot follow injected commands
  Qwen2.5-0.5B           1/3                 - a coin flip is not a lab
  Qwen2.5-1.5B bf16      3/3 but 9.0 GB RAM  - will not run on a student laptop
  Qwen2.5-1.5B Q4_K_M    3/3 and 1.19 GB RAM - this one
"""
import pathlib

from huggingface_hub import hf_hub_download

REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
DEST = pathlib.Path("/opt/lab-assets/models")

DEST.mkdir(parents=True, exist_ok=True)
path = hf_hub_download(repo_id=REPO, filename=FILE, local_dir=str(DEST))
size = pathlib.Path(path).stat().st_size
print(f"  baked {FILE}  {size/1e9:.2f} GB")
print(f"  -> {path}")
