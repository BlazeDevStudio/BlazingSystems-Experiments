# Future-release-only Authenticode signing and final artifact admission.
# Neither a synthetic test nor an unsigned preview is a production signature.
[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('Sign','Verify')][string]$Mode,
  [Parameter(Mandatory)][string[]]$InputPaths,
  [Parameter(Mandatory)][AllowEmptyString()][string]$PinnedCertSha256,
  [string]$PfxBase64 = '',
  [string]$PfxPassword = '',
  [string]$TimestampUrl = '',
  [string]$PortableZipPath = '',
  [string]$Sha256SumsPath = '',
  [string]$ExpectedVersion = '',
  [string]$ExpectedSourceCommit = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
function Deny([string]$why) { throw "SOFTTIMER RELEASE BLOCKED: $why" }
if ($PinnedCertSha256 -cnotmatch '^[a-fA-F0-9]{64}$') {
  Deny 'approved 64-hex DER certificate SHA256 pin is required'
}
$pin=$PinnedCertSha256.ToUpperInvariant()
if (-not $InputPaths -or $InputPaths.Count -lt 1) { Deny 'binary paths missing' }
if ($Mode -eq 'Sign') {
  if ([string]::IsNullOrWhiteSpace($PfxBase64)) { Deny 'signing PFX secret missing' }
  if ([string]::IsNullOrEmpty($PfxPassword)) { Deny 'signing PFX password missing' }
  if ($TimestampUrl -cnotmatch '^https://[^/\s]+(?:/.*)?$') {
    Deny 'approved HTTPS RFC3161 timestamp URL missing'
  }
}
function Get-Executable([string]$path) {
  $item=Get-Item -LiteralPath $path -ErrorAction Stop
  if ($item.PSIsContainer -or $item.Length -eq 0 -or $item.Extension -ine '.exe' -or
      (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
    Deny "unsafe, empty or non-EXE candidate: $path"
  }
  return $item
}
function Assert-RealSignature([IO.FileInfo]$item) {
  $sig=Get-AuthenticodeSignature -LiteralPath $item.FullName -ErrorAction Stop
  if ($null -eq $sig -or $sig.Status -ne [Management.Automation.SignatureStatus]::Valid -or
      $null -eq $sig.SignerCertificate -or [string]$sig.SignatureType -cne 'Authenticode') {
    Deny "$($item.Name) lacks trusted embedded Authenticode"
  }
  $fingerprint=[Convert]::ToHexString(
    [Security.Cryptography.SHA256]::HashData($sig.SignerCertificate.RawData))
  if ($fingerprint -cne $pin) { Deny "$($item.Name) signer certificate SHA256 mismatch" }
  if ($null -eq $sig.TimeStamperCertificate) { Deny "$($item.Name) lacks trusted timestamp" }
  $codeSigning=$false
  foreach ($ext in $sig.SignerCertificate.Extensions) {
    if ($ext.Oid.Value -eq '2.5.29.37') {
      $eku=[Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new($ext,$ext.Critical)
      foreach ($usage in $eku.EnhancedKeyUsages) {
        if ($usage.Value -ceq '1.3.6.1.5.5.7.3.3') { $codeSigning=$true }
      }
    }
  }
  if (-not $codeSigning) { Deny "$($item.Name) certificate lacks Code Signing EKU" }
}
$files=@($InputPaths | ForEach-Object { Get-Executable $_ })
$seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($file in $files) {
  if (-not $seen.Add($file.FullName)) { Deny 'duplicate signing target path' }
}
if ($Mode -eq 'Sign') {
  $bytes=$null
  $pfxFile=$null
  try {
    try { $bytes=[Convert]::FromBase64String($PfxBase64) }
    catch { Deny 'invalid signing PFX base64 secret' }
    $cert=[Security.Cryptography.X509Certificates.X509Certificate2]::new(
      $bytes,$PfxPassword,
      [Security.Cryptography.X509Certificates.X509KeyStorageFlags]::EphemeralKeySet)
    try {
      if (-not $cert.HasPrivateKey) { Deny 'PFX has no private signing key' }
      $actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($cert.RawData))
      if ($actual -cne $pin) { Deny 'PFX certificate does not match owner-approved SHA256 pin' }
    } finally { $cert.Dispose() }
    $sdk=Join-Path ([Environment]::GetFolderPath('ProgramFilesX86')) 'Windows Kits\10\bin'
    $tool=$null
    if (Test-Path -LiteralPath $sdk) {
      foreach ($dir in @(Get-ChildItem -LiteralPath $sdk -Directory | Sort-Object Name -Descending)) {
        $candidate=Join-Path $dir.FullName 'x64\signtool.exe'
        if (Test-Path -LiteralPath $candidate) { $tool=$candidate; break }
      }
    }
    if (-not $tool) { Deny 'Windows SDK x64 signtool.exe not installed' }
    $scratch=if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }
    $pfxFile=Join-Path $scratch ("blaze-sign-"+[guid]::NewGuid().ToString('N')+'.pfx')
    [IO.File]::WriteAllBytes($pfxFile,$bytes)
    foreach ($file in $files) {
      & $tool sign /fd SHA256 /tr $TimestampUrl /td SHA256 /f $pfxFile /p $PfxPassword $file.FullName
      if ($LASTEXITCODE -ne 0) { Deny "signtool refused $($file.Name)" }
      Assert-RealSignature $file
    }
    Write-Output "SOFTTIMER RELEASE SIGN: $($files.Count) actual EXE signatures validated"
  } finally {
    if ($pfxFile -and (Test-Path -LiteralPath $pfxFile)) { Remove-Item -LiteralPath $pfxFile -Force }
    if ($null -ne $bytes) { [Array]::Clear($bytes,0,$bytes.Length) }
  }
  return
}
if ($files.Count -ne 3) { Deny 'verify requires Setup, app and watchdog EXEs' }
if ($ExpectedVersion -notmatch '^\d+\.\d+\.\d+$' -or
    $ExpectedSourceCommit -cnotmatch '^[a-fA-F0-9]{40}$') {
  Deny 'explicit three-component version and exact 40-hex source commit are required'
}
$commit=$ExpectedSourceCommit.ToLowerInvariant()
foreach ($file in $files) { Assert-RealSignature $file }
foreach ($i in 0..2) {
  $info=$files[$i].VersionInfo
  if ($info.FileVersion -ne "$ExpectedVersion.0") { Deny "$($files[$i].Name) FileVersion mismatch" }
  if ($i -eq 0) {
    if ($info.ProductVersion -ne $ExpectedVersion) { Deny 'Setup ProductVersion mismatch' }
  } else {
    if ($info.ProductVersion -cne "$ExpectedVersion+$commit") {
      Deny "$($files[$i].Name) informational source commit mismatch"
    }
  }
}
$zip=Get-Item -LiteralPath $PortableZipPath -ErrorAction Stop
if ($zip.PSIsContainer -or $zip.Extension -ine '.zip' -or $zip.Length -eq 0 -or
    (($zip.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)) {
  Deny 'portable ZIP missing or unsafe'
}
Add-Type -AssemblyName System.IO.Compression
$archive=[IO.Compression.ZipFile]::OpenRead($zip.FullName)
try {
  foreach ($file in @($files[1],$files[2])) {
    $entries=@($archive.Entries | Where-Object { $_.FullName -ceq $file.Name })
    if ($entries.Count -ne 1) { Deny "$($file.Name) missing or duplicate in portable ZIP" }
    $stream=$entries[0].Open()
    try { $entrySha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($stream)) }
    finally { $stream.Dispose() }
    if ($entrySha -cne (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash) {
      Deny "$($file.Name) portable ZIP differs from signed EXE"
    }
  }
} finally { $archive.Dispose() }
$sumLines=@(Get-Content -LiteralPath $Sha256SumsPath -ErrorAction Stop)
if ($sumLines.Count -ne 2) { Deny 'SHA256SUMS must list exactly Setup and portable ZIP' }
$expectedLines=@(
  "$((Get-FileHash -LiteralPath $files[0].FullName -Algorithm SHA256).Hash.ToLowerInvariant())  $($files[0].Name)",
  "$((Get-FileHash -LiteralPath $zip.FullName -Algorithm SHA256).Hash.ToLowerInvariant())  $($zip.Name)"
)
foreach ($expected in $expectedLines) {
  if (@($sumLines | Where-Object { $_ -ceq $expected }).Count -ne 1) {
    Deny 'SHA256SUMS does not match final signed package bytes'
  }
}
Write-Output 'SOFTTIMER RELEASE VERIFY: signer, timestamp, versions, archive payload and final SHA256SUMS PASS'
