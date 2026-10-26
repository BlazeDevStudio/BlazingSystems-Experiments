<#
.SYNOPSIS
  Run the R281 sysupgrade compatibility test and clean its RAM-backed staging file.
.DESCRIPTION
  This never flashes the router. It uploads one image to /tmp, verifies SHA-256,
  runs sysupgrade -T, and removes that exact temporary image in a finally block.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Leaf })]
    [string] $Image,
    [ValidatePattern('^[A-Za-z0-9.-]+$')]
    [string] $Router = '192.168.1.1'
)

$ErrorActionPreference = 'Stop'
$resolved = (Resolve-Path -LiteralPath $Image).Path
$expected = (Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant()
$remote = '/tmp/easymode-firmware-test-' + $expected.Substring(0, 12) + '.bin'
$target = "root@${Router}"
$opts = @(
    '-o', 'StrictHostKeyChecking=yes',
    '-o', 'PubkeyAuthentication=no',
    '-o', 'PreferredAuthentications=password',
    '-o', 'ConnectTimeout=8'
)
$uploaded = $false
$passed = $false

try {
    & scp -O @opts $resolved "${target}:${remote}"
    if ($LASTEXITCODE -ne 0) { throw 'Could not upload the firmware test image.' }
    $uploaded = $true

    $line = & ssh @opts $target "sha256sum $remote"
    if ($LASTEXITCODE -ne 0) { throw 'Could not read the uploaded image checksum.' }
    $actual = (($line | Select-Object -Last 1) -split '\s+')[0].ToLowerInvariant()
    if ($actual -ne $expected) { throw 'Uploaded image checksum does not match the local file.' }

    & ssh @opts $target "sysupgrade --ignore-minor-compat-version -n -T $remote"
    if ($LASTEXITCODE -ne 0) { throw 'R281 rejected the firmware compatibility test.' }
    $passed = $true
    Write-Host "PASS: R281 accepted the image for compatibility testing; SHA-256 $expected"
}
finally {
    if ($uploaded) {
        & ssh @opts $target "rm -f $remote"
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not remove $remote from router RAM; remove it manually."
        }
    }
}
if (-not $passed) { exit 1 }
