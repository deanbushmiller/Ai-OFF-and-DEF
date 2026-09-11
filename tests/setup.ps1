# ===========================================================================
#  SecLLM Bootcamp - Lab 1 setup  (Windows)
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
$Lab       = 'lab1'
$Container = 'seclm-lab1-run'
$Here      = Split-Path -Parent $MyInvocation.MyCommand.Path
$Results   = Join-Path $Here 'lab1-results.txt'
if (-not $ExtraArgs) { $ExtraArgs = @() }

function Ok   ($m) { Write-Host "  [ OK ]  $m" -ForegroundColor Green }
function Bad  ($m) { Write-Host "  [FAIL]  $m" -ForegroundColor Red }
function Warn ($m) { Write-Host "  [WARN]  $m" -ForegroundColor Yellow }
function Info ($m) { Write-Host "          $m" }
function Hr        { Write-Host "----------------------------------------------------------------" }

Write-Host ""
Hr
Write-Host "  SecLLM Bootcamp - Lab 1: Data and model supply chain poisoning"
Write-Host "  Setup and launcher (Windows)"
Hr
Write-Host ""
Write-Host "  Checking prerequisites..."
Write-Host ""

# --- 1. Docker installed? ---------------------------------------------------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Bad "Docker is not installed."
    Write-Host ""
    Info "Install Docker Desktop, then run this script again:"
    Info "  https://www.docker.com/products/docker-desktop/"
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}
Ok "Docker is installed  ($((& docker --version) 2>$null))"

# --- 2. Docker daemon running? ----------------------------------------------
& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Bad "Docker is installed but not running."
    Write-Host ""
    Info "Open Docker Desktop from the Start menu and wait until it says"
    Info "'Engine running', then run this script again."
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}
Ok "Docker is running"

# --- 3. Detect operating system and hardware --------------------------------
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

# --- 4. Confirm or override --------------------------------------------------
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

# --- 5. Disk space -----------------------------------------------------------
try {
    $freeGb = [math]::Round((Get-PSDrive (Get-Item $Here).PSDrive.Name).Free / 1GB, 1)
    if ($freeGb -lt 2) { Warn "Only $freeGb GB free. The lab needs about 2 GB. It may fail." }
    else               { Ok   "Disk space: $freeGb GB free (need ~2 GB)" }
} catch { }

# --- 6. Pull -----------------------------------------------------------------
$Tag = "$Image`:$Lab-$Detected"
Write-Host ""
Hr
Write-Host "  Downloading the lab image. About 190-250 MB, usually 1-3 minutes."
Write-Host "  $Tag"
Hr
Write-Host ""

& docker pull $Tag
if ($LASTEXITCODE -ne 0) {
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
    Info "Contact the instructor through GitHub with the error above."
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}
Write-Host ""
Ok "Image downloaded"

# --- 7. Run ------------------------------------------------------------------
& docker rm -f $Container *> $null
Write-Host ""
Hr
Write-Host "  Starting the lab. You will TYPE five commands."
Write-Host "  Read each one before you run it."
Hr
Write-Host ""

& docker run -it --name $Container $Tag lab 1 @ExtraArgs
$runRc = $LASTEXITCODE

# --- 8. Recover the transcript ----------------------------------------------
Write-Host ""
& docker cp "$Container`:/labs/lab1/lab1-results.txt" $Results *> $null
if ($LASTEXITCODE -eq 0) {
    Ok "Results saved: $Results"
    Info "Paste BOTH scan summaries into the class chat - clean and poisoned."
} else {
    Warn "Could not save the results file (lab exit code $runRc)."
    Info "Scroll up in this window to copy your scan output instead."
}

& docker rm -f $Container *> $null
Write-Host ""
Hr
Write-Host "  Lab 1 complete. The image stays on your machine for the next lab."
Hr
Write-Host ""
Read-Host "Press Enter to close"
