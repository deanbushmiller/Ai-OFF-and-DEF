# Student setup

Do this **before class**. It takes 20–40 minutes the first time, and almost none of that is
work — it is waiting for downloads and one reboot.

The 10 minutes at the start of class covers starting a lab and nothing else.

---

## Everyone: what you need

- A Mac or Windows computer. No GPU.
- **Docker Desktop 4.90 or newer.**
- About **2 GB free disk**, 4 GB free RAM.
- A terminal.

No API key, no ChatGPT or Claude subscription, no Python, no cloud account.

---

## macOS

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Open it and wait for the whale icon in the menu bar to stop animating.
3. Run the lab 1 setup script:

```bash
bash labs/lab1/setup/setup.sh
```

That is all. The script checks everything else and tells you if something is wrong.

---

## Windows — read this, it is not optional

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

```bash
powershell -ExecutionPolicy Bypass -File .\labs\lab1\setup\setup.ps1
```

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
| `WSL kernel version too low` | `wsl --update` then `wsl --shutdown`, as Administrator |
