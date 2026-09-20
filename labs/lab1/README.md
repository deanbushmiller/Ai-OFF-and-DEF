# Lab 1 — Data and model supply chain poisoning

**Time:** 12–15 minutes · **You type seven commands.** You write no code.

---

## The question this lab answers

When you download a model from a public hub, what did you actually just put on your machine?

---

## Before you start

> **First time? Start here.**
> **[The setup guide](../../docs/student-setup.md)** covers getting the course files,
> installing Docker, and the extra steps Windows needs. Work through it once and every
> later lab just runs.

You are ready when `docker --version` works in your terminal.

---

## How the lab works — read this once

Every step is a small experiment, and it always has the same three beats:

**1. Why** — one or two lines telling you what you are about to do and what to watch for.

**2. The command** — you type or paste it. The lab checks what you typed before it runs
anything. Get it wrong and it shows you the right command; get it wrong twice and it runs
the correct one for you.

**3. What it meant** — lines beginning with `^` underneath the output, on the steps where
something just changed.

> **The `^` lines are the point of the lab.** The output shows you *what happened*; the `^`
> lines tell you *why it matters*. If you read one thing, read those.

### The output will run off your screen. Nothing is lost.

Some steps print more than a screenful. That is expected, and there are three reasons not
to worry about it:

- **The lab never moves on by itself.** It waits at every step until you type something.
  Read first, type second. The 12–15 minutes assumes you are reading.
- **You can scroll back at any time.** The mouse wheel works everywhere. macOS Terminal and
  most Linux terminals also take `Shift`+`PageUp`; Windows Terminal takes
  `Ctrl`+`Shift`+`PageUp`. Scrolling does not interrupt the lab.
- **The whole transcript is saved to a file**, including every `^` line. When the lab
  finishes it is copied out to `lab1-results.txt`, next to the setup script you ran. If
  something scrolled past, open that file afterwards rather than hunting for it in the
  terminal — and it is the same file you use as evidence.

---

## Run the lab

Open a terminal **in the course folder** — the `Ai-OFF-and-DEF` folder you cloned, wherever
you put it. Not sure you are in it? `dir` on Windows, `ls` on macOS and Linux: you should
see a `labs` folder.

**Windows** — PowerShell, opened **as Administrator** (Start menu → type `powershell` →
right-click → **Run as administrator**):

```bash
cd $HOME\Documents\Ai-OFF-and-DEF
```

```bash
powershell -ExecutionPolicy Bypass -File .\labs\lab1\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab1/setup/setup.sh
```

The script checks Docker, works out whether your machine needs the Intel or ARM image,
downloads it (~190–250 MB, 1–3 minutes), and starts the lab.

**If it fails**, the script tells you why in plain English. Send that message to the
instructor through GitHub.

---

## How the lab works

You type each command yourself. The runner checks what you typed before anything runs.

- Get it right → the real command runs and you see its output.
- Get it wrong → `Not quite. The command should be: <X>` and you try again.
- Wrong twice → it runs the correct command for you so the lab keeps moving.

Extra or missing spaces are forgiven. Flags, filenames, and capitals must be exact —
because in this lab a single wrong character is the difference between a scan that
passes and a scan that fails.

> Nothing you type is ever executed. Your input is only *compared* to the expected
> command; the runner then runs its own known-good copy. A security lab should not
> itself contain an "execute whatever the user typed" bug.

## The seven commands

| # | Command | Why |
|---|---|---|
| 1 | `cat make_model.py` | Read the exploit before you run it. Find `__reduce__`. |
| 2 | `python make_model.py --clean` | Build a model file from the genuine weights, unchanged. |
| 3 | `picklescan -p bert_tiny_clean.pt -g` | Scan it. Expect `Infected files: 0`. |
| 4 | `python make_model.py --poison` | Same script, one word different. Adds the hidden payload. |
| 5 | `picklescan -p bert_tiny_poisoned.pt -g` | Scan it. Expect `Infected files: 1`. |
| 6 | `python unpack.py bert_tiny_poisoned.pt` | A `.pt` is a ZIP. Pull the pickle out as `data.pkl`. |
| 7 | `fickling --check-safety --print-results data.pkl` | A second scanner, opposite logic. |

Same script. Same weights. Same scanner. One extra dictionary key, opposite verdict.

Steps 6 and 7 get a **second opinion**. picklescan uses a *denylist* — it knows which
imports are dangerous. fickling uses an *allowlist* — it knows which are safe and distrusts
everything else, so it is noisier on purpose: it flags torch's own legitimate imports too.
Read its last line before the warning, and the wording it reserves for that one:
*"overtly malicious"*. Two tools, two methods, same conclusion.

---

## Architecture

```
   YOUR MACHINE                    INSIDE THE CONTAINER (no network)
   ------------                    ---------------------------------
   Docker Desktop  ──── runs ────▶  /opt/lab-assets/hf/...
                                      prajjwal1/bert-tiny
   setup.sh                            pytorch_model.bin   ← genuine, 17.8 MB
   setup.ps1                                 │
        │                          make_model.py reads it
        │                            ┌───────┴───────┐
        │                        --clean          --poison
        │                            │                │
        │                   bert_tiny_clean.pt   bert_tiny_poisoned.pt
        │                            │                │
        │                        picklescan       picklescan
        │                            │                │
        │                      Infected: 0      Infected: 1
        ▼                            └───────┬────────┘
   lab1-results.txt  ◀── docker cp ──────────┘
```

The container binds **no ports** and has **no network access** during the lab.
Every asset was baked in at build time.

---

## The vulnerable configuration

Two facts, and the attack lives in the gap between them.

1. **`prajjwal1/bert-tiny` ships `pytorch_model.bin` and no safetensors file.**
   That `.bin` is a Python **pickle**.
