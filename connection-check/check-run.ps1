# check-run.ps1 - connection check, test 2:
# can this computer download a script from GitHub and run it, without admin rights?
#
# Students run it with the one command on connection-check/README.md. If this
# text is on screen as output, both download and execution already worked.

$ok = $true
Write-Host ""
Write-Host "  ================================================================"
Write-Host "   Test 2 - can this computer download and run a script?"
Write-Host "  ================================================================"
Write-Host "  [OK] Downloaded a file from GitHub"
Write-Host "  [OK] Ran the downloaded script"

# Administrator? Not required for this test - reported so we know.
$admin = $false
try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $admin = ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
} catch { }
if ($admin) { Write-Host "  [i]  Running as administrator: yes" }
else        { Write-Host "  [i]  Running as administrator: no (that is fine for this test)" }

# Language mode: ConstrainedLanguage means an organisation policy (AppLocker or
# Windows Defender Application Control) restricts PowerShell. The lab setup
# scripts will not run there.
$mode = $ExecutionContext.SessionState.LanguageMode
if ("$mode" -eq 'FullLanguage') {
    Write-Host "  [OK] PowerShell is not restricted ($mode)"
} else {
    Write-Host "  [!!] PowerShell is restricted by your organisation ($mode)"
    $ok = $false
}

# CPU type - the labs ship a separate image for Intel/AMD (AMD64) and ARM (ARM64).
$arch = $env:PROCESSOR_ARCHITECTURE
if (-not $arch) { $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture }
Write-Host ("  [i]  Processor type: {0}    PowerShell {1}" -f $arch, $PSVersionTable.PSVersion)

# Tidy up: this script deletes itself.
if ($PSCommandPath) { Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue }

Write-Host ""
if ($ok) {
    Write-Host "  RESULT: PASS - continue on to the next test."
} else {
    Write-Host "  RESULT: STOP - your computer blocks PowerShell scripts."
    Write-Host "  The labs cannot run on this computer. Tell your instructor"
    Write-Host "  before class, or use a computer you control."
}
Write-Host ""
