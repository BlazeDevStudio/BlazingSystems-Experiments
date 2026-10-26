$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$Router = Read-Host 'Router IP address or hostname'
if ($Router -notmatch '^[a-zA-Z0-9.:-]+$') { throw 'Invalid router address' }
Write-Host 'This installs the monitoring package only. It does not flash firmware. SSH will request your administrator password.'
$archive = Join-Path $env:TEMP ('easymode-' + [guid]::NewGuid().ToString('N') + '.tar.gz')
try {
 $packages = @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ipk' -File | Select-Object -ExpandProperty Name)
 if ($packages.Count -ne 2) { throw 'Extract exactly one edition archive into its own directory.' }
 if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'PACKAGE-SHA256SUMS'))) { throw 'Package checksum file is missing.' }
 & tar -czf $archive -- @packages install.sh PACKAGE-SHA256SUMS
 if ($LASTEXITCODE) { throw 'Could not prepare package archive' }
 & scp -O $archive "root@${Router}:/tmp/easymode-v7.tar.gz"
 if ($LASTEXITCODE) { throw 'SSH transfer failed; no installation attempted' }
 & ssh "root@$Router" 'umask 077; mkdir -p /tmp/easymode-v7; tar -xzf /tmp/easymode-v7.tar.gz -C /tmp/easymode-v7 && sh /tmp/easymode-v7/install.sh'
 if ($LASTEXITCODE) { throw 'Installation stopped. Read the reported error before retrying.' }
 Write-Host "Installed. Open http://$Router/traffic/"
} finally { if (Test-Path -LiteralPath $archive) { Remove-Item -LiteralPath $archive } }