2. **Pickle is not a data format. It is a program.**
   A `__reduce__` method tells pickle "to rebuild me, call this function with these
   arguments." Pickle obeys, at load time, before you have used the model for anything.

So "downloading a model" and "running someone else's code" can be the same action.

Scanners like **picklescan**, **fickling** (both used here), and **modelscan** read the pickle opcodes
*without* running them. They flag a `GLOBAL` opcode importing a system-execution primitive
(`os.system`, `subprocess.Popen`) paired with a `REDUCE` opcode.

> **Watch for this in step 5.** You will read `os.system` in the script, but the scanner
> reports **`posix.system`**. On Linux, `os` is a thin wrapper over `posix`. Same function.
> Renaming an import does not hide you from a scanner.

---

## OWASP mapping

The numbering **changed between editions**, so both are given.

| 2026 (v1.0) | 2025 (2.0) | Relevance |
|---|---|---|
| **LLM04:2026 Supply Chain** | LLM03:2025 Supply Chain | Primary. 2026 item **#4 Weak Provenance and Unsigned Model Artifacts**. |
| **LLM05:2026 Data and Model Poisoning** | LLM04:2025 Data and Model Poisoning | The mechanism — "malicious pickling, which can execute harmful code when the model is loaded." |

**2026 Scenario #7 under LLM04 is this lab, verbatim:** a developer loads a third-party
model using unsafe serialization, embedded code executes during loading, host compromise
follows.

- 2026: <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/> (PDF also in `Activity-Labs/`, pp. 27–37)
- 2025: <https://github.com/OWASP/www-project-top-10-for-large-language-model-applications/tree/main/2_0_vulns>

## MITRE ATLAS mapping

> **Note on the first ID.** ATLAS retired `AML.T0058` *Publish Poisoned Models* and replaced
> it with **`AML.T0115` Publish Poisoned AI Artifacts**, which is what lab 9 cites. The
> chain below is corrected. **The lab's own on-screen text still prints the retired
> `AML.T0058`** — it is baked into the published image, and correcting it would cost a
> rebuild and republish for a label change. Cite `AML.T0115`.

```
AML.T0115          →  AML.T0018.000  →  AML.T0010.003   →  AML.T0011.000
Publish Poisoned      Poison AI          AI Supply Chain    User Execution:
AI Artifacts          Model              Compromise: Model  Unsafe AI Artifacts
(Resource Dev)        (Persistence)      (Initial Access)   (Execution)
```

`AML.T0011.000 Unsafe AI Artifacts` is the closest ID in ATLAS to what this lab shows:
nobody runs an exploit. A developer calls `torch.load()`.

---

## How this differs from a real attack

| This lab | A real attack |
|---|---|
| The command is `echo` | Reverse shell, credential stealer, or miner |
| Key is named `_security_demo_payload` | Key named to blend in with real weight names |
| File never leaves the container | File uploaded to a public hub under a plausible org |
| A 17.8 MB test model | A model thousands of people pull |
| You scan before loading | The victim loads and never scans |
| Built to be caught | Built to survive the scanner |

---

## The defence

1. **Prefer safetensors.** It cannot execute code by design.
2. **Scan every pickle-based model you did not build yourself.**
3. **Keep `torch.load(weights_only=True)`.** Never switch it off to clear an error.
4. **Verify provenance** — signatures and hashes, not hub reputation.

### What this lab does not prove

You will watch a scanner catch this attack. Do not leave thinking scanners make you safe.
OWASP 2026 calls scanners and safe-loader flags defence in depth, **not guarantees**:

- **nullifAI** — models on Hugging Face using broken or compression-wrapped pickle streams
  that execute *before* a scanner reaches the malformed byte (Zanki, 2025)
- **picklescan itself has had zero-days** (Cohen, 2025)
- **`torch.load` `weights_only` has had a bypass** — CVE-2025-32434
- **ShadowLogic** — a backdoor in the computation graph of a "safe" format like ONNX, with
  no executable code for a serialization scanner to find (Wickens et al., 2024)

Our payload was built to be easy to catch. A real one would be built to survive the exact
tool you just ran.

---

## Proof of completion

Paste **both** scan summaries into the class chat — the clean one and the poisoned one.
The pair is the proof; either alone means nothing.

```
bert_tiny_clean.pt      Scanned files: 1   Infected files: 0
bert_tiny_poisoned.pt   Scanned files: 1   Infected files: 1   posix.system
```

Your full transcript is saved as `lab1-results.txt` next to the setup script.

---

## Before you close the window

The setup script will offer to download **Lab 2** for you. **Say yes.**

The eight labs share most of their container layers, so each next lab is a small
delta rather than another full download — and doing it now, while you are already
online, means no waiting at the start of the next session.

If you skip it, run this before the next class:

```bash
docker pull ghcr.io/deanbushmiller/seclm-labs:lab2-amd64
```

Swap `amd64` for `arm64` on Apple Silicon or Windows on ARM. If it reports *not found*,
that lab is not published yet — harmless, just try again later.

---

## Tools used

| Tool | Licence | Role |
|---|---|---|
| [picklescan](https://github.com/mmaitre314/picklescan) 1.0.5 | MIT | Scans pickle opcodes without executing them |
| [fickling](https://github.com/trailofbits/fickling) 0.1.12 | LGPL-3.0 | Allowlist scanner and pickle decompiler |
| [PyTorch](https://pytorch.org) 2.9.1 (CPU) | BSD-3 | `torch.save` / `torch.load` |
| [prajjwal1/bert-tiny](https://huggingface.co/prajjwal1/bert-tiny) | MIT | The genuine 17.8 MB model |

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
