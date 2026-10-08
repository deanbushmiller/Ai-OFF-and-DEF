# Mac and Linux setup

*On Windows? Use the [Windows setup guide](windows-setup.md).*

Do this **before class**. It takes 20–40 minutes the first time, and almost none of that is
work — it is waiting for downloads.

The 10 minutes at the start of class covers starting a lab and nothing else.

---

## Step 1 — Get the course files

Everything else assumes you have the course folder on your machine.

### Choose where the labs will live

**Anywhere you like.** Nothing in this course depends on the location — the scripts work
out where they are and where everything else is, so your own Documents folder is fine.

One thing to avoid:

- **Folders synced by OneDrive, iCloud or Dropbox.** Sync services lock files mid-write and
  it causes odd failures that look like lab bugs.

The commands below use `~`, which resolves to your own home folder whatever your
username is. Put it somewhere else if you prefer — just run the same commands from there
instead.

### Use git

Git takes about two minutes to install and makes updates one command instead of a
re-download. The course is in beta and fixes ship between sessions — that has already
happened twice.

**macOS** — open **Terminal** and run:

```bash
git --version
```

macOS does not ship git, but typing that command pops up an installer for Apple's
Command Line Tools. Click **Install**, wait, then run it again. Then:

```bash
cd ~/Documents && git clone https://github.com/deanbushmiller/Ai-OFF-and-DEF.git
```

```bash
cd Ai-OFF-and-DEF
```

Both commands are relative to where you are, so put the course somewhere else if you
prefer — just `cd` there first instead.

**Linux** — git is in every distro's repositories, and often already installed:

```bash
git --version || sudo apt install git      # or dnf install git / pacman -S git
```

```bash
cd ~/Documents && git clone https://github.com/deanbushmiller/Ai-OFF-and-DEF.git
```

```bash
cd Ai-OFF-and-DEF
```

Both commands are relative to where you are, so put the course somewhere else if you
prefer — just `cd` there first instead.

### Last resort — ZIP, if you genuinely cannot install git

Download <https://github.com/deanbushmiller/Ai-OFF-and-DEF/archive/refs/heads/main.zip>
and unzip it into the folder you chose.

Two things to know before you choose this:

1. **The folder is named differently** — `Ai-OFF-and-DEF-main`, not `Ai-OFF-and-DEF`. Every
   path in this guide needs adjusting by hand.
2. **Updates mean downloading and unzipping again**, and remembering to do it.

If you hit any of these, installing git is faster than working around them.

> **Never** paste a command that pipes a downloaded script straight into a shell
> (`irm ... | iex`, `curl ... | bash`), no matter who suggests it. This is a security
> course; running code you have not read is the thing we are here to stop. Every command
> in this course is one you can read first.

---

## What you need

- A Mac, Windows or Linux computer. No GPU.
- **Docker Desktop 4.90 or newer.**
- About **6 GB free disk**, 4 GB free RAM. The whole course is a 2 GB download, and Docker
  keeps about 5.2 GB on disk once it has unpacked it (measured 2026-09-22).
- A terminal.

No API key, no ChatGPT or Claude subscription, no Python, no cloud account.

---
## macOS

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Open it and wait for the whale icon in the menu bar to stop animating.
3. From inside the course folder — the `Ai-OFF-and-DEF` folder you cloned — run the
   lab 1 setup script:

```bash
bash labs/lab1/setup/setup.sh
```

If that says "No such file or directory", you are in the wrong folder. Run `pwd` — it
should end in `Ai-OFF-and-DEF`.

That is all. The script checks everything else and tells you if something is wrong.

---

## Linux

The easiest platform of the three. The lab images **are** Linux containers, so they run
natively — no virtual machine, no WSL, none of the Windows setup applies.

### 1. Install Docker Engine

You want Docker **Engine**, not Docker Desktop. Desktop works, but it adds a VM you do not
need on Linux.

| Distro | Command |
|---|---|
| Debian / Ubuntu | `sudo apt install docker.io` |
| Fedora / RHEL | `sudo dnf install docker` |
| Arch | `sudo pacman -S docker` |

Or the official packages, which track newer versions:
<https://docs.docker.com/engine/install/>

### 2. Start it, and enable it at boot

```bash
sudo systemctl enable --now docker
```

### 3. Add yourself to the docker group — then log out

This is the step people miss, and it produces a confusing error.

```bash
sudo usermod -aG docker $USER
```

**Now log out and back in.** A new terminal is not enough — group membership is attached
when you log in. On some desktops you need a full reboot.

Check it worked:

```bash
groups | grep docker
```

Without this, every `docker` command needs `sudo`, and the setup script will stop and tell
you so rather than letting you guess.

### 4. Run the setup script

From inside the course folder:

```bash
bash labs/lab1/setup/setup.sh
```

### Architecture

The script works out whether you need the `amd64` or `arm64` image. Note that Linux reports
ARM chips as `aarch64` where macOS says `arm64` — same chip, different string. The script
handles both, and cross-checks against what the Docker engine itself reports.

### Rootless Docker

If you run Docker rootless, the group step does not apply and `docker info` will already
work. The script only mentions the group when `docker info` fails **and** you are not in
the group, so a rootless setup passes straight through.

---

## Download sizes

The labs share container layers, so only the first is a full download.

| | Download |
|---|---|
| Lab 1 | ~190 MB (Apple Silicon) / ~250 MB (Intel) |
| Lab 2 | ~520 MB (Apple Silicon) / ~580 MB (Intel) |
| Lab 3 | ~1.1 GB |
| Each later lab | a small delta |

Each lab ends by offering to fetch the next one. **Say yes** — doing it while you are
already online means no waiting next session.

---

## If something goes wrong

The setup script names the specific cause. Send its output to the instructor through
GitHub — not a screenshot of the whole screen, just the lines starting `[FAIL]` or `[WARN]`.

Common ones:

| What you see | What it means |
|---|---|
| `Docker is not installed` | Install Docker Desktop |
| `Docker is installed but not running` | Start Docker Desktop (Mac) or `sudo systemctl start docker` (Linux) |
| `Hardware virtualization is not available` | BIOS/UEFI, or nested virtualization in your VM |
| `denied` / `unauthorized` on pull | The instructor has not published that lab yet |
| `You are not in the 'docker' group` | Linux: `sudo usermod -aG docker $USER`, then **log out and back in** |
| `permission denied ... docker.sock` | Linux: same as above — the group, not the daemon |
