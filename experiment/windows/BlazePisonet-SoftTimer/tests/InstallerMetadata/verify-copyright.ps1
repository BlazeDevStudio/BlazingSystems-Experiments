[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SetupPath
)

$ErrorActionPreference = 'Stop'

# Read the native resource as data. Never launch the installer.
$setup = Get-Item -LiteralPath $SetupPath
if ($setup.PSIsContainer) { throw 'SetupPath must identify a native Setup file.' }
$metadata = [Diagnostics.FileVersionInfo]::GetVersionInfo($setup.FullName)

# Keep this test ASCII-only so Windows PowerShell cannot misdecode its oracle.
$expected = 'Copyright ' + [char]0x00A9 + ' 2026 BlazeSystems'
if (-not [string]::Equals($metadata.LegalCopyright, $expected, [StringComparison]::Ordinal)) {
    $points = ($metadata.LegalCopyright.ToCharArray() | ForEach-Object { 'U+{0:X4}' -f [int]$_ }) -join ' '
    throw "Native Setup LegalCopyright differs from the exact owner text: $points"
}

Write-Host 'PASS: native Setup LegalCopyright preserves U+00A9 exactly (no installer execution).'
