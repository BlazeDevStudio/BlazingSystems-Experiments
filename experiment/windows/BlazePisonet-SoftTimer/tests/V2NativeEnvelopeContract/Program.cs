// PAY-0715: OFF-DEVICE .NET 8 protocol contract fixture ONLY.
// This console code is excluded from the SoftTimer production application and
// installer. Never pass real controller secrets on process command lines.
// The existing v1 SHA256 Vendo protocol is deliberately NOT a fallback.
// Accepted v2 bytes are matched to tools/v060_journal_authority_native.c.
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

internal static class Program
{
    private const string Domain = "BLAZE-V2-AUTH-FIXTURE/1";
    private static readonly Regex Identifier = new(
        "^[A-Za-z][A-Za-z0-9_.-]{0,31}$", RegexOptions.CultureInvariant);
    private static readonly Regex Secret = new(
        "^[0-9a-f]{64}$", RegexOptions.CultureInvariant);

    private sealed record Command(string Controller, ulong Sequence, string Event,
        string Operation, string Subject, string Target, ulong Units, ulong Now);

    private static Command Create(string id, string sequence, string operation,
        string subject, string target, string units, string timestamp)
    {
        if (!Identifier.IsMatch(id) || !Identifier.IsMatch(subject)
            || (target != "-" && !Identifier.IsMatch(target)))
            throw new ArgumentException("noncanonical controller or member identity");

        static ulong ParseCanonical(string value, ulong maximum, bool nonzero)
        {
            if (string.IsNullOrEmpty(value) || value.Length > 15
                || (value.Length > 1 && value[0] == '0')
                || !ulong.TryParse(value, NumberStyles.None,
                    CultureInfo.InvariantCulture, out var parsed)
                || parsed > maximum || (nonzero && parsed == 0)
                || !string.Equals(value, parsed.ToString(CultureInfo.InvariantCulture),
                    StringComparison.Ordinal))
                throw new ArgumentException("noncanonical sequence, units or timestamp");
            return parsed;
        }

        var seq = ParseCanonical(sequence, 100_000_000, true);
        var amount = ParseCanonical(units, 31_536_000, true);
        var now = ParseCanonical(timestamp, 2_000_000_000, false);
        if (operation is not ("AM" or "SM" or "TM" or "LR")
            || (operation == "TM" && (target == "-" || target == subject))
            || (operation != "TM" && target != "-"))
            throw new ArgumentException("invalid v2 opcode or target");
        return new Command(id, seq, id + ":" + sequence, operation, subject,
            target, amount, now);
    }

    private static string Canonical(Command c) =>
        string.Join("\t", Domain, c.Controller,
            c.Sequence.ToString(CultureInfo.InvariantCulture), c.Event,
            c.Operation, c.Subject, c.Target,
            c.Units.ToString(CultureInfo.InvariantCulture),
            c.Now.ToString(CultureInfo.InvariantCulture)) + "\n";

    private static string Fingerprint(Command c) =>
        Convert.ToHexString(SHA256.HashData(Encoding.ASCII.GetBytes(
            string.Join("|", c.Controller,
                c.Sequence.ToString(CultureInfo.InvariantCulture), c.Event,
                c.Operation, c.Subject, c.Target,
                c.Units.ToString(CultureInfo.InvariantCulture),
                c.Now.ToString(CultureInfo.InvariantCulture), "v2"))))
            .ToLowerInvariant();

    private static string Sign(Command command, string hexkey)
    {
        if (!Secret.IsMatch(hexkey))
            throw new ArgumentException("v2 controller secret must be 32 bytes of lowercase hex");
        byte[] key = Convert.FromHexString(hexkey);
        try
        {
            var bytes = Encoding.ASCII.GetBytes(Canonical(command));
            return Convert.ToHexString(HMACSHA256.HashData(key, bytes))
                .ToLowerInvariant();
        }
        finally { CryptographicOperations.ZeroMemory(key); }
    }

