"""Build-time asset baking. Runs during `docker build` only - never at run time.

MITRE ATLAS, distilled. ~1.2 MB in, ~33 KB out, and NO pip dependency.

PINNED: ATLAS v2026.08, BY URL AND BY SHA-256. Instructor decision 2026-09-22.
---------------------------------------------------------------------------
Until 2026-09-22 this fetched atlas-navigator-data/main/dist/stix-atlas.json - an
UNPINNED branch. MITRE deprecated that repo in June 2026 and its `main` is frozen at
ATLAS 5.6.0, so the lab was quietly teaching a release that had been superseded:
AML.T0058 retired, AML.TA0001 renamed, seven mitigations renamed, four added, and the
lab's own headline ("9 of 20 techniques have no mitigation") no longer true.

It now fetches the v2026.08 RELEASE ASSET from mitre-atlas/atlas-data. A release asset
URL does not move, but "does not move" is a promise and the sha256 below is a check: the
build FAILS LOUDLY if the bytes are not exactly the ones this lab was tested against.
Changing ATLAS release is a deliberate act - bump SRC, SHA256 and ATLAS_VERSION together,
rebuild, and re-run the INSTRUCTOR-TEST checks, because the runner asserts the headline
numbers and a new release will (correctly) trip them.

WHY THE STIX FILE AND NOT ATLAS.yaml
------------------------------------
`ATLAS.yaml` is the friendlier format, but parsing it needs PyYAML, and lab 8 is the one
lab in this course that installs no Python packages at all. The STIX bundle carries the
same content and `json` is in the standard library. The v2026.08 bundle is the SAME STIX
shape as 5.6.0 and this parser reads it unchanged: 197 techniques, 39 mitigations, 16
tactics (measured 2026-09-22). The bundle carries no version field of its own, which is
why ATLAS_VERSION is written down here rather than read.

WHAT GETS KEPT
--------------
Only what the lab reads: technique id, name, parent, tactics, CREATION DATE; tactic id and
name; mitigation id, name, and which techniques it mitigates. Descriptions are dropped -
they are most of the 1.2 MB and the lab never prints them.

The creation date is kept so beat 7 can print WHEN each unmitigated technique entered
ATLAS next to the claim, rather than asking the student to take it on trust.

The output lands in /opt/lab-assets/atlas/, which is the SHARED cache path. Lab 8 is the
natural home for ATLAS data in the merged 8-lab image. Note that labs 1-7 hard-code their
technique IDs in their own text and read nothing at run time, so nothing points at this
file yet - retrofitting them would mean republishing seven images for zero student-visible
benefit. See assets.json.

TIMESTAMPS
----------
Same discipline as the model labs: a Docker layer is a tar and a tar records mtimes, so
the mtime is pinned to the epoch and the download is deleted in the same RUN. Small here -
the file is ~33 KB - but the rule is the rule, and it costs nothing.
"""
import hashlib
import json
import os
import pathlib
import sys
import urllib.request

ATLAS_VERSION = "v2026.08"
SRC = ("https://github.com/mitre-atlas/atlas-data/releases/download/"
       "v2026.08/stix-atlas.json")
# sha256 of the exact 1,176,189 bytes this lab was built and tested against, 2026-09-22.
SHA256 = "6550ac8a7322e2d43d7c6c10234f0f381e74734ac6c734255fb1fc467bf16d7c"
DEST = pathlib.Path("/opt/lab-assets/atlas")
OUT = DEST / "atlas.json"

DEST.mkdir(parents=True, exist_ok=True)


def die(msg):
    print("", file=sys.stderr)
    print("=" * 68, file=sys.stderr)
    print(" ATLAS FETCH FAILED - refusing to bake data this lab was not tested on",
          file=sys.stderr)
    print("=" * 68, file=sys.stderr)
    print("   " + msg, file=sys.stderr)
    print(f"   source: {SRC}", file=sys.stderr)
    sys.exit(1)


try:
    with urllib.request.urlopen(SRC, timeout=120) as r:
        raw = r.read()
except Exception as e:  # noqa: BLE001 - any failure here must stop the build
    die(f"download failed: {e!r}")

