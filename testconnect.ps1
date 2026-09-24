# testconnect.ps1 - check that this computer can download the course's language model.
#
# Run it from the course folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\testconnect.ps1
# Then copy the ONE line that starts with GHCR-TEST into the class chat.
#
# What it does (up to about 70 seconds, writes nothing to disk):
#   1. Pings the server Docker downloads the lab images from, 10 times.
#   2. Downloads 20 MB of the real model layer over ONE connection - the same
#      request Docker makes - and measures the speed.
#   3. Prints one line with the results and a verdict.
#
# Why the speed matters: GitHub's download link for each image layer expires
# 5-10 minutes after it is issued, and the download is cut when it does. The
# language model is one 1.09 GB layer, so it must arrive at about 1.8 MB/s or
# faster or it can never finish.

# Older Windows PowerShell may not use TLS 1.2 by default; GitHub requires it.
[Net.ServicePointManager]::SecurityProtocol = 'Tls12'

$HostName = 'pkg-containers.githubusercontent.com'
$Repo     = 'deanbushmiller/seclm-labs'
$Layer    = 'sha256:d9ae46c7ff1e789554d81c957ae0b48bcba3f48601761937e6274ebfb57b1e9b'
$Pings    = 10

Write-Host ""
Write-Host "  ================================================================"
Write-Host "   Course connection check"
Write-Host "  ================================================================"
Write-Host "  Please stand by for up to 70 seconds while we test whether the"
Write-Host "  labs will download on your network: speed, latency, and firewall"
Write-Host "  filtering. Nothing is installed or saved."
Write-Host ""

# ---------------------------------------------------------------------------
# 1. Latency and packet loss. Some networks block ping; that is fine.
#    One ping at a time so the bar can move. Works on Windows PowerShell 5.1
#    (StatusCode/ResponseTime) and PowerShell 7 (Status/Latency).
# ---------------------------------------------------------------------------
Write-Host "  [1/2] Latency and packet loss"
Write-Host "        $Pings pings to the course image server ($HostName)."
Write-Host "        High latency or lost packets slow down every download."
$times = @()
for ($i = 1; $i -le $Pings; $i++) {
    $r = Test-Connection $HostName -Count 1 -ErrorAction SilentlyContinue |
         Where-Object { $_.StatusCode -eq 0 -or "$($_.Status)" -eq 'Success' }
    if ($r) {
        $times += $(if ($null -ne $r.Latency) { $r.Latency } else { $r.ResponseTime })
    }
    $bar = ('#' * $i).PadRight($Pings)
    Write-Host -NoNewline ("`r        [{0}] {1}/{2} pings" -f $bar, $i, $Pings)
}
Write-Host ("`r        [{0}] done          " -f ('#' * $Pings))
$loss = [math]::Round(($Pings - $times.Count) * 100 / $Pings)
if ($times.Count) {
    $latency = [math]::Round(($times | Measure-Object -Average).Average, 1)
} else {
    $latency = 'blocked'
    $loss    = 'blocked'
}
Write-Host ""

# ---------------------------------------------------------------------------
# 2. Download speed and firewall filtering: 20 MB of the model layer over one
#    connection, anonymous read-only token. curl.exe (built into Windows 10
#    and 11) draws its own progress bar.
# ---------------------------------------------------------------------------
Write-Host "  [2/2] Download speed and firewall filtering"
Write-Host "        20 MB of the real lab model over one connection - the same way"
Write-Host "        Docker downloads it. A firewall or proxy that blocks the course"
Write-Host "        server shows up here."
$note  = ''
$speed = 0
try {
    $token = (Invoke-RestMethod "https://ghcr.io/token?scope=repository:${Repo}:pull&service=ghcr.io" -TimeoutSec 20 -ErrorAction Stop).token
} catch { $token = $null }
if (-not $token) {
    # ghcr.io could not be reached at all: a firewall or proxy, not a slow line.
    Write-Host "        !! Could not reach ghcr.io"
    $note = ' note=BLOCKED-cannot-reach-ghcr.io(firewall/proxy?)'
} else {
    $null_device = if ($IsLinux -or $IsMacOS) { '/dev/null' } else { 'NUL' }
    Write-Host -NoNewline "        "
    $bytesPerSec = curl.exe -# -L -o $null_device -r 0-20971519 `
        -H "Authorization: Bearer $token" `
        -w "%{speed_download}" `
        "https://ghcr.io/v2/$Repo/blobs/$Layer"
    $speed = [double]$bytesPerSec / 1e6
    if ($speed -eq 0) { $note = ' note=BLOCKED-download-failed(firewall/proxy?)' }
}

Write-Host ""
Write-Host "  ================================================================"
Write-Host "   Done. Copy the line below into the class chat and add your country:"
Write-Host "  ================================================================"
Write-Host ""

# ---------------------------------------------------------------------------
# 3. One line to paste.
#    now=   the lab images as published today (single 1.09 GB model layer)
#    split= the model split into six layers of at most 190 MB (being tested)
#    OK = downloads first time; RETRY = finishes after some restarts; FAIL = cannot finish
# ---------------------------------------------------------------------------
$now   = if ($speed -ge 3.6)  { 'OK' } elseif ($speed -ge 1.8)  { 'RETRY' } else { 'FAIL' }
$split = if ($speed -ge 0.63) { 'OK' } elseif ($speed -ge 0.32) { 'RETRY' } else { 'FAIL' }
"GHCR-TEST speed={0:N2}MB/s latency={1}ms loss={2}% now={3} split={4}{5}" -f $speed, $latency, $loss, $now, $split, $note
Write-Host ""
