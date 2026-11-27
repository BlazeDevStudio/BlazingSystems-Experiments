using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace BlazePisonet.SoftTimer;

public sealed record BlazePwifiMemberSnapshot(long Revision, IReadOnlyList<MemberAccount> Members);

public sealed record BlazePwifiMemberMutationResult(
    string EventId,
    long ResultSeconds,
    long BankedSeconds,
    long Revision);

public sealed class BlazePwifiClient : IDisposable
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(4) };
    private readonly System.Threading.Timer _timer;
    private AppConfig _config;
    private string _targetNonce = string.Empty;
    private bool _insertWindow;
    private int _busy;
    private DateTimeOffset _lastMemberSync = DateTimeOffset.MinValue;

    public event Action<string>? StatusChanged;
    public event Action<BlazePwifiMemberSnapshot>? MembersReceived;
    public bool InsertWindow => _insertWindow;
    public string TargetNonce => _targetNonce;

    public BlazePwifiClient(AppConfig config)
    {
        _config = config;
        _timer = new System.Threading.Timer(async _ => await Poll(), null, Timeout.Infinite, Timeout.Infinite);
    }

    public void UpdateConfig(AppConfig config) => _config = config;

    public void Start()
    {
        if (!_config.BlazePwifiEnabled) return;
        _timer.Change(0, 2500);
    }

    public void Stop() => _timer.Change(Timeout.Infinite, Timeout.Infinite);

    private async Task Poll()
    {
        if (!_config.BlazePwifiEnabled || string.IsNullOrWhiteSpace(_config.BlazePwifiVendoKey)) return;
        if (Interlocked.Exchange(ref _busy, 1) != 0) return;
        try
        {
            var json = await Call("poll", 0, string.Empty);
            if (json is null)
            {
                StatusChanged?.Invoke("BlazePwifi offline");
                return;
            }
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            _insertWindow = root.TryGetProperty("insert", out var ins) && (ins.ValueKind == JsonValueKind.True || (ins.ValueKind == JsonValueKind.Number && ins.GetInt32() == 1));
            _targetNonce = root.TryGetProperty("target_nonce", out var tn) ? tn.GetString() ?? string.Empty : string.Empty;

            var status = _insertWindow ? "BlazePwifi connected · coin window active" : "BlazePwifi connected";
            if (_config.BlazePwifiMemberAuthorityEnabled
                && DateTimeOffset.UtcNow - _lastMemberSync >= TimeSpan.FromSeconds(Math.Clamp(_config.BlazePwifiMemberSyncSeconds, 5, 300)))
            {
                var snapshot = await SyncMembersCoreAsync();
                if (snapshot is not null)
                {
                    _lastMemberSync = DateTimeOffset.UtcNow;
                    status += $" · members r{snapshot.Revision}";
                }
            }
            StatusChanged?.Invoke(status);
        }
        catch (Exception ex) { StatusChanged?.Invoke("BlazePwifi error: " + ex.Message); }
        finally { Interlocked.Exchange(ref _busy, 0); }
    }

    public async Task<bool> ForwardCoinAsync(int pulses = 1)
    {
        if (!_config.BlazePwifiEnabled || !_config.MirrorLocalCoinsToBlazePwifi || !_insertWindow || string.IsNullOrWhiteSpace(_targetNonce)) return false;
        try
        {
            var json = await Call("coin", Math.Clamp(pulses, 1, 20), _targetNonce);
            if (json is null) return false;
            using var doc = JsonDocument.Parse(json);
            return doc.RootElement.TryGetProperty("ok", out var ok) && ok.GetBoolean();
        }
        catch { return false; }
    }

    public async Task<BlazePwifiMemberSnapshot?> SyncMembersAsync()
    {
        if (!_config.BlazePwifiEnabled || !_config.BlazePwifiMemberAuthorityEnabled) return null;
        var snapshot = await SyncMembersCoreAsync();
        if (snapshot is not null) _lastMemberSync = DateTimeOffset.UtcNow;
        return snapshot;
    }

    private async Task<BlazePwifiMemberSnapshot?> SyncMembersCoreAsync()
    {
        var call = await CallDetailed("member_snapshot", 0, string.Empty);
        if (call is null) return null;

        using var doc = JsonDocument.Parse(call.Json);
        var root = doc.RootElement;
        if (!root.TryGetProperty("ok", out var ok) || ok.ValueKind != JsonValueKind.True) return null;
        if (!root.TryGetProperty("members", out var membersElement) || membersElement.ValueKind != JsonValueKind.Array) return null;

        var revision = root.TryGetProperty("member_revision", out var rev) ? rev.GetInt64() : 0;
        var payloadHash = root.TryGetProperty("payload_sha256", out var ph) ? ph.GetString() ?? string.Empty : string.Empty;
        var responseSig = root.TryGetProperty("response_sig", out var rs) ? rs.GetString() ?? string.Empty : string.Empty;
        var membersRaw = membersElement.GetRawText();
        if (!FixedHexEquals(payloadHash, HexSha256(membersRaw))) return null;

        var id = Storage.NormalizeId(_config.BlazePwifiControllerId);
        var expectedSig = HexSha256($"{_config.BlazePwifiVendoKey}|member_snapshot|{id}|{call.Nonce}|{revision}|{payloadHash}|{_config.BlazePwifiVendoKey}");
        if (!FixedHexEquals(responseSig, expectedSig)) return null;

        var members = new List<MemberAccount>();
        foreach (var item in membersElement.EnumerateArray())
        {
            var username = item.TryGetProperty("username", out var u) ? u.GetString() ?? string.Empty : string.Empty;
            if (string.IsNullOrWhiteSpace(username)) continue;
            var updatedUnix = item.TryGetProperty("updated", out var updated) && updated.TryGetInt64(out var unix) ? unix : 0;
            members.Add(new MemberAccount
            {
                Username = username,
                Label = item.TryGetProperty("label", out var label) ? label.GetString() ?? string.Empty : string.Empty,
                Enabled = item.TryGetProperty("enabled", out var enabled) && enabled.GetInt32() == 1,
                PasswordScheme = item.TryGetProperty("scheme", out var scheme) ? scheme.GetString() ?? "sha256i" : "sha256i",
                PasswordSalt = item.TryGetProperty("salt", out var salt) ? salt.GetString() ?? string.Empty : string.Empty,
                PasswordHash = string.Empty,
                PasswordRounds = item.TryGetProperty("rounds", out var rounds) ? rounds.GetInt32() : 4096,
                BankedSeconds = item.TryGetProperty("banked_seconds", out var banked) ? banked.GetInt64() : 0,
                Revision = item.TryGetProperty("revision", out var memberRev) ? memberRev.GetInt64() : revision,
                RemoteManaged = true,
                UpdatedUtc = updatedUnix > 0 ? DateTimeOffset.FromUnixTimeSeconds(updatedUnix) : DateTimeOffset.UtcNow
            });
        }

        var snapshot = new BlazePwifiMemberSnapshot(revision, members);
        MembersReceived?.Invoke(snapshot);
        return snapshot;
    }

    public Task<BlazePwifiMemberMutationResult?> BankMemberAsync(
        MemberAccount member,
        string password,
        long seconds,
        string? eventId = null) =>
        MemberMutationAsync("member_bank", member, password, member.Username, seconds, "banked_seconds", eventId);

    public Task<BlazePwifiMemberMutationResult?> RestoreMemberAsync(
        MemberAccount member,
        string password,
        string? eventId = null) =>
        MemberMutationAsync("member_restore", member, password, member.Username, 0, "banked_seconds", eventId);

    public Task<BlazePwifiMemberMutationResult?> TransferMemberAsync(
        MemberAccount sourceMember,
        string password,
        string toUsername,
        long seconds,
        string? eventId = null) =>
        MemberMutationAsync("member_transfer", sourceMember, password, $"{sourceMember.Username}>{toUsername}", seconds, "source_banked_seconds", eventId);

    private async Task<BlazePwifiMemberMutationResult?> MemberMutationAsync(
        string action,
        MemberAccount member,
        string password,
        string memberToken,
        long seconds,
        string balanceField,
        string? eventIdOverride)
    {
        if (!_config.BlazePwifiEnabled
            || !_config.BlazePwifiMemberAuthorityEnabled
            || !member.Enabled
            || !member.PasswordScheme.Equals("sha256i", StringComparison.OrdinalIgnoreCase)
            || seconds < 0
            || seconds > 31_536_000)
            return null;

        var id = Storage.NormalizeId(_config.BlazePwifiControllerId);
        var eventId = string.IsNullOrWhiteSpace(eventIdOverride)
            ? CreateMemberEventId(action, memberToken, member.Revision, seconds)
            : eventIdOverride;

        for (var attempt = 0; attempt < 2; attempt++)
        {
            var nonce = Convert.ToHexString(RandomNumberGenerator.GetBytes(8)).ToLowerInvariant();
            var verifier = Passwords.DeriveSha256iVerifier(password, member.PasswordSalt, member.PasswordRounds);
            var proof = HexSha256($"{verifier}|{nonce}|{id}|{_config.BlazePwifiVendoKey}");
            var target = $"{memberToken}:{eventId}:{proof}";

            var call = await CallDetailedWithNonce(action, checked((int)seconds), target, nonce);
            if (call is null) continue;

            using var doc = JsonDocument.Parse(call.Json);
            var root = doc.RootElement;
            if (!root.TryGetProperty("ok", out var ok) || ok.ValueKind != JsonValueKind.True)
                return null;

            var returnedEvent = root.TryGetProperty("event_id", out var eid) ? eid.GetString() ?? string.Empty : string.Empty;
            if (!returnedEvent.Equals(eventId, StringComparison.OrdinalIgnoreCase))
                return null;

            var resultSeconds = root.TryGetProperty("result_seconds", out var result) ? result.GetInt64() : 0;
            var balanceSeconds = root.TryGetProperty(balanceField, out var balance) ? balance.GetInt64() : 0;
            var revision = root.TryGetProperty("member_revision", out var rev) ? rev.GetInt64() : 0;
            var responseSig = root.TryGetProperty("response_sig", out var sig) ? sig.GetString() ?? string.Empty : string.Empty;

            var expectedSig = HexSha256(
                $"{_config.BlazePwifiVendoKey}|{action}|{id}|{call.Nonce}|{eventId}|{memberToken}|{resultSeconds}|{balanceSeconds}|{revision}|{_config.BlazePwifiVendoKey}");
            if (!FixedHexEquals(responseSig, expectedSig))
                return null;

            return new BlazePwifiMemberMutationResult(eventId, resultSeconds, balanceSeconds, revision);
        }

        return null;
    }

    public string CreateMemberEventId(string action, string memberToken, long memberRevision, long seconds)
    {
        _ = action;
        _ = memberToken;
        _ = memberRevision;
        _ = seconds;
        return Convert.ToHexString(RandomNumberGenerator.GetBytes(16)).ToLowerInvariant();
    }

    public async Task<BlazePwifiMemberMutationResult?> ReplayMemberOperationAsync(PendingMemberOperation pending)
    {
        if (!_config.BlazePwifiEnabled || !_config.BlazePwifiMemberAuthorityEnabled)
            return null;

        var balanceField = pending.Action == "member_transfer"
            ? "source_banked_seconds"
            : "banked_seconds";
        if (pending.Action is not ("member_bank" or "member_restore" or "member_transfer"))
            return null;

        var nonce = Convert.ToHexString(RandomNumberGenerator.GetBytes(8)).ToLowerInvariant();
        var target = $"{pending.MemberToken}:{pending.EventId}:replay";
        var call = await CallDetailedWithNonce(
            pending.Action,
            checked((int)Math.Clamp(pending.Seconds, 0, 31_536_000)),
            target,
            nonce);
        if (call is null) return null;

        using var doc = JsonDocument.Parse(call.Json);
        var root = doc.RootElement;
        if (!root.TryGetProperty("ok", out var ok) || ok.ValueKind != JsonValueKind.True)
            return null;

        var returnedEvent = root.TryGetProperty("event_id", out var eid)
            ? eid.GetString() ?? string.Empty
            : string.Empty;
        if (!returnedEvent.Equals(pending.EventId, StringComparison.OrdinalIgnoreCase))
            return null;

        var resultSeconds = root.TryGetProperty("result_seconds", out var result)
            ? result.GetInt64()
            : 0;
        var balanceSeconds = root.TryGetProperty(balanceField, out var balance)
            ? balance.GetInt64()
            : 0;
        var revision = root.TryGetProperty("member_revision", out var rev)
            ? rev.GetInt64()
            : 0;
        var responseSig = root.TryGetProperty("response_sig", out var sig)
            ? sig.GetString() ?? string.Empty
            : string.Empty;

        var id = Storage.NormalizeId(_config.BlazePwifiControllerId);
        var expectedSig = HexSha256(
            $"{_config.BlazePwifiVendoKey}|{pending.Action}|{id}|{call.Nonce}|{pending.EventId}|{pending.MemberToken}|{resultSeconds}|{balanceSeconds}|{revision}|{_config.BlazePwifiVendoKey}");
        if (!FixedHexEquals(responseSig, expectedSig))
            return null;

        return new BlazePwifiMemberMutationResult(
            pending.EventId,
            resultSeconds,
            balanceSeconds,
            revision);
    }

    public async Task<bool> PingAsync()
    {
        var json = await Call("ping", 0, string.Empty);
        return json is not null;
    }

    private async Task<string?> Call(string action, int pulses, string target)
    {
        var result = await CallDetailed(action, pulses, target);
        return result?.Json;
    }

    private Task<CallResult?> CallDetailed(string action, int pulses, string target) =>
        CallDetailedWithNonce(action, pulses, target, null);

    private async Task<CallResult?> CallDetailedWithNonce(string action, int pulses, string target, string? nonceOverride)
    {
        if (string.IsNullOrWhiteSpace(_config.BlazePwifiVendoUrl)
            || string.IsNullOrWhiteSpace(_config.BlazePwifiVendoKey))
            return null;

        var id = Storage.NormalizeId(_config.BlazePwifiControllerId);
        var nonce = string.IsNullOrWhiteSpace(nonceOverride)
            ? Convert.ToHexString(RandomNumberGenerator.GetBytes(8)).ToLowerInvariant()
            : nonceOverride;
        var sig = Signature(_config.BlazePwifiVendoKey, action, id, nonce, pulses, target);
        var form = new Dictionary<string, string>
        {
            ["action"] = action,
            ["id"] = id,
            ["nonce"] = nonce,
            ["pulses"] = pulses.ToString(),
            ["target"] = target,
            ["sig"] = sig
        };
        using var resp = await _http.PostAsync(_config.BlazePwifiVendoUrl, new FormUrlEncodedContent(form));
        var text = await resp.Content.ReadAsStringAsync();
        if (!resp.IsSuccessStatusCode)
        {
            Storage.Log($"BlazePwifi {action} failed {(int)resp.StatusCode}: {text}");
            return null;
        }
        return new CallResult(text, nonce);
    }

    public static string Signature(string secret, string action, string id, string nonce, int pulses, string target)
    {
        var raw = $"{secret}|{action}|{id}|{nonce}|{pulses}|{target}|{secret}";
        return HexSha256(raw);
    }

    private static string HexSha256(string value) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();

    private static bool FixedHexEquals(string left, string right)
    {
        if (left.Length != right.Length || left.Length == 0) return false;
        return CryptographicOperations.FixedTimeEquals(
            Encoding.ASCII.GetBytes(left.ToLowerInvariant()),
            Encoding.ASCII.GetBytes(right.ToLowerInvariant()));
    }

    public void Dispose()
    {
        _timer.Dispose();
        _http.Dispose();
    }

    private sealed record CallResult(string Json, string Nonce);
}
