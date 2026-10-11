// PAY-0716: OFF-DEVICE / SYNTHETIC ONLY. Never ship with SoftTimer.
// One immutable pending v2 controller command and monotonic sequence reservation.
// This is a process-restart/atomic-rename fixture, NOT proven physical durability,
// customer ACK verification, independently witnessed antirollback or a v1 sender.
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

internal sealed record Pending(int Sequence, string Op, string Subject,
    string Target, int Units, long Now)
{
    public string Arguments(string id) => string.Join(" ", id,
        Sequence.ToString(CultureInfo.InvariantCulture),
        Op, Subject, Target, Units.ToString(CultureInfo.InvariantCulture),
        Now.ToString(CultureInfo.InvariantCulture));
}
internal sealed record Snapshot(string Controller, int Floor, Pending? Pending);
internal static class Program
{
    private const string Marker = "BLAZE-V2-PENDING-SYNTHETIC-ONLY\n";
    private const int MaxSeq = 100_000_000;
    private static readonly Regex Id = new(@"\A[A-Za-z][A-Za-z0-9_.-]{0,31}\z", RegexOptions.CultureInvariant);
    private static readonly Regex Hex = new(@"\A[0-9a-f]{64}\z", RegexOptions.CultureInvariant);
    private static string Number(long n) => n.ToString(CultureInfo.InvariantCulture);
    private static bool Canonical(string s, long min, long max) =>
        long.TryParse(s, NumberStyles.None, CultureInfo.InvariantCulture, out var n)
        && n >= min && n <= max && string.Equals(s, Number(n), StringComparison.Ordinal);
    private static int ParseInt(string s, int min, int max) =>
        Canonical(s, min, max) ? int.Parse(s, CultureInfo.InvariantCulture) :
        throw new InvalidOperationException("invalid canonical integer");

