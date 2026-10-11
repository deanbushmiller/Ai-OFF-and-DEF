"""Re-save google/flan-t5-small's weights as several files of at most 100 MB.

Runs in the build-only `model` stage (see the Dockerfile); never in a lab.

Why (2026-10-10): GHCR serves each image layer through a download link that expires
5-10 minutes after it is issued and cuts a download still running. flan-t5-small's
weights are one 308 MB file, so they formed a single 370 MB layer with MiniLM - too
big to finish inside one link on a slow connection. Several files mean several
layers, each small enough, and a cut download repeats one file, not the model.

The weights are not changed: they are loaded and saved again in Transformers' own
multi-file format (an index plus numbered .safetensors files), which from_pretrained
reads natively. The files are put into the Hugging Face cache where the single file
was, so the labs still load the model by name and no lab code changes.
"""
import os
import pathlib
import shutil

from transformers import AutoModelForSeq2SeqLM

REPO = "google/flan-t5-small"
SHARD_DIR = pathlib.Path("/opt/lab-assets/flan-t5-small-shards")  # where the final image puts them
STAGING = pathlib.Path("/shards")                                  # copied out one file per layer
hub = pathlib.Path(os.environ.get("HF_HOME", "/opt/lab-assets/hf")) / "hub"
(snapshot,) = (hub / "models--google--flan-t5-small" / "snapshots").iterdir()

model = AutoModelForSeq2SeqLM.from_pretrained(REPO)
tmp = pathlib.Path("/tmp/flan-resaved")
model.save_pretrained(tmp, max_shard_size="100MB", safe_serialization=True)
shards = sorted(tmp.glob("model-*-of-*.safetensors"))
index = tmp / "model.safetensors.index.json"
assert len(shards) >= 2 and index.exists(), f"expected a multi-file save, got {sorted(p.name for p in tmp.iterdir())}"

# Remove the single 308 MB file (snapshot symlink and the blob it points at).
single = snapshot / "model.safetensors"
blob = (single.parent / os.readlink(single)).resolve()
single.unlink()
blob.unlink()

# Index next to the config; each piece linked from the snapshot to its own directory.
shutil.copyfile(index, snapshot / index.name)
STAGING.mkdir()
for s in shards:
    shutil.move(str(s), STAGING / s.name)
    (snapshot / s.name).symlink_to(SHARD_DIR / s.name)
shutil.rmtree(tmp)

for p in [snapshot / index.name, *STAGING.iterdir()]:
    os.chmod(p, 0o644)
    os.utime(p, (0, 0))
print(f"  flan-t5-small re-saved as {len(shards)} files:",
      ", ".join(f"{p.name} {p.stat().st_size/1e6:.0f} MB" for p in sorted(STAGING.iterdir())))
