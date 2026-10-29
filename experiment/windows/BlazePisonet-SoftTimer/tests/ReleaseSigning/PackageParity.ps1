# Native Windows payload parity. This reads package bytes only; no signing or EXE execution.
# Runs before invoking the installed app, and again after portable ZIP/checksums exist.
[CmdletBinding()]
param(
  [Parameter(Mandatory)][ValidateSet('Selftest','Installed','Portable')][string]$Mode,
  [string]$BundlePath='out/bundle',
  [string]$InstallPath='',
  [string]$PortablePath='portable',
  [string]$ZipPath='',
  [string]$SetupPath='',
  [string]$SumsPath='SHA256SUMS'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$payloads=@('BlazePisonet.SoftTimer.exe','BlazePisonet.SoftTimer.Watchdog.exe')
$portableMembers=@(
  'BlazePisonet.SoftTimer.exe',
  'BlazePisonet.SoftTimer.Watchdog.exe',
  'README.md',
  'RELEASE_NOTES.md',
  'docs/ASAPP-BEHAVIOR-MAP.md',
  'docs/INTEGRATION.md',
  'docs/SECURITY.md'
)
function Deny([string]$why) { throw "PACKAGE-PARITY BLOCKED: $why" }
function RequireFile([string]$path) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Deny "missing file: $path" }
  $item=Get-Item -LiteralPath $path -ErrorAction Stop
  if ($item.PSIsContainer -or $item.Length -lt 1 -or
      ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    Deny "empty or linked file: $path"
  }
  return $item
}
function FileHash([string]$path) {
  $item=RequireFile $path
  return (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
}
function CompareBytes([string]$left,[string]$right,[string]$label) {
  $a=RequireFile $left
  $b=RequireFile $right
  if ($a.Length -ne $b.Length -or (FileHash $a.FullName) -cne (FileHash $b.FullName)) {
    Deny "$label differs from build-stage executable bytes"
  }
}
function Check-Installed([string]$bundle,[string]$installed) {
  if (-not $installed) { Deny 'installed directory not specified' }
  foreach ($name in $payloads) {
    CompareBytes (Join-Path $bundle $name) (Join-Path $installed $name) "installed $name"
  }
  Write-Output 'PACKAGE-PARITY installed App+Watchdog SHA256/length equals staged build payloads'
}
function Check-Portable([string]$bundle,[string]$portable,[string]$zipPath,[string]$setup,[string]$manifest) {
  $zipItem=RequireFile $zipPath
  $setupItem=RequireFile $setup
  $expected=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  foreach ($name in $portableMembers) {
    [void]$expected.Add($name)
    [void](RequireFile (Join-Path $portable ($name.Replace('/',[IO.Path]::DirectorySeparatorChar))))
  }
  $actualFiles=@(Get-ChildItem -LiteralPath $portable -Recurse -File -Force)
  if ($actualFiles.Count -ne $portableMembers.Count) { Deny 'unexpected or missing portable staging files' }
  foreach ($file in $actualFiles) {
    if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { Deny 'linked portable file' }
    $relative=[IO.Path]::GetRelativePath((Resolve-Path -LiteralPath $portable).Path,$file.FullName).Replace('\','/')
    if (-not $expected.Contains($relative)) { Deny "unapproved portable member: $relative" }
  }
  foreach ($name in $payloads) {
    CompareBytes (Join-Path $bundle $name) (Join-Path $portable $name) "portable staged $name"
  }
  Add-Type -AssemblyName System.IO.Compression
  $zip=[IO.Compression.ZipFile]::OpenRead($zipItem.FullName)
  try {
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($entry in $zip.Entries) {
      $path=$entry.FullName
      if (-not $path -or $path.StartsWith('/') -or $path.Contains('\') -or
          $path.Contains(':') -or $path.StartsWith('./') -or
          ($path.Split('/') | Where-Object { $_ -eq '..' }).Count -gt 0) {
        Deny "unsafe archive member path: $path"
      }
      if (-not $entry.Name) {
        if ($path -cne 'docs/') { Deny "unapproved archive directory: $path" }
        continue
      }
      if (-not $expected.Contains($path)) { Deny "unapproved archive file: $path" }
      if (-not $seen.Add($path)) { Deny "duplicate archive file: $path" }
      $source=Join-Path $portable ($path.Replace('/',[IO.Path]::DirectorySeparatorChar))
      $input=$entry.Open()
      try {
        $digest=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($input))
      } finally { $input.Dispose() }
      if ($digest -cne (FileHash $source)) { Deny "archive entry SHA256 differs: $path" }
      if ($entry.Length -ne (Get-Item -LiteralPath $source).Length) { Deny "archive member length differs: $path" }
    }
    if ($seen.Count -ne $expected.Count) { Deny 'portable ZIP is missing expected files' }
  } finally { $zip.Dispose() }
  $lines=@(Get-Content -LiteralPath $manifest -ErrorAction Stop)
  if ($lines.Count -ne 2) { Deny 'SHA256SUMS does not list exactly Setup and ZIP' }
  $expectedSums=@(
    ('{0}  {1}' -f (FileHash $setupItem.FullName).ToLowerInvariant(),$setupItem.Name),
    ('{0}  {1}' -f (FileHash $zipItem.FullName).ToLowerInvariant(),$zipItem.Name)
  )
  foreach ($line in $expectedSums) {
    if (@($lines | Where-Object { $_ -ceq $line }).Count -ne 1) {
      Deny 'SHA256SUMS does not match signed/unsigned final package bytes'
    }
  }
  Write-Output "PACKAGE-PARITY portable ZIP exact $($seen.Count)/$($expected.Count) approved files, SHA256SUMS Setup+ZIP and App+Watchdog parity PASS"
}
function MustDeny([string]$label,[scriptblock]$action,[string]$text) {
  $denied=$false
  try { & $action | Out-Null }
  catch {
    if (-not $_.Exception.Message.Contains($text)) {
      throw "Unexpected failure in $label : $($_.Exception.Message)"
    }
    $denied=$true
  }
  if (-not $denied) { throw "PACKAGE-PARITY failed negative control: $label" }
}
function Selftest {
  $temp=Join-Path ([IO.Path]::GetTempPath()) ("softtimer-parity-"+[guid]::NewGuid().ToString('N'))
  $bundle=Join-Path $temp 'bundle'
  $installed=Join-Path $temp 'installed'
  $portable=Join-Path $temp 'portable'
  $docs=Join-Path $portable 'docs'
  $zip=Join-Path $temp 'preview.zip'
  $setup=Join-Path $temp 'Setup.exe'
  $sums=Join-Path $temp 'SHA256SUMS'
  New-Item -ItemType Directory -Force -Path $bundle,$installed,$docs | Out-Null
  function MakeSums {
    @(
      ('{0}  {1}' -f (FileHash $setup).ToLowerInvariant(),(Split-Path -Leaf $setup)),
      ('{0}  {1}' -f (FileHash $zip).ToLowerInvariant(),(Split-Path -Leaf $zip))
    ) | Set-Content -LiteralPath $sums -Encoding ascii
  }
  try {
    [IO.File]::WriteAllBytes($setup,[byte[]](77,90,32,40,41))
    $seed=41
    foreach ($name in $payloads) {
      $bytes=[byte[]](77,90,$seed,88,122)
      [IO.File]::WriteAllBytes((Join-Path $bundle $name),$bytes)
      [IO.File]::WriteAllBytes((Join-Path $installed $name),$bytes)
      [IO.File]::WriteAllBytes((Join-Path $portable $name),$bytes)
      $seed+=1
    }
    [IO.File]::WriteAllText((Join-Path $portable 'README.md'),'README')
    [IO.File]::WriteAllText((Join-Path $portable 'RELEASE_NOTES.md'),'RELEASE')
    foreach ($name in @('ASAPP-BEHAVIOR-MAP.md','INTEGRATION.md','SECURITY.md')) {
      [IO.File]::WriteAllText((Join-Path $docs $name),"DOC $name")
    }
    Compress-Archive -Path (Join-Path $portable '*') -DestinationPath $zip -CompressionLevel Optimal
    MakeSums
    Check-Installed $bundle $installed
    Check-Portable $bundle $portable $zip $setup $sums
    $bad=Join-Path $installed $payloads[0]
    [IO.File]::WriteAllBytes($bad,[byte[]](77,90,255,88,122))
    MustDeny 'modified installed binary' { Check-Installed $bundle $installed } 'installed'
    Copy-Item -LiteralPath (Join-Path $bundle $payloads[0]) -Destination $bad -Force
    $bad=Join-Path $portable $payloads[1]
    [IO.File]::WriteAllBytes($bad,[byte[]](77,90,1,88,122))
    MustDeny 'altered portable EXE' { Check-Portable $bundle $portable $zip $setup $sums } 'portable staged'
    Copy-Item -LiteralPath (Join-Path $bundle $payloads[1]) -Destination $bad -Force
    $lines=@(Get-Content -LiteralPath $sums)
    $lines[0]=('0'*64)+'  Setup.exe'
    $lines | Set-Content -LiteralPath $sums -Encoding ascii
    MustDeny 'incorrect final SHA256SUMS' { Check-Portable $bundle $portable $zip $setup $sums } 'SHA256SUMS'
    MakeSums
    $extra=Join-Path $temp 'inject.txt'
    [IO.File]::WriteAllText($extra,'not approved')
    $archive=[IO.Compression.ZipFile]::Open($zip,[IO.Compression.ZipArchiveMode]::Update)
    try { [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,$extra,'unexpected.txt') }
    finally { $archive.Dispose() }
    MakeSums
    MustDeny 'unexpected ZIP entry' { Check-Portable $bundle $portable $zip $setup $sums } 'unapproved archive file'
    Remove-Item -LiteralPath $zip -Force
    Compress-Archive -Path (Join-Path $portable '*') -DestinationPath $zip -CompressionLevel Optimal
    MakeSums
    $archive=[IO.Compression.ZipFile]::Open($zip,[IO.Compression.ZipArchiveMode]::Update)
    try { [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,(Join-Path $bundle $payloads[0]),$payloads[0]) }
    finally { $archive.Dispose() }
    MakeSums
    MustDeny 'duplicate ZIP entry' { Check-Portable $bundle $portable $zip $setup $sums } 'duplicate archive file'
    Write-Output 'PACKAGE-PARITY SELFTEST PASS: valid bytes, mutated installed/portable EXEs, checksum error, rogue and duplicate ZIP entries refused'
  } finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
  }
}
switch ($Mode) {
  'Selftest' { Selftest }
  'Installed' { Check-Installed $BundlePath $InstallPath }
  'Portable' { Check-Portable $BundlePath $PortablePath $ZipPath $SetupPath $SumsPath }
}
