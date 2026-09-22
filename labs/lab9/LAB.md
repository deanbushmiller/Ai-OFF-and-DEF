# Lab 9 — Defending the model supply chain

The first defend lab. It pairs with lab 1, where you built a model file that ran a command
when it loaded. This time you stand up the control that stops it, watch it miss something,
and tune it.

**Defends:** lab 1 — data and model supply chain poisoning
**OWASP:** LLM04:2026 Supply Chain (risks 3 and 4) · LLM05:2026 Data and Model Poisoning
(scenario 7, prevention 4)
**ATLAS:** defends `AML.T0115.001` → `AML.T0010.003` → `AML.T0011.000`, with `AML.M0016`
Vulnerability Scanning, `AML.M0011` Restrict Library Loading, `AML.M0024` AI Telemetry Logging

---

## The architecture

```
   a model file from somewhere you do not control
                     |
                     v
        +------------------------+
        |   gate.py   PREVENT    |   sha256 -> block list
        |                        |   picklescan
        |                        |   rules.json (your own list)
        +------------------------+
             |              |
       allowed           blocked
             |
             v
        +------------------------+
        | sandboxed_load.py      |   separate process
        |            DETECT      |   --network none
        |                        |   audit hook: imports,
        |                        |   commands, sockets
        +------------------------+
             |              |
        nothing          it acted
                            |
                            v
        +------------------------+
        | quarantine.py  RECOVER |   move the file aside
        | tune.py                |   record the hash + evidence
        |                        |   add the indicator to rules.json
        +------------------------+
                            |
                            +---> the gate now catches it earlier
```

## The vulnerable configuration and the defended one

| | Vulnerable (lab 1) | Defended (this lab) |
|---|---|---|
| Ingest | download and use | hash, scan, and apply your own rules first |
| Loading | `torch.load()` in your own process | a separate process, no network, every action logged |
| Scanner errors | treated as "nothing found" | `on_scanner_error: block` — no verdict is not a clean verdict |
| A bad artifact | stays on disk, maybe gets loaded again | moved to `quarantine/`, hash on a block list with its evidence |
| Next time | same result | blocked at the gate, before anything runs |

---

## The steps

The wording below is what the runner prints, word for word.

