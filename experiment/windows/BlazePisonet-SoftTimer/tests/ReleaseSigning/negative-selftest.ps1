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

  # Workflow-token boundary: untrusted PR builds must never receive a write-capable token.
  $jobsStart=$workflow.IndexOf('jobs:')
  if ($jobsStart -lt 0) { throw 'Workflow jobs section missing' }
  $workflowPolicy=$workflow.Substring(0,$jobsStart)
  if ($workflowPolicy -notmatch '(?m)^permissions:\r?\n  contents: read\r?$' -or
      $workflowPolicy -match '(?m)^  contents: write\s*$') {
    throw 'Workflow-wide GITHUB_TOKEN must be contents: read only'
  }

  $buildStart=$workflow.IndexOf("  build-windows:")
  $publisherStart=$workflow.IndexOf("  publish-release:")
  if ($buildStart -lt 0 -or $publisherStart -le $buildStart) {
    throw 'A separate gated publish-release job is required after build-windows'
  }
  $buildJob=$workflow.Substring($buildStart,$publisherStart-$buildStart)
  if ($buildJob -notmatch '(?m)^    permissions:\r?\n      contents: read\r?$' -or
      $buildJob -match '(?m)^\s+contents: write\s*$' -or
      $buildJob.Contains('GH_TOKEN:') -or
      $buildJob.Contains('Publish GitHub Release')) {
    throw 'Build job must remain read-only and must not publish'
  }
  if (([regex]::Matches($buildJob,[regex]::Escape('vars.SOFTTIMER_RELEASE_VERSION == env.VERSION'))).Count -ne 3) {
    throw 'All three signing/verification steps must require the approved release version to match VERSION'
  }

  $admissionStart=$workflow.IndexOf("  release-admission:")
  if ($admissionStart -le $buildStart -or $publisherStart -le $admissionStart) {
    throw 'A separate read-only release-admission job is required before the write-capable publisher'
  }
  $admissionJob=$workflow.Substring($admissionStart,$publisherStart-$admissionStart)
  if (-not $admissionJob.Contains('permissions:') -or
      -not $admissionJob.Contains('contents: read') -or
      -not $admissionJob.Contains("github.event_name == 'push'") -or
      -not $admissionJob.Contains("github.ref == 'refs/heads/main'") -or
      -not $admissionJob.Contains("vars.SOFTTIMER_RELEASE_APPROVED == 'true'") -or
      -not $admissionJob.Contains("vars.SOFTTIMER_RELEASE_VERSION != ''") -or
      -not $admissionJob.Contains("vars.SOFTTIMER_RELEASE_VERSION != '0.4.0'") -or
      -not $admissionJob.Contains('steps.version.outputs.approved') -or
      -not $admissionJob.Contains('$VERSION') -or
      -not $admissionJob.Contains('$SOFTTIMER_RELEASE_VERSION') -or
      -not $admissionJob.Contains('approved=false') -or
      -not $admissionJob.Contains('approved=true') -or
      $admissionJob.Contains('contents: write') -or
      $admissionJob.Contains('GH_TOKEN:')) {
    throw 'Release admission must compare the approved version with workflow VERSION using read-only permissions'
  }

  $publisherJob=$workflow.Substring($publisherStart)
  if (-not $publisherJob.Contains('permissions:') -or
      -not $publisherJob.Contains('contents: write') -or
      -not $publisherJob.Contains('actions: read') -or
      -not $publisherJob.Contains('needs: [build-windows, release-admission]') -or
      -not $publisherJob.Contains("if: needs.release-admission.outputs.approved == 'true'") -or
      -not $publisherJob.Contains('actions/download-artifact@v4') -or
      -not $publisherJob.Contains('persist-credentials: false') -or
      -not $publisherJob.Contains('GH_TOKEN: ${{ github.token }}') -or
      -not $publisherJob.Contains('candidate/out/bundle/BlazePisonet.SoftTimer.exe') -or
      -not $publisherJob.Contains('candidate/out/bundle/BlazePisonet.SoftTimer.Watchdog.exe') -or
      -not $publisherJob.Contains('GITHUB_SHA_EXPECTED: ${{ github.sha }}')) {
    throw 'Publisher must be isolated, approved by the read-only version gate, source-pinned and re-admit downloaded artifacts'
  }
  $uploadStart=$workflow.IndexOf('      - name: Upload validated release candidates')
  if ($uploadStart -lt 0 -or $uploadStart -ge $publisherStart) { throw 'Build artifact upload must precede isolated publisher' }
  $uploadBlock=$workflow.Substring($uploadStart,$publisherStart-$uploadStart)
  if (-not $uploadBlock.Contains('out/bundle/BlazePisonet.SoftTimer.exe') -or
      -not $uploadBlock.Contains('out/bundle/BlazePisonet.SoftTimer.Watchdog.exe')) {
    throw 'Publisher verification binaries must be included in the candidate artifact'
  }
  Write-Output 'RELEASE-TOKEN-BOUNDARY: PR build read-only; write token gated by read-only version admission'
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
  # Preview only: do not mutate actual VERSION, create tags or publish assets.
  $future='0.4.1'
  # Construct the Actions expression without embedding YAML template delimiters.
  $template=('{0}{1}{1} env.VERSION {2}{2}' -f [char]36,[char]123,[char]125)
  $start=$workflow.IndexOf('      - name: Upload validated release candidates',[StringComparison]::Ordinal)
  $end=$workflow.IndexOf('  publish-release:',[StringComparison]::Ordinal)
  if ($start -lt 0 -or $end -le $start) { throw 'Upload/publisher blocks missing' }
  $upload=$workflow.Substring($start,$end-$start)
  foreach ($suffix in @(
    ('name: BlazePisonet-SoftTimer-v'+$template+'-win-x64'),
    ('release/BlazePisonet-SoftTimer-Setup-v'+$template+'.exe'),
    ('BlazePisonet-SoftTimer-v'+$template+'-portable-win-x64.zip')
  )) {
    if (-not $upload.Contains($suffix)) { throw "Upload VERSION template missing: $suffix" }
  }
  if ($upload.Contains('v0.4.0')) { throw 'Frozen version hardcoded in upload metadata' }
  $futureUpload=$upload.Replace($template,$future)
  foreach ($name in @(
    'BlazePisonet-SoftTimer-v0.4.1-win-x64',
    'release/BlazePisonet-SoftTimer-Setup-v0.4.1.exe',
    'BlazePisonet-SoftTimer-v0.4.1-portable-win-x64.zip'
  )) {
    if (-not $futureUpload.Contains($name)) { throw "Future-version artifact not derived: $name" }
  }
  if ($futureUpload.Contains('v0.4.0')) { throw 'Future-version artifact points at frozen tag' }
  $notesTemplate='$env:PROJECT_DIR/RELEASE_NOTES_v$env:VERSION.md'
  if (([regex]::Matches($workflow,[regex]::Escape($notesTemplate))).Count -ne 2) {
    throw 'Both packaging and publisher must use version-specific release notes'
  }
  if (([regex]::Matches($workflow,[regex]::Escape('Test-Path -LiteralPath $releaseNotes -PathType Leaf'))).Count -ne 2) {
    throw 'Version-specific notes must fail closed for both packaging and publisher'
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
    if (-not $publisher.Contains($contract)) { throw "Publisher contract missing: $contract" }
  }
  if ($publisher.Contains('$env:TAG') -or $publisher.Contains('RELEASE_NOTES_v0.4.0.md')) {
    throw 'Publisher reuses frozen tag or notes'
  }
  # VERSION is authoritative for both native .NET artifacts and NSIS output.
  foreach ($entry in @(
    @{ Marker='-p:Version=$env:VERSION'; Count=2 },
    @{ Marker='-p:InformationalVersion=$env:VERSION+$source'; Count=2 },
    @{ Marker='-p:IncludeSourceRevisionInInformationalVersion=false'; Count=2 },
    @{ Marker='-warnaserror @versionArgs'; Count=2 },
    @{ Marker=' -o out/app @versionArgs'; Count=1 },
    @{ Marker=' -o out/watchdog @versionArgs'; Count=1 }
  )) {
    if (([regex]::Matches($workflow,[regex]::Escape($entry.Marker))).Count -ne $entry.Count) {
      throw "Release .NET/Watchdog VERSION contract changed: $($entry.Marker)"
    }
  }
  if (-not $workflow.Contains('"/DSOFTTIMER_VERSION=$env:VERSION"') -or
      -not $workflow.Contains('Version-MetadataProbe.ps1')) {
    throw 'NSIS version override or isolated native compiled probe absent'
  }
  $nsis=Get-Content -LiteralPath (Join-Path $PSScriptRoot '../../installer/BlazePisonet-SoftTimer.nsi') -Raw
  foreach ($required in @(
    '!ifndef SOFTTIMER_VERSION',
    'VIProductVersion "',
    'VIAddVersionKey /LANG=1033 "ProductVersion"',
    'OutFile "',
    '"DisplayVersion" "'
  )) {
    if (-not $nsis.Contains($required)) { throw "NSIS version source missing: $required" }
  }
  if (([regex]::Matches($nsis,'0[.]4[.]0')).Count -ne 2) {
    throw 'Frozen installer must retain only documented default 0.4.0 (not hardcoded metadata)'
  }
  Write-Output 'RELEASE-VERSION: build/publish/installer source and isolated native probe contracts PASS'

  Write-Output "RELEASE-PATHS: frozen v0.4.0 unchanged; hypothetical v$future template PASS"

  if ($ActualUnsignedSetup) {
    MustDeny 'actual CI-built unsigned native Setup' {
      & $gate -Mode Verify -InputPaths @($ActualUnsignedSetup,$fakeApp,$fakeWatchdog) -PinnedCertSha256 $pin -ExpectedVersion '0.4.0' -ExpectedSourceCommit ('a'*40)
    } 'lacks trusted embedded Authenticode'
  }
  Write-Output 'RELEASE-SIGN: fail-closed negative controls and signing order PASS; no certificate or signed positive claimed'
} finally {
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