    // PAY-0717: OFF-DEVICE ONLY. Test-native C emits the identical HMAC
    // response AFTER committed journal data has been verified/durably staged.
    // This signing oracle is a test harness, never a deployable server key.
    private static string AckFixture(Command command, string outcome,
        string result, string keyHex)
    {
        if (outcome is not ("COMMIT" or "REPLAY")
            || !ulong.TryParse(result, NumberStyles.None,
                CultureInfo.InvariantCulture, out var amount)
            || amount > 2_000_000_000
            || !string.Equals(result, amount.ToString(CultureInfo.InvariantCulture),
                StringComparison.Ordinal) || !Secret.IsMatch(keyHex))
            throw new ArgumentException("noncanonical authenticated synthetic receipt");
        string fingerprint = Fingerprint(command);
        string body = string.Join("\t", "BLAZE-V2-ACK-FIXTURE/1",
            command.Controller, command.Sequence.ToString(CultureInfo.InvariantCulture),
            fingerprint, result, outcome) + "\n";
        byte[] key = Convert.FromHexString(keyHex);
        try
        {
            string mac = Convert.ToHexString(HMACSHA256.HashData(key,
                Encoding.ASCII.GetBytes(body))).ToLowerInvariant();
            return string.Join("\t", "ACKV1", outcome, command.Controller,
                command.Sequence.ToString(CultureInfo.InvariantCulture),
                fingerprint, result, mac);
        }
        finally { CryptographicOperations.ZeroMemory(key); }
    }

    // PAY-0718 off-device independent server ACK key. The key ID, subject
    // request digest and result/outcome are MAC-bound. This is a symmetric
    // synthetic registry fixture, not deployed public-key server identity.
    private static string ServerAckFixture(Command command, string outcome,
        string result, string keyId, string serverKeyHex)
    {
        if (!Identifier.IsMatch(keyId) ||
            outcome is not ("COMMIT" or "REPLAY") ||
            !ulong.TryParse(result, NumberStyles.None,
                CultureInfo.InvariantCulture, out var amount) ||
            amount > 2_000_000_000 ||
            result != amount.ToString(CultureInfo.InvariantCulture) ||
            !Secret.IsMatch(serverKeyHex))
            throw new ArgumentException("noncanonical server ACK fixture");
        var fp = Fingerprint(command);
        var body = string.Join("\t", "BLAZE-V2-SERVER-ACK-FIXTURE/1",
            keyId, command.Controller,
            command.Sequence.ToString(CultureInfo.InvariantCulture),
            fp, result, outcome) + "\n";
        byte[] key = Convert.FromHexString(serverKeyHex);
        try
        {
            var mac = Convert.ToHexString(HMACSHA256.HashData(key,
                Encoding.ASCII.GetBytes(body))).ToLowerInvariant();
            return string.Join("\t", "ACKV2", outcome, command.Controller,
                command.Sequence.ToString(CultureInfo.InvariantCulture),
                fp, result, keyId, mac);
        }
        finally { CryptographicOperations.ZeroMemory(key); }
    }

    private static void ExpectReject(Action action)
    {
        try { action(); }
        catch (ArgumentException) { return; }
        throw new Exception("unsafe/noncanonical native v2 payload accepted");
    }

