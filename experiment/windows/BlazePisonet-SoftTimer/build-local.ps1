$ErrorActionPreference='Stop'
$root=Split-Path -Parent $MyInvocation.MyCommand.Path
$app=Join-Path $root 'src/BlazePisonet.SoftTimer/BlazePisonet.SoftTimer.csproj'
$wd=Join-Path $root 'src/BlazePisonet.SoftTimer.Watchdog/BlazePisonet.SoftTimer.Watchdog.csproj'
dotnet restore $app
dotnet restore $wd
dotnet build $app -c Release -warnaserror
dotnet build $wd -c Release -warnaserror
Write-Host 'Build passed.'
