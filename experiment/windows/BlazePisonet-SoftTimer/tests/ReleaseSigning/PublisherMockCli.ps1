# Execute the literal publisher run block with a function-scoped fake gh CLI.
# Credential-free: no network, no signing key, no release mutation.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workflowPath = Join-Path $PSScriptRoot '../../../../../.github/workflows/blazepisonet-softtimer-release.yml'
$workflow = Get-Content -LiteralPath $workflowPath -Raw
$marker = '      - name: Publish GitHub Release'
$start = $workflow.IndexOf($marker, [StringComparison]::Ordinal)
if ($start -lt 0) { throw 'Publisher step missing' }
$stepTail = $workflow.Substring($start)
$runMatch = [regex]::Match($stepTail, '(?m)^        run: \\|\\r?\\n')
if (-not $runMatch.Success) { throw 'Publisher executable block missing' }
$scriptTail = $stepTail.Substring($runMatch.Index + $runMatch.Length)
$scriptLines = @()
foreach ($line in ($scriptTail -split "\\r?\\n")) {
  if ($line -and -not $line.StartsWith('          ')) { break }
  if ($line.StartsWith('          ')) { $scriptLines += $line.Substring(10) }
  else { $scriptLines += '' }
}
$body = $scriptLines -join "`n"
if (-not $body.Contains('gh api -i') -or -not $body.Contains('gh release create')) {
  throw 'Expected publisher commands missing'
}
$root = Join-Path ([IO.Path]::GetTempPath()) ('phx-publisher-mock-' + [guid]::NewGuid().ToString('N'))
$oldProject = $env:PROJECT_DIR
$oldVersion = $env:VERSION
$oldRepository = $env:GITHUB_REPOSITORY
try {
  New-Item -ItemType Directory -Force -Path (Join-Path $root 'tests/ReleaseSigning') | Out-Null
  $env:PROJECT_DIR = $root
  $env:VERSION = '0.4.1'
  $env:GITHUB_REPOSITORY = 'fixture/no-network'
  Set-Content -LiteralPath (Join-Path $root 'RELEASE_NOTES_v0.4.1.md') -Value 'SYNTHETIC ONLY'
  $fakeGate = Join-Path $root 'tests/ReleaseSigning/Release-Authenticode.ps1'
  Set-Content -LiteralPath $fakeGate -Value 'param($Mode,$InputPaths,$PinnedCertSha256,$PortableZipPath,$Sha256SumsPath,$ExpectedVersion,$ExpectedSourceCommit); $global:LASTEXITCODE = $global:fixtureVerifierExit'
  function git { $global:LASTEXITCODE = 0; 'a' * 40 }
  function gh {
    if ($args.Count -ge 2 -and $args[0] -eq 'api' -and $args[1] -eq '-i') {
      $global:LASTEXITCODE = $global:fixtureLookupExit
      return $global:fixtureLookupOutput
    }
    if ($args.Count -ge 2 -and $args[0] -eq 'release' -and $args[1] -eq 'create') {
      $global:fixtureCreateCount++
      $global:LASTEXITCODE = 0
      return 'MOCK CREATE ONLY'
    }
    throw 'Unexpected gh command in mocked publisher'
  }
  $cases = @(
    @{ Name='missing tag verifier denies'; Output='HTTP/2.0 404 Not Found'; Exit=1; Verify=7; Create=0 },
    @{ Name='missing tag verifier accepts'; Output='HTTP/2.0 404 Not Found'; Exit=1; Verify=0; Create=1 },
    @{ Name='unauthorized'; Output='HTTP/2.0 401 Unauthorized'; Exit=1; Verify=0; Create=0 },
    @{ Name='forbidden'; Output='HTTP/2.0 403 Forbidden'; Exit=1; Verify=0; Create=0 },
    @{ Name='server error'; Output='HTTP/2.0 500 Internal Server Error'; Exit=1; Verify=0; Create=0 },
    @{ Name='transport'; Output='connection refused'; Exit=1; Verify=0; Create=0 },
    @{ Name='ambiguous'; Output="HTTP/2.0 200 OK`nHTTP/2.0 404 Not Found"; Exit=1; Verify=0; Create=0 },
    @{ Name='duplicate 404'; Output="HTTP/2.0 404 Not Found`nHTTP/2.0 404 Not Found"; Exit=1; Verify=0; Create=0 },
    @{ Name='existing release'; Output='HTTP/2.0 200 OK'; Exit=0; Verify=0; Create=0 }
  )
  foreach ($case in $cases) {
    $global:fixtureLookupOutput = $case.Output
    $global:fixtureLookupExit = $case.Exit
    $global:fixtureVerifierExit = $case.Verify
    $global:fixtureCreateCount = 0
    $denied = $false
    try { & ([scriptblock]::Create($body)) | Out-Null }
    catch { $denied = $true }
    if ($global:fixtureCreateCount -ne $case.Create) {
      throw "Mock publisher $($case.Name): expected $($case.Create) creates, observed $global:fixtureCreateCount"
    }
    if ($denied -eq ($case.Create -eq 1)) {
      throw "Mock publisher $($case.Name): unexpected completion/denial"
    }
  }
  Write-Output 'RELEASE-PUBLISHER-MOCK: 9 actual publisher command-path fixtures PASS; gh was mocked; no publication'
} finally {
  $env:PROJECT_DIR = $oldProject
  $env:VERSION = $oldVersion
  $env:GITHUB_REPOSITORY = $oldRepository
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Variable fixtureLookupOutput,fixtureLookupExit,fixtureVerifierExit,fixtureCreateCount -Scope Global -ErrorAction SilentlyContinue
}
