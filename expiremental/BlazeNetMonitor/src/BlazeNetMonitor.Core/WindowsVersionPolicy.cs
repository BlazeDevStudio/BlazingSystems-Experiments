namespace BlazeNetMonitor.Core;

/// <summary>
/// Classify the NT kernel version for shell integration gates.
/// Windows 10 and Windows 11 both report NT major 10; use build threshold 22000.
/// Future builds default to the non-invasive path until explicitly validated.
/// </summary>
public static class WindowsVersionPolicy
{
    public static string ShellFamily(Version version)
    {
        if (version.Major == 10 && version.Build >= 10240 && version.Build < 22000)
            return "Windows10Classic";
        if (version.Major == 10 && version.Build >= 22000)
            return "Windows11OrLater";
        return "Unknown";
    }

    public static bool CanUseClassicDeskBand(Version version) =>
        ShellFamily(version) == "Windows10Classic";

    // OS eligibility is not an installed/registered COM module or proof of active integration.
    public static bool IsNativeHostReady(Version version, bool verifiedHostInstalled) =>
        CanUseClassicDeskBand(version) && verifiedHostInstalled;
}
