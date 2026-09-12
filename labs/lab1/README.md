# Lab 1 — Data and model supply chain poisoning

**Time:** 12–15 minutes · **You type seven commands.** You write no code.

---

## The question this lab answers

When you download a model from a public hub, what did you actually just put on your machine?

---

## Setup

You need **Docker Desktop** installed and running. Nothing else. The lab installs nothing
on your computer — everything lives inside a container.

### Windows students: read this before class

Docker Desktop on Windows does not run on its own. It runs its engine inside **WSL2**,
which needs hardware virtualization. Do these **in this order** — installing Docker first
is the usual reason it will not start.

**Step 1 — Install WSL, from GitHub, not the Store.**

<https://github.com/microsoft/WSL/releases>

Take the newest release **not** marked *Pre-release* — **2.7.14** or later — and download:

| Your CPU | File |
|---|---|
| Intel / AMD | `wsl.<version>.x64.msi` |
| Windows on ARM (Snapdragon, Surface) | `wsl.<version>.arm64.msi` |

Run the MSI, then **reboot**.

> **Why not `wsl --install`?** That command installs through the Microsoft Store, and the
> Store route fails on VMs, Windows Server, and company-managed machines — usually with an
> unhelpful error. The MSI works in all of those. If `wsl --install` already worked for
> you, you are fine; this is the fallback that actually succeeds when it does not.

**Step 2 — Install Docker Desktop 4.90 or newer.**

<https://www.docker.com/products/docker-desktop/>

Start it and wait until it says *Engine running*.

> **The first launch is slow — expect several minutes.** Docker Desktop builds its Linux
> disk image (`ext4.vhdx`) the first time it starts, and the window can look frozen while
> it does. Let it finish. This happens **once**; every later start is quick.
>
> This is why all of Step 1–3 must be done **before class**, not in the setup window.
> WSL install + reboot + Docker install + first launch + image pull adds up to well over
> half an hour, and none of it is work you want to do while the class waits.

**Step 3 — Running Windows inside a virtual machine?** (VMware, VirtualBox, Parallels, Hyper-V)

You must enable **nested virtualization** — passing the CPU's virtualization features
through to the guest. **Shut the VM down first**; this cannot be changed while it runs.

| Your VM software | Where to turn it on |
|---|---|
| VMware | VM Settings → Processors → *Virtualize Intel VT-x/EPT or AMD-V/RVI* |
| VirtualBox | Settings → System → Processor → *Enable Nested VT-x/AMD-V* |
| Parallels | Hardware → CPU & Memory → Advanced → *Enable nested virtualization* |
| Hyper-V | On the **host**, admin PowerShell: `Set-VMProcessor -VMName <name> -ExposeVirtualizationExtensions $true` |

**Also in a VM: preallocate the virtual disk.** This one costs 10–20 minutes if you skip it.

Docker builds its Linux disk image (`ext4.vhdx`) the first time it starts. If your VM's
virtual disk grows on demand — "dynamically allocated", "expanding", "thin provisioned" —
that growth happens *while you wait*, and it looks exactly like Docker has hung.

| Your VM software | Set the disk to |
|---|---|
| VMware | *Allocate all disk space now* (set when the disk is created) |
| VirtualBox | *Fixed size*, not *Dynamically allocated* |
| Hyper-V | *Fixed size* VHDX, not *Dynamically expanding* |
| Parallels | Hardware → Hard Disk → uncheck *Expanding disk* |

Give the VM **at least 20 GB free**. The lab image is under 1 GB, but Docker's own disk
image needs room on top of it.

**On real hardware instead?** If Docker still will not start, virtualization may be off in
firmware. Reboot into BIOS/UEFI and enable **Intel VT-x** or **AMD-V / SVM Mode**.

`setup.ps1` checks all of this before it downloads anything and tells you which one is
wrong — so run it early rather than discovering this in class.

**macOS**

```bash
bash setup.sh
```

**Windows** (PowerShell, in this folder)

```bash
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The script checks Docker, works out whether your machine needs the Intel or ARM image,
downloads it (~190–250 MB, 1–3 minutes), and starts the lab.

**Hard mode:** add `--challenge` to either command and the runner describes each step but
hides the command, so you work it out yourself. Same checking, same corrections.

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

```
AML.T0058          →  AML.T0018.000  →  AML.T0010.003   →  AML.T0011.000
Publish Poisoned      Poison AI          AI Supply Chain    User Execution:
Models                Model              Compromise: Model  Unsafe AI Artifacts
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
