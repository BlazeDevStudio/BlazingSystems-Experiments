// PHX-PISONET #216 native CLR regression, actual extracted source methods.
// Original four tests retained: valid A, stale A->B, disable after await,
// and initially-disabled. Fake transport follows REAL CGI form/target_nonce ACK.
// No hardware, authenticated server receipt or actual financial credit.
using BlazePisonet.SoftTimer;

if (args.Contains("--invalid-setup", StringComparer.Ordinal))
{
    Console.Error.WriteLine("INCONCLUSIVE_EXIT_3: explicit fake-setup control");
    return 3;
}

try
{
    const string A = "aaaaaaaaaaaaaaaa";
    const string B = "bbbbbbbbbbbbbbbb";

    static void Require(bool pass, string why)
    {
        if (!pass) throw new InvalidOperationException(why);
    }
    static (AppController App, FakeCentralServer Central, BlazePwifiClient Client, AppConfig Config)
        Make(string nonce = "aaaaaaaaaaaaaaaa")
    {
        var cfg = new AppConfig
        {
            Enabled = true, BlazePwifiEnabled = true, MirrorLocalCoinsToBlazePwifi = true,
            CoinTopology = CoinTopologyMode.CentralizedCoordinator, SecondsPerCoin = 60,
            BlazePwifiControllerId = "softtimer-01",
            BlazePwifiVendoUrl = "http://example.invalid/cgi-bin/vendo",
            BlazePwifiVendoKey = "fixture-secret"
        };
        var central = new FakeCentralServer();
        var client = new BlazePwifiClient(cfg, nonce);
        return (new AppController(cfg, central, client), central, client, cfg);
    }

    // #216 original positive A: real awaited central completion, then A.
    {
        var (app, central, client, _) = Make(A);
        var pending = app.InvokeCoinPulseAsync();
        Require(central.Calls == 1 && !pending.IsCompleted, "positive did not await");
        central.Complete(true);
        await pending;
        Require(client.ForwardedTargets.SequenceEqual(new[] { A }),
            "original legitimate A was not forwarded");
        Require(client.AckResults.SequenceEqual(new[] { A }), "A ACK echo not verified");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_VALID_CONTROL_PASS: target=A calls=1 ack_bound=A");
    }

    // #216 original unsafe A->B session/target regression, now required safe.
    {
        var (app, central, client, _) = Make(A);
        var pending = app.InvokeCoinPulseAsync();
        Require(central.Calls == 1 && !pending.IsCompleted, "stale test did not await");
        app.Serial.SessionGeneration = 2;
        client.TargetNonce = B;
        central.Complete(true);
        await pending;
        Require(client.ForwardedTargets.Count == 0,
            "STALE_TARGET_RED: old A event forwarded to new B or retired session");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_STALE_TARGET_GREEN: old A/session1 not sent to B/session2");
    }

    // #216 original disable-after-central-await regression, now required safe.
    {
        var (app, central, client, cfg) = Make(A);
        var pending = app.InvokeCoinPulseAsync();
        Require(central.Calls == 1 && !pending.IsCompleted, "disable test did not await");
        cfg.Enabled = false;
        central.Complete(true);
        await pending;
        Require(client.ForwardedTargets.Count == 0,
            "DISABLED_AFTER_AWAIT_RED: revoked coin still forwarded");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_DISABLED_GREEN: post-await revoke blocked");
    }

    // #216 original initially-disabled positive negative control retained.
    {
        var (app, central, client, cfg) = Make(A);
        cfg.Enabled = false;
        await app.InvokeCoinPulseAsync();
        Require(central.Calls == 0 && client.ForwardedTargets.Count == 0,
            "initially disabled incorrectly dispatched");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_DISABLED_INITIAL_CONTROL_PASS");
    }

    // A->B even within same serial session must not use mutable window B.
    {
        var (app, central, client, _) = Make(A);
        var pending = app.InvokeCoinPulseAsync();
        Require(central.Calls == 1 && !pending.IsCompleted, "nonce-only test did not await");
        client.TargetNonce = B;
        central.Complete(true);
        await pending;
        Require(client.ForwardedTargets.Count == 0,
            "NONCE_REBIND_RED: a previously captured event followed B");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_NONCE_REBIND_GREEN");
    }

    // Same window but changed controller ID must not reuse old coin.
    {
        var (app, central, client, cfg) = Make(A);
        var pending = app.InvokeCoinPulseAsync();
        Require(central.Calls == 1 && !pending.IsCompleted, "controller test did not await");
        cfg.BlazePwifiControllerId = "other-controller";
        central.Complete(true);
        await pending;
        Require(client.ForwardedTargets.Count == 0,
            "CONTROLLER_REBIND_RED: changed controller dispatched original event");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_CONTROLLER_REBIND_GREEN");
    }

    // Real legacy CGI response must echo target_nonce. Forged/missing echo
    // cannot be treated as original-event ACK even with ok=true.
    {
        var (_, _, client, _) = Make(A);
        var snapshot = client.CaptureCoinWindow() ??
            throw new InvalidOperationException("valid initial window missing");
        client.AckTargetOverride = B;
        var accepted = await client.ForwardCoinAsync(snapshot, 1);
        Require(!accepted && client.ForwardedTargets.SequenceEqual(new[] { A }),
            "FOREIGN_ACK_RED: ok:true with B nonce counted for A");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_FOREIGN_ACK_DENIED_PASS");
    }
    {
        var (_, _, client, _) = Make(A);
        var snapshot = client.CaptureCoinWindow() ??
            throw new InvalidOperationException("valid initial window missing");
        client.RemoveAckTarget = true;
        var accepted = await client.ForwardCoinAsync(snapshot, 1);
        Require(!accepted && client.ForwardedTargets.SequenceEqual(new[] { A }),
            "MISSING_ACK_RED: ok:true without target_nonce counted");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_MISSING_ACK_DENIED_PASS");
    }
    // Repeated unchanged polls MUST preserve the window revision so an
    // already-sent original ACK is not lost solely due to normal polling.
    {
        var (_, _, client, _) = Make(A);
        var snapshot = client.CaptureCoinWindow(new SerialCoinAcceptance()) ??
            throw new InvalidOperationException("original event scope missing");
        Require(snapshot.SerialSessionEpoch == 1 && snapshot.SerialEventSequence == 7,
            "serial event not represented in immutable snapshot");
        Require(client.SimulatePoll(client.WindowVersion, true, A),
            "same-target poll rejected");
        Require(client.WindowVersion == snapshot.Version,
            "SAME_TARGET_POLL_RED: unchanged polling invalidated original event");
        Require(await client.ForwardCoinAsync(snapshot, 1),
            "same-target original ACK rejected after harmless poll");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_UNCHANGED_POLL_ACK_CONTROL_PASS");
    }

    // Retrying the SAME event must reuse its original v1 request nonce,
    // which the existing CGI folds into its duplicate-credit event key.
    {
        var (_, _, client, _) = Make(A);
        var snapshot = client.CaptureCoinWindow(new SerialCoinAcceptance()) ??
            throw new InvalidOperationException("retry event scope missing");
        Require(await client.ForwardCoinAsync(snapshot, 1), "original A ACK missing");
        Require(await client.ForwardCoinAsync(snapshot, 1), "same event retry denied");
        Require(client.RequestNonces.Count == 2 &&
                client.RequestNonces[0] == client.RequestNonces[1] &&
                client.RequestNonces[0] == snapshot.EventNonce,
                "RETRY_NONCE_RED: one event minted two different financial event nonces");
        Require(client.SimulatePoll(client.WindowVersion, true, B),
            "retarget poll not accepted");
        Require(!await client.ForwardCoinAsync(snapshot, 1),
            "STALE_RETRY_RED: original A retried into new B window");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_STABLE_EVENT_NONCE_RETRY_PASS");
    }
    // Legacy entry point has no accepted serial event owner: fail closed.
    {
        var (_, _, client, _) = Make(A);
        Require(!await client.ForwardCoinAsync(1) && client.ForwardedTargets.Count == 0,
            "UNOWNED_LEGACY_EVENT_RED: no-event forward dispatched money");
        Console.WriteLine("NATIVE_ASYNC_DISPATCH_UNOWNED_LEGACY_DENIED_PASS");
    }

    Console.WriteLine("NATIVE_ASYNC_DISPATCH_SOURCE_GREEN: original 4/4 corrected; controller/nonce and malformed-ACK cases passed");
    return 0;
}
catch (InvalidOperationException ex)
{
    Console.Error.WriteLine("NATIVE_ASYNC_DISPATCH_SAFETY_RED_EXIT_2: " + ex.Message);
    return 2;
}
catch (Exception ex)
{
    Console.Error.WriteLine("INCONCLUSIVE_EXIT_3: " + ex);
    return 3;
}

