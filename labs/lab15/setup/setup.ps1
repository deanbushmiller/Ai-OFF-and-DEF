# ===========================================================================
#  SecLLM Bootcamp - Lab 15 setup  (Windows)
#
#  Mac students: use setup.sh instead.
#
#  Run it: open PowerShell in this folder and type:
#              powershell -ExecutionPolicy Bypass -File .\setup.ps1
#  Hard mode:  powershell -ExecutionPolicy Bypass -File .\setup.ps1 --challenge
#
#  This script installs nothing on your machine. It checks that Docker is
#  ready, works out which image your PC needs, downloads it, runs the lab,
#  and saves your results next to this file.
# ===========================================================================

param([Parameter(ValueFromRemainingArguments = $true)] $ExtraArgs)

$ErrorActionPreference = 'Continue'

$Image     = 'ghcr.io/deanbushmiller/seclm-labs'
$Lab       = 'lab15'
# EMPTY ON PURPOSE. Lab 15 is the last PULLED lab. Lab 16 is INSTRUCTOR-ONLY:
# the instructor runs it live in the final session from a multi-container stack
# that is never published to the student registry. There is no student
# deliverable and nothing for a student to pre-pull. See section 10.
$NextLab   = ''
$Container = 'seclm-lab15-run'
$Here      = Split-Path -Parent $MyInvocation.MyCommand.Path
$Results   = Join-Path $Here 'lab15-results.txt'
$DetectLog = Join-Path $Here 'lab15-detect-log.jsonl'
$DetectCfg = Join-Path $Here 'lab15-detector.json'
if (-not $ExtraArgs) { $ExtraArgs = @() }

function Ok   ($m) { Write-Host "  [ OK ]  $m" -ForegroundColor Green }
function Bad  ($m) { Write-Host "  [FAIL]  $m" -ForegroundColor Red }
function Warn ($m) { Write-Host "  [WARN]  $m" -ForegroundColor Yellow }
function Info ($m) { Write-Host "          $m" }
function Hr        { Write-Host "----------------------------------------------------------------" }

Write-Host ""
Hr
Write-Host "  SecLLM Bootcamp - Lab 15: Defending against AI-scaled attacks"
Write-Host "  Setup and launcher (Windows)"
Hr
Write-Host ""
# Where am I, and can this student control this machine? Both answers matter before
# anything else runs, and both are cheap to get.
#
# The script resolves its own location, so it does not matter where the course was cloned
# or which directory the student launched from. Printing it means a clone that landed
# somewhere unexpected is visible immediately, instead of surfacing later as a confusing
# docker cp failure.
#
# The Administrator check is a CAPABILITY PROBE, not a requirement. This lab runs fine
# unelevated. But installing Docker Desktop and WSL both need elevation, so a student who
# cannot get an Administrator window cannot complete the setup on this machine - and that
# is worth knowing in the first ten seconds of class, not twenty minutes in.
Info "Course folder : $(Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $Here)))"
Info "Results go to : $Here"
$isAdmin = $false
try {
    $isAdmin = ([Security.Principal.WindowsPrincipal] `
        [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
} catch { }
if ($isAdmin) {
    Ok "Running as Administrator"
} else {
    Warn "Not running as Administrator."
    Info "This lab does not need it, so we will carry on. But installing Docker"
    Info "Desktop or WSL does, and if you cannot open an Administrator PowerShell"
    Info "window at all, say so in the class chat now - that is the usual reason a"
    Info "student cannot finish the course on a work laptop."
    Info "Start menu > type powershell > right-click > Run as administrator."
}
if ($Here -like "$env:SystemRoot*") {
    Write-Host ""
    Warn "The course is inside a Windows system folder."
    Info "An Administrator PowerShell window starts in C:\Windows\System32, so cloning"
    Info "without changing directory first puts it here. Writing lab results into a"
    Info "system folder may fail or need elevation every time."
    Info "Move the course somewhere of your own and run this again:"
    Info "    cd `$HOME\Documents"
    Info "    git clone https://github.com/deanbushmiller/Ai-OFF-and-DEF.git"
}
Write-Host ""
Write-Host "  Checking prerequisites..."
Write-Host ""

# --- 1. Docker installed? ---------------------------------------------------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Bad "Docker is not installed."
    Write-Host ""
    Info "Install Docker Desktop 4.90 or newer, then run this again:"
    Info "  https://www.docker.com/products/docker-desktop/"
    Write-Host ""
    Info "IMPORTANT - install WSL FIRST, or Docker will not start."
    Info "  https://github.com/microsoft/WSL/releases  (2.7.14 or newer)"
    Info ""
    Info "AFTER downloading, before Docker will start, you also need WSL."
    Info "Open PowerShell AS ADMINISTRATOR and run:"
    Info "    wsl --install"
    Info "Then REBOOT, and run:"
    Info "    wsl --update"
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}
Ok "Docker is installed  ($((& docker --version) 2>$null))"

