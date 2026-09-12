"""
Show what a .pt file actually is, and pull out the part that matters.

A .pt file is not a special binary model format. It is a ZIP archive, and one
entry inside it is a Python pickle. That pickle is what runs when you load the
model - so that is what a scanner needs to read.

Extracts the inner pickle to data.pkl in the current directory.
"""
import shutil
import sys
import zipfile

src = sys.argv[1]
archive = zipfile.ZipFile(src)
names = archive.namelist()

print(f"{src} is a ZIP archive. Inside it:\n")
for name in names[:5]:
    print(f"    {name}")
if len(names) > 5:
    print(f"    ... and {len(names) - 5} more entries (the raw weight tensors)")

inner = next(n for n in names if n.endswith("data.pkl"))
with archive.open(inner) as fsrc, open("data.pkl", "wb") as fdst:
    shutil.copyfileobj(fsrc, fdst)

print(f"\nThe entry that runs on load is {inner}")
print("Extracted it to  data.pkl  so a scanner can read it directly.")