**1 — build the artifacts.** Build the four artifacts you will defend against. Same real
bert-tiny weights in all four; the difference is one key. `clean` nothing added; `poisoned`
runs a command on load (lab 1's file); `beacon` opens a connection on load; `corrupt`
poisoned, with its stream clipped one byte short.

**2 — gate the clean file.** PREVENT. The gate is what stands between a hub and your build.
Hash the file, scan it, apply your own rules. Start with the genuine article. Expect: allowed.

> ^ The scanner read the whole file and found nothing. That is what a real, unmodified
> download from a real hub looks like.

**3 — gate the poisoned file.** Now the poisoned file from lab 1. Same weights, one extra
key. Expect: blocked — and read WHICH line blocked it.

> ^ Blocked by rules.json — your own list, not the scanner's. `posix.system` was in your
> rules before the scan even ran.

**4 — gate the corrupt file.** The corrupt file. Its pickle stream stops one byte early, so
the scanner cannot finish reading it. The question is not what the scanner found. It is what
your gate does when the scanner cannot answer.

> ^ Fail closed. `rules.json` says `on_scanner_error = block`, so a file nobody could read
> does not get the benefit of the doubt. Two models sat on Hugging Face for eight months in
> 2025 because a scanner errored and a gate read that as fine.

**5 — sandbox the clean file.** DETECT. The gate read the file. This RUNS it, on purpose,
somewhere it cannot reach anything: a separate process, no network, and an audit hook
watching every import, command and socket call. Start with the clean file, so you know what
quiet looks like.

> ^ Nothing. Remember this screen — it is your baseline, and it is the half of the evidence
> people forget to collect.

**6 — sandbox the corrupt file.** Now load the corrupt file — the one your gate just refused.
It is broken, so the load cannot finish. Watch what happens before it fails.

> ^ Read the order. The payload ran, THEN the load fell over. Pickle executes as it reads, so
> a broken file is not a safe file — the damage is done before the error appears. That is
> exactly how the nullifAI models worked.

**7 — sandbox the beacon file.** The beacon file. Its payload does not run a command — it
opens a socket to `203.0.113.10:4444`. This container has no network at all, and the hook
refuses the call as well. Two controls, and you get to see the address.

> ^ Blocked before `connect()` was ever called. You now know the address and the port the
> artifact wanted — which is an indicator you can act on, and you got it without letting a
> single packet leave.

**8 — quarantine.** RECOVER. Contain it: move the file out of the build path, and record its
hash with the evidence your sandbox produced. Moved, not deleted. You cannot investigate what
you destroyed.

> ^ The hash is recorded with the reason and the evidence. The gate refuses that file from now
> on without scanning it.

**9 — tune.** TUNE. A block list catches the file you already saw. This step re-uploads the
same payload with one byte changed — a new hash your block list has never seen — and asks the
gate again. Then it adds your sandbox's own indicator to `rules.json`.

> ^ Same verdict, different authority. Before the edit, a vendor's denylist was the only thing
> standing there. picklescan has had 58 published CVEs since February 2025, every one a way
> past that list. Now you have a rule of your own as well.

---

## The command list

Expert runs all of it. Beginner mode runs only the lines marked 🅱️.

```
cd /labs/lab9

🅱️ python make_model.py --all
🅱️ python gate.py bert_tiny_clean.pt
🅱️ python gate.py bert_tiny_poisoned.pt
🅱️ python gate.py bert_tiny_corrupt.pt
   python gate.py bert_tiny_beacon.pt
🅱️ python sandboxed_load.py bert_tiny_clean.pt
🅱️ python sandboxed_load.py bert_tiny_corrupt.pt
🅱️ python sandboxed_load.py bert_tiny_beacon.pt
🅱️ python quarantine.py bert_tiny_beacon.pt
🅱️ python tune.py --add socket.create_connection

   cat sandbox-log.jsonl
   cat blocklist.json
   nano rules.json
   python check.py
```

**Order matters for one expert step.** `quarantine.py` *moves* `bert_tiny_beacon.pt` into
`quarantine/`, so gate the beacon file where the list puts it — before the sandbox — not
after. Read which line blocks it: the scanner's, not yours. That is what `tune.py` fixes.

Expert mode edits `rules.json` by hand with `nano` instead of running `tune.py`. Add
`"socket.create_connection"` to `blocked_globals`, and look hard at `on_scanner_error` while
you are in there. Then `python check.py` tells you whether the defence holds together.

---

## Reading the code

Four files, none of them long. Read them before you trust them.

| File | What it is |
|---|---|
| `gate.py` | the ingest gate. Hash, scan, rules, in that order |
| `sandboxed_load.py` | starts the child and reports what it saw |
| `_sandbox_child.py` | the audit hook itself — about 120 lines, and the heart of the lab |
| `rules.json` | your policy. Two lines matter and you edit one of them |

---

## What this lab does not prove

The audit hook is **telemetry, not a boundary**. Code already running in that process has
already won; the hook reports what happened, it does not guarantee what cannot. The boundary
was the container and `--network none` the whole time.

A production gate also prefers a format that cannot execute code at all (safetensors), and
verifies a signature bound to a publisher identity — OpenSSF Model Signing with Sigstore —
before it ever gets to scanning. Signing proves origin and integrity, not safety: a validly
signed model from a compromised supplier is still backdoored.

---

## Evidence to submit

Paste **two** things into the class chat:

1. the `blocklist.json` entry you created — the hash, the date, the reason and the evidence
2. the sandbox line showing the blocked connection, with the address and port

The pair is the proof: something was caught, and something was recorded about it.

Your full transcript is saved to `lab9-results.txt` and copied out to the course folder when
the lab exits.