# --- 2. Virtualization, then WSL --------------------------------------------
# Order matters. Docker Desktop runs its engine inside WSL2, and WSL2 needs
# hardware virtualization. If virtualization is off there is no point touching
# WSL at all - fix the CPU/VM setting first or nothing else can work.
$virtFirmware = $null
$hypervisor   = $null
$model        = ''
try {
    $virtFirmware = (Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue |
                     Select-Object -First 1).VirtualizationFirmwareEnabled
    $cs           = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue
    $hypervisor   = $cs.HypervisorPresent
    $model        = $cs.Model
} catch { }

$inVM = $model -match 'Virtual|VMware|VirtualBox|KVM|Parallels|Hyper-V'
# Virtualization is usable if the firmware says so, or a hypervisor is already
# running (which is the normal reading inside a VM with nesting enabled).
$virtOk = ($virtFirmware -eq $true) -or ($hypervisor -eq $true)

if ($inVM) {
    Info "This looks like a virtual machine ($model)."
    Write-Host ""
    Warn "VM disk: make sure it is PREALLOCATED, not growing on demand."
    Info "Docker builds a Linux disk image (ext4.vhdx) on first start. If the"
    Info "VM's virtual disk grows on demand, that expansion happens while you"
    Info "wait - 10 to 20 minutes, and it looks like Docker has hung."
    Info "Preallocate the disk BEFORE class:"
    Info "  VMware:     tick 'Allocate all disk space now' when creating the"
    Info "              disk. On an existing VM: VM Settings > Hard Disk >"
    Info "              Utilities > Expand, then Defragment."
    Info "  VirtualBox: use a 'Fixed size' disk, not 'Dynamically allocated'."
    Info "  Hyper-V:    use a 'Fixed size' VHDX, not 'Dynamically expanding'."
    Info "  Parallels:  Hardware > Hard Disk > uncheck 'Expanding disk'."
    Info "Give the VM at least 20 GB free so the image has room."
    Write-Host ""
}

if (-not $virtOk) {
    Bad "Hardware virtualization is not available."
    Write-Host ""
    Info "Docker cannot run without it, and installing WSL will not help"
    Info "until this is fixed. Fix this first:"
    Write-Host ""
    if ($inVM) {
        Info "You are inside a VM, so NESTED virtualization must be turned on."
        Info "SHUT THE VM DOWN first - this cannot be changed while it runs."
        Info "  VMware:     VM Settings > Processors >"
        Info "              'Virtualize Intel VT-x/EPT or AMD-V/RVI'"
        Info "  VirtualBox: Settings > System > Processor >"
        Info "              'Enable Nested VT-x/AMD-V'"
        Info "  Parallels:  Hardware > CPU & Memory > Advanced >"
        Info "              'Enable nested virtualization'"
        Info "  Hyper-V:    on the HOST, in an admin PowerShell:"
        Info "              Set-VMProcessor -VMName <name> ``"
        Info "                -ExposeVirtualizationExtensions `$true"
    } else {
        Info "Reboot into BIOS/UEFI and enable Intel VT-x, or AMD-V / SVM Mode."
    }
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}
Ok "Hardware virtualization is available"

