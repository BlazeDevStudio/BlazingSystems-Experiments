using Microsoft.Win32;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace BlazePisonet.SoftTimer;

public sealed class WindowsSecurity : IDisposable
{
    private const int WhKeyboardLl = 13;
    private const int WmKeyDown = 0x0100;
    private const int WmSysKeyDown = 0x0104;
    private const int VkTab = 0x09;
    private const int VkEscape = 0x1B;
    private const int VkF4 = 0x73;
    private const int VkSpace = 0x20;
    private const int VkLwin = 0x5B;
    private const int VkRwin = 0x5C;
    private const int VkHome = 0x24;
    private const int VkControl = 0x11;
    private const int VkShift = 0x10;
    private const int VkMenu = 0x12;

    private readonly LowLevelKeyboardProc _keyboardProc;
    private IntPtr _keyboardHook;
    private readonly System.Threading.Timer _processTimer;
    private AppConfig _config;
    private volatile bool _locked;
    private volatile bool _secretArmed;
    private int _inputCounter;
    private DateTimeOffset _inputWindowStart = DateTimeOffset.UtcNow;

    public event Action? AdminSecretRequested;
    public event Action? UnusualInputThresholdReached;

    public WindowsSecurity(AppConfig config)
    {
        _config = config;
        _keyboardProc = KeyboardHook;
        _processTimer = new System.Threading.Timer(_ => ProcessGuardTick(), null, 1000, 1500);
    }

    public void UpdateConfig(AppConfig config)
    {
        _config = config;
        if (!_locked) return;
        if (_config.LockMouseToScreen) ApplyMouseRestriction(); else ReleaseMouseRestriction();
    }

    public void StartKeyboardHook()
    {
        if (_keyboardHook != IntPtr.Zero || !OperatingSystem.IsWindows()) return;
        using var cur = Process.GetCurrentProcess();
        using var module = cur.MainModule;
        _keyboardHook = SetWindowsHookEx(WhKeyboardLl, _keyboardProc, GetModuleHandle(module?.ModuleName), 0);
        if (_keyboardHook == IntPtr.Zero) Storage.Log("Keyboard hook installation failed: " + Marshal.GetLastWin32Error());
    }

    public void SetLocked(bool locked)
    {
        _locked = locked;
        _inputCounter = 0;
        _inputWindowStart = DateTimeOffset.UtcNow;
        if (locked)
        {
            ApplyPolicies();
            if (_config.LockMouseToScreen) ApplyMouseRestriction();
        }
        else
        {
            ReleaseMouseRestriction();
            RestorePolicies();
        }
    }

    public void ArmAdminSecret(TimeSpan duration)
    {
        _secretArmed = true;
        _ = Task.Run(async () =>
        {
            await Task.Delay(duration);
            _secretArmed = false;
        });
    }

    private void ApplyMouseRestriction()
    {
        if (!OperatingSystem.IsWindows()) return;
        try
        {
            var bounds = Screen.PrimaryScreen?.Bounds ?? SystemInformation.VirtualScreen;
            var rect = new ClipRect { Left = bounds.Left, Top = bounds.Top, Right = bounds.Right, Bottom = bounds.Bottom };
            ClipCursor(ref rect);
        }
        catch (Exception ex) { Storage.Log("Mouse restriction failed: " + ex.Message); }
    }

    private static void ReleaseMouseRestriction()
    {
        if (!OperatingSystem.IsWindows()) return;
        try { ClipCursor(IntPtr.Zero); } catch { }
    }

    public void ApplyPolicies()
    {
        if (!OperatingSystem.IsWindows()) return;
        try
        {
            using var system = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Policies\System", true);
            using var explorer = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", true);
            SetOrDelete(system, "DisableTaskMgr", _config.BlockTaskManager);
            SetOrDelete(system, "DisableRegistryTools", _config.BlockRegistryTools);
            SetOrDelete(explorer, "NoLogoff", _config.DisableLogoff);
            SetOrDelete(explorer, "NoClose", _config.DisablePowerOptions);
            ApplyHostsBlock();
        }
        catch (Exception ex) { Storage.Log("Security policy apply failed: " + ex.Message); }
    }

    public void RestorePolicies()
    {
        if (!OperatingSystem.IsWindows()) return;
        try
        {
            using var system = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Policies\System", true);
            using var explorer = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", true);
            system?.DeleteValue("DisableTaskMgr", false);
            system?.DeleteValue("DisableRegistryTools", false);
            explorer?.DeleteValue("NoLogoff", false);
            explorer?.DeleteValue("NoClose", false);
            RemoveHostsBlock();
        }
        catch (Exception ex) { Storage.Log("Security policy restore failed: " + ex.Message); }
    }

    public static TimeSpan GetIdleTime()
    {
        if (!OperatingSystem.IsWindows()) return TimeSpan.Zero;
        var info = new LastInputInfo { cbSize = (uint)Marshal.SizeOf<LastInputInfo>() };
        if (!GetLastInputInfo(ref info)) return TimeSpan.Zero;
        var idle = unchecked((uint)Environment.TickCount - info.dwTime);
        return TimeSpan.FromMilliseconds(idle);
    }

