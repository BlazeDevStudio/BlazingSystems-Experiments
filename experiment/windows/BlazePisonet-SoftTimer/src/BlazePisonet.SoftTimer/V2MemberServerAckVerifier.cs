using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace BlazePisonet.SoftTimer;

// PAY-0720: REAL compiled WinExe verification boundary, PUBLIC KEY ONLY.
// DO NOT send v2 financial transactions or clear PendingMemberOperation from
// this verifier: server durable journal, quiesced migration, external freshness
// witness, key distribution and physical power cut have not been accepted.
// There is deliberately NO signing/private-key API in this application.
internal sealed record VerifiedV2MemberServerAck(
    string ControllerId, long Sequence, string EventId, string RequestSha256,
    long ResultSeconds, long MemberRevision, bool IsReplay, string KeyId);

internal static class V2MemberServerAckVerifier
{
    // Exact UTF-8 bytes: Domain + LF + first NINE tab-separated ACKP1
    // fields + LF. Wire field 10 is base64 RFC3279 DER ECDSA signature.
    // P-256/SHA-256; symmetric ACKV1/ACKV2 or v1 response_sig NEVER accepted.
    internal const string Domain = "BLAZEPWIFI-MEMBER-V2-ACK/ECDSA-P256-SHA256/1";
    private static readonly Regex Id = new(
        @"\A[A-Za-z][A-Za-z0-9_.-]{0,31}\z", RegexOptions.CultureInvariant);
    private static readonly Regex Digest = new(
        @"\A[0-9a-f]{64}\z", RegexOptions.CultureInvariant);

    internal static bool SameTrustAnchor(AppConfig a, AppConfig b) =>
        string.Equals(a.BlazePwifiV2ServerKeyId, b.BlazePwifiV2ServerKeyId,
            StringComparison.Ordinal)
        && string.Equals(a.BlazePwifiV2ServerPublicKeySpkiBase64,
            b.BlazePwifiV2ServerPublicKeySpkiBase64, StringComparison.Ordinal);

    private static bool CanonicalNumber(string value, long min, long max, out long result)
    {
        result = 0;
        return value.Length is > 0 and <= 10
            && long.TryParse(value, NumberStyles.None, CultureInfo.InvariantCulture,
                out result)
            && result >= min && result <= max
            && string.Equals(value, result.ToString(CultureInfo.InvariantCulture),
                StringComparison.Ordinal);
    }

    private static bool CanonicalBase64(string raw, int min, int max, out byte[] bytes)
    {
        bytes = Array.Empty<byte>();
        if (raw.Length < min || raw.Length > max ||
            raw.Any(c => !(char.IsAsciiLetterOrDigit(c) || c is '+' or '/' or '=')))
            return false;
        try
        {
            bytes = Convert.FromBase64String(raw);
            return string.Equals(Convert.ToBase64String(bytes), raw,
                StringComparison.Ordinal);
        }
        catch (FormatException) { return false; }
    }

    internal static bool TryVerify(
        AppConfig config, string response, string expectedController,
        long expectedSequence, string expectedRequestSha256,
        out VerifiedV2MemberServerAck? verified)
    {
        verified = null;
        if (config is null || !config.BlazePwifiRequireV2MemberProtocol ||
            string.IsNullOrEmpty(response) || response.Length > 1536 ||
            !Id.IsMatch(config.BlazePwifiV2ServerKeyId ?? "") ||
            !Id.IsMatch(expectedController) ||
            !Digest.IsMatch(expectedRequestSha256) ||
            expectedSequence is < 1 or > 100_000_000)
            return false;

        // Exactly one optional final LF permitted; reject CR, second LF,
        // controls or unexpected whitespace inside signed fields.
        if (response.EndsWith('\n')) response = response[..^1];
        if (response.Any(c => c is '\r' or '\n' or '\0'))
            return false;
        var fields = response.Split('\t');
        if (fields.Length != 10 || fields[0] != "ACKP1" ||
            fields[1] is not ("COMMIT" or "REPLAY") ||
            fields[2] != config.BlazePwifiV2ServerKeyId ||
            fields[3] != expectedController ||
            !CanonicalNumber(fields[4], 1, 100_000_000, out var sequence) ||
            sequence != expectedSequence ||
            fields[5] != expectedController + ":" +
                expectedSequence.ToString(CultureInfo.InvariantCulture) ||
            !string.Equals(fields[6], expectedRequestSha256,
                StringComparison.Ordinal) ||
            !CanonicalNumber(fields[7], 0, 2_147_483_647, out var result) ||
            !CanonicalNumber(fields[8], 0, 2_147_483_647, out var revision) ||
            !CanonicalBase64(fields[9], 8, 200, out var signature) ||
            signature.Length is < 64 or > 80 ||
            !CanonicalBase64(config.BlazePwifiV2ServerPublicKeySpkiBase64 ?? "",
                80, 800, out var pub) ||
            pub.Length is < 70 or > 300)
            return false;

        try
        {
            using var ecdsa = ECDsa.Create();
            ecdsa.ImportSubjectPublicKeyInfo(pub, out int read);
            if (read != pub.Length || ecdsa.KeySize != 256)
                return false;
            var parameters = ecdsa.ExportParameters(false);
            if (parameters.Curve.Oid.Value != "1.2.840.10045.3.1.7" ||
                !ecdsa.ExportSubjectPublicKeyInfo().AsSpan().SequenceEqual(pub))
                return false;

            var message = Encoding.ASCII.GetBytes(Domain + "\n" +
                string.Join("\t", fields.Take(9)) + "\n");
            if (!ecdsa.VerifyData(message, signature, HashAlgorithmName.SHA256,
                    DSASignatureFormat.Rfc3279DerSequence))
                return false;

            verified = new VerifiedV2MemberServerAck(
                expectedController, sequence, fields[5], fields[6],
                result, revision, fields[1] == "REPLAY", fields[2]);
            return true;
        }
        catch (Exception ex) when (ex is CryptographicException
            or ArgumentException or NotSupportedException)
        {
            return false;
        }
    }
}
