using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace BlazePisonet.SoftTimer;

public sealed class RuntimeState
{
    public long RemainingSeconds { get; set; }
    public bool TimerRunning { get; set; }
    public DateTimeOffset UpdatedUtc { get; set; } = DateTimeOffset.UtcNow;
    public long SalesPulseCount { get; set; }
    public HashSet<string> AppliedEventIds { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, MemberAccount> Members { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, MemberAccount> RemoteMembers { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public long RemoteMemberRevision { get; set; }
    public PendingMemberOperation? PendingMemberOperation { get; set; }
}

public sealed class PendingMemberOperation
{
    public string Action { get; set; } = string.Empty;
    public string Username { get; set; } = string.Empty;
    public string MemberToken { get; set; } = string.Empty;
    public string EventId { get; set; } = string.Empty;
    public long Seconds { get; set; }
    public long MemberRevision { get; set; }
    public DateTimeOffset CreatedUtc { get; set; } = DateTimeOffset.UtcNow;
}

public sealed class MemberAccount
{
    public string Username { get; set; } = string.Empty;
    public string Label { get; set; } = string.Empty;
    public bool Enabled { get; set; } = true;
    public string PasswordScheme { get; set; } = "pbkdf2-sha256";
    public string PasswordSalt { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public int PasswordRounds { get; set; } = 120000;
    public long BankedSeconds { get; set; }
    public long Revision { get; set; }
    public bool RemoteManaged { get; set; }
    public DateTimeOffset UpdatedUtc { get; set; } = DateTimeOffset.UtcNow;
}

public static class Storage
{
    public static readonly JsonSerializerOptions JsonOptions = new()
    {
        WriteIndented = true,
        PropertyNameCaseInsensitive = true
    };

    public static string RootDirectory => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
        "BlazeSystems", "BlazePisonetSoftTimer");

    public static string ConfigPath => Path.Combine(RootDirectory, "config.json");
    public static string StatePath => Path.Combine(RootDirectory, "state.json");
    public static string LogPath => Path.Combine(RootDirectory, "softtimer.log");
    public static string MaintenancePath => Path.Combine(RootDirectory, "maintenance.until");

    public static AppConfig LoadConfig()
    {
        Directory.CreateDirectory(RootDirectory);
        if (!File.Exists(ConfigPath))
        {
            var cfg = new AppConfig
            {
                CentralSharedKey = Convert.ToHexString(RandomNumberGenerator.GetBytes(24)).ToLowerInvariant(),
                BlazePwifiControllerId = "softtimer-" + NormalizeId(Environment.MachineName)
            };
            SaveConfig(cfg);
            return cfg;
        }

        try
        {
            var cfg = JsonSerializer.Deserialize<AppConfig>(File.ReadAllText(ConfigPath), JsonOptions) ?? new AppConfig();
            if (string.IsNullOrWhiteSpace(cfg.CentralSharedKey))
                cfg.CentralSharedKey = Convert.ToHexString(RandomNumberGenerator.GetBytes(24)).ToLowerInvariant();
            if (string.IsNullOrWhiteSpace(cfg.BlazePwifiControllerId))
                cfg.BlazePwifiControllerId = "softtimer-" + NormalizeId(Environment.MachineName);
            cfg.Version = "0.4.0";
            EnsureSchedules(cfg);
            return cfg;
        }
        catch (Exception ex)
        {
            Log("Config load failed: " + ex.Message);
            return new AppConfig
            {
                CentralSharedKey = Convert.ToHexString(RandomNumberGenerator.GetBytes(24)).ToLowerInvariant(),
                BlazePwifiControllerId = "softtimer-" + NormalizeId(Environment.MachineName)
            };
        }
    }

    public static void SaveConfig(AppConfig config)
    {
        EnsureSchedules(config);
        AtomicWrite(ConfigPath, JsonSerializer.Serialize(config, JsonOptions));
    }

    private static void EnsureSchedules(AppConfig config)
    {
        config.NotificationSchedules ??= new List<NotificationSchedule>();
        while (config.NotificationSchedules.Count < 3)
            config.NotificationSchedules.Add(new NotificationSchedule { Name = $"Schedule {config.NotificationSchedules.Count + 1}" });
        if (config.NotificationSchedules.Count > 3)
            config.NotificationSchedules = config.NotificationSchedules.Take(3).ToList();

        for (var i = 0; i < config.NotificationSchedules.Count; i++)
        {
            var schedule = config.NotificationSchedules[i];
            if (string.IsNullOrWhiteSpace(schedule.Name)) schedule.Name = $"Schedule {i + 1}";
            schedule.Days ??= Enum.GetValues<DayOfWeek>().ToHashSet();
        }
    }

    public static RuntimeState LoadState()
    {
        Directory.CreateDirectory(RootDirectory);
        if (!File.Exists(StatePath)) return new RuntimeState();
        try
        {
            var state = JsonSerializer.Deserialize<RuntimeState>(File.ReadAllText(StatePath), JsonOptions) ?? new RuntimeState();
            state.Members ??= new Dictionary<string, MemberAccount>(StringComparer.OrdinalIgnoreCase);
            state.RemoteMembers ??= new Dictionary<string, MemberAccount>(StringComparer.OrdinalIgnoreCase);
            if (state.TimerRunning && state.RemainingSeconds > 0 && state.PendingMemberOperation is null)
            {
                var elapsed = Math.Max(0, (long)(DateTimeOffset.UtcNow - state.UpdatedUtc).TotalSeconds);
                state.RemainingSeconds = Math.Max(0, state.RemainingSeconds - elapsed);
                state.TimerRunning = state.RemainingSeconds > 0;
                state.UpdatedUtc = DateTimeOffset.UtcNow;
            }
            else if (state.PendingMemberOperation is not null)
            {
                state.UpdatedUtc = DateTimeOffset.UtcNow;
            }
            return state;
        }
        catch (Exception ex)
        {
            Log("State load failed: " + ex.Message);
            return new RuntimeState();
        }
    }

    public static void SaveState(RuntimeState state)
    {
        state.UpdatedUtc = DateTimeOffset.UtcNow;
        if (state.AppliedEventIds.Count > 2048)
        {
            state.AppliedEventIds = state.AppliedEventIds.TakeLast(1024).ToHashSet(StringComparer.OrdinalIgnoreCase);
        }
        AtomicWrite(StatePath, JsonSerializer.Serialize(state, JsonOptions));
    }

    public static void AtomicWrite(string path, string content)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temp = path + ".tmp";
        var backup = path + ".bak";
        File.WriteAllText(temp, content, new UTF8Encoding(false));
        using (var fs = new FileStream(temp, FileMode.Open, FileAccess.Read, FileShare.Read)) fs.Flush(true);
        if (File.Exists(path))
        {
            try { File.Replace(temp, path, backup, true); }
            catch
            {
                File.Copy(path, backup, true);
                File.Move(temp, path, true);
            }
        }
        else File.Move(temp, path, true);
    }

    public static void Log(string line)
    {
        try
        {
            Directory.CreateDirectory(RootDirectory);
            File.AppendAllText(LogPath, $"{DateTimeOffset.Now:yyyy-MM-dd HH:mm:ss zzz}  {line}{Environment.NewLine}");
        }
        catch { }
    }

    public static string NormalizeId(string value)
    {
        var sb = new StringBuilder();
        foreach (var c in value)
            if (char.IsLetterOrDigit(c) || c is '.' or '_' or '-') sb.Append(char.ToLowerInvariant(c));
        return sb.Length == 0 ? "pc" : sb.ToString()[..Math.Min(40, sb.Length)];
    }
}

public static class Passwords
{
    public static void SetAdminPassword(AppConfig config, string password)
    {
        var salt = RandomNumberGenerator.GetBytes(24);
        var hash = Rfc2898DeriveBytes.Pbkdf2(password, salt, config.AdminPasswordIterations, HashAlgorithmName.SHA256, 32);
        config.AdminPasswordSalt = Convert.ToBase64String(salt);
        config.AdminPasswordHash = Convert.ToBase64String(hash);
    }

    public static bool VerifyAdminPassword(AppConfig config, string password)
    {
        if (!config.HasAdminPassword) return false;
        try
        {
            var salt = Convert.FromBase64String(config.AdminPasswordSalt);
            var expected = Convert.FromBase64String(config.AdminPasswordHash);
            var actual = Rfc2898DeriveBytes.Pbkdf2(password, salt, config.AdminPasswordIterations, HashAlgorithmName.SHA256, expected.Length);
            return CryptographicOperations.FixedTimeEquals(actual, expected);
        }
        catch { return false; }
    }

    public static (string Salt, string Hash) HashMemberPassword(string password, int iterations = 120000)
    {
        var salt = RandomNumberGenerator.GetBytes(20);
        var hash = Rfc2898DeriveBytes.Pbkdf2(password, salt, iterations, HashAlgorithmName.SHA256, 32);
        return (Convert.ToBase64String(salt), Convert.ToBase64String(hash));
    }

    public static bool VerifyMemberPassword(MemberAccount member, string password, int iterations = 120000)
    {
        if (!member.Enabled) return false;
        try
        {
            if (member.PasswordScheme.Equals("sha256i", StringComparison.OrdinalIgnoreCase))
            {
                var value = DeriveSha256iVerifier(password, member.PasswordSalt, member.PasswordRounds);
                var got = Encoding.ASCII.GetBytes(value);
                var expected = Encoding.ASCII.GetBytes(member.PasswordHash.ToLowerInvariant());
                return got.Length == expected.Length && CryptographicOperations.FixedTimeEquals(got, expected);
            }

            var salt = Convert.FromBase64String(member.PasswordSalt);
            var expectedPbkdf = Convert.FromBase64String(member.PasswordHash);
            var roundsPbkdf = member.PasswordRounds > 0 ? member.PasswordRounds : iterations;
            var actual = Rfc2898DeriveBytes.Pbkdf2(password, salt, roundsPbkdf, HashAlgorithmName.SHA256, expectedPbkdf.Length);
            return CryptographicOperations.FixedTimeEquals(actual, expectedPbkdf);
        }
        catch { return false; }
    }

    public static string DeriveSha256iVerifier(string password, string salt, int rounds)
    {
        rounds = Math.Clamp(rounds, 1, 20000);
        var value = HexSha256($"{salt}|{password}|{salt}");
        for (var i = 1; i < rounds; i++)
            value = HexSha256($"{value}|{password}|{salt}");
        return value;
    }

    private static string HexSha256(string value) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();
}
