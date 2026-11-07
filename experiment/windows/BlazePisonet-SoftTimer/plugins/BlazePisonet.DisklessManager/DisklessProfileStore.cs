using System.Text.Json;

namespace BlazePisonet.SoftTimer;

// Profiles are isolated from SoftTimer paid-time, member and watchdog state.
public static class DisklessProfileStore
{
    private static readonly JsonSerializerOptions Json = new() { PropertyNameCaseInsensitive = true };
    public static string ProfilePath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
        "BlazeSystems", "BlazePisonetDisklessManager", "profiles.json");

    public static List<DisklessClientAssignment> Load(string? path = null)
    {
        path ??= ProfilePath;
        if (!File.Exists(path)) return new List<DisklessClientAssignment>();
        try
        {
            return DisklessProfileRegistry.Validate(
                JsonSerializer.Deserialize<List<DisklessClientAssignment>>(File.ReadAllText(path), Json)).ToList();
        }
        catch (Exception ex) when (ex is JsonException or InvalidOperationException)
        {
            throw new InvalidDataException("Corrupt diskless profiles; refusing overwrite.", ex);
        }
    }

    public static void Save(IReadOnlyList<DisklessClientAssignment> profiles, string? path = null)
    {
        path ??= ProfilePath;
        var validated = DisklessProfileRegistry.Validate(profiles);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temp = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            File.WriteAllText(temp, JsonSerializer.Serialize(validated, Json));
            File.Move(temp, path, overwrite: true);
        }
        finally
        {
            if (File.Exists(temp)) File.Delete(temp);
        }
    }

    public static IReadOnlyList<DisklessClientAssignment> ReadLegacySoftTimerProfiles(string? legacyPath = null)
    {
        legacyPath ??= Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
            "BlazeSystems", "BlazePisonetSoftTimer", "config.json");
        if (!File.Exists(legacyPath)) return Array.Empty<DisklessClientAssignment>();
        using var doc = JsonDocument.Parse(File.ReadAllText(legacyPath));
        if (!doc.RootElement.TryGetProperty("DisklessProfiles", out var profiles))
            return Array.Empty<DisklessClientAssignment>();
        return DisklessProfileRegistry.Validate(profiles.Deserialize<List<DisklessClientAssignment>>(Json));
    }

    public static int VerifyIsolatedStore()
    {
        var dir = Path.Combine(Path.GetTempPath(), "blaze-diskless-test-" + Guid.NewGuid().ToString("N"));
        var path = Path.Combine(dir, "profiles.json");
        var legacy = Path.Combine(dir, "legacy.json");
        try
        {
            var profile = new DisklessClientAssignment("pc-01", "10.20.30.40",
                "iqn.2026-10.local.blaze:disk-pc-01", "iqn.2026-10.local.blaze:client-pc-01");
            Save(new[] { profile }, path);
            if (Load(path).Count != 1 || Load(path)[0] != profile) return 10;
            var before = File.ReadAllText(path);
            try { Save(new[] { profile, profile }, path); return 11; }
            catch (InvalidOperationException) { }
            if (File.ReadAllText(path) != before) return 12;
            File.WriteAllText(legacy, "{\"DisklessProfiles\":" + before + "}");
            if (ReadLegacySoftTimerProfiles(legacy).Single() != profile) return 13;
            File.WriteAllText(path, "{invalid");
            try { Load(path); return 14; } catch (InvalidDataException) { }
            return File.ReadAllText(path) == "{invalid" ? 0 : 15;
        }
        finally
        {
            if (Directory.Exists(dir)) Directory.Delete(dir, recursive: true);
        }
    }
}
