namespace BlazePisonet.SoftTimer;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length == 1 &&
            string.Equals(args[0], "--verify-profile-store", StringComparison.OrdinalIgnoreCase))
            return DisklessProfileStore.VerifyIsolatedStore();
        ApplicationConfiguration.Initialize();
        Application.Run(new DisklessManagerForm());
        return 0;
    }
}
