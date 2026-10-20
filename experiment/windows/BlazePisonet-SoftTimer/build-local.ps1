$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$app=Join-Path $root 'src/BlazePisonet.SoftTimer/BlazePisonet.SoftTimer.csproj'
$wd=Join-Path $root 'src/BlazePisonet.SoftTimer.Watchdog/BlazePisonet.SoftTimer.Watchdog.csproj'
dotnet restore $app
if ($LASTEXITCODE -ne 0) { throw "SoftTimer restore failed (dotnet exit code $LASTEXITCODE)." }
dotnet restore $wd
if ($LASTEXITCODE -ne 0) { throw "Watchdog restore failed (dotnet exit code $LASTEXITCODE)." }
dotnet build $app -c Release -warnaserror
if ($LASTEXITCODE -ne 0) { throw "SoftTimer build failed (dotnet exit code $LASTEXITCODE)." }
dotnet build $wd -c Release -warnaserror
if ($LASTEXITCODE -ne 0) { throw "Watchdog build failed (dotnet exit code $LASTEXITCODE)." }
Write-Host 'Build passed.'
