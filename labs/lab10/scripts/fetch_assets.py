"""Build-time asset baking. Runs during `docker build` only - never at run time.

Both models are SHARED. Keep these exact IDs in every lab that needs an
embedding model or a small generator, so the merged 8-lab image stores them once.
"""
import json
import os
import pathlib

from transformers import AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer

MODELS = [
    ("sentence-transformers/all-MiniLM-L6-v2", AutoModel),
    ("google/flan-t5-small", AutoModelForSeq2SeqLM),
]

resolved = {}
for repo, cls in MODELS:
    AutoTokenizer.from_pretrained(repo)
    cls.from_pretrained(repo)
    resolved[repo] = "cached"
    print(f"  baked {repo}")

out = pathlib.Path("/opt/lab-assets/lab2_assets.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(resolved, indent=2))

total = sum(f.stat().st_size for f in pathlib.Path("/opt/lab-assets/hf").rglob("*") if f.is_file())
print(f"\n  shared asset cache now: {total/1e6:.1f} MB")
