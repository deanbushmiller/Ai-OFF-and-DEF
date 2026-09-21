# SecLLM Bootcamp — AI Offense and Defense Labs

> **Beta — rebuilt 2026-09**
> Eight hands-on labs. Three are published; labs 4–8 are in progress.

An eight-hour remote course for intermediate security professionals. You learn to attack
LLM systems so you can defend them. Every lab uses harmless local targets and synthetic
data, and runs entirely on your own machine.

## What you need

- A Mac, Windows or Linux computer. **No GPU.**
- **Docker Desktop 4.90 or newer** (macOS/Windows), or **Docker Engine** (Linux),
  installed and running before class.
- About **2 GB of free disk**, and 4 GB of free RAM.
- A terminal: macOS Terminal, Windows PowerShell, or any Linux shell.

You do **not** need an API key, a ChatGPT or Claude subscription, Python, or a cloud
account. Every model the labs use is small, open, and baked into the container image.

**Windows students: [read the setup guide first](docs/student-setup.md).** Windows needs
two extra steps that Docker's own installer does not do for you, and skipping either one
looks identical to "Docker is broken".

## Getting the course files

```bash
git clone https://github.com/deanbushmiller/Ai-OFF-and-DEF.git
```

No git? [Step 0 of the setup guide](docs/student-setup.md) covers installing it on both
platforms, choosing where to put the labs, and the no-git ZIP alternative.

Run every command below **from inside the course folder**.

## How the labs run

Each lab is a self-contained container. There is no shared server, nothing hosted, and
**no network access once the image is pulled** — every model and dataset is baked in at
build time.

You run a setup script rather than raw Docker commands. It checks your prerequisites,
works out whether your machine needs the Intel or ARM image, downloads it, and starts the
lab.

**macOS and Linux**

```bash
bash labs/lab1/setup/setup.sh
```

**Windows** (PowerShell)

```bash
powershell -ExecutionPolicy Bypass -File .\labs\lab1\setup\setup.ps1
```

Most labs offer two modes. **Beginner** shows each command, you type it, and it is checked
before anything runs. **Expert** drops you into a real shell to work from the lab's
`LAB.md`. Add `--expert` or `--challenge` to the setup command to pick.

Each lab ends by offering to download the next one. Say yes — the labs share container
layers, so most labs after the first are a small delta rather than a full download. Lab 8
closes the attack half by listing the evidence for all eight instead of offering a pre-pull.

**Lab 9 costs about 28 KB if you already have lab 1** — it reuses lab 1's model and
libraries down to the byte. It is also the first lab that runs with `--network none` — no
network at all — because egress control is what it teaches.

**Lab 3 is the exception: about 1.2 GB.** It runs a real language model locally, and that
model is reused by several later labs. Take lab 2's offer to pre-fetch it and you will not
wait. Lab 3 is also the only lab so far that serves a page — on `127.0.0.1:8003`, your own
machine only.

## The labs

Sixteen labs in one continuous numbering. The first eight teach the attack; the second eight
defend the same ground, one for one.

### Attack labs (1–8)

| # | Lab | OWASP 2026 | Status |
|---|---|---|---|
| 1 | [Data and model supply chain poisoning](labs/lab1/) | LLM04, LLM05 | **published** |
| 2 | [RAG and semantic ingestion attacks](labs/lab2/) | LLM01, LLM07, LLM09 | **published** |
| 3 | [Advanced prompt injection](labs/lab3/) | LLM01 | **published** |
| 4 | [Multimodal and vision-based exploits](labs/lab4/) | LLM01, LLM02 | **published** |
| 5 | [Exploiting AI agents and excessive agency](labs/lab5/) | LLM03 | **published** |
| 6 | [MCP and interface hijacking](labs/lab6/) | LLM01, LLM08 | **published** |
| 7 | [AI-powered attack orchestration](labs/lab7/) | LLM10, LLM02 | **published** |
| 8 | [Offensive recap and transition to defense](labs/lab8/) | *all of the above* | **published** |

### Defend labs (9–16)

Each defend lab pairs with an attack lab and turns it into a control you build, run and tune.

| # | Lab | Defends | OWASP 2026 | Status |
|---|---|---|---|---|
| 9 | [Defending the model supply chain](labs/lab9/) | lab 1 | LLM04, LLM05 | **published** |
| 10 | [Defending RAG ingestion](labs/lab10/) | lab 2 | LLM09, LLM07 | **published** |
| 11 | [Defending multimodal input](labs/lab11/) | lab 4 | LLM01, LLM02 | **published** |
| 12 | [Defending against prompt injection](labs/lab12/) | lab 3 | LLM01, LLM02 | **published** |
| 13 | [Defending AI agents](labs/lab13/) | lab 5 | LLM01, LLM03 | **published** |
| 14 | [Defending MCP tool calls](labs/lab14/) | lab 6 | LLM01, LLM08, ASI04 | **published** |
| 15 | [Defending against AI-scaled attacks](labs/lab15/) | lab 7 | LLM10, LLM02, LLM06 | **published** |
| 16 | [Red-team process](https://github.com/deanbushmiller/Ai-OFF-and-DEF/wiki/Lab-16-After-class) | — | — | **You build** |

## Course materials

- [Student setup](docs/student-setup.md) — start here, especially on Windows
- [OWASP threat mapping](docs/owasp-threat-mapping.md) — how each lab maps to the 2026 Top 10

## Safety

Every lab is contained by design:

- Payloads are benign stand-ins. Lab 1's "malicious" code runs `echo`. Lab 2's poison is a
  false sentence, not an instruction.
- Models are toy-sized and open. Nothing sends data anywhere.
- Containers bind no ports and have no network access during the lab.
- Nothing leaves your machine.

Use this material only for authorised education and local testing. What you learn here
applies to systems you own or have written permission to test.
