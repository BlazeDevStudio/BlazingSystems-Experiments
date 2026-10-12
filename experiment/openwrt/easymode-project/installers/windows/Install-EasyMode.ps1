$ErrorActionPreference = 'Stop'
$package = Join-Path (Get-Location) 'Update-EasyMode.ps1'
if (Test-Path -LiteralPath $package) { & $package; exit }
throw 'Extract one EasyMode v7 edition archive, then run its Update-EasyMode.bat. The incomplete v5 launcher is retired.'
