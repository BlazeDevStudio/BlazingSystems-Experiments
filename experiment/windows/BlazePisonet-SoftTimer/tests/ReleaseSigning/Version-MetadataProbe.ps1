# Compiles hypothetical future-version Windows metadata. Never signs, installs, uploads,
# publishes, runs generated EXEs, changes VERSION or reuses customer devices.
[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$CurrentVersion,
  [Parameter(Mandatory)][string]$FutureVersion
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($CurrentVersion -cne '0.4.0' -or $FutureVersion -cne '0.4.1') {
  throw 'VERSION-META: only frozen v0.4.0 versus nonshipping hypothetical v0.4.1 is authorized'
}
if (-not $env:NSIS_EXE -or -not (Test-Path -LiteralPath $env:NSIS_EXE -PathType Leaf)) {
  throw 'VERSION-META: real Windows NSIS compiler required'
}
$source=(git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $source -cnotmatch '^[0-9a-f]{40}$') {
  throw 'VERSION-META: full literal Git checkout identity required'
}
$project=$env:PROJECT_DIR
$probe=Join-Path (Get-Location).Path 'out/version-probe'
$appOut=Join-Path $probe 'app'
$watchOut=Join-Path $probe 'watchdog'
$bundle=Join-Path $probe 'bundle'
$normal=@(
  'out/bundle/BlazePisonet.SoftTimer.exe',
  'out/bundle/BlazePisonet.SoftTimer.Watchdog.exe'
)
$prior=@{}
foreach ($file in $normal) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "VERSION-META: current bundle missing $file" }
  $prior[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
}
function Assert-PeMetadata([string]$File,[string]$Version,[string]$Product) {
  if (-not (Test-Path -LiteralPath $File -PathType Leaf)) {
    throw "VERSION-META: compiled executable missing $File"
  }
  $info=[Diagnostics.FileVersionInfo]::GetVersionInfo((Resolve-Path -LiteralPath $File).Path)
  if ($info.FileVersion -cne "$Version.0" -or $info.ProductVersion -cne $Product) {
    throw "VERSION-META: compiled $(Split-Path -Leaf $File) mismatch, file=$($info.FileVersion), product=$($info.ProductVersion), expected=$Version.0/$Product"
  }
  Write-Output "VERSION-META compiled $(Split-Path -Leaf $File): FileVersion=$($info.FileVersion) ProductVersion=$($info.ProductVersion)"
}
try {
  if (Test-Path -LiteralPath $probe) { throw 'VERSION-META: probe directory already exists; refusing overwrite' }
  New-Item -ItemType Directory -Force -Path $appOut,$watchOut,$bundle | Out-Null
  $versionArgs=@(
    "-p:Version=$FutureVersion",
    "-p:FileVersion=$FutureVersion.0",
    "-p:AssemblyVersion=$FutureVersion.0",
    "-p:InformationalVersion=$FutureVersion+$source",
    '-p:IncludeSourceRevisionInInformationalVersion=false'
  )
  $appProject=Join-Path $project 'src/BlazePisonet.SoftTimer/BlazePisonet.SoftTimer.csproj'
  $watchProject=Join-Path $project 'src/BlazePisonet.SoftTimer.Watchdog/BlazePisonet.SoftTimer.Watchdog.csproj'
  # These lightweight apphost PE files are never executed or shipped.
  dotnet publish $appProject -c Release -r win-x64 --self-contained false --no-restore -p:PublishSingleFile=false -p:UseAppHost=true -o $appOut @versionArgs
  if ($LASTEXITCODE -ne 0) { throw 'VERSION-META: hypothetical app compilation failed' }
  dotnet publish $watchProject -c Release -r win-x64 --self-contained false --no-restore -p:PublishSingleFile=false -p:UseAppHost=true -o $watchOut @versionArgs
  if ($LASTEXITCODE -ne 0) { throw 'VERSION-META: hypothetical watchdog compilation failed' }
  $appExe=Join-Path $appOut 'BlazePisonet.SoftTimer.exe'
  $watchExe=Join-Path $watchOut 'BlazePisonet.SoftTimer.Watchdog.exe'
  Assert-PeMetadata $appExe $FutureVersion "$FutureVersion+$source"
  Assert-PeMetadata $watchExe $FutureVersion "$FutureVersion+$source"
  Copy-Item -LiteralPath $appExe -Destination $bundle -Force
  Copy-Item -LiteralPath $watchExe -Destination $bundle -Force
  Push-Location (Join-Path $project 'installer')
  try {
    # Paths are relative to the actual installer .nsi, not this test script.
    & "$env:NSIS_EXE" "/DSOFTTIMER_VERSION=$FutureVersion" '/DSOFTTIMER_PAYLOAD_ROOT=..\..\..\..\out\version-probe\bundle' '/DSOFTTIMER_OUTPUT_ROOT=..\..\..\..\out\version-probe' /V3 'BlazePisonet-SoftTimer.nsi'
    if ($LASTEXITCODE -ne 0) { throw 'VERSION-META: hypothetical native NSIS compilation failed' }
  } finally { Pop-Location }
  $setup=Join-Path $probe "BlazePisonet-SoftTimer-Setup-v$FutureVersion.exe"
  Assert-PeMetadata $setup $FutureVersion $FutureVersion
  pwsh -NoProfile -File (Join-Path $project 'tests/InstallerMetadata/verify-copyright.ps1') -SetupPath $setup
  if ($LASTEXITCODE -ne 0) { throw 'VERSION-META: Unicode metadata regression in hypothetical Setup' }
  $wrongRejected=$false
  try { Assert-PeMetadata $setup $CurrentVersion $CurrentVersion } catch {
    if ($_.Exception.Message -notlike 'VERSION-META: compiled*') { throw }
    $wrongRejected=$true
  }
  if (-not $wrongRejected) { throw 'VERSION-META: wrong-version control was not rejected' }
  foreach ($file in $normal) {
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -cne $prior[$file]) {
      throw "VERSION-META: nonshipping probe changed production bundle $file"
    }
  }
  Write-Output "VERSION-META PASS: actual compiled hypothetical v$FutureVersion App/Watchdog/Setup matched full source SHA, native owner U+00A9, and current v$CurrentVersion bundle hashes remained unchanged. Probe not executed or shipped."
} finally {
  if (Test-Path -LiteralPath $probe) { Remove-Item -LiteralPath $probe -Recurse -Force }
}