# --- WSL: show the student the real status, then offer to fix it ------------
Write-Host ""
Info "Checking WSL (Docker Desktop runs its engine inside WSL2):"
Write-Host ""
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    & wsl --status
    $wslOk = ($LASTEXITCODE -eq 0)
    # `wsl --version` exists only on the modern Store WSL. If it fails, the
    # kernel is the old inbox build and Docker reports
    # "WSL kernel version too low".
    & wsl --version *> $null
    $wslCurrent = ($LASTEXITCODE -eq 0)
} else {
    Write-Host "    wsl command not found"
    $wslOk = $false; $wslCurrent = $false
}
Write-Host ""

if ($wslOk -and $wslCurrent) {
    Ok "WSL is installed and current"
} else {
    if ($wslOk) {
        Warn "WSL is installed but its kernel looks out of date."
        Info "Docker fails with 'WSL kernel version too low' until you update."
        $action = 'update'
    } else {
        Warn "WSL is not installed or not configured."
        $action = 'install'
    }
    Write-Host ""
    Info "Two ways to fix this. The second one is more reliable."
    Write-Host ""
    Info "  A) Let this script run 'wsl --install' for you (needs Admin)."
    Info "     This goes through the Microsoft Store, which often FAILS on"
    Info "     VMs, Windows Server, and locked-down company machines."
    Write-Host ""
    Info "  B) Install the MSI directly - works where the Store does not:"
    Info "       https://github.com/microsoft/WSL/releases"
    Info "     Take the newest release that is NOT marked pre-release"
    Info "     (2.7.14 or later) and download:"
    Info "       wsl.<version>.x64.msi     for Intel/AMD"
    Info "       wsl.<version>.arm64.msi   for Windows on ARM"
    Info "     Run it, reboot, then run this script again."
    Write-Host ""
    $answer = Read-Host "  Try option A now? [y/N]"
    if ($answer -match '^[Yy]') {
        if ($action -eq 'install') {
            $inner = 'wsl --install; wsl --update; Write-Host ""; ' +
                     'Write-Host "WSL set up. REBOOT, then run setup.ps1 again." ' +
                     '-ForegroundColor Yellow; Read-Host "Press Enter to close"'
        } else {
            $inner = 'wsl --update; wsl --shutdown; Write-Host ""; ' +
                     'Write-Host "WSL updated. Start Docker Desktop, then run setup.ps1 again." ' +
                     '-ForegroundColor Yellow; Read-Host "Press Enter to close"'
        }
        try {
            Start-Process powershell -Verb RunAs -ArgumentList @(
                '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $inner
            ) -ErrorAction Stop
            Write-Host ""
            Ok "An Administrator window is running it now."
            Info "Follow it, REBOOT if it asks, then run this script again."
        } catch {
            Write-Host ""
            Bad "Could not open an elevated window (you may have declined the prompt)."
            Info "Use option B instead - download the MSI from:"
            Info "    https://github.com/microsoft/WSL/releases"
        }
    } else {
        Write-Host ""
        Info "Skipped. Option B, which is the one that works in a VM:"
        Info "    https://github.com/microsoft/WSL/releases"
        Info "    Download wsl.<version>.x64.msi, run it, reboot."
        Write-Host ""
        Info "Or by hand, in PowerShell AS ADMINISTRATOR:"
        Info "    wsl --install     (then REBOOT)"
        Info "    wsl --update"
        Info "    wsl --shutdown"
    }
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

# --- 3. Docker daemon running? ----------------------------------------------
& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Bad "Docker is installed but not running."
    Write-Host ""
    Info "Open Docker Desktop from the Start menu and wait until it says"
    Info "'Engine running', then run this script again."
    Write-Host ""
    Info "If it will not start, work through these in order:"
    Info "  1. WSL missing or out of date? PowerShell AS ADMINISTRATOR:"
    Info "         wsl --install     (then REBOOT)"
    Info "         wsl --update      (fixes 'kernel version too low')"
    Info "         wsl --shutdown    (forces the new kernel to load)"
    Info "  2. In a VM (VMware, VirtualBox, Parallels, Hyper-V)? Nested"
    Info "     virtualization must be enabled in the VM's processor"
    Info "     settings while the VM is powered OFF. See the notes above."
    Info "  3. On real hardware? Enable Intel VT-x or AMD-V in BIOS/UEFI."
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}
Ok "Docker is running"

