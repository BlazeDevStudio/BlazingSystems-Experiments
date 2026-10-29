# Credential-free negative controls. These cannot prove a real production signature.
[CmdletBinding()]
param([string]$ActualUnsignedSetup = '')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$gate=Join-Path $PSScriptRoot 'Release-Authenticode.ps1'
$pin='0'*64
$root=Join-Path ([IO.Path]::GetTempPath()) ('softtimer-sign-negative-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
function MustDeny([string]$label,[scriptblock]$action,[string]$needle) {
  $rejected=$false
  try { & $action | Out-Null }
  catch {
    if (-not $_.Exception.Message.Contains($needle)) {
      throw "Unexpected rejection for $label : $($_.Exception.Message)"
    }
    $rejected=$true
  }
  if (-not $rejected) { throw "Signing negative control accepted: $label" }
}
try {
  $fake=Join-Path $root 'fixture.exe'
  [IO.File]::WriteAllBytes($fake,[byte[]](77,90,0,0))
  MustDeny 'missing pin' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 '' } '64-hex'
  MustDeny 'malformed pin' { & $gate -Mode Verify -InputPaths @($fake,$fake,$fake) -PinnedCertSha256 '123' } '64-hex'
  MustDeny 'missing PFX' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 $pin } 'PFX secret missing'
  MustDeny 'missing password' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 $pin -PfxBase64 'AA==' } 'PFX password missing'
  MustDeny 'missing timestamp URL' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 $pin -PfxBase64 'AA==' -PfxPassword 'fixture' } 'timestamp URL missing'
  MustDeny 'unapproved http timestamp' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 $pin -PfxBase64 'AA==' -PfxPassword 'fixture' -TimestampUrl 'http://example.invalid' } 'timestamp URL missing'
  MustDeny 'missing EXE' { & $gate -Mode Sign -InputPaths @((Join-Path $root 'missing.exe')) -PinnedCertSha256 $pin -PfxBase64 'AA==' -PfxPassword 'fixture' -TimestampUrl 'https://example.invalid' } 'missing.exe'
  MustDeny 'unsigned fixture' { & $gate -Mode Verify -InputPaths @($fake,$fake,$fake) -PinnedCertSha256 $pin -ExpectedVersion '0.4.0' -ExpectedSourceCommit ('a'*40) } 'lacks trusted embedded Authenticode'

  $workflow=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../../../.github/workflows/blazepisonet-softtimer-release.yml') -Raw
  $markers=@(
    'RELEASE-SIGN test fail-closed negative controls',
    'Publish self-contained Windows x64 EXEs',
    'RELEASE-SIGN sign portable executables before NSIS',
    'Build native Setup EXE',
    'Verify compiled Setup preserves exact Unicode owner text',
    'RELEASE-SIGN sign native Setup after metadata verification',
    'Smoke-test Setup EXE install and uninstall',
    'Build portable EXE-only package and checksums',
    'RELEASE-SIGN verify final signed packages before upload',
    'Upload validated release candidates',
    'Publish GitHub Release'
  )
  $last=-1
  foreach ($marker in $markers) {
    $idx=$workflow.IndexOf("      - name: $marker",[StringComparison]::Ordinal)
    if ($idx -le $last) { throw "Release signing workflow ordering invalid: $marker" }
    $last=$idx
  }
  if (-not $workflow.Contains("vars.SOFTTIMER_RELEASE_APPROVED == 'true'") -or
      -not $workflow.Contains('tests/InstallerMetadata/verify-copyright.ps1') -or
      -not $workflow.Contains('github.event.pull_request.head.sha || github.sha')) {
    throw 'Release approval, Unicode gate or literal checkout lost'
  }
  if ($ActualUnsignedSetup) {
    MustDeny 'actual CI-built unsigned native Setup' {
      & $gate -Mode Verify -InputPaths @($ActualUnsignedSetup,$fake,$fake) -PinnedCertSha256 $pin -ExpectedVersion '0.4.0' -ExpectedSourceCommit ('a'*40)
    } 'lacks trusted embedded Authenticode'
  }
  Write-Output 'RELEASE-SIGN: fail-closed negative controls and signing order PASS; no certificate or signed positive claimed'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
