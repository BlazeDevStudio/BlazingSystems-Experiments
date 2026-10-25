# Windows hosted runner: verifies the real Flutter executable stays alive.
# This is a process/window lifecycle smoke test, NOT a cross-device call.
$ErrorActionPreference = 'Stop'
$exe = Join-Path (Get-Location) 'build/windows/x64/runner/Release/lan_messenger.exe'
if (!(Test-Path -LiteralPath $exe)) { throw "Missing Windows release executable: $exe" }
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class LanMessengerSmokeWindow {
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool IsWindow(IntPtr hwnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool ShowWindow(IntPtr hwnd, int command);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool PostMessage(IntPtr hwnd, uint message, IntPtr wparam, IntPtr lparam);
}
'@
$proc = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) -PassThru
try {
    Start-Sleep -Seconds 12
    $proc.Refresh()
    if ($proc.HasExited) { throw "Windows application exited during startup: $($proc.ExitCode)" }
    Write-Host "Windows cloud startup alive: pid=$($proc.Id)"

    # Hosted Windows Actions may run in a non-interactive desktop session.
    # Only exercise genuine native minimize/restore when an HWND is available.
    $hwnd = [IntPtr]::Zero
    for ($i = 0; $i -lt 12; $i++) {
        $proc.Refresh()
        if ($proc.HasExited) { throw "Windows app exited before UI check: $($proc.ExitCode)" }
        $hwnd = $proc.MainWindowHandle
        if ($hwnd -ne [IntPtr]::Zero -and [LanMessengerSmokeWindow]::IsWindow($hwnd)) { break }
        Start-Sleep -Milliseconds 500
    }
    if ($hwnd -eq [IntPtr]::Zero) {
        Write-Warning 'No interactive desktop HWND available on this runner; native window lifecycle NOT tested.'
    } else {
        Write-Host "Found native window HWND: $hwnd"
        [void][LanMessengerSmokeWindow]::ShowWindow($hwnd, 6) # SW_MINIMIZE
        Start-Sleep -Seconds 2
        $proc.Refresh()
        if ($proc.HasExited) { throw 'App exited unexpectedly upon minimizing.' }
        [void][LanMessengerSmokeWindow]::ShowWindow($hwnd, 9) # SW_RESTORE
        Start-Sleep -Seconds 2
        $proc.Refresh()
        if ($proc.HasExited) { throw 'App exited unexpectedly upon restoring.' }
        [void][LanMessengerSmokeWindow]::PostMessage(
            $hwnd, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) # WM_CLOSE / tray
        Start-Sleep -Seconds 3
        $proc.Refresh()
        if ($proc.HasExited) { throw 'App exited instead of minimizing to tray on close.' }
        Write-Host 'Minimize, restore, close-to-tray lifecycle passed.'
    }
    Write-Host 'Windows cloud process-survival smoke passed.'
} finally {
    $proc.Refresh()
    if (!$proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}
