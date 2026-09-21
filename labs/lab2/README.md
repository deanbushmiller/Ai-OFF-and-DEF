# Lab 2 — RAG and semantic ingestion attacks

**Time:** 12–15 minutes · You write no code.

Lines marked 🅱️ are the **core attack commands**. Beginner mode runs only those.
Expert mode runs the whole list, including the steps beginner skips.

---

## Before you start

> **First lab? Not set up yet?**
> Go to **[the setup guide](../../docs/student-setup.md)** first. It covers getting the
> course files, installing Docker, and the extra steps Windows needs. Come back here when
> `docker --version` works.

If you have already done lab 1, you are ready — nothing new to install.

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
  finishes it is copied out to `lab2-results.txt`, next to the setup script you ran. If
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
powershell -ExecutionPolicy Bypass -File .\labs\lab2\setup\setup.ps1
```

The first line assumes you cloned into your Documents. If you cloned somewhere else, `cd`
there instead — the second line is relative to the course folder, so it works from any
location.

**macOS and Linux**

```bash
bash labs/lab2/setup/setup.sh
```

The script checks Docker, works out whether your machine needs the Intel or ARM image,
fetches it if you do not already have it, and starts the lab.

### Choose a mode

The lab asks which you want. You can re-run it to switch.

**Beginner** — the default, and the right choice if you are not sure. The lab shows you
each command with a short explanation of what it does and why. You type or paste it, and
the lab checks it before anything runs. Get it wrong and it tells you what the command
should have been; get it wrong twice and it runs the correct one for you so you are never
stuck. Ten commands.

**Expert** — drops you into a real shell in the lab folder. No commands shown, no
corrections. You work from [`LAB.md`](LAB.md), which lists every command. Expert also adds
the steps beginner skips: moving around the folder yourself, and editing the payload with
`nano` to put your own name in it. Finish with `python check.py` to confirm it worked.

To go straight to expert mode, add `--expert` to the command above.

**If it fails**, the script tells you why in plain English. Send that message to the
instructor via email or post to class Q&A.

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

---

## Reference

ATLAS technique and mitigation IDs in this lab are cited **as of ATLAS release 2026.09**.
The authoritative, always-current definitions are at
<https://atlas.mitre.org/>, and the underlying data is at
<https://github.com/mitre-atlas/atlas-data>.

OWASP GenAI LLM Top 10 (2026): <https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/>
