# testconnect.ps1 - check that this computer can download the course's language model.
#
# Run it from the course folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\testconnect.ps1
# Then copy the ONE line that starts with GHCR-TEST into the class chat.
#
# What it does (about 15-70 seconds, writes nothing to disk):
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

# 1. Latency and packet loss. Some networks block ping; that is fine.
#    Works on Windows PowerShell 5.1 (StatusCode/ResponseTime) and PowerShell 7 (Status/Latency).
$replies = @(Test-Connection $HostName -Count 10 -ErrorAction SilentlyContinue |
             Where-Object { $_.StatusCode -eq 0 -or "$($_.Status)" -eq 'Success' })
$loss = [math]::Round((10 - $replies.Count) * 10)
if ($replies.Count) {
    $latency = [math]::Round(($replies | ForEach-Object {
        if ($null -ne $_.Latency) { $_.Latency } else { $_.ResponseTime }
    } | Measure-Object -Average).Average, 1)
} else {
    $latency = 'blocked'
}

# 2. Speed: 20 MB of the model layer, one connection, anonymous read-only token.
#    curl.exe is built into Windows 10 and 11.
$token = (Invoke-RestMethod "https://ghcr.io/token?scope=repository:${Repo}:pull&service=ghcr.io").token
$null_device = if ($IsLinux -or $IsMacOS) { '/dev/null' } else { 'NUL' }
$bytesPerSec = curl.exe -sL -o $null_device -r 0-20971519 `
    -H "Authorization: Bearer $token" `
    -w "%{speed_download}" `
    "https://ghcr.io/v2/$Repo/blobs/$Layer"
$speed = [double]$bytesPerSec / 1e6

# 3. One line to paste.
#    now=   the lab images as published today (single 1.09 GB model layer)
#    split= the model split into six layers of at most 190 MB (being tested)
#    OK = downloads first time; RETRY = finishes after some restarts; FAIL = cannot finish
$now   = if ($speed -ge 3.6)  { 'OK' } elseif ($speed -ge 1.8)  { 'RETRY' } else { 'FAIL' }
$split = if ($speed -ge 0.63) { 'OK' } elseif ($speed -ge 0.32) { 'RETRY' } else { 'FAIL' }
"GHCR-TEST speed={0:N2}MB/s latency={1}ms loss={2}% now={3} split={4}" -f $speed, $latency, $loss, $now, $split