got = hashlib.sha256(raw).hexdigest()
if not raw or got != SHA256:
    die(f"sha256 mismatch.\n   expected {SHA256}\n   got      {got}  "
        f"({len(raw):,} bytes)\n   If MITRE really republished {ATLAS_VERSION}, "
        "re-test the lab before\n   changing SHA256 - the headline numbers may move.")
print(f"  sha256 OK  {got}  ({len(raw):,} bytes, ATLAS {ATLAS_VERSION})")

bundle = json.loads(raw)
objs = bundle.get("objects") or []
if not objs:
    die("the bundle parsed but has no STIX objects in it")


def atlas_id(o):
    for ref in o.get("external_references", []):
        eid = str(ref.get("external_id", ""))
        if eid.startswith("AML."):
            return eid
    return None


by_ref = {o["id"]: o for o in objs}
techniques = {atlas_id(o): o for o in objs
              if o.get("type") == "attack-pattern" and atlas_id(o)}
mitigations = {atlas_id(o): o for o in objs
               if o.get("type") == "course-of-action" and atlas_id(o)}
tactics = {atlas_id(o): o for o in objs
           if o.get("type") == "x-mitre-tactic" and atlas_id(o)}
shortname = {o.get("x_mitre_shortname"): atlas_id(o)
             for o in objs if o.get("type") == "x-mitre-tactic"}

parent, mitigates = {}, {}
for rel in objs:
    if rel.get("type") != "relationship":
        continue
    src, tgt = by_ref.get(rel["source_ref"]), by_ref.get(rel["target_ref"])
    if not src or not tgt:
        continue
    if rel["relationship_type"] == "subtechnique-of":
        parent[atlas_id(src)] = atlas_id(tgt)
    elif rel["relationship_type"] == "mitigates":
        mitigates.setdefault(atlas_id(tgt), []).append(atlas_id(src))


def tactic_ids(tid):
    """Subtechniques carry no phases of their own; they inherit the parent's.

    Getting this wrong is silent: on ATLAS 5.6.0 it reported 9 of 16 tactics instead
    of 12 of 16 during the research, and nothing errored.
    """
    phases = techniques[tid].get("kill_chain_phases") or []
    if not phases and parent.get(tid):
        phases = techniques[parent[tid]].get("kill_chain_phases") or []
    return [shortname[p["phase_name"]] for p in phases
            if p.get("phase_name") in shortname]


# The matrix column order, which the ATLAS Navigator and atlas.mitre.org both use.
order = []
matrix = next((o for o in objs if o.get("type") == "x-mitre-matrix"), None)
if matrix:
    order = [atlas_id(by_ref[r]) for r in matrix.get("tactic_refs", [])
             if r in by_ref and atlas_id(by_ref[r])]

out = {
    "source": SRC,
    "sha256": SHA256,
    # The bundle has no version field of its own - so this is the pinned release,
    # guaranteed by the sha256 check above rather than read from the data.
    "atlas_version": ATLAS_VERSION,
    "tactic_order": order or sorted(tactics),
    # shortname ("reconnaissance") as well as id ("AML.TA0002"): a Navigator
    # layer entry keys on the SHORTNAME, and without it a technique that sits
    # under several tactics does not place correctly on the matrix.
    "tactics": {t: {"name": o["name"], "shortname": o.get("x_mitre_shortname", "")}
                for t, o in tactics.items()},
    "techniques": {
        t: {"name": o["name"], "parent": parent.get(t), "tactics": tactic_ids(t),
            "created": (o.get("created") or "")[:10],
            "mitigations": sorted(mitigates.get(t, []))}
        for t, o in techniques.items()},
    "mitigations": {m: {"name": o["name"]} for m, o in mitigations.items()},
}
OUT.write_text(json.dumps(out, separators=(",", ":"), sort_keys=True))
os.chmod(OUT, 0o644)
for path in (OUT, DEST, DEST.parent):
    os.utime(path, (0, 0))

if not (out["techniques"] and out["mitigations"] and out["tactics"]):
    die("distilled to an empty table - the STIX shape has changed")
print(f"  baked ATLAS {ATLAS_VERSION}: {len(out['techniques'])} techniques, "
      f"{len(out['mitigations'])} mitigations, {len(out['tactics'])} tactics")
print(f"  -> {OUT}  {OUT.stat().st_size/1024:.0f} KB  "
      f"(mtime pinned to the epoch for a reproducible layer)")
