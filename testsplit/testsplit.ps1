# testsplit.ps1 - INSTRUCTOR TEST: download the six model parts of the split
# lab 12 image (lab12-splittest-amd64) one at a time, with progress, outside Docker.
#
# Run from the course folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\testsplit\testsplit.ps1
#   powershell -ExecutionPolicy Bypass -File .\testsplit\testsplit.ps1 -Parts 1     (first part only)
#
# For each part it shows curl's progress bar, then OK or CUT. A CUT part is
# retried (up to 3 attempts), the way Docker retries a layer. Nothing is saved.
#
# How to read it:
#   all parts OK          the split downloads on this network; if docker pull still
#                         sits at "Pulling fs layer", the problem is Docker on this machine
#   parts CUT, then OK    GitHub's download link expired mid-part; the retry finished it
#   a part CUT 3 times    this network is too slow even for 190 MB parts

param([int]$Parts = 6, [int]$Attempts = 3)

[Net.ServicePointManager]::SecurityProtocol = 'Tls12'
$Repo = 'deanbushmiller/seclm-labs'
$Shards = @(
  @('sha256:b7e83f18d2689008ad17313f9418f27346d849e34269d2ddcce0df8078fd803f', 190209381),
  @('sha256:4493b0e053f93efa4c3fdc5d9a5061940cce68fde1e4717d3de346d1ed34634f', 186026772),
  @('sha256:6646e146359f4ab8fde51c84d166b5d99f9642ea6211ecff8d174fe10606ee34', 181150035),
  @('sha256:6fbe2009c25e470f45bcd78396b0c3eef79f329d35b75ad10f0fefd39cb74bea', 188174566),
  @('sha256:d81f296f8439fd9120b48a00c3054eef3e06cb504249b6a008d798f42829bfa4', 188259357),
  @('sha256:3e99ba9076d815af9c6c9e73bd3ca1bede7cb51dab00ac5ca31ea7937addf8c9', 158570409)
)
$Parts = [math]::Max(1, [math]::Min($Parts, $Shards.Count))
$nul = if ($IsLinux -or $IsMacOS) { '/dev/null' } else { 'NUL' }

function Fmt([double]$s) { '{0}m{1:00}s' -f [math]::Floor($s / 60), [math]::Floor($s % 60) }

Write-Host ""
Write-Host "  ================================================================"
Write-Host "   Split-model download test (lab12-splittest-amd64)"
Write-Host "  ================================================================"
Write-Host "  Downloads $Parts model part(s) of up to 190 MB each, one at a time,"
Write-Host "  the way Docker would. At 0.4 MB/s each part takes about 8 minutes."
Write-Host "  Nothing is saved. Press Ctrl+C to stop at any time."
Write-Host ""

$ok = 0; $tries = 0; $start = Get-Date
for ($i = 0; $i -lt $Parts; $i++) {
    $digest = $Shards[$i][0]; $size = $Shards[$i][1]
    $done = $false
    for ($a = 1; $a -le $Attempts -and -not $done; $a++) {
        $tries++
        Write-Host ("  [part {0}/{1}] {2:N0} MB   attempt {3} of {4}" -f ($i + 1), $Parts, ($size / 1e6), $a, $Attempts)
        try {
            $token = (Invoke-RestMethod "https://ghcr.io/token?scope=repository:${Repo}:pull&service=ghcr.io" -TimeoutSec 20 -ErrorAction Stop).token
        } catch {
            Write-Host "        !! Could not reach ghcr.io (firewall/proxy?)"; continue
        }
        Write-Host -NoNewline "        "
        $t0 = Get-Date
        $out = curl.exe -# -L -o $nul -H "Authorization: Bearer $token" `
            -w "%{size_download} %{speed_download}" "https://ghcr.io/v2/$Repo/blobs/$digest"
        $rc = $LASTEXITCODE
        $secs = ((Get-Date) - $t0).TotalSeconds
        $got, $bps = "$out".Trim() -split ' '
        $got = [double]$got; $mbs = [double]$bps / 1e6
        if ($rc -eq 0 -and $got -eq $size) {
            Write-Host ("        OK    {0:N0} MB in {1}  ({2:N2} MB/s)" -f ($got / 1e6), (Fmt $secs), $mbs)
            $ok++; $done = $true
        } else {
            Write-Host ("        CUT   at {0:N0} of {1:N0} MB after {2}  (curl exit {3}) - link expired or connection dropped" -f ($got / 1e6), ($size / 1e6), (Fmt $secs), $rc)
        }
    }
    Write-Host ""
}

$total = ((Get-Date) - $start).TotalSeconds
Write-Host "  ================================================================"
Write-Host "   Done. Result:"
Write-Host "  ================================================================"
"SPLIT-TEST parts_ok={0}/{1} attempts={2} total_time={3}" -f $ok, $Parts, $tries, (Fmt $total)
Write-Host ""
