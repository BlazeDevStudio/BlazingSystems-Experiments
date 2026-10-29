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
  $fakeApp=Join-Path $root 'fixture-app.exe'
  $fakeWatchdog=Join-Path $root 'fixture-watchdog.exe'
  [IO.File]::WriteAllBytes($fakeApp,[byte[]](77,90,0,1))
  [IO.File]::WriteAllBytes($fakeWatchdog,[byte[]](77,90,0,2))
  MustDeny 'missing pin' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 '' } '64-hex'
  MustDeny 'malformed pin' { & $gate -Mode Verify -InputPaths @($fake,$fake,$fake) -PinnedCertSha256 '123' } '64-hex'
  MustDeny 'missing PFX' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 $pin } 'PFX secret missing'
  MustDeny 'missing password' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 $pin -PfxBase64 'AA==' } 'PFX password missing'
  MustDeny 'missing timestamp URL' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 $pin -PfxBase64 'AA==' -PfxPassword 'fixture' } 'timestamp URL missing'
  MustDeny 'unapproved http timestamp' { & $gate -Mode Sign -InputPaths @($fake) -PinnedCertSha256 $pin -PfxBase64 'AA==' -PfxPassword 'fixture' -TimestampUrl 'http://example.invalid' } 'timestamp URL missing'
  MustDeny 'missing EXE' { & $gate -Mode Sign -InputPaths @((Join-Path $root 'missing.exe')) -PinnedCertSha256 $pin -PfxBase64 'AA==' -PfxPassword 'fixture' -TimestampUrl 'https://example.invalid' } 'missing.exe'
  MustDeny 'unsigned fixture' { & $gate -Mode Verify -InputPaths @($fake,$fakeApp,$fakeWatchdog) -PinnedCertSha256 $pin -ExpectedVersion '0.4.0' -ExpectedSourceCommit ('a'*40) } 'lacks trusted embedded Authenticode'

  $workflow=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../../../../.github/workflows/blazepisonet-softtimer-release.yml') -Raw
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
  # Future-version simulation is string-only: no tag, version change, build or publication.
  # Assert that upload metadata/paths, notes and tag use the SAME VERSION.
  $future='0.4.1'
  $template='
    MustDeny 'actual CI-built unsigned native Setup' {
      & $gate -Mode Verify -InputPaths @($ActualUnsignedSetup,$fakeApp,$fakeWatchdog) -PinnedCertSha256 $pin -ExpectedVersion '0.4.0' -ExpectedSourceCommit ('a'*40)
    } 'lacks trusted embedded Authenticode'
  }
  Write-Output 'RELEASE-SIGN: fail-closed negative controls and signing order PASS; no certificate or signed positive claimed'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
+'{{ env.VERSION }}'
  $start=$workflow.IndexOf('      - name: Upload validated release candidates',[StringComparison]::Ordinal)
  $end=$workflow.IndexOf('      - name: Publish GitHub Release',[StringComparison]::Ordinal)
  if ($start -lt 0 -or $end -le $start) { throw 'Upload/publisher blocks missing' }
  $upload=$workflow.Substring($start,$end-$start)
  $expectedUpload=@(
    ('name: BlazePisonet-SoftTimer-v'+$template+'-win-x64'),
    ('release/BlazePisonet-SoftTimer-Setup-v'+$template+'.exe'),
    ('BlazePisonet-SoftTimer-v'+$template+'-portable-win-x64.zip')
  )
  foreach ($entry in $expectedUpload) {
    if (-not $upload.Contains($entry)) { throw "Upload VERSION template missing: $entry" }
  }
  if ($upload.Contains('v0.4.0')) { throw 'Frozen v0.4.0 hardcoding remains in upload block' }
  $expanded=$upload.Replace($template,$future)
  foreach ($name in @(
    'BlazePisonet-SoftTimer-v0.4.1-win-x64',
    'release/BlazePisonet-SoftTimer-Setup-v0.4.1.exe',
    'BlazePisonet-SoftTimer-v0.4.1-portable-win-x64.zip'
  )) {
    if (-not $expanded.Contains($name)) { throw "Hypothetical future upload not derived: $name" }
  }
  if ($expanded.Contains('v0.4.0')) { throw 'Hypothetical future upload uses frozen release version' }
  $notesTemplate='$env:PROJECT_DIR/RELEASE_NOTES_v$env:VERSION.md'
  if (($workflow.Split([string[]]@($notesTemplate),[StringSplitOptions]::None).Count - 1) -ne 2) {
    throw 'Portable and publisher notes must both derive RELEASE_NOTES_vVERSION.md'
  }
  if (($workflow.Split([string[]]@('Test-Path -LiteralPath $releaseNotes -PathType Leaf'),[StringSplitOptions]::None).Count - 1) -ne 2) {
    throw 'Missing-version notes must fail closed in both package and publisher'
  }
  $publisher=$workflow.Substring($end)
  foreach ($contract in @(
    '$releaseTag="softtimer-v$env:VERSION"',
    'gh release view $releaseTag',
    'gh release create $releaseTag',
    '--notes-file $releaseNotes',
    "vars.SOFTTIMER_RELEASE_APPROVED == 'true'",
    "env.VERSION != '0.4.0'"
  )) {
    if (-not $publisher.Contains($contract)) { throw "Publisher future-version policy absent: $contract" }
  }
  if ($publisher.Contains('$env:TAG') -or $publisher.Contains('RELEASE_NOTES_v0.4.0.md')) {
    throw 'Frozen version was hardcoded into future publication'
  }
  Write-Output "RELEASE-PATHS: frozen 0.4.0 unchanged; hypothetical $future upload, notes and tag derivation PASS"

  if ($ActualUnsignedSetup) {
    MustDeny 'actual CI-built unsigned native Setup' {
      & $gate -Mode Verify -InputPaths @($ActualUnsignedSetup,$fakeApp,$fakeWatchdog) -PinnedCertSha256 $pin -ExpectedVersion '0.4.0' -ExpectedSourceCommit ('a'*40)
    } 'lacks trusted embedded Authenticode'
  }
  Write-Output 'RELEASE-SIGN: fail-closed negative controls and signing order PASS; no certificate or signed positive claimed'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
