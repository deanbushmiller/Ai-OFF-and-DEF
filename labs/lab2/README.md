# Lab 2 — RAG and semantic ingestion attacks

**Time:** 12–15 minutes · You write no code.

Lines marked 🅱️ are the **core attack commands**. Beginner mode runs only those.
Expert mode runs the whole list, including the steps beginner skips.

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


**Expert mode:** add `--expert` to go straight to a shell.
**Hard mode:** add `--challenge` for beginner mode with the commands hidden.

---

## The question this lab answers

If anyone can add a document to the knowledge base your assistant reads,
**who decides what is true?**

---

## Architecture

```
   corpus/  15 plain-text documents, one historical figure each
        │
        │   python rag.py build
        ▼
   index.npz          embeddings from all-MiniLM-L6-v2
        │             (saved as .npz, not pickle — see lab 1)
        │
        │   python rag.py ask "Who invented the telephone?"
        ▼
   cosine similarity ──► top 3 chunks ──► pasted into the prompt
                                               │
                                               ▼
                                        flan-t5-small
                                               │
                                               ▼
                                         "Alexander Graham Bell"

   ... then one PDF is added to the index, and the same question
       returns a different answer.
```

No ports. No network. Everything is local to the container.

## The vulnerable configuration

Open `rag.py` and find `build_prompt()`. It is four lines and it is the whole bug:

```python
context = "\n".join(chunks)
return (f"Answer the question using only the context.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:")
```

Retrieved text is pasted straight into the prompt — unlabelled, unmarked, and
indistinguishable from the instruction around it. OWASP LLM01:2026 calls this
**context-window pooling**: the model sees system prompt, question and retrieved
documents as one flat stream of tokens with no enforced trust boundary.

Whatever is in the index is treated as true.

---

## The commands

### Set up the knowledge base

🅱️ `ls corpus/`
See the knowledge base — 15 documents, one per historical figure.

🅱️ `python rag.py build`
Embed all 15 documents into a searchable index. This is what a real ingestion
pipeline does to a SharePoint or wiki export.

### Establish ground truth

🅱️ `python rag.py ask "Who invented the telephone?"`
The pipeline retrieves the most similar documents, then answers using only those.
Note the answer **and** the similarity scores. You will see them beaten.

### Craft the poison

🅱️ `cat make_poison.py`
Read the attack before running it. Two text layers: black 11pt for humans,
white-on-white 6pt for the extractor. The last payload line is keyword stuffing,
so the document ranks highly for the questions we expect.

**Expert only:** `nano poison_source.txt`
Edit the payload. Put **your own name** in place of Dean Bushmiller, then rebuild
and watch the answer change to whatever you wrote. This is the step that makes it
concrete: you are choosing what the assistant believes.

🅱️ `python make_poison.py`
Build the poisoned PDF. It looks like an IT onboarding checklist.

🅱️ `python peek_pdf.py poisoned_handbook.pdf`
See the gap between what a human sees and what the machine reads. Colour is a
rendering instruction; extraction ignores it completely.

### Poison the knowledge base

🅱️ `python rag.py ingest poisoned_handbook.pdf`
Add the PDF the way a document gets uploaded to a wiki or synced from a shared
drive. Nobody reviews it. Nothing checks where it came from.

### Show the damage

🅱️ `python rag.py ask "Who invented the telephone?"`
The exact same question. Same model, same code, one new document.

🅱️ `python rag.py ask "Who painted the Mona Lisa?"`
A completely unrelated question, to show this is not a one-off. One document
poisoned the whole knowledge base.

🅱️ `python rag.py evidence`
Before and after, side by side, with the retrieval scores that decided it.

**Expert only:** `python check.py`
Confirms the evidence exists and the attack actually worked.

---

## OWASP mapping (2026)

| Entry | Why |
|---|---|
| **LLM01:2026 Prompt Injection** | Indirect injection through retrieved content — the payload rides in a RAG passage. |
| **LLM07:2026 Misinformation** | The pipeline confidently returns a false fact. The model is not broken; it is faithfully reporting a poisoned corpus. |
| **LLM09:2026 Vector and Embedding Weaknesses** | The retrieval step only. Keyword stuffing exploits similarity-search mechanics to outrank the true document. |

Not **LLM05:2026 Data and Model Poisoning** — that entry covers *training-time*
poisoning. Nothing here retrains anything.

## MITRE ATLAS mapping

```
AML.T0064  →  AML.T0066   →  AML.T0068   →  AML.T0051.001  →  AML.T0070
Gather RAG    Retrieval      LLM Prompt     LLM Prompt        RAG
Indexed       Content        Obfuscation    Injection:        Poisoning
Targets       Crafting                      Indirect
(Recon)       (Resource      (Defense       (Execution)       (Impact)
              Development)   Evasion)
```

`AML.T0066 Retrieval Content Crafting` — *"writing content designed to be
retrieved by user queries to influence system users"* — is the skill you actually
practise here, and the one most people have never heard of.

---

## How this differs from a real attack

| This lab | A real attack |
|---|---|
| Payload names someone you know is wrong | A phishing URL, or a plausible wrong policy |
| One obvious PDF | Dozens of documents, drip-fed over weeks |
| Local corpus, 15 documents | SharePoint, Confluence, a ticket queue |
| You ingest it yourself | An outsider uploads it and waits |
| White text, easy to find | Unicode tricks, metadata, image alt text |

---

## The defence

1. **Treat retrieved text as data, never as instructions.** Mark it in the prompt
   so the model can tell where it came from.
2. **Gate ingestion.** Who may add documents, and who reviewed them?
3. **Keep provenance per chunk** and show it with the answer, so a user can see
   the source that produced it.
4. **Extract and inspect the full text layer at upload time.** White text and
   zero-width characters are invisible to a reviewer and obvious to a scanner.
5. **Prefer ground-truth sources** for facts that matter, and make the assistant
   cite them.

---

## Proof of completion

Paste the output of `python rag.py evidence` into the class chat — the **BEFORE
and AFTER** block. Both halves, or it proves nothing.

Your full transcript is saved as `lab2-results.txt` next to the setup script.
