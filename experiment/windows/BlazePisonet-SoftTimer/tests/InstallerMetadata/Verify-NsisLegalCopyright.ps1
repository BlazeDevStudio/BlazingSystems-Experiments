# SOFTTIMER-NSIS-UNICODE-20261027: check the actual compiled Setup resource.
# Never runs the installer; no synthetic string check can replace a real PE.
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$Setup)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expected = 'Copyright ' + [char]0x00A9 + ' 2026 BlazeSystems'
function Assert-ExactCopyright([string]$Actual) {
    if ($Actual -cne $expected) {
        $points = [string]::Join(' ', @($Actual.ToCharArray() | ForEach-Object {
            'U+{0:X4}' -f [int][char]$_
        }))
        throw "LegalCopyright mismatch: expected exactly Copyright U+00A9 2026 BlazeSystems; actual points: $points"
    }
}

# Nonvacuous positive and observed Â© negative controls, not compiled evidence.
Assert-ExactCopyright $expected
$broken = 'Copyright ' + [char]0x00C2 + [char]0x00A9 + ' 2026 BlazeSystems'
$rejected = $false
try {
    Assert-ExactCopyright $broken
} catch {
    if ($_.Exception.Message -notlike 'LegalCopyright mismatch:*') { throw }
    $rejected = $true
}
if (-not $rejected) { throw 'Malformed U+00C2 U+00A9 synthetic negative was not refused' }

if (-not (Test-Path -LiteralPath $Setup -PathType Leaf)) {
    throw "Compiled native Setup EXE missing: $Setup"
}
$resolved = (Resolve-Path -LiteralPath $Setup).Path
if ([IO.Path]::GetExtension($resolved) -ine '.exe') { throw 'Expected a compiled EXE file' }
$version = [Diagnostics.FileVersionInfo]::GetVersionInfo($resolved)
Assert-ExactCopyright ([string]$version.LegalCopyright)
Write-Output 'SOFTTIMER-NSIS-UNICODE: compiled Setup LegalCopyright exact U+00A9 PASS'
