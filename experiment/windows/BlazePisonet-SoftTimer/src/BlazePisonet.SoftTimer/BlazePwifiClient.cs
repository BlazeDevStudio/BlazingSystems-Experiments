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

// Immutable, in-process request scope. Captures the exact original controller
// identity, target nonce and connection settings; never a server-signed receipt.
internal sealed record CoinWindowSnapshot(
    AppConfig ConfigReference,
    string ControllerId,
    string TargetNonce,
    string VendoUrl,
    string VendoKey,
    long Version);

public sealed class BlazePwifiClient : IDisposable
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(4) };
    private readonly System.Threading.Timer _timer;
    private AppConfig _config;
    private string _targetNonce = string.Empty;
    private bool _insertWindow;
    private readonly object _coinWindowGate = new();
    private long _coinWindowVersion;
    private int _busy;
    private DateTimeOffset _lastMemberSync = DateTimeOffset.MinValue;

    public event Action<string>? StatusChanged;
    public event Action<BlazePwifiMemberSnapshot>? MembersReceived;
    public bool InsertWindow => _insertWindow;

    // PAY-0720: compiled Windows path for publicly verifiable server ACKs.
    // NOT called from legacy v1 or pending-money clearance: the remote v2
    // authority is still denied on OpenWrt. Consumers must supply the exact
    // immutable signed pending-request fingerprint from their durable queue.
    internal bool TryVerifyV2MemberServerAck(string envelope, long sequence,
        string pendingRequestSha256, out VerifiedV2MemberServerAck? verified) =>
        V2MemberServerAckVerifier.TryVerify(_config, envelope,
            Storage.NormalizeId(_config.BlazePwifiControllerId), sequence,
            pendingRequestSha256, out verified);

    // PAY-0719: this is a *deny* gate, not a v2 implementation or feature flag
    // that authorizes migration. A required v2 protocol MUST never send an
    // unsigned/legacy member request or accept a v1 money acknowledgment.
    public static bool LegacyMemberWireAllowed(AppConfig config, string action) =>
        !config.BlazePwifiRequireV2MemberProtocol
        || !action.StartsWith("member_", StringComparison.Ordinal);

    // Headless compiled-product regression: no network, UI, hardware or money.
    public static int VerifyV2MemberProtocolGate()
    {
        var config = new AppConfig
        {
            BlazePwifiEnabled = true,
            BlazePwifiMemberAuthorityEnabled = true,
            BlazePwifiRequireV2MemberProtocol = true
        };
        foreach (var action in new[]
        {
            "member_snapshot", "member_auth", "member_bank",
            "member_restore", "member_transfer", "member_v2_negotiate"
        })
            if (LegacyMemberWireAllowed(config, action)) return 21;
        if (!LegacyMemberWireAllowed(config, "poll")
            || !LegacyMemberWireAllowed(config, "ping")) return 22;
        using (var client = new BlazePwifiClient(config))
        {
            if (client.SyncMembersAsync().GetAwaiter().GetResult() is not null) return 23;
            var syntheticMember = new MemberAccount
            {
                Username = "fixture", Enabled = true, PasswordScheme = "sha256i"
            };
            if (client.BankMemberAsync(syntheticMember, "", 60).GetAwaiter().GetResult() is not null)
                return 24;
            if (client.RestoreMemberAsync(syntheticMember, "").GetAwaiter().GetResult() is not null)
                return 25;
        }
        config.BlazePwifiRequireV2MemberProtocol = false;
        foreach (var action in new[] { "member_snapshot", "member_auth", "member_bank",
            "member_restore", "member_transfer" })
            if (!LegacyMemberWireAllowed(config, action)) return 26;
        return 0;
    }
    public string TargetNonce => _targetNonce;

    public BlazePwifiClient(AppConfig config)
    {
        _config = config;
        _timer = new System.Threading.Timer(async _ => await Poll(), null, Timeout.Infinite, Timeout.Infinite);
    }

    public void UpdateConfig(AppConfig config)
    {
        lock (_coinWindowGate)
        {
            _config = config;
            _coinWindowVersion++;
            _insertWindow = false;
            _targetNonce = string.Empty;
        }
    }

    public void Start()
    {
        if (!_config.BlazePwifiEnabled) return;
        _timer.Change(0, 2500);
    }

    public void Stop()
    {
        _timer.Change(Timeout.Infinite, Timeout.Infinite);
        lock (_coinWindowGate)
        {
            _coinWindowVersion++;
            _insertWindow = false;
            _targetNonce = string.Empty;
        }
    }

    private async Task Poll()
    {
        if (!_config.BlazePwifiEnabled || string.IsNullOrWhiteSpace(_config.BlazePwifiVendoKey)) return;
        if (Interlocked.Exchange(ref _busy, 1) != 0) return;
        long requestedVersion;
        lock (_coinWindowGate) requestedVersion = _coinWindowVersion;
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
            bool newWindow = root.TryGetProperty("insert", out var ins) &&
                (ins.ValueKind == JsonValueKind.True ||
                 (ins.ValueKind == JsonValueKind.Number && ins.GetInt32() == 1));
            string newTarget = root.TryGetProperty("target_nonce", out var tn) &&
                tn.ValueKind == JsonValueKind.String
                    ? tn.GetString() ?? string.Empty : string.Empty;
            lock (_coinWindowGate)
            {
                // Old HTTP poll results cannot reopen a window after Stop or
                // update/reconnect. Each response creates a new window version.
                if (requestedVersion != _coinWindowVersion) return;
                _coinWindowVersion++;
                _insertWindow = newWindow;
                _targetNonce = newTarget;
            }

            var status = newWindow ? "BlazePwifi connected · coin window active" : "BlazePwifi connected";
            if (_config.BlazePwifiMemberAuthorityEnabled
                && !_config.BlazePwifiRequireV2MemberProtocol
                && DateTimeOffset.UtcNow - _lastMemberSync >= TimeSpan.FromSeconds(Math.Clamp(_config.BlazePwifiMemberSyncSeconds, 5, 300)))
            {
                var snapshot = await SyncMembersCoreAsync();
                if (snapshot is not null)
                {
                    _lastMemberSync = DateTimeOffset.UtcNow;
                    status += $" · members r{snapshot.Revision}";
                }
            }
            if (_config.BlazePwifiRequireV2MemberProtocol)
                status += " · V2 member authority unavailable: legacy member operations BLOCKED";
            StatusChanged?.Invoke(status);
        }
        catch (Exception ex) { StatusChanged?.Invoke("BlazePwifi error: " + ex.Message); }
        finally { Interlocked.Exchange(ref _busy, 0); }
    }

    // Capture ONCE before an upstream await. A changed target, controller,
    // policy or window generation can never be silently substituted.
    internal CoinWindowSnapshot? CaptureCoinWindow()
    {
        lock (_coinWindowGate)
        {
            var cfg = _config;
            var id = Storage.NormalizeId(cfg.BlazePwifiControllerId);
            if (!cfg.Enabled || !cfg.BlazePwifiEnabled ||
                !cfg.MirrorLocalCoinsToBlazePwifi || !_insertWindow ||
                string.IsNullOrWhiteSpace(_targetNonce) ||
                string.IsNullOrWhiteSpace(id) ||
                string.IsNullOrWhiteSpace(cfg.BlazePwifiVendoUrl) ||
                string.IsNullOrWhiteSpace(cfg.BlazePwifiVendoKey))
                return null;
            return new CoinWindowSnapshot(
                cfg, id, _targetNonce, cfg.BlazePwifiVendoUrl,
                cfg.BlazePwifiVendoKey, _coinWindowVersion);
        }
    }

    private bool CoinWindowStillOwned(CoinWindowSnapshot captured)
    {
        lock (_coinWindowGate)
        {
            var cfg = _config;
            return captured.Version == _coinWindowVersion &&
                ReferenceEquals(captured.ConfigReference, cfg) &&
                cfg.Enabled && cfg.BlazePwifiEnabled &&
                cfg.MirrorLocalCoinsToBlazePwifi && _insertWindow &&
                string.Equals(captured.TargetNonce, _targetNonce, StringComparison.Ordinal) &&
                string.Equals(captured.ControllerId,
                    Storage.NormalizeId(cfg.BlazePwifiControllerId), StringComparison.Ordinal) &&
                string.Equals(captured.VendoUrl, cfg.BlazePwifiVendoUrl, StringComparison.Ordinal) &&
                string.Equals(captured.VendoKey, cfg.BlazePwifiVendoKey, StringComparison.Ordinal);
        }
    }

    // This compatibility entry point also captures the window once. It must
    // not be used to rediscover a target after an unrelated await.
    public Task<bool> ForwardCoinAsync(int pulses = 1)
    {
        var snapshot = CaptureCoinWindow();
        return snapshot is null ? Task.FromResult(false) : ForwardCoinAsync(snapshot, pulses);
    }

    internal async Task<bool> ForwardCoinAsync(CoinWindowSnapshot captured, int pulses = 1)
    {
        if (captured is null || !CoinWindowStillOwned(captured)) return false;
        try
        {
            var nonce = Convert.ToHexString(RandomNumberGenerator.GetBytes(8)).ToLowerInvariant();
            var sig = Signature(captured.VendoKey, "coin", captured.ControllerId,
                nonce, Math.Clamp(pulses, 1, 20), captured.TargetNonce);
            // The actual legacy v1 form fields are action/id/nonce/pulses/
            // target/sig. All values come from the ORIGINAL window, not _config.
            var form = new Dictionary<string, string>
            {
                ["action"] = "coin",
                ["id"] = captured.ControllerId,
                ["nonce"] = nonce,
                ["pulses"] = Math.Clamp(pulses, 1, 20).ToString(),
                ["target"] = captured.TargetNonce,
                ["sig"] = sig
            };
            if (!CoinWindowStillOwned(captured)) return false;
            using var resp = await _http.PostAsync(captured.VendoUrl,
                new FormUrlEncodedContent(form));
            var json = await resp.Content.ReadAsStringAsync();
            if (!resp.IsSuccessStatusCode || !CoinWindowStillOwned(captured))
                return false;
            using var doc = JsonDocument.Parse(json);
            var root = doc.RootElement;
            // The actual v1 CGI echoes target_nonce on BOTH first and replay
            // coin ACKs. Missing/mismatched echo is never considered success.
            // This remains a correlation check, not a signed paid receipt.
            return root.TryGetProperty("ok", out var ok) &&
                ok.ValueKind == JsonValueKind.True &&
                root.TryGetProperty("target_nonce", out var tn) &&
                tn.ValueKind == JsonValueKind.String &&
                string.Equals(tn.GetString(), captured.TargetNonce,
                    StringComparison.Ordinal);
        }
        catch { return false; }
    }

    public async Task<BlazePwifiMemberSnapshot?> SyncMembersAsync()
    {
        if (!_config.BlazePwifiEnabled || !_config.BlazePwifiMemberAuthorityEnabled
            || !LegacyMemberWireAllowed(_config, "member_snapshot")) return null;
        var snapshot = await SyncMembersCoreAsync();
        if (snapshot is not null) _lastMemberSync = DateTimeOffset.UtcNow;
        return snapshot;
    }

    private async Task<BlazePwifiMemberSnapshot?> SyncMembersCoreAsync()
    {
        if (!LegacyMemberWireAllowed(_config, "member_snapshot")) return null;
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
            || !LegacyMemberWireAllowed(_config, action)
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
        if (!_config.BlazePwifiEnabled || !_config.BlazePwifiMemberAuthorityEnabled
            || !LegacyMemberWireAllowed(_config, pending.Action))
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
        // Final dispatch boundary: even a future caller bypassing the public
        // method guards cannot downgrade a v2-required member transaction.
        if (!LegacyMemberWireAllowed(_config, action)) return null;
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
