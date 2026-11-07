using System.Diagnostics;

namespace BlazePisonet.SoftTimer;

// Optional companion executable. No diskless type or assembly is linked to SoftTimer.
public sealed partial class MainForm
{
    private void BuildAddons()
    {
        var root = NewPage("Add-ons", "Optional administrator tools. Paid PC sessions do not require them.");
        var card = Card("Diskless Manager", "Separate Windows tool for FOG, iSCSI and PXE preparation. Not installed with SoftTimer.");
        card.Controls.Add(Button("OPEN DISKLESS MANAGER", (_, _) => OpenDisklessManager()));
        root.Controls.Add(card);
        _pages["Add-ons"] = root;
    }

    private void OpenDisklessManager()
    {
        // Run only from the fixed administrator-installation directory.
        // Never run an arbitrary path from a customer setting or a network response.
        var executable = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),
            "BlazeSystems", "BlazePisonet Diskless Manager",
            "BlazePisonet.DisklessManager.exe");
        if (!File.Exists(executable))
        {
            MessageBox.Show(
                "Diskless Manager is optional and not installed. Install the standalone add-on to manage FOG and iSCSI; the SoftTimer continues normally.",
                "Optional add-on", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        try
        {
            Process.Start(new ProcessStartInfo(executable)
            {
                UseShellExecute = false,
                WorkingDirectory = Path.GetDirectoryName(executable)!
            });
        }
        catch (Exception ex) when (ex is System.ComponentModel.Win32Exception or IOException or UnauthorizedAccessException)
        {
            MessageBox.Show("Unable to open Diskless Manager: " + ex.Message,
                "Optional add-on", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }
    }
}
