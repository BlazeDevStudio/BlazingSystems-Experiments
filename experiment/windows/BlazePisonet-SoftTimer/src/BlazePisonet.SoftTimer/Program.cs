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
        // PAY-0720: exercise the SAME shipped WinExe verifier with externally
        // generated public-only ACK fixtures. Never reads a private signing
        // key, connects to a router, clears pending time or writes config.
        if (args.Length == 4 && args[0] == "--verify-v2-server-ack-files")
        {
            try
            {
                var context = File.ReadAllLines(args[3]);
                if (context.Length != 4 ||
                    !long.TryParse(context[2], System.Globalization.NumberStyles.None,
                        System.Globalization.CultureInfo.InvariantCulture, out var sequence))
                    return 80;
                var config = new AppConfig
                {
                    BlazePwifiRequireV2MemberProtocol = true,
                    BlazePwifiControllerId = context[1],
                    BlazePwifiV2ServerKeyId = context[0],
                    BlazePwifiV2ServerPublicKeySpkiBase64 =
                        File.ReadAllText(args[1]).TrimEnd('\r', '\n')
                };
                using var client = new BlazePwifiClient(config);
                return client.TryVerifyV2MemberServerAck(File.ReadAllText(args[2]),
                    sequence, context[3], out _) ? 0 : 79;
            }
            catch (Exception) { return 80; }
        }
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