    private static void SelfTest()
    {
        // Fixed fixtures cross-checked with Python hmac and OpenSSL SHA256.
        // These secrets are synthetic, deliberately not production credentials.
        var a = Create("ctrlOne", "1", "AM", "alice", "-", "40", "1000");
        var b = Create("ctrlOne", "2", "TM", "alice", "bob", "30", "1000");
        var c = Create("ctrlTwo", "1", "SM", "bob", "-", "5", "1000");
        var k1 = new string('3', 64);
        var k2 = new string('4', 64);
        if (Sign(a, k1) != "21dabcd6e4c86c7216f9213ad6f829594e9c7338f595b48c7d5c4a850168433b"
            || Sign(b, k1) != "b73348d448f105db3af41b30e0a382f914f317decce224ead75ba8240eab1be2"
            || Sign(c, k2) != "3bc0c46811d0d4daae453138a4b42fff3f484c66e2daeed7ce48ba4fa5323c60"
            || Fingerprint(a) != "a4c7a747b0fa7062067fba15f6b39d81473b739cd88c524648d02fdbd468bff3"
            || Fingerprint(b) != "6d5c203e477485f27c925f13db3cddb27b69df0703600601745dd81bc280e681")
            throw new Exception("native journal canonical HMAC/digest vector mismatch");
        ExpectReject(() => Create("ctrlOne", "01", "AM", "alice", "-", "40", "1000"));
        ExpectReject(() => Create("ctrlOne", "0", "AM", "alice", "-", "40", "1000"));
        ExpectReject(() => Create("ctrlOne", "100000001", "AM", "alice", "-", "40", "1000"));
        ExpectReject(() => Create("ctrlOne", "1", "AM", "alice", "-", "0", "1000"));
        ExpectReject(() => Create("ctrlOne", "1", "TM", "alice", "alice", "10", "1000"));
        ExpectReject(() => Create("ctrlOne", "1", "TM", "alice", "-", "10", "1000"));
        ExpectReject(() => Create("ctrlOne", "1", "AM", "alice", "bob", "10", "1000"));
        ExpectReject(() => Create("ctrlOne", "1", "RM", "alice", "-", "10", "1000"));
        ExpectReject(() => Create("ctrlOne", "1", "AM", "álîce", "-", "10", "1000"));
        ExpectReject(() => Create("ctrlOne", "1", "AM", "alice", "-", "31536001", "1000"));
        ExpectReject(() => Create("ctrlOne", "1", "AM", "alice", "-", "1", "2000000001"));
        ExpectReject(() => Sign(a, new string('0', 63)));
        ExpectReject(() => Sign(a, new string('F', 64)));
        var receipt = AckFixture(a, "COMMIT", "140", k1);
        if (!receipt.StartsWith("ACKV1\tCOMMIT\tctrlOne\t1\t", StringComparison.Ordinal)
            || receipt.Split('\t').Length != 7
            || receipt == AckFixture(a, "REPLAY", "140", k1)
            || receipt == AckFixture(a, "COMMIT", "141", k1)
            || receipt == AckFixture(b, "COMMIT", "140", k1)
            || receipt == AckFixture(a, "COMMIT", "140", k2))
            throw new Exception("authenticated ACK lacks separation or request binding");
        ExpectReject(() => AckFixture(a, "OK", "140", k1));
        ExpectReject(() => AckFixture(a, "COMMIT", "0140", k1));
        var independent = ServerAckFixture(a, "COMMIT", "140", "serverA",
            new string('5', 64));
        if (!independent.StartsWith("ACKV2\tCOMMIT\tctrlOne\t1\t", StringComparison.Ordinal)
            || independent.Split('\t').Length != 8
            || independent == ServerAckFixture(a, "COMMIT", "140", "serverB", new string('5', 64))
            || independent == ServerAckFixture(a, "COMMIT", "140", "serverA", k1)
            || independent == ServerAckFixture(a, "REPLAY", "140", "serverA", new string('5', 64)))
            throw new Exception("independent server ACK key ID binding mismatch");
        ExpectReject(() => ServerAckFixture(a, "COMMIT", "140", "bad key", new string('5', 64)));
        ExpectReject(() => ServerAckFixture(a, "COMMIT", "0140", "serverA", new string('5', 64)));
        if (Sign(Create("ctrlOne", "1", "AM", "alice", "-", "41", "1000"), k1) == Sign(a, k1)
            || Sign(Create("ctrlOne", "1", "AM", "bob", "-", "40", "1000"), k1) == Sign(a, k1)
            || Sign(Create("ctrlOne", "1", "AM", "alice", "-", "40", "1001"), k1) == Sign(a, k1))
            throw new Exception("signed native fields not bound to payment identity");
        Console.WriteLine("PAY-0715 .NET-to-C canonical v2 envelope fixture PASS (lab only)");
    }

    private static int Main(string[] args)
    {
        try
        {
            if (args.Length == 1 && args[0] == "--selftest")
            {
                SelfTest();
                return 0;
            }
            if (args.Length == 11 && args[0] == "--ack-fixture")
            {
                var expected = Create(args[1], args[2], args[3], args[4],
                    args[5], args[6], args[7]);
                Console.WriteLine(AckFixture(expected, args[8], args[9], args[10]));
                return 0;
            }
            if (args.Length == 12 && args[0] == "--server-ack-fixture")
            {
                var expected = Create(args[1], args[2], args[3], args[4],
                    args[5], args[6], args[7]);
                Console.WriteLine(ServerAckFixture(expected, args[8], args[9],
                    args[10], args[11]));
                return 0;
            }
            if (args.Length != 9 || args[0] != "--emit")
                throw new ArgumentException(
                    "test-only usage: --emit CTRL SEQ OP SUBJECT TARGET UNITS NOW KEY | --ack-fixture CTRL SEQ OP SUBJECT TARGET UNITS NOW OUTCOME RESULT KEY");
            var command = Create(args[1], args[2], args[3], args[4], args[5], args[6], args[7]);
            var signature = Sign(command, args[8]);
            Console.WriteLine(string.Join(" ", command.Controller,
                command.Sequence.ToString(CultureInfo.InvariantCulture),
                command.Event, command.Operation, command.Subject, command.Target,
                command.Units.ToString(CultureInfo.InvariantCulture),
                command.Now.ToString(CultureInfo.InvariantCulture), signature));
            return 0;
        }
        catch (ArgumentException)
        {
            // Deliberately don't echo secret, input envelope or command line.
            Console.Error.WriteLine("PAY-0715 REJECT: unsafe/noncanonical synthetic request");
            return 8;
        }
        catch (Exception)
        {
            Console.Error.WriteLine("PAY-0715 FAIL: test fixture contract mismatch");
            return 9;
        }
    }
}
