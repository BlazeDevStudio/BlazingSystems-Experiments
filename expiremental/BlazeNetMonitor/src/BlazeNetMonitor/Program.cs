using System.Runtime.InteropServices;
using System.Threading;

namespace BlazeNetMonitor;

internal static class Program
{
    internal const string RequestAckName = @"Local\BlazeSystems.BlazeNetMonitor.RequestAcknowledged";

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint RegisterWindowMessage(string name);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PostMessage(nint hWnd, uint msg, nint wParam, nint lParam);

    internal static readonly uint ShowSettingsMessage =
        RegisterWindowMessage("BlazeSystems.BlazeNetMonitor.ShowSettings.v1");

    [STAThread]
    private static void Main()
    {
        using var single = new Mutex(true, @"Local\BlazeSystems.BlazeNetMonitor", out var owner);
        using var acknowledged = new EventWaitHandle(false, EventResetMode.AutoReset, RequestAckName);
        if (!owner)
        {
            // Reopen the running instance's settings instead of spawning duplicates.
            if (ShowSettingsMessage != 0)
                PostMessage((nint)0xFFFF, ShowSettingsMessage, 0, 0); // HWND_BROADCAST
            if (!acknowledged.WaitOne(650))
                MessageBox.Show(
                    "BlazeNetMonitor is already running. The existing process may be an older version. " +
                    "Use the notification-area (hidden icons ^) menu → Exit BlazeNetMonitor, " +
                    "then launch this new version. Do not run both builds together.",
                    "BlazeNetMonitor · Already running",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        ApplicationConfiguration.Initialize();
        Application.Run(new MonitorForm());
    }
}
