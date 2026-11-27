using System.Media;
using System.Runtime.InteropServices;

namespace BlazePisonet.SoftTimer;

internal static class WarningSound
{
    private const uint SndAsync = 0x0001;
    private const uint SndNoDefault = 0x0002;
    private const uint SndFileName = 0x00020000;
    private const uint SndPurge = 0x0040;

    public static void Play(AppConfig config)
    {
        if (!config.WarningSoundEnabled) return;
        try
        {
            if (!string.IsNullOrWhiteSpace(config.WarningSoundPath) && File.Exists(config.WarningSoundPath))
            {
                if (PlaySound(config.WarningSoundPath, IntPtr.Zero, SndAsync | SndNoDefault | SndFileName))
                    return;
            }
            SystemSounds.Exclamation.Play();
        }
        catch (Exception ex)
        {
            Storage.Log("Warning sound failed: " + ex.Message);
        }
    }

    public static void Stop()
    {
        if (!OperatingSystem.IsWindows()) return;
        try { PlaySound(null, IntPtr.Zero, SndPurge); } catch { }
    }

    [DllImport("winmm.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool PlaySound(string? pszSound, IntPtr hmod, uint fdwSound);
}
