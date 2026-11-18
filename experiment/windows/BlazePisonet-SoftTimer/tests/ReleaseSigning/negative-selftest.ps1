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
  # Superseded PR checks may be cancelled, but push/manual runs can enter the
  # write-privileged publisher and must not be interrupted mid-release.
  $cancelOnPullRequest=('  cancel-in-progress: {0}{1}{1} github.event_name == ''pull_request'' {2}{2}' -f [char]36,[char]123,[char]125)
  if (-not $workflow.Contains($cancelOnPullRequest) -or
      ([regex]::Matches($workflow,'(?m)^  cancel-in-progress:')).Count -ne 1) {
    throw 'Release workflow must cancel only superseded pull-request checks; publisher-capable runs must be non-cancellable'
  }
  Write-Output 'RELEASE-CONCURRENCY: PR checks cancellable, push/manual publisher-capable runs non-cancellable PASS'

  # Release-capable workflows must pin every external action to a full immutable commit SHA.
  # YAML action steps may use either '- uses:' or a named-step 'uses:' property.
  $actionUseLines = @($workflow -split '\r?\n' | Where-Object { $_ -match '^\s*(?:-\s*)?uses:\s+' })
  if ($actionUseLines.Count -ne 6) {
    throw "Unexpected external action count in release workflow: $($actionUseLines.Count)"
  }
  foreach ($line in $actionUseLines) {
    if ($line -notmatch '^\s*(?:-\s*)?uses:\s+[^@\s]+@[0-9a-f]{40}(?:\s+#.*)?$') {
      throw "Release workflow uses a mutable or non-immutable action reference: $line"
    }
  }
  # Each immutable commit below was read back from its upstream version tag;
  # the corresponding upstream action.yml declares runs.using: node24.
  $requiredActionPins = @(
    @{ Action='actions/checkout'; Version='v7.0.1'; Sha='3d3c42e5aac5ba805825da76410c181273ba90b1'; Count=3 },
    @{ Action='actions/setup-dotnet'; Version='v6.1.0'; Sha='0f4a354dd5547a28c70b7853dbd95d5b67886e73'; Count=1 },
    @{ Action='actions/upload-artifact'; Version='v7.0.2'; Sha='cf430e030ddbb5b0abf93d22962f4752f3646cd9'; Count=1 },
    @{ Action='actions/download-artifact'; Version='v8.0.2'; Sha='9000827ccba6bdab643e8b6fd33ac0654aef8333'; Count=1 }
  )
  foreach ($entry in $requiredActionPins) {
    $pattern = '^\s*(?:-\s*)?uses:\s+' + [regex]::Escape($entry.Action+'@'+$entry.Sha) + '(?:\s+#.*)?$'
    $count = @($actionUseLines | Where-Object { $_ -match $pattern }).Count
    if ($count -ne $entry.Count) {
      throw "Release action pin mismatch for $($entry.Action) $($entry.Version): expected $($entry.Count), found $count"
    }
  }
  Write-Output 'RELEASE-ACTIONS: all external actions pinned to verified immutable Node24-compatible commit SHAs PASS'
  # Every checkout job executes PR-controlled project code; do not persist even
  # the read-only GitHub token in local Git config after the checkout completes.
  $checkoutStepMatches = [regex]::Matches(
    $workflow,
    '(?ms)^[ ]{6}- uses: actions/checkout@[0-9a-f]{40}[^\r\n]*\r?\n(?<block>.*?)(?=^[ ]{6}- |^[ ]{2}[A-Za-z0-9_-]+:|\z)'
  )
  if ($checkoutStepMatches.Count -ne 3) {
    throw "Expected exactly three checkout steps, found $($checkoutStepMatches.Count)"
  }
  foreach ($checkoutStep in $checkoutStepMatches) {
    if ($checkoutStep.Groups['block'].Value -notmatch '(?m)^[ ]{10}persist-credentials: false') {
      throw 'Every release workflow checkout must set persist-credentials: false'
    }
  }
  Write-Output 'RELEASE-CHECKOUT: all three checkout steps disable persisted Git credentials PASS'

  # The PR build executes project code; it must never carry release-write authority.
  # The PR build executes project code; it must never carry release-write authority.
  if ($workflow -notmatch '(?m)^permissions:\r?\n  contents: read\r?$') {
    throw 'Pull-request/build workflow token must be read-only'
  }
  $publisherJobStart=$workflow.IndexOf('  publish-release:',[StringComparison]::Ordinal)
  if ($publisherJobStart -lt 0) { throw 'Dedicated publisher job missing' }
  $buildPart=$workflow.Substring(0,$publisherJobStart)
  $publisherJob=$workflow.Substring($publisherJobStart)
  # Reuse the authoritative immutable pin table so the publisher readback
  # assertion cannot drift from the action-pin regression above.
  $downloadArtifactPins = @($requiredActionPins | Where-Object { $_.Action -eq 'actions/download-artifact' })
  if ($downloadArtifactPins.Count -ne 1) { throw 'Exactly one download-artifact pin is required' }
  $downloadArtifactPin = $downloadArtifactPins[0]
  if ($buildPart.Contains('contents: write') -or $buildPart.Contains('gh release create')) {
    throw 'Untrusted build or PR code retains GitHub release write authority'
  }
  if ($publisherJob -notmatch '(?m)^    permissions:\r?\n      contents: write\r?$' -or
      -not $publisherJob.Contains('needs: build-windows') -or
      -not $publisherJob.Contains("vars.SOFTTIMER_RELEASE_APPROVED == 'true'") -or
      -not $publisherJob.Contains("github.ref == 'refs/heads/main'") -or
      -not $publisherJob.Contains('persist-credentials: false') -or
      -not $publisherJob.Contains('actions/download-artifact@'+$downloadArtifactPin.Sha) -or
      -not $publisherJob.Contains('gh release create $releaseTag')) {
    throw 'Publisher authorization, artifact readback or dependent build gate missing'
  }
  foreach ($name in @(
    'out/bundle/BlazePisonet.SoftTimer.exe',
    'out/bundle/BlazePisonet.SoftTimer.Watchdog.exe'
  )) {
    if (-not $buildPart.Contains('            '+$name)) {
      throw "Publisher re-verification payload missing from uploaded artifact: $name"
    }
  }
  # A skipped publish step is insufficient: a skipped privileged JOB is required.
  # Only valid future builds may export an eligibility output from a job
  # without write access, after package byte validation has completed.
  $expectedOutputTemplate=('{0}{1}{1} steps.release_version_gate.outputs.future_release_eligible {2}{2}' -f [char]36,[char]123,[char]125)
  if (-not $buildPart.Contains('future_release_eligible: '+$expectedOutputTemplate) -or
      -not $buildPart.Contains('id: release_version_gate') -or
      -not $buildPart.Contains('future_release_eligible=false') -or
      -not $buildPart.Contains('future_release_eligible=true') -or
      -not $buildPart.Contains("throw 'RELEASE-ADMISSION: invalid version") -or
      $buildPart.IndexOf('id: release_version_gate',[StringComparison]::Ordinal) -lt
        $buildPart.IndexOf('Upload validated release candidates',[StringComparison]::Ordinal)) {
    throw 'Release candidate eligibility must be derived after artifact validation and fail closed for frozen/invalid versions'
  }
  $jobIfEnd=$publisherJob.IndexOf('    runs-on:',[StringComparison]::Ordinal)
  if ($jobIfEnd -lt 0) { throw 'Publisher job conditional or runner declaration missing' }
  $publisherGuard=$publisherJob.Substring(0,$jobIfEnd)
  $publisherIfLines=@($publisherGuard -split '\r?\n' | Where-Object { $_ -match '^\s*if:' })
  if ($publisherIfLines.Count -ne 1 -or
      -not $publisherIfLines[0].Contains("needs.build-windows.outputs.future_release_eligible == 'true'") -or
      $publisherIfLines[0].Contains('env.VERSION')) {
    throw 'Writable publisher job itself must require validated future-version output, not unsupported env context'
  }
  Write-Output 'RELEASE-ELIGIBILITY: frozen and invalid version deny write-token publisher job PASS'

  Write-Output 'RELEASE-TOKEN: read-only build/PR, separate owner-approved publisher with downloaded signed payload PASS'

  # Preview only: do not mutate actual VERSION, create tags or publish assets.
  $future='0.4.1'
  # Construct the Actions expression without embedding YAML template delimiters.
  $template=('{0}{1}{1} env.VERSION {2}{2}' -f [char]36,[char]123,[char]125)
  $start=$workflow.IndexOf('      - name: Upload validated release candidates',[StringComparison]::Ordinal)
  $end=$workflow.IndexOf('      - name: Publish GitHub Release',[StringComparison]::Ordinal)
  if ($start -lt 0 -or $end -le $start) { throw 'Upload/publisher blocks missing' }
  # Stop at the next job's admission step: its intentional frozen-version
  # denial must not be mistaken for a hardcoded artifact filename.
  $uploadEnd=$workflow.IndexOf('      - name: RELEASE-ADMISSION prevent frozen version',[StringComparison]::Ordinal)
  if ($uploadEnd -le $start -or $uploadEnd -ge $end) {
    throw 'Validated upload block and future-release admission step not in expected order'
  }
  $upload=$workflow.Substring($start,$uploadEnd-$start)

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
    'gh api -i',
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
  # An explicit HTTP 404 lookup is expected for a new release tag.
  # A PowerShell verifier may not update LASTEXITCODE on success; the stale
  # API lookup status must be cleared BEFORE the verifier, never after it.
  $viewIdx=$publisher.IndexOf('$lookupOutput = gh api -i',[StringComparison]::Ordinal)
  # A failed release lookup must be a confirmed HTTP 404, not any CLI/API failure.
  if (-not $publisher.Contains('gh api -i') -or
      -not $publisher.Contains("Groups[1].Value -ne '404'") -or
      -not $publisher.Contains('Release lookup failed') -or
      -not $publisher.Contains('$httpStatuses.Count -ne 1') -or
      $publisher.Contains('if (gh release view $releaseTag *> $null)')) {
    throw 'Publisher must distinguish missing release (404) from API/auth/network failures'
  }
  $resetIdx=$publisher.IndexOf('$global:LASTEXITCODE = 0',[StringComparison]::Ordinal)
  $verifyIdx=$publisher.IndexOf('& $gate -Mode Verify -InputPaths',[StringComparison]::Ordinal)
  $rejectIdx=$publisher.IndexOf('if ($LASTEXITCODE -ne 0) { throw "Publisher final artifact verification failed',[StringComparison]::Ordinal)
  $createIdx=$publisher.IndexOf('gh release create $releaseTag',[StringComparison]::Ordinal)
  if ($viewIdx -lt 0 -or $resetIdx -le $viewIdx -or
      $verifyIdx -le $resetIdx -or $rejectIdx -le $verifyIdx -or
      $createIdx -le $rejectIdx) {
    throw 'Publisher must clear only the stale missing-tag exit, run final Verify, then deny nonzero verifier exit before gh release create'
  }
  # Execute the actual lookup admission statements extracted from the publisher,
  # rather than merely searching the workflow for a string. Synthetic API output
  # must never exercise the real GitHub CLI or the write-privileged release job.
  $lookupStart=$publisher.IndexOf('          $lookupExit = $LASTEXITCODE',[StringComparison]::Ordinal)
  $lookupEnd=$publisher.IndexOf('          # Re-admit the FINAL shipped bytes',[StringComparison]::Ordinal)
  if ($lookupStart -lt 0 -or $lookupEnd -le $lookupStart) { throw 'Publisher lookup decision block missing' }
  $lookupDecision=$publisher.Substring($lookupStart,$lookupEnd-$lookupStart)
  # Substitute only the CLI's captured exit code. The status parser and throws
  # below remain literal source from the production publisher workflow.
  $lookupDecision=$lookupDecision.Replace('$lookupExit = $LASTEXITCODE','$lookupExit = $fixtureExit')
  foreach ($case in @(
    @{ Name='missing tag'; Exit=1; Output="HTTP/2.0 404 Not Found"; Allowed=$true },
    @{ Name='existing tag'; Exit=0; Output="HTTP/2.0 200 OK"; Allowed=$false },
    @{ Name='unauthorized'; Exit=1; Output="HTTP/2.0 401 Unauthorized"; Allowed=$false },
    @{ Name='forbidden'; Exit=1; Output="HTTP/2.0 403 Forbidden"; Allowed=$false },
    @{ Name='server error'; Exit=1; Output="HTTP/2.0 500 Internal Server Error"; Allowed=$false },
    @{ Name='transport failure'; Exit=1; Output="connection refused"; Allowed=$false },
    @{ Name='ambiguous response'; Exit=1; Output="HTTP/2.0 200 OK`nHTTP/2.0 404 Not Found"; Allowed=$false },
    @{ Name='duplicate not-found'; Exit=1; Output="HTTP/2.0 404 Not Found`nHTTP/2.0 404 Not Found"; Allowed=$false },
    @{ Name='successful CLI with 404'; Exit=0; Output="HTTP/2.0 404 Not Found"; Allowed=$false }
  )) {
    $fixtureExit=[int]$case.Exit
    $lookupOutput=[string]$case.Output
    $accepted=$true
    try { & ([scriptblock]::Create($lookupDecision)) | Out-Null }
    catch { $accepted=$false }
    if ($accepted -ne [bool]$case.Allowed) {
      throw "RELEASE-PUBLISHER executable lookup regression: $($case.Name) accepted=$accepted"
    }
  }
  Write-Output 'RELEASE-PUBLISHER: 9 executed synthetic HTTP/CLI lookup decisions PASS (no publication invoked)'
  Write-Output 'RELEASE-PUBLISHER: missing-tag status cleared before verify, nonzero verifier blocks publish PASS'

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
) {
      throw 'Every release workflow checkout must set persist-credentials: false'
    }
  }
  Write-Output 'RELEASE-CHECKOUT: all three checkout steps disable persisted Git credentials PASS'

  # The PR build executes project code; it must never carry release-write authority.
  if ($workflow -notmatch '(?m)^permissions:\r?\n  contents: read\r?$') {
    throw 'Pull-request/build workflow token must be read-only'
  }
  $publisherJobStart=$workflow.IndexOf('  publish-release:',[StringComparison]::Ordinal)
  if ($publisherJobStart -lt 0) { throw 'Dedicated publisher job missing' }
  $buildPart=$workflow.Substring(0,$publisherJobStart)
  $publisherJob=$workflow.Substring($publisherJobStart)
  # Reuse the authoritative immutable pin table so the publisher readback
  # assertion cannot drift from the action-pin regression above.
  $downloadArtifactPins = @($requiredActionPins | Where-Object { $_.Action -eq 'actions/download-artifact' })
  if ($downloadArtifactPins.Count -ne 1) { throw 'Exactly one download-artifact pin is required' }
  $downloadArtifactPin = $downloadArtifactPins[0]
  if ($buildPart.Contains('contents: write') -or $buildPart.Contains('gh release create')) {
    throw 'Untrusted build or PR code retains GitHub release write authority'
  }
  if ($publisherJob -notmatch '(?m)^    permissions:\r?\n      contents: write\r?$' -or
      -not $publisherJob.Contains('needs: build-windows') -or
      -not $publisherJob.Contains("vars.SOFTTIMER_RELEASE_APPROVED == 'true'") -or
      -not $publisherJob.Contains("github.ref == 'refs/heads/main'") -or
      -not $publisherJob.Contains('persist-credentials: false') -or
      -not $publisherJob.Contains('actions/download-artifact@'+$downloadArtifactPin.Sha) -or
      -not $publisherJob.Contains('gh release create $releaseTag')) {
    throw 'Publisher authorization, artifact readback or dependent build gate missing'
  }
  foreach ($name in @(
    'out/bundle/BlazePisonet.SoftTimer.exe',
    'out/bundle/BlazePisonet.SoftTimer.Watchdog.exe'
  )) {
    if (-not $buildPart.Contains('            '+$name)) {
      throw "Publisher re-verification payload missing from uploaded artifact: $name"
    }
  }
  # A skipped publish step is insufficient: a skipped privileged JOB is required.
  # Only valid future builds may export an eligibility output from a job
  # without write access, after package byte validation has completed.
  $expectedOutputTemplate=('{0}{1}{1} steps.release_version_gate.outputs.future_release_eligible {2}{2}' -f [char]36,[char]123,[char]125)
  if (-not $buildPart.Contains('future_release_eligible: '+$expectedOutputTemplate) -or
      -not $buildPart.Contains('id: release_version_gate') -or
      -not $buildPart.Contains('future_release_eligible=false') -or
      -not $buildPart.Contains('future_release_eligible=true') -or
      -not $buildPart.Contains("throw 'RELEASE-ADMISSION: invalid version") -or
      $buildPart.IndexOf('id: release_version_gate',[StringComparison]::Ordinal) -lt
        $buildPart.IndexOf('Upload validated release candidates',[StringComparison]::Ordinal)) {
    throw 'Release candidate eligibility must be derived after artifact validation and fail closed for frozen/invalid versions'
  }
  $jobIfEnd=$publisherJob.IndexOf('    runs-on:',[StringComparison]::Ordinal)
  if ($jobIfEnd -lt 0) { throw 'Publisher job conditional or runner declaration missing' }
  $publisherGuard=$publisherJob.Substring(0,$jobIfEnd)
  $publisherIfLines=@($publisherGuard -split '\r?\n' | Where-Object { $_ -match '^\s*if:' })
  if ($publisherIfLines.Count -ne 1 -or
      -not $publisherIfLines[0].Contains("needs.build-windows.outputs.future_release_eligible == 'true'") -or
      $publisherIfLines[0].Contains('env.VERSION')) {
    throw 'Writable publisher job itself must require validated future-version output, not unsupported env context'
  }
  Write-Output 'RELEASE-ELIGIBILITY: frozen and invalid version deny write-token publisher job PASS'

  Write-Output 'RELEASE-TOKEN: read-only build/PR, separate owner-approved publisher with downloaded signed payload PASS'

  # Preview only: do not mutate actual VERSION, create tags or publish assets.
  $future='0.4.1'
  # Construct the Actions expression without embedding YAML template delimiters.
  $template=('{0}{1}{1} env.VERSION {2}{2}' -f [char]36,[char]123,[char]125)
  $start=$workflow.IndexOf('      - name: Upload validated release candidates',[StringComparison]::Ordinal)
  $end=$workflow.IndexOf('      - name: Publish GitHub Release',[StringComparison]::Ordinal)
  if ($start -lt 0 -or $end -le $start) { throw 'Upload/publisher blocks missing' }
  # Stop at the next job's admission step: its intentional frozen-version
  # denial must not be mistaken for a hardcoded artifact filename.
  $uploadEnd=$workflow.IndexOf('      - name: RELEASE-ADMISSION prevent frozen version',[StringComparison]::Ordinal)
  if ($uploadEnd -le $start -or $uploadEnd -ge $end) {
    throw 'Validated upload block and future-release admission step not in expected order'
  }
  $upload=$workflow.Substring($start,$uploadEnd-$start)

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
    'gh api -i',
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
  # An explicit HTTP 404 lookup is expected for a new release tag.
  # A PowerShell verifier may not update LASTEXITCODE on success; the stale
  # API lookup status must be cleared BEFORE the verifier, never after it.
  $viewIdx=$publisher.IndexOf('$lookupOutput = gh api -i',[StringComparison]::Ordinal)
  # A failed release lookup must be a confirmed HTTP 404, not any CLI/API failure.
  if (-not $publisher.Contains('gh api -i') -or
      -not $publisher.Contains("Groups[1].Value -ne '404'") -or
      -not $publisher.Contains('Release lookup failed') -or
      -not $publisher.Contains('$httpStatuses.Count -ne 1') -or
      $publisher.Contains('if (gh release view $releaseTag *> $null)')) {
    throw 'Publisher must distinguish missing release (404) from API/auth/network failures'
  }
  $resetIdx=$publisher.IndexOf('$global:LASTEXITCODE = 0',[StringComparison]::Ordinal)
  $verifyIdx=$publisher.IndexOf('& $gate -Mode Verify -InputPaths',[StringComparison]::Ordinal)
  $rejectIdx=$publisher.IndexOf('if ($LASTEXITCODE -ne 0) { throw "Publisher final artifact verification failed',[StringComparison]::Ordinal)
  $createIdx=$publisher.IndexOf('gh release create $releaseTag',[StringComparison]::Ordinal)
  if ($viewIdx -lt 0 -or $resetIdx -le $viewIdx -or
      $verifyIdx -le $resetIdx -or $rejectIdx -le $verifyIdx -or
      $createIdx -le $rejectIdx) {
    throw 'Publisher must clear only the stale missing-tag exit, run final Verify, then deny nonzero verifier exit before gh release create'
  }
  # Execute the actual lookup admission statements extracted from the publisher,
  # rather than merely searching the workflow for a string. Synthetic API output
  # must never exercise the real GitHub CLI or the write-privileged release job.
  $lookupStart=$publisher.IndexOf('          $lookupExit = $LASTEXITCODE',[StringComparison]::Ordinal)
  $lookupEnd=$publisher.IndexOf('          # Re-admit the FINAL shipped bytes',[StringComparison]::Ordinal)
  if ($lookupStart -lt 0 -or $lookupEnd -le $lookupStart) { throw 'Publisher lookup decision block missing' }
  $lookupDecision=$publisher.Substring($lookupStart,$lookupEnd-$lookupStart)
  # Substitute only the CLI's captured exit code. The status parser and throws
  # below remain literal source from the production publisher workflow.
  $lookupDecision=$lookupDecision.Replace('$lookupExit = $LASTEXITCODE','$lookupExit = $fixtureExit')
  foreach ($case in @(
    @{ Name='missing tag'; Exit=1; Output="HTTP/2.0 404 Not Found"; Allowed=$true },
    @{ Name='existing tag'; Exit=0; Output="HTTP/2.0 200 OK"; Allowed=$false },
    @{ Name='unauthorized'; Exit=1; Output="HTTP/2.0 401 Unauthorized"; Allowed=$false },
    @{ Name='forbidden'; Exit=1; Output="HTTP/2.0 403 Forbidden"; Allowed=$false },
    @{ Name='server error'; Exit=1; Output="HTTP/2.0 500 Internal Server Error"; Allowed=$false },
    @{ Name='transport failure'; Exit=1; Output="connection refused"; Allowed=$false },
    @{ Name='ambiguous response'; Exit=1; Output="HTTP/2.0 200 OK`nHTTP/2.0 404 Not Found"; Allowed=$false },
    @{ Name='duplicate not-found'; Exit=1; Output="HTTP/2.0 404 Not Found`nHTTP/2.0 404 Not Found"; Allowed=$false },
    @{ Name='successful CLI with 404'; Exit=0; Output="HTTP/2.0 404 Not Found"; Allowed=$false }
  )) {
    $fixtureExit=[int]$case.Exit
    $lookupOutput=[string]$case.Output
    $accepted=$true
    try { & ([scriptblock]::Create($lookupDecision)) | Out-Null }
    catch { $accepted=$false }
    if ($accepted -ne [bool]$case.Allowed) {
      throw "RELEASE-PUBLISHER executable lookup regression: $($case.Name) accepted=$accepted"
    }
  }
  Write-Output 'RELEASE-PUBLISHER: 9 executed synthetic HTTP/CLI lookup decisions PASS (no publication invoked)'
  Write-Output 'RELEASE-PUBLISHER: missing-tag status cleared before verify, nonzero verifier blocks publish PASS'

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