    private static void Validate(string op, string from, string to, int units, long now)
    {
        if (!Id.IsMatch(from) || (to != "-" && !Id.IsMatch(to))
            || op is not ("AM" or "SM" or "TM" or "LR")
            || (op == "TM" && (to == "-" || to == from))
            || (op != "TM" && to != "-")
            || units < 1 || units > 31_536_000 || now < 0 || now > 2_000_000_000)
            throw new InvalidOperationException("unsafe canonical v2 command");
    }
    private static string Root(string path)
    {
        var absolute = Path.GetFullPath(path);
        var parent = Path.GetFullPath(Path.GetTempPath())
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        var dir = Path.GetDirectoryName(absolute);
        var name = Path.GetFileName(absolute);
        if (!string.Equals(dir, parent, OperatingSystem.IsWindows() ?
                StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal)
            || !Regex.IsMatch(name, @"\Ablaze-v2-pending-[A-Za-z0-9]{6,24}\z")
            || !Directory.Exists(absolute) || IsLink(absolute))
            throw new InvalidOperationException("refuse nonfixture directory");
        var marker = Path.Combine(absolute, ".blaze-v2-pending-synthetic-only");
        if (!File.Exists(marker) || IsLink(marker) || File.ReadAllText(marker) != Marker)
            throw new InvalidOperationException("refuse missing synthetic marker");
        if (!OperatingSystem.IsWindows())
        {
            var dirMode = File.GetUnixFileMode(absolute);
            var markMode = File.GetUnixFileMode(marker);
            if ((dirMode & (UnixFileMode.GroupRead | UnixFileMode.GroupWrite |
                     UnixFileMode.GroupExecute | UnixFileMode.OtherRead |
                     UnixFileMode.OtherWrite | UnixFileMode.OtherExecute)) != 0
                || (markMode & (UnixFileMode.GroupRead | UnixFileMode.GroupWrite |
                    UnixFileMode.GroupExecute | UnixFileMode.OtherRead |
                    UnixFileMode.OtherWrite | UnixFileMode.OtherExecute)) != 0)
                throw new InvalidOperationException("fixture not private");
        }
        return absolute;
    }
    private static bool IsLink(string path) =>
        (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0;

    private static string Body(Snapshot s)
    {
        if (!Id.IsMatch(s.Controller) || s.Floor < 0 || s.Floor > MaxSeq)
            throw new InvalidOperationException("invalid controller floor");
        if (s.Pending is { } p)
        {
            Validate(p.Op, p.Subject, p.Target, p.Units, p.Now);
            if (p.Sequence != s.Floor || p.Sequence <= 0)
                throw new InvalidOperationException("pending sequence mismatch");
        }
        return string.Join("\n", "V\t1", "C\t" + s.Controller,
            "Q\t" + Number(s.Floor),
            s.Pending is null ? "P\t-" :
                string.Join("\t", "P", Number(s.Pending.Sequence), s.Pending.Op,
                    s.Pending.Subject, s.Pending.Target, Number(s.Pending.Units),
                    Number(s.Pending.Now))) + "\n";
    }
    private static string Sha(string value) =>
        Convert.ToHexString(SHA256.HashData(Encoding.ASCII.GetBytes(value))).ToLowerInvariant();
    private static Snapshot Read(string root)
    {
        var file = Path.Combine(root, "sequence.state");
        if (!File.Exists(file) || IsLink(file))
            throw new InvalidOperationException("missing controller authority; no reset");
        var bytes = File.ReadAllBytes(file);
        if (bytes.Length < 80 || bytes.Length > 1024 || bytes.Any(x => x > 127 || x == 0 || x == 13))
            throw new InvalidOperationException("corrupted controller authority");
        var raw = Encoding.ASCII.GetString(bytes);
        var lines = raw.Split('\n');
        if (lines.Length != 6 || lines[5].Length != 0)
            throw new InvalidOperationException("invalid state framing");
        var body = string.Join("\n", lines.Take(4)) + "\n";
        if (!lines[4].StartsWith("H\t", StringComparison.Ordinal) ||
            !Hex.IsMatch(lines[4][2..]) || lines[4][2..] != Sha(body))
            throw new InvalidOperationException("controller state checksum failure");
        if (lines[0] != "V\t1" || !lines[1].StartsWith("C\t", StringComparison.Ordinal) ||
            !lines[2].StartsWith("Q\t", StringComparison.Ordinal))
            throw new InvalidOperationException("invalid state header");
        var ctrl = lines[1][2..];
        var floor = ParseInt(lines[2][2..], 0, MaxSeq);
        var parts = lines[3].Split('\t');
        Pending? pending = null;
        if (parts.Length == 2 && parts[0] == "P" && parts[1] == "-") { }
        else if (parts.Length == 7 && parts[0] == "P")
        {
            pending = new Pending(ParseInt(parts[1], 1, MaxSeq), parts[2],
                parts[3], parts[4], ParseInt(parts[5], 1, 31_536_000),
                Canonical(parts[6], 0, 2_000_000_000) ?
                    long.Parse(parts[6], CultureInfo.InvariantCulture) :
                    throw new InvalidOperationException("invalid timestamp"));
        }
        else throw new InvalidOperationException("invalid pending framing");
        var state = new Snapshot(ctrl, floor, pending);
        if (!string.Equals(Body(state), body, StringComparison.Ordinal))
            throw new InvalidOperationException("noncanonical stored state");
        return state;
    }
    private static void Write(string root, Snapshot state)
    {
        // Exclusive process file lock is held by the caller.
        var destination = Path.Combine(root, "sequence.state");
        var temporary = Path.Combine(root, ".pending-stage-" +
            Convert.ToHexString(RandomNumberGenerator.GetBytes(12)).ToLowerInvariant());
        var body = Body(state);
        var data = Encoding.ASCII.GetBytes(body + "H\t" + Sha(body) + "\n");
        try
        {
            using (var stream = new FileStream(temporary, FileMode.CreateNew,
                FileAccess.Write, FileShare.None, 4096, FileOptions.WriteThrough))
            {
                stream.Write(data);
                stream.Flush(flushToDisk: true);
            }
            if (!OperatingSystem.IsWindows())
                File.SetUnixFileMode(temporary, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            if (Environment.GetEnvironmentVariable("BLAZE_V2_PENDING_FAULT") == "before-rename")
                throw new InvalidOperationException("injected precommit failure");
            // Only the sequence+pending authority is replaced. We do NOT claim
            // that Windows directory metadata has been durably flushed.
            File.Move(temporary, destination, overwrite: true);
            if (Environment.GetEnvironmentVariable("BLAZE_V2_PENDING_FAULT") == "after-rename")
                throw new InvalidOperationException("injected uncertain postcommit failure");
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }
    // PAY-0718: strictly local, private, synthetic trust registry. HMAC key
    // differs from the controller command key and is selected by a versioned
    // ACKV2 key ID. This is NOT real server identity provisioning or public
    // verification. Never import this registry into customer SoftTimer.
    private static byte[] ReadServerAckKey(string root, string controller,
        string keyId)
    {
        string path = Path.Combine(root, "trusted-server-ack-keys.tsv");
        if (!File.Exists(path) || IsLink(path))
            throw new InvalidOperationException("unprovisioned server ACK trust");
        if (!OperatingSystem.IsWindows())
        {
            var mode = File.GetUnixFileMode(path);
            if ((mode & (UnixFileMode.GroupRead | UnixFileMode.GroupWrite |
                UnixFileMode.GroupExecute | UnixFileMode.OtherRead |
                UnixFileMode.OtherWrite | UnixFileMode.OtherExecute)) != 0)
                throw new InvalidOperationException("unprivate server trust");
        }
        byte[] data = File.ReadAllBytes(path);
        if (data.Length == 0 || data.Length > 16384 || data[^1] != 10 ||
            data.Any(c => c == 0 || c == 13 || c > 127))
            throw new InvalidOperationException("invalid server trust framing");
        string[] rows = Encoding.ASCII.GetString(data)
            .Split('\n', StringSplitOptions.None);
        var seenIds = new HashSet<string>(StringComparer.Ordinal);
        var seenKeys = new HashSet<string>(StringComparer.Ordinal);
        int activeForController = 0;
        string? selected = null;
        foreach (var line in rows[..^1])
        {
            var parts = line.Split('\t');
            if (parts.Length != 4 || !Id.IsMatch(parts[0]) ||
                !Id.IsMatch(parts[1]) || parts[2] is not ("active" or "revoked") ||
                !Hex.IsMatch(parts[3]) ||
                !seenIds.Add(parts[0]) || !seenKeys.Add(parts[3]) ||
                parts[3] == new string('0', 64))
                throw new InvalidOperationException("invalid server trust registry");
            if (parts[1] == controller && parts[2] == "active")
            {
                activeForController++;
                if (parts[0] == keyId) selected = parts[3];
            }
        }
        if (activeForController != 1 || selected is null)
            throw new InvalidOperationException("unknown/revoked/rotated server ACK key");
        return Convert.FromHexString(selected);
    }

    private static void VerifyNativeServerAck(string root, Snapshot state,
        Pending pending, string reply)
    {
        string[] f = reply.Split('\t');
        if (f.Length != 8 || f[0] != "ACKV2" ||
            f[1] is not ("COMMIT" or "REPLAY") ||
            f[2] != state.Controller ||
            f[3] != Number(pending.Sequence) ||
            !Canonical(f[5], 0, 2_000_000_000) ||
            !Hex.IsMatch(f[4]) || !Id.IsMatch(f[6]) || !Hex.IsMatch(f[7]))
            throw new InvalidOperationException("noncanonical server ACK");
        string fingerprint = Sha(string.Join("|", state.Controller,
            Number(pending.Sequence), state.Controller + ":" + Number(pending.Sequence),
            pending.Op, pending.Subject, pending.Target, Number(pending.Units),
            Number(pending.Now), "v2"));
        if (fingerprint != f[4])
            throw new InvalidOperationException("server ACK not bound to pending");
        byte[] key = ReadServerAckKey(root, state.Controller, f[6]);
        try
        {
            string body = string.Join("\t", "BLAZE-V2-SERVER-ACK-FIXTURE/1",
                f[6], state.Controller, Number(pending.Sequence), fingerprint,
                f[5], f[1]) + "\n";
            byte[] expected = HMACSHA256.HashData(key,
                Encoding.ASCII.GetBytes(body));
            byte[] observed = Convert.FromHexString(f[7]);
            if (!CryptographicOperations.FixedTimeEquals(observed, expected))
                throw new InvalidOperationException("server ACK signature mismatch");
        }
        finally { CryptographicOperations.ZeroMemory(key); }
    }

    private static string Execute(string[] a)
    {
        if (a.Length < 2) throw new InvalidOperationException("missing lab command");
        var action = a[0]; var root = Root(a[1]);
        var lockPath = Path.Combine(root, ".pending.lock");
        if (File.Exists(lockPath) && IsLink(lockPath))
            throw new InvalidOperationException("invalid lock file");
        using var guard = new FileStream(lockPath, FileMode.OpenOrCreate,
            FileAccess.ReadWrite, FileShare.None);
        if (Directory.EnumerateFiles(root, ".pending-stage-*").Any())
            throw new InvalidOperationException("orphaned intent requires manual reconciliation");
        if (action == "--init" && a.Length == 3)
        {
            if (File.Exists(Path.Combine(root, "sequence.state")) ||
                !Id.IsMatch(a[2])) throw new InvalidOperationException("seed denied");
            Write(root, new Snapshot(a[2], 0, null));
            return "INITIALIZED";
        }
        var s = Read(root); // Missing/corrupt state is NEVER reset from v1.
        if (action == "--pending" && a.Length == 2)
            return s.Pending is null ? "EMPTY" : s.Pending.Arguments(s.Controller);
        if (action == "--reserve" && a.Length == 7)
        {
            var op = a[2]; var from = a[3]; var to = a[4];
            int units = ParseInt(a[5], 1, 31_536_000);
            if (!Canonical(a[6], 0, 2_000_000_000))
                throw new InvalidOperationException("bad timestamp");
            long now = long.Parse(a[6], CultureInfo.InvariantCulture);
            Validate(op, from, to, units, now);
            if (s.Pending is { } existing)
            {
                if (existing.Op != op || existing.Subject != from ||
                    existing.Target != to || existing.Units != units ||
                    existing.Now != now)
                    throw new InvalidOperationException("unresolved pending v2 event; refuse new sequence");
                return existing.Arguments(s.Controller);
            }
            if (s.Floor == MaxSeq)
                throw new InvalidOperationException("sequence exhausted");
            var p = new Pending(s.Floor + 1, op, from, to, units, now);
            Write(root, s with { Floor = p.Sequence, Pending = p });
            return p.Arguments(s.Controller);
        }
        if (action == "--ack-server" && a.Length == 9)
        {
            var p = s.Pending ?? throw new InvalidOperationException("no pending event");
            int seq = ParseInt(a[2], 1, MaxSeq);
            int units = ParseInt(a[6], 1, 31_536_000);
            if (!Canonical(a[7], 0, 2_000_000_000) ||
                p.Sequence != seq || p.Op != a[3] ||
                p.Subject != a[4] || p.Target != a[5] || p.Units != units ||
                Number(p.Now) != a[7])
                throw new InvalidOperationException("ACK differs from pending event");
            VerifyNativeServerAck(root, s, p, a[8]);
            Write(root, s with { Pending = null });
            return "ACKED";
        }
        throw new InvalidOperationException("unsupported v2 lab command");
    }
    private static int Main(string[] args)
    {
        try { Console.WriteLine(Execute(args)); return 0; }
        catch (Exception ex) when (ex is InvalidOperationException or IOException
            or UnauthorizedAccessException or ArgumentException)
        {
            // Never print state, key, ID, balance, raw exception or a v1 fallback.
            if (Environment.GetEnvironmentVariable("BLAZE_V2_LAB_DIAG") == "synthetic-only"
                && ex is InvalidOperationException
                && (ex.Message is "noncanonical server ACK"
                    or "server ACK not bound to pending"
                    or "unprovisioned server ACK trust"
                    or "unprivate server trust"
                    or "invalid server trust framing"
                    or "invalid server trust registry"
                    or "unknown/revoked/rotated server ACK key"
                    or "server ACK signature mismatch"
                    or "ACK differs from pending event"))
                Console.Error.WriteLine("PAY-0718 LAB REASON: " + ex.Message);
            Console.Error.WriteLine("PAY-0716 DENIED: pending authority invalid or uncertain (LAB ONLY)");
            return 8;
        }
    }
}
