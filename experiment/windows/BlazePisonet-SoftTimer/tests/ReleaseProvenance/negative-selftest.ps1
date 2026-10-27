# WIN-SIGN-P0 synthetic NEGATIVE controls. No signer, no live EXE, no
# installer execution, no trusted positive signature claim.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$gate=Join-Path $PSScriptRoot 'Verify-ProductionSignature.ps1'
$root=Join-Path ([IO.Path]::GetTempPath()) ('blaze-win-sign-negative-'+[Guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $root -Force
try {
    $setup=Join-Path $root 'BlazePisonet-SoftTimer-Setup-v0.4.0.exe'
    $app=Join-Path $root 'BlazePisonet.SoftTimer.exe'
    $watchdog=Join-Path $root 'BlazePisonet.SoftTimer.Watchdog.exe'
    $zip=Join-Path $root 'candidate.zip'
    [IO.File]::WriteAllBytes($setup,[byte[]](77,90,0,0))
    [IO.File]::WriteAllBytes($app,[byte[]](77,90,0,1))
    [IO.File]::WriteAllBytes($watchdog,[byte[]](77,90,0,2))
    [IO.File]::WriteAllBytes($zip,[byte[]](80,75,3,4))
    $passed=0
    function MustRefuse([string]$Case, [hashtable]$Overrides, [string]$ExpectedReason='') {
        $args=@{
            SetupPath=$setup
            AppPath=$app
            WatchdogPath=$watchdog
            PortableZipPath=$zip
            ExpectedVersion='0.4.0'
            ExpectedSourceCommit=('a'*40)
            ExpectedSignerCertificateSha256=('A'*64)
        }
        foreach ($key in $Overrides.Keys) { $args[$key]=$Overrides[$key] }
        $wasBlocked=$false
        try {
            & $gate @args 1>$null
        } catch {
            $wasBlocked=$true
            if ($ExpectedReason -and -not $_.Exception.Message.Contains($ExpectedReason)) {
                throw "WIN-SIGN-P0 wrong rejection for $Case: $($_.Exception.Message)"
            }
        }
        if (-not $wasBlocked) {
            throw "WIN-SIGN-P0 regression: $Case unexpectedly passed"
        }
        $script:passed++
    }
    MustRefuse 'missing owner signer pin' @{ExpectedSignerCertificateSha256=''} 'approved SHA-256 signer certificate pin'
    MustRefuse 'invalid owner signer pin' @{ExpectedSignerCertificateSha256='not-a-pin'} 'approved SHA-256 signer certificate pin'
    MustRefuse 'invalid release version' @{ExpectedVersion='0.4.0-rc'} 'three-part numeric'
    MustRefuse 'invalid source SHA' @{ExpectedSourceCommit='bad-sha'} 'exact 40-hex Git source commit'
    MustRefuse 'missing Setup binary' @{SetupPath=(Join-Path $root 'missing.exe')}
    MustRefuse 'reused EXE path' @{WatchdogPath=$app}
    MustRefuse 'unsigned fixture EXEs' @{}
    if ($passed -ne 7) {throw 'WIN-SIGN-P0 negative selftest did not execute all controls'}
    Write-Output 'WIN-SIGN-P0 PASS: 7/7 synthetic negative calls refused, four exact fail-reason assertions; signed positive path requires real owner cert and final package'
} finally {
    if (Test-Path -LiteralPath $root) {
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}
