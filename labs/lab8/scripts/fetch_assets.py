"""Build-time asset baking. Runs during `docker build` only - never at run time.

MITRE ATLAS, distilled. ~450 KB in, ~100 KB out, and NO pip dependency.

WHY THE STIX FILE AND NOT ATLAS.yaml
------------------------------------
`atlas-data/dist/ATLAS.yaml` is the friendlier format, but parsing it needs PyYAML, and
lab 8 is the one lab in this course that installs no Python packages at all. The STIX
bundle carries exactly the same content - 170 techniques, 35 mitigations, 16 tactics, 246
`mitigates` relationships - and `json` is in the standard library.

VERIFIED, not assumed: distilling from the STIX bundle reproduces the numbers taken from
ATLAS.yaml exactly - all 20 of the course's technique IDs resolve, 12 of 16 tactics are
covered, and 9 techniques have no mitigation. See lab-research/lab8/probe-transcripts/.

WHAT GETS KEPT
--------------
Only what the lab reads: technique id, name, parent, tactics, CREATION DATE; tactic id and
name; mitigation id, name, and which techniques it mitigates. Descriptions are dropped -
they are most of the 450 KB and the lab never prints them.

The creation date is kept for one specific reason: beat 7 claims the defensive literature
lags the offensive literature and that you can see it by reading the dates. Without the
dates in the data that is an assertion the student has to take on trust. With them, the
lab prints the evidence next to the claim.

The output lands in /opt/lab-assets/atlas/, which is the SHARED cache path. Lab 8 is the
natural home for ATLAS data in the merged 8-lab image. Note that labs 1-7 hard-code their
technique IDs in their own text and read nothing at run time, so nothing points at this
file yet - retrofitting them would mean republishing seven images for zero student-visible
benefit. See assets.json.

TIMESTAMPS
----------
Same discipline as the model labs: a Docker layer is a tar and a tar records mtimes, so
the mtime is pinned to the epoch and the download is deleted in the same RUN. Small here -
the file is ~100 KB - but the rule is the rule, and it costs nothing.
"""
import json
import os
import pathlib
import urllib.request

SRC = ("https://raw.githubusercontent.com/mitre-atlas/atlas-navigator-data"
       "/main/dist/stix-atlas.json")
DEST = pathlib.Path("/opt/lab-assets/atlas")
OUT = DEST / "atlas.json"

DEST.mkdir(parents=True, exist_ok=True)

with urllib.request.urlopen(SRC, timeout=120) as r:
    bundle = json.loads(r.read())
objs = bundle["objects"]


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

    Getting this wrong is silent: it reported 9 of 16 tactics instead of 12 of 16
    during the research, and nothing errored.
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
    "atlas_version": bundle.get("x_mitre_version") or "ATLAS (STIX bundle)",
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

print(f"  baked ATLAS: {len(out['techniques'])} techniques, "
      f"{len(out['mitigations'])} mitigations, {len(out['tactics'])} tactics")
print(f"  -> {OUT}  {OUT.stat().st_size/1024:.0f} KB  "
      f"(mtime pinned to the epoch for a reproducible layer)")