# --- 4. Detect operating system and hardware --------------------------------
$osCaption = (Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue).Caption
if (-not $osCaption) { $osCaption = 'Windows' }

# RuntimeInformation is the reliable source. PROCESSOR_ARCHITECTURE lies
# inside a 32-bit PowerShell host, which students sometimes launch by accident.
try {
    $osArch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
} catch {
    $osArch = $env:PROCESSOR_ARCHITECTURE
}

switch -Regex ($osArch) {
    'Arm64'     { $Detected = 'arm64'; $Config = 'Windows on ARM (Snapdragon / Surface)'; break }
    'X64|AMD64' { $Detected = 'amd64'; $Config = 'Windows on Intel or AMD';               break }
    default     { $Detected = '';      $Config = "unrecognised hardware: $osArch" }
}

# Cross-check against the Docker engine. The engine is the authority.
$engineArch = (& docker version --format '{{.Server.Arch}}') 2>$null
if ($engineArch) { $engineArch = $engineArch.Trim() }
if ($engineArch -and $Detected -and ($engineArch -ne $Detected)) {
    Warn "Your hardware says $Detected but the Docker engine says $engineArch."
    Info "Trusting the Docker engine. Using $engineArch."
    $Detected = $engineArch
}
if (-not $Detected -and $engineArch) { $Detected = $engineArch }

Ok "Detected: $osCaption  /  $osArch"
Info "Configuration: $Config"
Info "Image needed:  $Detected"

# --- 5. Confirm or override --------------------------------------------------
Write-Host ""
Hr
Write-Host "  Is this right?"
Write-Host ""
Write-Host "    [Enter]  Yes - use $Detected   (detected automatically)"
Write-Host "    1        Windows, Intel or AMD          -> amd64"
Write-Host "    2        Windows on ARM (Snapdragon)    -> arm64"
Hr
switch (Read-Host "  Choice") {
    '1' { $Detected = 'amd64' }
    '2' { $Detected = 'arm64' }
}
Write-Host ""
Ok "Using image architecture: $Detected"

# --- 6. Disk space -----------------------------------------------------------
try {
    # Get-PSDrive is NOT safe here. On a UNC path or a redirected Documents
    # folder, (Get-Item $Here).PSDrive.Name comes back empty, and Get-PSDrive
    # with an empty required parameter makes PowerShell PROMPT FOR INPUT - which
    # a student sees as the script hanging with a blinking cursor, right after
    # "Using image architecture", with no hint what it wants. Hit on a real
    # Windows box, lab 5, 2026-09-13.
    #
    # DriveInfo takes a path root and cannot prompt. On a UNC root it throws,
    # which the surrounding catch swallows - so the check is skipped rather than
    # blocking the lab. A disk-space HINT must never be able to stop the lab.
    $root = [System.IO.Path]::GetPathRoot($Here)
    if (-not $root) { throw 'no path root' }
    $freeGb = [math]::Round((New-Object System.IO.DriveInfo $root).AvailableFreeSpace / 1GB, 1)
    # A VM needs headroom for Docker's ext4.vhdx on top of the lab image.
    $needGb = if ($inVM) { 20 } else { 1 }
    if ($freeGb -lt $needGb) {
        Warn "Only $freeGb GB free; recommend at least $needGb GB."
        if ($inVM) {
            Info "Inside a VM, Docker's disk image needs room to grow. If the"
            Info "virtual disk is thin-provisioned you will wait 10-20 minutes"
            Info "while it expands - or run out of space mid-lab."
        }
    } else {
        Ok "Disk space: $freeGb GB free (want $needGb GB)"
    }
} catch { }

