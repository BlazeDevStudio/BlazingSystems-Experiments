# LAN Messenger - local Windows crash diagnostics (does not upload data).
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\tool\windows_crash_report.ps1
#   powershell -ExecutionPolicy Bypass -File .\tool\windows_crash_report.ps1 -LookbackMinutes 1440
#   powershell -ExecutionPolicy Bypass -File .\tool\windows_crash_report.ps1 -SelfTest
#
# Reads Windows Application Error (1000) and Windows Error Reporting (1001)
# for lan_messenger.exe. Exports ONLY fault module/code/offset/timestamps.
# Never exports raw event messages, file paths, device identifiers, call
# content or crash dumps. Neither modifies registry nor sends telemetry.
[CmdletBinding()]
param(
    [ValidateRange(1,10080)][int]$LookbackMinutes = 1440,
    [string]$OutputFile = "",
    [switch]$SelfTest
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-EventField([string]$Message, [string]$Label) {
    $pattern = "(?im)^\s*" + [regex]::Escape($Label) + "\s*:\s*(.*?)\s*$"
    $match = [regex]::Match($Message, $pattern)
    if ($match.Success) { return $match.Groups[1].Value.Trim() }
    return $null
}

function Get-PropertyOrNull($Event, [int]$Index) {
    if ($Event.Properties -and $Event.Properties.Count -gt $Index) {
        return [string]$Event.Properties[$Index].Value
    }
    return $null
}

if ($SelfTest) {
    $sample = "Faulting application name: lan_messenger.exe`r`nFaulting module name: flutter_webrtc_plugin.dll`r`nException code: 0xc0000005`r`nFault offset: 0x1234"
    if ((Get-EventField $sample "Faulting module name") -ne "flutter_webrtc_plugin.dll" -or
        (Get-EventField $sample "Exception code") -ne "0xc0000005" -or
        (Get-EventField $sample "Fault offset") -ne "0x1234") {
        throw "Crash-report field parser failed synthetic contract"
    }
    Write-Output "PASS: local Windows crash-report parser"
    exit 0
}

if ([string]::IsNullOrWhiteSpace($OutputFile)) {
    $OutputFile = Join-Path ([System.IO.Path]::GetTempPath()) "LAN-Messenger-Windows-Crash-Report.json"
}
$since = (Get-Date).AddMinutes(-$LookbackMinutes)
$events = @()
$readError = $null
try {
    $events = @(Get-WinEvent -FilterHashtable @{
        LogName = "Application"
        Id = @(1000,1001)
        StartTime = $since
    } -ErrorAction Stop)
} catch {
    $readError = $_.Exception.GetType().Name
    Write-Warning "Application Event Log unavailable or contains no matching entries. Report will explain the limitation."
}

$results = @(
    foreach ($event in $events) {
        $message = [string]$event.Message
        $appProperty = if ($event.Id -eq 1000) { Get-PropertyOrNull $event 0 } else { $null }
        if ($message -notmatch "(?i)\blan_messenger\.exe\b" -and
            $appProperty -notmatch "(?i)^lan_messenger\.exe$") { continue }

        $module = Get-EventField $message "Faulting module name"
        $code = Get-EventField $message "Exception code"
        $offset = Get-EventField $message "Fault offset"
        # Application Error event 1000 has language-neutral, structured values.
        if ($event.Id -eq 1000) {
            if ([string]::IsNullOrWhiteSpace($module)) { $module = Get-PropertyOrNull $event 3 }
            if ([string]::IsNullOrWhiteSpace($code)) { $code = Get-PropertyOrNull $event 6 }
            if ([string]::IsNullOrWhiteSpace($offset)) { $offset = Get-PropertyOrNull $event 7 }
        }
        [pscustomobject]@{
            AtUtc = $event.TimeCreated.ToUniversalTime().ToString("o")
            EventId = $event.Id
            Provider = $event.ProviderName
            FaultingModule = $module
            ExceptionCode = $code
            FaultOffset = $offset
        }
    }
)
$results = @($results | Sort-Object AtUtc -Descending | Select-Object -First 20)
$report = [pscustomobject]@{
    Application = "lan_messenger.exe"
    GeneratedAtUtc = (Get-Date).ToUniversalTime().ToString("o")
    LookbackMinutes = $LookbackMinutes
    MatchedEvents = $results.Count
    EventLogReadErrorType = $readError
    Crashes = $results
    ContainsRawEventMessagesOrDumps = $false
}
$parent = Split-Path -Parent $OutputFile
if ($parent -and !(Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputFile -Encoding UTF8
Write-Output ("Crash report: " + $OutputFile)
Write-Output ("Matched LAN Messenger crash events: " + $results.Count)
if ($results.Count -eq 0) {
    Write-Output "No matching Application Error/WER event in this window. Check Reliability Monitor (perfmon /rel)."
} else {
    $results | Format-Table AtUtc,EventId,FaultingModule,ExceptionCode,FaultOffset -AutoSize | Out-String | Write-Output
}
