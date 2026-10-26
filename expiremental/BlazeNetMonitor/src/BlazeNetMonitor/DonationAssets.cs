using System.Drawing.Imaging;

namespace BlazeNetMonitor;

/// <summary>Authentic operator-supplied donation image only; no invented payment links.
/// Stores one locally imported PNG, never sends its contents to a server.</summary>
internal static class DonationAssets
{
    public static string LocalPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "BlazeSystems", "BlazeNetMonitor", "paypal-donation.png");

    public static Bitmap? TryLoad()
    {
        foreach (var path in new[] { LocalPath,
            Path.Combine(AppContext.BaseDirectory, "paypal-donation.png") })
        {
            if (!File.Exists(path)) continue;
            try
            {
                if (new FileInfo(path).Length > 2 * 1024 * 1024) continue;
                using var image = Image.FromFile(path);
                if (image.Width is < 90 or > 3000 || image.Height is < 90 or > 3000) continue;
                return new Bitmap(image);
            }
            catch (Exception) { /* malformed image, continue looking */ }
        }
        return null;
    }

    public static bool ImportFromPicker(IWin32Window owner)
    {
        using var dlg = new OpenFileDialog
        {
            Title = "Select your authentic PayPal donation QR image",
            Filter = "Image files|*.png;*.jpg;*.jpeg;*.bmp|All files|*.*",
            CheckFileExists = true, Multiselect = false
        };
        if (dlg.ShowDialog(owner) != DialogResult.OK) return false;
        try
        {
            if (new FileInfo(dlg.FileName).Length > 2 * 1024 * 1024)
                throw new InvalidDataException("The QR image must be smaller than 2 MB.");
            using var source = Image.FromFile(dlg.FileName);
            if (source.Width is < 90 or > 3000 || source.Height is < 90 or > 3000)
                throw new InvalidDataException("QR image must be between 90 and 3000 pixels.");
            Directory.CreateDirectory(Path.GetDirectoryName(LocalPath)!);
            var tmp = LocalPath + ".tmp";
            source.Save(tmp, ImageFormat.Png);
            File.Move(tmp, LocalPath, true);
            return true;
        }
        catch (Exception e)
        {
            MessageBox.Show(owner, e.Message, "PayPal QR import",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return false;
        }
    }
}
