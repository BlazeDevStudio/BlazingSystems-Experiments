# WIN-SIGN-P0-20261027. Windows release-only Authenticode/provenance gate.
# This NEVER signs, runs, installs, or alters packages. The caller MUST
# provide the real independently approved production certificate SHA-256.
# Synthetic/dev signing identities are not an acceptable substitute.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SetupPath,
    [Parameter(Mandatory=$true)][string]$AppPath,
    [Parameter(Mandatory=$true)][string]$WatchdogPath,
    [Parameter(Mandatory=$true)][string]$PortableZipPath,
    [Parameter(Mandatory=$true)][string]$ExpectedVersion,
    [Parameter(Mandatory=$true)][string]$ExpectedSourceCommit,
    [Parameter(Mandatory=$true)][AllowEmptyString()][string]$ExpectedSignerCertificateSha256
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Deny([string]$Why) {
    throw "WIN-SIGN-P0 BLOCKED: $Why"
}
if ($ExpectedVersion -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
    Deny 'release version must be an explicit three-part numeric value'
}
if ($ExpectedSourceCommit -cnotmatch '^[A-Fa-f0-9]{40}$') {
    Deny 'exact 40-hex Git source commit is required for Windows package provenance'
}
$expectedCommit = $ExpectedSourceCommit.ToLowerInvariant()
if ($ExpectedSignerCertificateSha256 -cnotmatch '^[A-Fa-f0-9]{64}$') {
    Deny 'an independently approved SHA-256 signer certificate pin is mandatory'
}
$pin = $ExpectedSignerCertificateSha256.ToUpperInvariant()
$files = @(
    @{ Name='Setup'; Path=$SetupPath },
    @{ Name='SoftTimer'; Path=$AppPath },
    @{ Name='Watchdog'; Path=$WatchdogPath }
)
$seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($file in $files) {
    $item = Get-Item -LiteralPath $file.Path -ErrorAction Stop
    if ($item.PSIsContainer -or $item.Length -le 0 -or
        ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        Deny "$($file.Name) must be a nonempty, regular, nonsymlink EXE"
    }
    if ([IO.Path]::GetExtension($item.Name) -ine '.exe' -or -not $seen.Add($item.FullName)) {
        Deny "$($file.Name) has an unsafe or reused path"
    }
    $file['Item'] = $item
    # A matching filename or AssemblyVersion does not prove resource metadata.
    $expectedFileVersion = "$ExpectedVersion.0"
    $info = $item.VersionInfo
    if ($info.FileVersion -ne $expectedFileVersion) {
        Deny "$($file.Name) file version mismatch"
    }
    # NSIS embeds plain ProductVersion; .NET 8 SDK appends the full source
    # revision to ProductVersion. Require the EXACT checkout SHA, not merely
    # a matching major/minor version or an arbitrary +commit suffix.
    if ($file.Name -eq 'Setup') {
        if ($info.ProductVersion -ne $ExpectedVersion -and
            $info.ProductVersion -ne $expectedFileVersion) {
            Deny 'Setup product version mismatch'
        }
    } else {
        $expectedProductVersion = "$ExpectedVersion+$expectedCommit"
        if ($info.ProductVersion -cne $expectedProductVersion) {
            Deny "$($file.Name) informational version does not match exact Git source commit"
        }
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $item.FullName -ErrorAction Stop
    if ($signature.Status -ne [System.Management.Automation.SignatureStatus]::Valid -or
        $null -eq $signature.SignerCertificate) {
        Deny "$($file.Name) is not trusted Authenticode-signed"
    }
    # Catalog trust on this runner is not a transportable signature on a
    # downloaded EXE. Require an EMBEDDED Authenticode signature.
    if ($signature.SignatureType.ToString() -cne 'Authenticode') {
        Deny "$($file.Name) relies on catalog trust instead of an embedded signature"
    }
    $actualPin = [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($signature.SignerCertificate.RawData))
    if ($actualPin -cne $pin) {
        Deny "$($file.Name) signer differs from approved certificate"
    }
    # Require a time-stamped signature to remain verifiable after expiry.
    if ($null -eq $signature.TimeStamperCertificate) {
        Deny "$($file.Name) lacks an Authenticode timestamp"
    }
    $codeSigningEku = $false
    foreach ($extension in $signature.SignerCertificate.Extensions) {
        if ($extension.Oid.Value -eq '2.5.29.37') {
            $decoded = [Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new($extension, $extension.Critical)
            foreach ($usage in $decoded.EnhancedKeyUsages) {
                if ($usage.Value -ceq '1.3.6.1.5.5.7.3.3') {
                    $codeSigningEku = $true
                }
            }
        }
    }
    if (-not $codeSigningEku) {
        Deny "$($file.Name) certificate does not permit code signing"
    }
}
# The portable archive must embed the SAME signed application/watchdog bytes,
# not stale unsigned copies from before signing. Read as data: never extract
# or execute, and never trust a ZIP filename without hashing its contents.
$zipFile = Get-Item -LiteralPath $PortableZipPath -ErrorAction Stop
if ($zipFile.PSIsContainer -or $zipFile.Length -le 0 -or
    ($zipFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
    $zipFile.Extension -ine '.zip') {
    Deny 'portable archive must be a nonempty regular ZIP'
}
Add-Type -AssemblyName System.IO.Compression
$archive = [System.IO.Compression.ZipFile]::OpenRead($zipFile.FullName)
try {
    foreach ($file in $files | Where-Object { $_.Name -ne 'Setup' }) {
        $expectedName = $file['Item'].Name
        $matches = @($archive.Entries | Where-Object { $_.FullName -ceq $expectedName })
        if ($matches.Count -ne 1) {
            Deny "$($file.Name) portable archive identity missing or ambiguous"
        }
        $stream = $matches[0].Open()
        try {
            $hasher = [Security.Cryptography.SHA256]::Create()
            try {
                $entryHash = [Convert]::ToHexString($hasher.ComputeHash($stream))
            } finally {
                $hasher.Dispose()
            }
        } finally {
            $stream.Dispose()
        }
        $fileHash = (Get-FileHash -LiteralPath $file['Item'].FullName -Algorithm SHA256).Hash
        if ($entryHash -cne $fileHash) {
            Deny "$($file.Name) ZIP payload does not match signed EXE"
        }
    }
} finally {
    $archive.Dispose()
}
Write-Output 'WIN-SIGN-P0 PASS: all EXEs trusted, timestamped and pinned; versions and portable member hashes agree'
