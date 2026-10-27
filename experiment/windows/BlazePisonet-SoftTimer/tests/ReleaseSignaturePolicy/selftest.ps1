# RELEASE-20261027 synthetic-only tests of the future-release signature gate.
# No Setup binaries, certificates, private keys, or customer systems used.
$ErrorActionPreference='Stop'
$gate = Join-Path $PSScriptRoot 'require-signed-candidates.ps1'
$work = Join-Path ([System.IO.Path]::GetTempPath()) ("blaze-signature-negative-" + [guid]::NewGuid().ToString('N'))
New-Item -Path $work -ItemType Directory -Force | Out-Null
$pin = '0123456789abcdef0123456789abcdef01234567'
$wrong = 'ffffffffffffffffffffffffffffffffffffffff'
$paths = @('setup.exe', 'app.exe', 'watchdog.exe') | ForEach-Object { Join-Path $work $_ }
$global:BlazeTestStatus = 'Valid'
$global:BlazeTestSigner = $pin
$global:BlazeTestSignatureCount = 0

# A scoped fake result intentionally tests POLICY LOGIC, not trust of a
# synthetic certificate. Real release execution uses the Windows cmdlet.
function Get-AuthenticodeSignature {
  param([string]$LiteralPath)
  $global:BlazeTestSignatureCount++
  [pscustomobject]@{
    Status=$global:BlazeTestStatus
    SignerCertificate=[pscustomobject]@{ Thumbprint=$global:BlazeTestSigner }
  }
}
function Invoke-Gate([string]$Pin) {
  & $gate -Setup $paths[0] -App $paths[1] -Watchdog $paths[2] -ExpectedThumbprint $Pin | Out-Null
}
function Expect-Denied([string]$Label, [scriptblock]$Action) {
  $refused = $false
  try { & $Action } catch { $refused = $true }
  if (-not $refused) { throw "RELEASE-20261027 FAIL: $Label was accepted" }
}
try {
  foreach ($p in $paths) { [System.IO.File]::WriteAllText($p, 'SYNTHETIC FIXTURE - NOT AN EXE') }
  Expect-Denied 'missing publisher pin' { Invoke-Gate '' }
  Expect-Denied 'malformed publisher pin' { Invoke-Gate '1234' }
  $global:BlazeTestSignatureCount=0
  Invoke-Gate $pin
  if ($global:BlazeTestSignatureCount -ne 3) {
    throw 'RELEASE-20261027 FAIL: positive control did not verify all three files'
  }
  $global:BlazeTestSigner=$wrong
  Expect-Denied 'mismatched trusted certificate' { Invoke-Gate $pin }
  $global:BlazeTestSigner=$pin
  foreach ($status in @('NotSigned', 'UnknownError', 'NotTrusted', 'HashMismatch')) {
    $global:BlazeTestStatus=$status
    Expect-Denied "invalid signature status $status" { Invoke-Gate $pin }
  }
  $global:BlazeTestStatus='Valid'
  Remove-Item -LiteralPath $paths[2] -Force
  Expect-Denied 'missing watchdog executable' { Invoke-Gate $pin }
  $workflow=Get-Content -Raw (Join-Path $PSScriptRoot '../../../../../.github/workflows/blazepisonet-softtimer-release.yml')
  # PowerShell String.Split(string) can bind the char[] overload, splitting
  # at individual marker characters rather than the exact workflow step.
  # Use an unambiguous ordinal substring to inspect the actual publish block.
  $marker='      - name: Publish GitHub Release'
  $offset=$workflow.IndexOf($marker, [StringComparison]::Ordinal)
  if ($offset -lt 0) {
    throw 'RELEASE-20261027 FAIL: release publication workflow step missing'
  }
  $publish=$workflow.Substring($offset)
  # Parse only executable command lines, not prose comments mentioning
  # "gh release create" or helper names. An arbitrary comment must never
  # count as a functioning pre-publication identity admission.
  $gateCommand=[regex]::Match($publish, '(?m)^[ \t]*&[ \t]+\$signedGate[ \t]+-Setup[ \t]+')
  $releaseCommand=[regex]::Match($publish, '(?m)^[ \t]*gh[ \t]+release[ \t]+create[ \t]+')
  if (-not $gateCommand.Success -or -not $releaseCommand.Success -or
      -not $publish.Contains('require-signed-candidates.ps1') -or
      -not $publish.Contains('SOFTTIMER_SIGNER_SHA1') -or
      $gateCommand.Index -ge $releaseCommand.Index) {
    throw "RELEASE-20261027 FAIL: actual publisher command lines not ordered (gate=$($gateCommand.Success), publish=$($releaseCommand.Success))"
  }
  Write-Output 'RELEASE-20261027 PASS: missing/invalid/wrong signer or executable blocks publication; three-signature positive POLICY control; future publish guard comes before release create'
} finally {
  Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item Function:Get-AuthenticodeSignature -ErrorAction SilentlyContinue
  Remove-Variable BlazeTestStatus, BlazeTestSigner, BlazeTestSignatureCount -Scope Global -ErrorAction SilentlyContinue
}
