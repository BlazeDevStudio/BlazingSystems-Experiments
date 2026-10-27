# RELEASE-20261027: fail-closed Authenticode admission for any NEW SoftTimer
# GitHub release. This verifies signatures only; no certificate or private key
# is imported/created, and historical frozen v0.4.0 artifacts are not altered.
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Setup,
  [Parameter(Mandatory = $true)][string]$App,
  [Parameter(Mandatory = $true)][string]$Watchdog,
  [Parameter(Mandatory = $true)][AllowEmptyString()][string]$ExpectedThumbprint
)
$ErrorActionPreference = 'Stop'

# Thumbprints are SHA-1 *certificate identifiers*, not package checksums.
# They must come from an explicitly pinned publisher GitHub repository
# variable; never auto-trust whichever certificate signs the payload.
if ($ExpectedThumbprint -cnotmatch '^[0-9a-fA-F]{40}$') {
  throw 'RELEASE BLOCKED: pinned publisher certificate SHA-1 thumbprint missing or malformed'
}
$pinned = $ExpectedThumbprint.ToUpperInvariant()
foreach ($entry in @(
  @{ Label = 'Setup'; Path = $Setup },
  @{ Label = 'Application'; Path = $App },
  @{ Label = 'Watchdog'; Path = $Watchdog }
)) {
  $item = Get-Item -LiteralPath $entry.Path -ErrorAction Stop
  if ($item.PSIsContainer -or $item.Extension -ine '.exe' -or $item.Length -le 0) {
    throw "RELEASE BLOCKED: $($entry.Label) is not a nonempty executable"
  }
  $signature = Get-AuthenticodeSignature -LiteralPath $item.FullName -ErrorAction Stop
  if ($null -eq $signature -or [string]$signature.Status -cne 'Valid' -or
      $null -eq $signature.SignerCertificate) {
    throw "RELEASE BLOCKED: $($entry.Label) lacks a trusted valid Authenticode signature"
  }
  $got = [string]$signature.SignerCertificate.Thumbprint
  if ($got -cnotmatch '^[0-9a-fA-F]{40}$' -or
      $got.ToUpperInvariant() -cne $pinned) {
    throw "RELEASE BLOCKED: $($entry.Label) signer is not the pinned publisher identity"
  }
}
Write-Output 'RELEASE SIGNATURE PASS: all three executables have valid matching pinned Authenticode identities'
