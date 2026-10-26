using System.Threading;

namespace BlazeNetMonitor;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        using var single = new Mutex(true, "Local\\BlazeSystems.BlazeNetMonitor", out var owner);
        if (!owner) { MessageBox.Show("BlazeNetMonitor is already running in your notification area.", "BlazeNetMonitor"); return; }
        ApplicationConfiguration.Initialize();
        Application.Run(new MonitorForm());
    }
}
