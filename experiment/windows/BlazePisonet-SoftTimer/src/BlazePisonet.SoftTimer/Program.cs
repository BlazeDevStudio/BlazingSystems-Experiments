namespace BlazePisonet.SoftTimer;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        // Safe headless regression mode. Runs before mutex/UI/setup/device access.
        if (args.Any(a => string.Equals(a, "--verify-timer-math", StringComparison.OrdinalIgnoreCase)))
            return TimerEngine.VerifyTimerMath();
        if (args.Any(a => string.Equals(a, "--verify-v2-member-protocol-gate", StringComparison.OrdinalIgnoreCase)))
            return BlazePwifiClient.VerifyV2MemberProtocolGate();
        if (args.Any(a => string.Equals(a, "--install-system-integration", StringComparison.OrdinalIgnoreCase)))
            return SystemIntegration.Install();
        if (args.Any(a => string.Equals(a, "--uninstall-system-integration", StringComparison.OrdinalIgnoreCase)))
            return SystemIntegration.Uninstall();
        if (args.Any(a => string.Equals(a, "--verify-system-integration", StringComparison.OrdinalIgnoreCase)))
            return SystemIntegration.Verify();

        using var mutex = new Mutex(true, @"Global\BlazePisonetSoftTimer", out var created);
        if (!created) return 0;

        ApplicationConfiguration.Initialize();
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
        Application.ThreadException += (_, e) => Storage.Log("UI exception: " + e.Exception);
        AppDomain.CurrentDomain.UnhandledException += (_, e) => Storage.Log("Unhandled exception: " + e.ExceptionObject);

        try
        {
            var config = Storage.LoadConfig();
            using var controller = new AppController(config);
            using var main = new MainForm(controller);
            Application.Run(main);
            return 0;
        }
        catch (Exception ex)
        {
            Storage.Log("Fatal startup exception: " + ex);
            MessageBox.Show(ex.ToString(), "BlazePisonet SoftTimer could not start", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
