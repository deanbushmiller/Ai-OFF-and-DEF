# check-software.ps1 - connection check, test 3: software needed for the labs.
#   1. git installed
#   2. Docker installed and running
#   3. any other Docker work already on this computer (counted, never changed)
#
# Students run it with the one command on connection-check/README.md.
# Needs no administrator rights. Changes nothing.

$ok = $true
$CourseImage = 'ghcr.io/deanbushmiller/seclm-labs'

Write-Host ""
Write-Host "  ================================================================"
Write-Host "   Test 3 - software needed for the labs"
Write-Host "  ================================================================"

# --- 1. git ----------------------------------------------------------------
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gv = (git --version) -replace 'git version ', ''
    Write-Host "  [OK] git is installed ($gv)"
} else {
    Write-Host "  [!!] git is NOT installed. Install it from https://git-scm.com/download/win"
    $ok = $false
}

# --- 2. Docker -------------------------------------------------------------
$dockerRunning = $false
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "  [!!] Docker is NOT installed. Install Docker Desktop:"
    Write-Host "       https://www.docker.com/products/docker-desktop/"
    $ok = $false
} else {
    $dv = (docker --version) -replace 'Docker version ', '' -replace ',.*', ''
    Write-Host "  [OK] Docker is installed ($dv)"
    $info = (docker info --format '{{.ServerVersion}}' 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Docker is running (engine $info)"
        $dockerRunning = $true
    } elseif ($info -match 'denied|permission') {
        Write-Host "  [!!] Docker is installed, but your account is not allowed to use it."
        Write-Host "       Ask for your account to be added to the 'docker-users' group,"
        Write-Host "       then sign out of Windows and back in."
        $ok = $false
    } else {
        Write-Host "  [!!] Docker is installed but NOT running."
        Write-Host "       Start Docker Desktop from the Start menu, wait until it says"
        Write-Host "       'Engine running', then run this test again."
        $ok = $false
    }
}

# --- 3. Other Docker work already here (counts only) ------------------------
if ($dockerRunning) {
    $images     = @(docker images --format '{{.Repository}}' 2>$null)
    $course     = @($images | Where-Object { $_ -eq $CourseImage }).Count
    $other      = $images.Count - $course
    $containers = @(docker ps -aq 2>$null).Count
    $running    = @(docker ps -q 2>$null).Count
    $volumes    = @(docker volume ls -q 2>$null).Count
    if ($other -eq 0 -and $containers -eq 0 -and $volumes -eq 0) {
        Write-Host "  [i]  No other Docker work on this computer."
    } else {
        Write-Host ("  [i]  Other Docker work on this computer: {0} image(s), {1} container(s)" -f $other, $containers)
        Write-Host ("       ({0} running), {1} volume(s)." -f $running, $volumes)
        Write-Host "       The labs will NOT touch, change or delete any of these."
        Write-Host "       They only add their own images (seclm-labs) and remove their own"
        Write-Host "       containers (named seclm-labN-run)."
    }
    if ($course -gt 0) {
        Write-Host ("  [i]  Course lab images already downloaded: {0}" -f $course)
    }
}

# Tidy up: this script deletes itself.
if ($PSCommandPath) { Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue }

Write-Host ""
if ($ok) {
    Write-Host "  RESULT: PASS - continue on to the next test."
} else {
    Write-Host "  RESULT: STOP - fix the [!!] item(s) above, then run this test again."
}
Write-Host ""