# --- 7. Pull -----------------------------------------------------------------
$Tag = "$Image`:$Lab-$Detected"
Write-Host ""
Hr

# The previous lab offers to pre-pull this image when it finishes. If the
# student took that offer, it is already here and there is nothing to download.
& docker image inspect $Tag *> $null
$alreadyHave = ($LASTEXITCODE -eq 0)

if ($alreadyHave) {
    Write-Host "  Lab image is already on your machine."
    Write-Host "  $Tag"
    Hr
    Write-Host ""
    Ok "No download needed - the previous lab fetched this for you."
} else {
    Write-Host "  Downloading the lab image."
    Write-Host ""
    Write-Host "  If you have done any of labs 3 to 8, 12, 13 or 14 on this"
    Write-Host "  machine, this is a small delta - about 56 KB. Those labs"
    Write-Host "  and this one share the same base, the same Python packages and"
    Write-Host "  the same 1.09 GB language model, byte for byte, so none of it"
    Write-Host "  is downloaded twice. From a clean machine it is about 1.2 GB."
    Write-Host "  $Tag"
    Hr
    Write-Host ""
    & docker pull $Tag
}

if (-not $alreadyHave -and $LASTEXITCODE -ne 0) {
    Write-Host ""
    Bad "Could not download the lab image."
    Write-Host ""
    Info "Most likely causes, in order:"
    Info "  1. The image is not public yet. Tell the instructor you got"
    Info "     'denied' or 'unauthorized' on $Tag"
    Info "  2. No internet connection, or a workplace VPN blocking ghcr.io."
    Info "  3. Docker Desktop is running but has lost its network - quit and"
    Info "     reopen it, then try again."
    Write-Host ""
    Info "Email the error above to the instructor, or post to class Q&A."
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}
Write-Host ""
Ok "Image downloaded"

# --- 8. Run ------------------------------------------------------------------
& docker rm -f $Container *> $null
Write-Host ""
Hr
Write-Host "  This lab runs with NO NETWORK AT ALL - --network none, below."
Write-Host "  That is the lesson, not a precaution: this lab is about spotting"
Write-Host "  traffic leaving a network, so it is given no network to leave."
Write-Host "  The estate telemetry, the mock collector, the detector, the"
Write-Host "  model and the log are all inside the container."
Write-Host "  The collector binds 127.0.0.1:8015 in there. No port is"
Write-Host "  published and none is needed - nothing to open in a browser."
Write-Host ""
Write-Host "  Starting the lab. You will be asked to choose beginner or"
Write-Host "  expert mode. Beginner types 10 checked commands; expert gets"
Write-Host "  a real shell and works from LAB.md."
Write-Host ""
Write-Host "  If you did labs 3 to 8 or 12 to 14 on this machine, the 1.09 GB"
Write-Host "  model layer is already on your disk and is not fetched again."
Write-Host ""
Write-Host "  A local language model runs ONCE in this lab, for about 20"
Write-Host "  seconds on two cores. Everything else is plain Python and runs"
Write-Host "  in well under a second."
Write-Host ""
Write-Host "  One step is SUPPOSED to get past your detector. When you reach"
Write-Host "  it the lab says so. That is the most useful step in the lab."
Hr
Write-Host ""

# --network none, as labs 9 to 14 do. The addendum's rule is that a defend lab
# runs under the control it teaches, and this lab is about detecting traffic
# leaving a network - so it is given no network to leave.
#
# NO -p. Lab 15 runs its mock collector on 127.0.0.1:8015 INSIDE the container,
# started and stopped by the lab itself. A loopback bind inside a container
# cannot be reached from the host - lab 12 measured that - so -p would promise
# a browser view that does not work. There is nothing to publish: the collector
# answers one local process and exits with it.
& docker run -it --network none --name $Container $Tag lab 15 @ExtraArgs
$runRc = $LASTEXITCODE