    private IntPtr KeyboardHook(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0 && (wParam == (IntPtr)WmKeyDown || wParam == (IntPtr)WmSysKeyDown))
        {
            var vk = Marshal.ReadInt32(lParam);
            if (_locked)
            {
                RecordInput();
                if (vk == VkHome && _secretArmed)
                {
                    _secretArmed = false;
                    AdminSecretRequested?.Invoke();
                    return (IntPtr)1;
                }

                if (_config.BlockWindowsKeys)
                {
                    var alt = (GetAsyncKeyState(VkMenu) & 0x8000) != 0;
                    var ctrl = (GetAsyncKeyState(VkControl) & 0x8000) != 0;
                    var shift = (GetAsyncKeyState(VkShift) & 0x8000) != 0;
                    var block = vk is VkLwin or VkRwin
                        || (alt && vk is VkTab or VkEscape or VkF4 or VkSpace)
                        || (ctrl && vk == VkEscape)
                        || (ctrl && shift && vk == VkEscape);
                    if (block) return (IntPtr)1;
                }
            }
        }
        return CallNextHookEx(_keyboardHook, nCode, wParam, lParam);
    }

    private void RecordInput()
    {
        var now = DateTimeOffset.UtcNow;
        if ((now - _inputWindowStart).TotalSeconds > Math.Max(30, _config.UnusualInputWindowSeconds))
        {
            _inputCounter = 0;
            _inputWindowStart = now;
        }
        _inputCounter++;
        if (_config.UnusualInputShutdownEnabled && _inputCounter >= Math.Max(100, _config.UnusualInputThreshold))
        {
            _inputCounter = 0;
            _inputWindowStart = now;
            UnusualInputThresholdReached?.Invoke();
        }
    }

    private void ProcessGuardTick()
    {
        if (!_locked) return;
        try
        {
            foreach (var raw in _config.BlockedProcesses)
            {
                var name = Path.GetFileNameWithoutExtension(raw.Trim());
                if (string.IsNullOrWhiteSpace(name)) continue;
                foreach (var process in Process.GetProcessesByName(name))
                {
                    try
                    {
                        if (process.Id != Environment.ProcessId) process.Kill(true);
                    }
                    catch { }
                    finally { process.Dispose(); }
                }
            }
        }
        catch { }
    }

    private void ApplyHostsBlock()
    {
        if (_config.BlockedWebsites.Count == 0) { RemoveHostsBlock(); return; }
        var path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "drivers", "etc", "hosts");
        if (!File.Exists(path)) return;
        var baseText = StripHostsBlock(File.ReadAllText(path));
        var sb = new StringBuilder(baseText.TrimEnd());
        sb.AppendLine().AppendLine("# BLAZEPISONET SOFTTIMER START");
        foreach (var host in _config.BlockedWebsites.Select(NormalizeHost).Where(h => h.Length > 0).Distinct(StringComparer.OrdinalIgnoreCase))
        {
            sb.Append("0.0.0.0 ").AppendLine(host);
            if (!host.StartsWith("www.", StringComparison.OrdinalIgnoreCase)) sb.Append("0.0.0.0 www.").AppendLine(host);
        }
        sb.AppendLine("# BLAZEPISONET SOFTTIMER END");
        File.WriteAllText(path, sb.ToString());
    }

    private void RemoveHostsBlock()
    {
        try
        {
            var path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "drivers", "etc", "hosts");
            if (File.Exists(path)) File.WriteAllText(path, StripHostsBlock(File.ReadAllText(path)));
        }
        catch { }
    }

    private static string StripHostsBlock(string text)
    {
        const string start = "# BLAZEPISONET SOFTTIMER START";
        const string end = "# BLAZEPISONET SOFTTIMER END";
        var s = text.IndexOf(start, StringComparison.Ordinal);
        if (s < 0) return text;
        var e = text.IndexOf(end, s, StringComparison.Ordinal);
        if (e < 0) return text[..s];
        e += end.Length;
        while (e < text.Length && (text[e] == '\r' || text[e] == '\n')) e++;
        return text.Remove(s, e - s);
    }

    private static string NormalizeHost(string host)
    {
        host = host.Trim();
        if (Uri.TryCreate(host.Contains("://") ? host : "http://" + host, UriKind.Absolute, out var uri)) return uri.Host;
        return host.Split('/')[0].Split(':')[0];
    }

    private static void SetOrDelete(RegistryKey? key, string name, bool enabled)
    {
        if (key is null) return;
        if (enabled) key.SetValue(name, 1, RegistryValueKind.DWord);
        else key.DeleteValue(name, false);
    }

    public void Dispose()
    {
        _processTimer.Dispose();
        if (_keyboardHook != IntPtr.Zero)
        {
            UnhookWindowsHookEx(_keyboardHook);
            _keyboardHook = IntPtr.Zero;
        }
        ReleaseMouseRestriction();
        RestorePolicies();
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ClipRect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    private struct LastInputInfo { public uint cbSize; public uint dwTime; }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);
    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);
    [DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);
    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr GetModuleHandle(string? lpModuleName);
    [DllImport("user32.dll")]
    private static extern short GetAsyncKeyState(int vKey);
    [DllImport("user32.dll")]
    private static extern bool GetLastInputInfo(ref LastInputInfo plii);
    [DllImport("user32.dll")]
    private static extern bool ClipCursor(ref ClipRect lpRect);
    [DllImport("user32.dll")]
    private static extern bool ClipCursor(IntPtr lpRect);
}
