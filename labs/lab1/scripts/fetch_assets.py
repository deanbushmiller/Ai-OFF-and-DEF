"""Build-time asset baking. Runs during `docker build` only - never at run time.

Pulls prajjwal1/bert-tiny into the shared cache at /opt/lab-assets/hf and records
the resolved paths so the lab can find them offline.

Keep the repo ID exactly as-is. The consolidation dedup rule means labs 2-8 that
need a tiny BERT must use this same ID so the merged image stores it once.
"""
import json
import os
import pathlib

from huggingface_hub import hf_hub_download

REPO_ID = "prajjwal1/bert-tiny"
FILES = ["config.json", "pytorch_model.bin", "vocab.txt"]

resolved = {}
total = 0
for name in FILES:
    path = hf_hub_download(repo_id=REPO_ID, filename=name)
    size = os.path.getsize(path)
    total += size
    resolved[name] = path
    print(f"  baked {name:<20} {size/1e6:>8.2f} MB  ->  {path}")

out = pathlib.Path("/opt/lab-assets/asset_paths.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(resolved, indent=2))
print(f"\n  total baked: {total/1e6:.2f} MB")
