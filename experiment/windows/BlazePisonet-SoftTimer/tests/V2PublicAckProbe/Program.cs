// PAY-0720: An external ephemeral signing test for the real compiled WinExe.
// The app contains ONLY a public-key verifier; the private key used here never
// leaves this test process, never enters customer binaries or any git artifact.
using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;

internal static class Program
{
    private const string Domain = "BLAZEPWIFI-MEMBER-V2-ACK/ECDSA-P256-SHA256/1";
    private const string Fingerprint =
        "abcdeffedcba0123456789abcdef0123456789abcdef0123456789abcdef0123";
    private const string Controller = "softtimer01";
    private const string ServerId = "router1";

    private static string Message(string[] fields, string domain = Domain) =>
        domain + "\n" + string.Join("\t", fields) + "\n";

    private static string Envelope(ECDsa signer, string[] fields, string domain = Domain)
    {
        byte[] sig = signer.SignData(Encoding.ASCII.GetBytes(Message(fields, domain)),
            HashAlgorithmName.SHA256, DSASignatureFormat.Rfc3279DerSequence);
        return string.Join("\t", fields) + "\t" + Convert.ToBase64String(sig);
    }

    private static int RunWinExe(string app, string folder, string publicKey,
        string ack, string context)
    {
        File.WriteAllText(Path.Combine(folder, "pub.txt"), publicKey);
        File.WriteAllText(Path.Combine(folder, "ack.txt"), ack);
        File.WriteAllText(Path.Combine(folder, "expected.txt"), context);
        var info = new ProcessStartInfo(app) { UseShellExecute = false };
        info.ArgumentList.Add("--verify-v2-server-ack-files");
        info.ArgumentList.Add(Path.Combine(folder, "pub.txt"));
        info.ArgumentList.Add(Path.Combine(folder, "ack.txt"));
        info.ArgumentList.Add(Path.Combine(folder, "expected.txt"));
        using var process = Process.Start(info)
            ?? throw new InvalidOperationException("Cannot launch compiled SoftTimer");
        if (!process.WaitForExit(30000))
        {
            process.Kill(entireProcessTree: true);
            throw new TimeoutException("Compiled SoftTimer verifier timed out");
        }
        return process.ExitCode;
    }

    private static int Main(string[] args)
    {
        if (args.Length != 1 || !File.Exists(args[0]))
            throw new ArgumentException("Pass the compiled real SoftTimer WinExe path");
        string app = Path.GetFullPath(args[0]);
        string directory = Path.Combine(Path.GetTempPath(),
            "blazepwifi-v2-public-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        int cases = 0;
        try
        {
            using var signer = ECDsa.Create(ECCurve.NamedCurves.nistP256);
            using var attacker = ECDsa.Create(ECCurve.NamedCurves.nistP256);
            using var wrongCurve = ECDsa.Create(ECCurve.NamedCurves.nistP384);
            string pub = Convert.ToBase64String(signer.ExportSubjectPublicKeyInfo());
            string otherPub = Convert.ToBase64String(attacker.ExportSubjectPublicKeyInfo());
            string p384Pub = Convert.ToBase64String(wrongCurve.ExportSubjectPublicKeyInfo());
            string context = $"{ServerId}\n{Controller}\n42\n{Fingerprint}\n";
            string[] fields =
            {
                "ACKP1","COMMIT",ServerId,Controller,"42",Controller+":42",
                Fingerprint,"60","17"
            };
            string valid = Envelope(signer, fields);
            string withNewline = valid + "\n";
            string replay = Envelope(signer,
                new[] { "ACKP1","REPLAY",ServerId,Controller,"42",
                    Controller+":42",Fingerprint,"60","17" });

            void Check(string name, bool shouldPass, string publicKey, string wire,
                string expected)
            {
                int code = RunWinExe(app, directory, publicKey, wire, expected);
                if ((code == 0) != shouldPass || (!shouldPass && code != 79))
                    throw new InvalidOperationException(
                        $"{name}: expected {(shouldPass ? "accept" : "reject")}; exit {code}");
                cases++;
            }

            Check("valid signed COMMIT",true,pub,valid,context);
            Check("valid signed REPLAY",true,pub,replay,context);
            Check("single trailing LF",true,pub,withNewline,context);
            Check("missing pinned public key",false,"",valid,context);
            Check("key substituted by attacker",false,otherPub,valid,context);
            Check("attacker signs with wrong private key",false,pub,
                Envelope(attacker,fields),context);
            Check("key rotation requires explicit trust anchor",false,pub,
                Envelope(attacker,fields),context);
            Check("P-384 algorithm mismatch",false,p384Pub,
                Envelope(wrongCurve,fields),context);
            Check("legacy symmetric ACKV2 must not be accepted",false,pub,
                valid.Replace("ACKP1","ACKV2",StringComparison.Ordinal),context);
            Check("tampered result",false,pub,
                valid.Replace("\t60\t17\t","\t61\t17\t",StringComparison.Ordinal),context);
            Check("tampered revision",false,pub,
                valid.Replace("\t60\t17\t","\t60\t18\t",StringComparison.Ordinal),context);
            Check("tampered signature",false,pub,valid[..^3]+"ABC",context);
            Check("extra delimiter",false,pub,valid+"\tunexpected",context);
            Check("extra newline",false,pub,valid+"\n\n",context);
            Check("wrong context/controller",false,pub,valid,
                $"{ServerId}\nothercontroller\n42\n{Fingerprint}\n");
            Check("wrong context/sequence",false,pub,valid,
                $"{ServerId}\n{Controller}\n43\n{Fingerprint}\n");
            Check("wrong request SHA",false,pub,valid,
                $"{ServerId}\n{Controller}\n42\n{new string('0',64)}\n");
            Check("revoked key identifier",false,pub,valid,
                $"revoked\n{Controller}\n42\n{Fingerprint}\n");
            Check("wrong signed domain",false,pub,
                Envelope(signer,fields,"BLAZEPWIFI-MEMBER-V2-ACK/ECDSA-P256-SHA256/0"),
                context);
            Check("noncanonical zero-padded sequence",false,pub,Envelope(signer,
                new[] {"ACKP1","COMMIT",ServerId,Controller,"042",Controller+":42",
                    Fingerprint,"60","17"}),context);
            Check("wrong event identity",false,pub,Envelope(signer,
                new[] {"ACKP1","COMMIT",ServerId,Controller,"42",Controller+":43",
                    Fingerprint,"60","17"}),context);
            Check("unsupported outcome",false,pub,Envelope(signer,
                new[] {"ACKP1","RETRY",ServerId,Controller,"42",Controller+":42",
                    Fingerprint,"60","17"}),context);
            Check("noncanonical result",false,pub,Envelope(signer,
                new[] {"ACKP1","COMMIT",ServerId,Controller,"42",Controller+":42",
                    Fingerprint,"060","17"}),context);
            Check("no private key as public pin",false,
                Convert.ToBase64String(signer.ExportECPrivateKey()),valid,context);
            Console.WriteLine($"PAY-0720 compiled Windows public-only P-256 signed ACK PASS ({cases} accept/reject cases)");
            Console.WriteLine("No signer/private key or production financial ACK deployed.");
            return 0;
        }
        finally
        {
            Directory.Delete(directory, recursive: true);
        }
    }
}