# --- 9. Recover the transcript and the images --------------------------------
Write-Host ""
& docker cp "$Container`:/labs/lab15/lab15-results.txt" $Results *> $null
if ($LASTEXITCODE -eq 0) {
    Ok "Results saved: $Results"
    Info "Paste the three numbers from the last step into the class chat:"
    Info "lab 7's detector on a real estate, yours after tuning, and what"
    Info "evasion cost the attacker. The middle one is the achievement."
} else {
    Warn "Could not save the results file (lab exit code $runRc)."
    Info "Scroll up in this window to copy the evidence block instead."
}

# The detector's own log comes out too. It is the evidence for this lab and the
# thing worth re-reading after class: every detector that ran, with its true and
# false positive counts. Regenerated on every run.
if (Test-Path $DetectLog) { Remove-Item -Force $DetectLog -ErrorAction SilentlyContinue }
& docker cp "$Container`:/labs/lab15/detect-log.jsonl" $DetectLog *> $null
if ($LASTEXITCODE -eq 0) {
    Ok "Detector log saved: $DetectLog"
    Info "One JSON object per verdict. The field to follow is 'precision':"
    Info "0.0069 with the detector you inherited from lab 7, 1.0000 with"
    Info "the one you tuned - same estate, same beacon, same day."
} else {
    Info "No detector log to copy - the lab did not run this time."
}

# The detector configuration as the student left it, so they can see their own
# two changes next to the log that prompted them.
if (Test-Path $DetectCfg) { Remove-Item -Force $DetectCfg -ErrorAction SilentlyContinue }
& docker cp "$Container`:/labs/lab15/detector.json" $DetectCfg *> $null
if ($LASTEXITCODE -eq 0) {
    Ok "Detector config saved: $DetectCfg"
    Info "Two edits: the threshold you chose from the sweep, and the"
    Info "matching window you widened after the miss. The second one is"
    Info "the interesting change, because it is not a number."
} else {
    Info "No detector config to copy."
}

& docker rm -f $Container *> $null

# --- 10. The hand-off, and there is nothing to download ----------------------
# DELIBERATELY NOT A PRE-PULL. Lab 15 is the last pulled lab. Lab 16 is run by
# the instructor in the final session from a multi-container red-team stack that
# is never deployed to GitHub and never pushed to the student registry. There is
# no student runbook and no student image, so offering
# "docker pull seclm-labs:lab16" here would promise a tag that will
# never exist. $NextLab is empty above for exactly this reason.
Write-Host ""
Hr
Write-Host "  THAT IS THE LAST LAB TO DOWNLOAD"
Hr
Write-Host ""
Info "Labs 1 to 15 are done. There is no lab 16 image and nothing more"
Info "to pull - and that is on purpose."
Write-Host ""
Info "Lab 16 is the red-team process: how you VALIDATE that the controls"
Info "you built in labs 9 to 15 still hold when somebody attacks them."
Info "Your instructor runs it live in the final session, against a target"
Info "stack built for it. Nothing to install, nothing to pull, nothing to"
Info "set up beforehand."
Write-Host ""
Info "You have already run the one-command version of it. Step 6 of this"
Info "lab generated a variant your detector had never seen and tested"
Info "your own control against it. ATLAS calls that AML.M0035, AI Red"
Info "Team. In the last session you watch that same move run end to end"
Info "as a scoped exercise, against a whole stack instead of one detector."

Write-Host ""
Hr
Write-Host "  BEFORE THE LAST SESSION"
Hr
Write-Host ""
Info "Check you have submitted evidence for every defend lab:"
Info "  lab  9  supply chain        lab 13  agents"
Info "  lab 10  RAG ingestion       lab 14  MCP tool calls"
Info "  lab 11  multimodal          lab 15  AI-scaled attacks  <- this one"
Info "  lab 12  injection firewall"
Write-Host ""
Info "Lab 16 builds on all seven. If one is missing, say so in the class"
Info "chat before the session rather than during it."

Write-Host ""
Hr
Write-Host "  Lab 15 complete. Labs 1 to 15 are done."
Hr
Write-Host ""