namespace BlazePisonet.SoftTimer
{
    public enum CoinTopologyMode { CentralizedCoordinator, StandardOneToOne, CentralizedStation }
    public enum TimerSourceMode { InternalPcTimer, ExternalTimerBoard }
    public sealed class AppConfig
    {
        public bool Enabled { get; set; }
        public bool BlazePwifiEnabled { get; set; }
        public bool MirrorLocalCoinsToBlazePwifi { get; set; }
        public CoinTopologyMode CoinTopology { get; set; }
        public TimerSourceMode TimerSource { get; set; }
        public int SecondsPerCoin { get; set; }
        public string BlazePwifiControllerId { get; set; } = "";
        public string BlazePwifiVendoUrl { get; set; } = "";
        public string BlazePwifiVendoKey { get; set; } = "";
    }
    public sealed record FakeDevice(string PortName);
    public sealed class SerialCoinAcceptance
    {
        public long SessionEpoch { get; } = 1;
        public long EventSequence { get; } = 7;
        public FakeDevice Device { get; } = new("COM9");
    }
    public sealed class FakeSerial
    {
        public int SessionGeneration { get; set; } = 1;
        public bool IsCoinSessionCurrent(SerialCoinAcceptance accepted) =>
            accepted.SessionEpoch == SessionGeneration;
    }
    public sealed class FakeTimer
    {
        public void AddCoin(int seconds, string source) { }
    }
    public sealed class FakeCentralServer
    {
        private readonly TaskCompletionSource<bool> _pending =
            new(TaskCreationOptions.RunContinuationsAsynchronously);
        public int Calls { get; private set; }
        public Task<bool> CreditCurrentAsync(long seconds)
        {
            Calls++;
            return _pending.Task;
        }
        public void Complete(bool routed) => _pending.SetResult(routed);
    }
    public static class Storage
    {
        public static string NormalizeId(string s) => s.Trim().ToLowerInvariant();
    }
    public sealed class FakeCoinHttpHandler : HttpMessageHandler
    {
        public readonly List<string> ForwardedTargets = new();
        public readonly List<string> ForwardedControllers = new();
        public readonly List<string> ForwardedRequestNonces = new();
        public readonly List<string> AckResults = new();
        public string? AckTargetOverride;
        public bool RemoveAckTarget;
        protected override async Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage req, CancellationToken token)
        {
            var content = await (req.Content?.ReadAsStringAsync(token) ??
                Task.FromResult(""));
            var fields = content.Split('&', StringSplitOptions.RemoveEmptyEntries)
                .Select(x => x.Split('=', 2))
                .ToDictionary(x => Uri.UnescapeDataString(x[0].Replace("+", " ")),
                    x => Uri.UnescapeDataString(x[1].Replace("+", " ")));
            if (fields["action"] != "coin" || fields["pulses"] != "1" ||
                string.IsNullOrWhiteSpace(fields["nonce"]) ||
                string.IsNullOrWhiteSpace(fields["sig"]))
                throw new InvalidOperationException("not actual coin form fields");
            ForwardedTargets.Add(fields["target"]);
            ForwardedControllers.Add(fields["id"]);
            ForwardedRequestNonces.Add(fields["nonce"]);
            string echo = AckTargetOverride ?? fields["target"];
            if (!RemoveAckTarget) AckResults.Add(echo);
            var response = RemoveAckTarget
                ? "{\"ok\":true,\"duplicate\":false,\"credited_cents\":100}"
                : System.Text.Json.JsonSerializer.Serialize(new
                    { ok = true, duplicate = false, credited_cents = 100, target_nonce = echo });
            return new HttpResponseMessage(System.Net.HttpStatusCode.OK)
            {
                Content = new StringContent(response)
            };
        }
    }
    public sealed partial class BlazePwifiClient
    {
        private AppConfig _config;
        private readonly object _coinWindowGate = new();
        private string _targetNonce;
        private bool _insertWindow = true;
        private long _coinWindowVersion = 1;
        private readonly FakeCoinHttpHandler _handler = new();
        private readonly HttpClient _http;
        public IReadOnlyList<string> ForwardedTargets => _handler.ForwardedTargets;
        public IReadOnlyList<string> AckResults => _handler.AckResults;
        public IReadOnlyList<string> RequestNonces => _handler.ForwardedRequestNonces;
        public long WindowVersion => _coinWindowVersion;
        public bool SimulatePoll(long originalVersion, bool active, string target) =>
            ApplyCoinWindowPollResult(originalVersion, active, target);
        public string? AckTargetOverride { set => _handler.AckTargetOverride = value; }
        public bool RemoveAckTarget { set => _handler.RemoveAckTarget = value; }
        public string TargetNonce
        {
            set { lock (_coinWindowGate) { _coinWindowVersion++; _targetNonce = value; } }
        }
        public BlazePwifiClient(AppConfig config, string nonce)
        {
            _config = config;
            _targetNonce = nonce;
            _http = new HttpClient(_handler);
        }
        public static string Signature(string key, string action, string id,
            string nonce, int pulses, string target) => new string('a', 64);
    }
    public sealed partial class AppController
    {
        public AppConfig Config { get; }
        private readonly FakeSerial _serial = new();
        private readonly FakeTimer _timer = new();
        private readonly FakeCentralServer? _centralServer;
        private readonly BlazePwifiClient _blazePwifi;
        private bool MemberReconciliationPending => false;
        public string HardwareStatus { get; private set; } = "";
        public event Action? StatusChanged;
        public AppController(AppConfig config, FakeCentralServer central, BlazePwifiClient client)
        {
            Config = config;
            _centralServer = central;
            _blazePwifi = client;
        }
        public FakeSerial Serial => _serial;
        public Task InvokeCoinPulseAsync() => HandleCoinPulse(new SerialCoinAcceptance());
    }
}
