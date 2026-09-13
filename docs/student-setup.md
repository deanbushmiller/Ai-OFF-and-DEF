# Student setup

Do this **before class**. It takes 20–40 minutes the first time, and almost none of that is
work — it is waiting for downloads and one reboot.

The 10 minutes at the start of class covers starting a lab and nothing else.

---

## Step 0 — Get the course files

Do this first. Everything else assumes you have the course folder on your machine.

### Choose where the labs will live

**Anywhere you like.** Nothing in this course depends on the location — the scripts work
out where they are and where everything else is, so your own Documents folder is fine.

Two things to avoid:

- **Folders synced by OneDrive, iCloud or Dropbox.** Sync services lock files mid-write and
  it causes odd failures that look like lab bugs.
- **Windows system folders.** A PowerShell window opened *as Administrator* starts in
  `C:\Windows\System32`, and cloning there is a bad idea. The commands below move you out
  of it first.

The commands below use `$HOME` (Windows) and `~` (macOS and Linux), which resolve to your
own home folder whatever your username is. Put it somewhere else if you prefer — just run
the same commands from there instead.

### Use git. On Windows, strongly.

Git takes about two minutes to install and makes updates one command instead of a
re-download. The course is in beta and fixes ship between sessions — that has already
happened twice.

**On Windows there is a second reason.** Files extracted from a downloaded ZIP carry
Windows' *Mark of the Web*, a flag saying they came from the internet. PowerShell treats
flagged `.ps1` files with suspicion: depending on your machine's policy you get a security
prompt, a warning, or a flat refusal to run. Files from `git clone` carry no such flag and
simply work.

If you only install one tool for this course, install git.

**Windows** — open **PowerShell as Administrator**: Start menu → type `powershell` →
right-click **Windows PowerShell** → **Run as administrator**. Do it this way every time
you work on the labs, including in class.

Then check whether you already have git:

```bash
git --version
```

If that errors, install it — this is the recommended path on Windows. Windows does not
ship git, but it does ship `winget`, so it is one command and no browser:

```bash
winget install --id Git.Git -e --source winget
```

**Close PowerShell and open a new one** after installing, so it picks up the new command.

An Administrator window starts inside a Windows system folder, so **move to your own
folder first**. `$HOME` works whatever your username is:

```bash
cd $HOME\Documents
```

Then download the course. This creates an `Ai-OFF-and-DEF` folder wherever you are:

```bash
git clone https://github.com/deanbushmiller/Ai-OFF-and-DEF.git
```

Then go into it:

```bash
cd Ai-OFF-and-DEF
```

That last command is relative, so it works no matter where you cloned. **This folder is the
"course folder" every later instruction refers to.** If you lose track of it, find it
again with:

```bash
Get-ChildItem -Path $HOME -Filter Ai-OFF-and-DEF -Directory -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
```

**macOS** — open **Terminal** and run:

```bash
git --version
```

macOS does not ship git either, but typing that command pops up an installer for Apple's
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

Three things to know before you choose this:

1. **The folder is named differently** — `Ai-OFF-and-DEF-main`, not `Ai-OFF-and-DEF`. Every
   path in this guide needs adjusting by hand.
2. **Updates mean downloading and unzipping again**, and remembering to do it.
3. **Windows only:** the extracted scripts carry the Mark of the Web. If PowerShell refuses
   to run `setup.ps1`, clear the flag from inside the course folder:

   ```bash
   Get-ChildItem -Recurse | Unblock-File
   ```

If you hit any of these, installing git is faster than working around them.

### Getting updates later

The course is in beta. If the instructor says to update, from inside the course folder:

```bash
git pull
```

**Do this before each session.** A lab script that misbehaves is often just an old copy —
fixes have shipped mid-course before.

> **Never** paste a command that pipes a downloaded script straight into a shell
> (`irm ... | iex`, `curl ... | bash`), no matter who suggests it. This is a security
> course; running code you have not read is the thing we are here to stop. Every command
> in this course is one you can read first.

---

## Everyone: what you need

- A Mac, Windows or Linux computer. No GPU.
- **Docker Desktop 4.90 or newer.**
- About **2 GB free disk**, 4 GB free RAM.
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
natively — no virtual machine, no WSL, none of the Windows section below applies.

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

## Windows — read this, it is not optional

