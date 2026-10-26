namespace BlazeNetMonitor.Core;

/// <summary>
/// Donation settings are purely opt-in. All copies of BlazeNetMonitor use the
/// same QR destination decoded and verified from the owner's uploaded PayPal QR.
/// </summary>
public static class DonationSplashPolicy
{
    public const string EveryLaunch = "EveryLaunch";
    public const string FirstLaunch = "FirstLaunch";
    public const string Never = "Never";
    public const string OwnerPayPalUrl =
        "https://www.paypal.com/qrcodes/p2pqrc/AEBWES36GX9K2";

    public static string Normalize(string? raw) =>
        raw is EveryLaunch or FirstLaunch or Never ? raw : EveryLaunch;

    public static bool ShouldShow(string? mode, bool shownBefore) =>
        Normalize(mode) switch
        {
            Never => false,
            FirstLaunch => !shownBefore,
            _ => true
        };

    public static bool MatchesOwner(Uri? decoded) =>
        decoded is not null && decoded.AbsoluteUri == OwnerPayPalUrl;

    // QR bitstream is embedded in code, so users cannot swap the payment QR.
    // 41x41 modules, generated from exactly OwnerPayPalUrl, EC-H (tested decoding).
    public const int QrModules = 41;
    private const string QrBits =
        "/hn2Fz/BOYEFkG6rZ4Qrt1t+sWXbpMMu0uwR63NFB/qqqqr+ANkkEAAbZ2zchh7HTwisi5tbZZ7YoHfhv6h3B40LHKKiagj3GV5eyZbqFisSrj9mq7XBfr+noaeB6SSMXj0OssvdZybkL5M1jCnpnHEKrEzhYPq+k6nqbmB5oKf+gnQcfdDNyX/xdy0TGmnveWuSHVclqjgyy918+Ldr4ubOMWbTyRIB/oBivsFFv696JeqQQmEfsTuq3wP/ndbSHMie6R80VW8Et8Mwnf5ektOuAA==";

    public static bool[,] ModuleMatrix()
    {
        byte[] bytes = Convert.FromBase64String(QrBits);
        if (bytes.Length != (QrModules * QrModules + 7) / 8)
            throw new InvalidDataException("Corrupted embedded donation QR bitstream");
        var matrix = new bool[QrModules, QrModules];
        for (int y = 0; y < QrModules; y++)
            for (int x = 0; x < QrModules; x++)
            {
                int offset = y * QrModules + x;
                matrix[y, x] = (bytes[offset / 8] & (1 << (7 - offset % 8))) != 0;
            }
        return matrix;
    }
}