> **Install git first.** See [Step 0](#step-0--get-the-course-files). On Windows it is
> `winget install --id Git.Git -e --source winget`, and it saves you the Mark-of-the-Web
> problems that come with a downloaded ZIP.

Docker Desktop on Windows does not run on its own. Its engine runs inside **WSL2**, which
needs hardware virtualization. Two extra steps, **in this order**. Installing Docker first
is the usual reason it will not start.

### Step 1 — Install WSL from GitHub, not the Store

<https://github.com/microsoft/WSL/releases>

Take the newest release **not** marked *Pre-release* — 2.7.14 or later — and download:

| Your CPU | File |
|---|---|
| Intel / AMD | `wsl.<version>.x64.msi` |
| Windows on ARM (Snapdragon, Surface) | `wsl.<version>.arm64.msi` |

Run the MSI, then **reboot**. Then, in PowerShell **as Administrator**:

```bash
wsl --update
```

```bash
wsl --shutdown
```

> **Why not `wsl --install`?** That command installs through the Microsoft Store, and the
> Store route fails on VMs, Windows Server, and company-managed machines — usually with an
> unhelpful error. The MSI works in all of those. If `wsl --install` already worked for
> you, you are fine; this is the route that succeeds when it does not.

### Step 2 — Install Docker Desktop 4.90 or newer

<https://www.docker.com/products/docker-desktop/>

**The first launch is slow. Expect several minutes.** Docker builds its Linux disk image
(`ext4.vhdx`) the first time it starts, and the window can look frozen while it does.
**Let it finish.** This happens once; every later start is quick.

### Step 3 — Running Windows inside a virtual machine?

(VMware, VirtualBox, Parallels, Hyper-V)

**a. Enable nested virtualization.** Shut the VM down first — this cannot be changed while
it runs.

| Your VM software | Where |
|---|---|
| VMware | VM Settings → Processors → *Virtualize Intel VT-x/EPT or AMD-V/RVI* |
| VirtualBox | Settings → System → Processor → *Enable Nested VT-x/AMD-V* |
| Parallels | Hardware → CPU & Memory → Advanced → *Enable nested virtualization* |
| Hyper-V | On the **host**, admin PowerShell: `Set-VMProcessor -VMName <name> -ExposeVirtualizationExtensions $true` |

**b. Preallocate the virtual disk.** This one costs 10–20 minutes if you skip it. If your
VM's disk grows on demand — "dynamically allocated", "expanding", "thin provisioned" —
that growth happens *while you wait* during Docker's first start, and it looks exactly
like Docker has hung.

| Your VM software | Set the disk to |
|---|---|
| VMware | *Allocate all disk space now* |
| VirtualBox | *Fixed size*, not *Dynamically allocated* |
| Hyper-V | *Fixed size* VHDX, not *Dynamically expanding* |
| Parallels | Hardware → Hard Disk → uncheck *Expanding disk* |

Give the VM at least **20 GB free**.

### Step 4 — Run the setup script

From inside the course folder, in PowerShell **as Administrator**:

```bash
powershell -ExecutionPolicy Bypass -File .\labs\lab1\setup\setup.ps1
```

If that says the file cannot be found, you are in the wrong folder. Run `pwd` — it should
end in `Ai-OFF-and-DEF`.

It checks virtualization, WSL, Docker, your CPU architecture and your disk space, and tells
you in plain English which one is wrong.

**On real hardware and Docker still will not start?** Virtualization may be off in
firmware. Reboot into BIOS/UEFI and enable **Intel VT-x** or **AMD-V / SVM Mode**.

---

## Download sizes

The labs share container layers, so only the first is a full download.

| | Download |
|---|---|
| Lab 1 | ~190 MB (Apple Silicon) / ~250 MB (Intel) |
| Lab 2 | ~590 MB |
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
| `Docker is installed but not running` | Start it; on Windows work through the WSL and virtualization steps above |
| `Hardware virtualization is not available` | BIOS/UEFI, or nested virtualization in your VM |
| `denied` / `unauthorized` on pull | The instructor has not published that lab yet |
| `WSL kernel version too low` | Windows: `wsl --update` then `wsl --shutdown`, as Administrator |
| `You are not in the 'docker' group` | Linux: `sudo usermod -aG docker $USER`, then **log out and back in** |
| `permission denied ... docker.sock` | Linux: same as above — the group, not the daemon |
