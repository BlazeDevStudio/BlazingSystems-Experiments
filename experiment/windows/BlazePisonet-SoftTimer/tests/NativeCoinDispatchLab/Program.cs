// TEST ONLY: verbatim production AppController.HandleCoinPulse and
// BlazePwifiClient.ForwardCoinAsync are extracted at CI time from guarded Git blobs.
// Fake only the central await, serial session, timer and HTTP/network boundary.
// --diagnostic exits 0 ONLY when the vulnerable native C# source behavior is
// reproduced. --safety-gate exits 2 on unsafe dispatch. Neither proves hardware.
using BlazePisonet.SoftTimer;

static void Require(bool condition, string message)
{
    if (!condition) throw new Exception("NATIVE_DISPATCH_MISMATCH: " + message);
}
static (AppController App, FakeCentralServer Central, BlazePwifiClient Client, AppConfig Config)
    Make(string nonce = "A")
{
    var cfg = new AppConfig
    {
        Enabled = true, BlazePwifiEnabled = true,
        MirrorLocalCoinsToBlazePwifi = true,
        CoinTopology = CoinTopologyMode.CentralizedCoordinator,
        SecondsPerCoin = 60
    };
    var central = new FakeCentralServer();
    var client = new BlazePwifiClient(cfg, nonce);
    return (new AppController(cfg, central, client), central, client, cfg);
}

// Nonvacuous positive control: source really awaits and forwards to original A.
{
    var (app, central, client, _) = Make();
    var pending = app.InvokeCoinPulseAsync();
    Require(central.Calls == 1 && !pending.IsCompleted, "central await not reached");
    central.Complete(true);
    await pending;
    Require(client.ForwardedTargets.SequenceEqual(new[] { "A" }), "valid target A not forwarded");
    Console.WriteLine("NATIVE_ASYNC_DISPATCH_VALID_CONTROL: target=A calls=1");
}

// Stale session/target: event originated at session 1/A. Reconnect/retarget
// during the actual extracted source await, before ForwardCoinAsync is called.
bool staleForward;
{
    var (app, central, client, _) = Make();
    var pending = app.InvokeCoinPulseAsync();
    Require(central.Calls == 1 && !pending.IsCompleted, "stale await not reached");
    app.Serial.SessionGeneration = 2; // fake replacement session
    client.TargetNonce = "B"; // fake new coin window; no new accepted coin
    central.Complete(true);
    await pending;
    staleForward = client.ForwardedTargets.SequenceEqual(new[] { "B" });
    Console.WriteLine($"NATIVE_ASYNC_DISPATCH_STALE_TARGET: origin=A/session1 forwarded={string.Join(",", client.ForwardedTargets)} current_session={app.Serial.SessionGeneration}");
}

// Disabling after the initial Config.Enabled check cannot cancel the already
// in-flight async void event handler; source has no post-await admission check.
bool disabledForward;
{
    var (app, central, client, cfg) = Make();
    var pending = app.InvokeCoinPulseAsync();
    Require(central.Calls == 1 && !pending.IsCompleted, "disable await not reached");
    cfg.Enabled = false;
    central.Complete(true);
    await pending;
    disabledForward = client.ForwardedTargets.SequenceEqual(new[] { "A" });
    Console.WriteLine($"NATIVE_ASYNC_DISPATCH_DISABLED: enabled_after_await={cfg.Enabled} forwarded={string.Join(",", client.ForwardedTargets)}");
}

// Negative control: initially disabled source does not enter central dispatch.
{
    var (app, central, client, cfg) = Make();
    cfg.Enabled = false;
    await app.InvokeCoinPulseAsync();
    Require(central.Calls == 0 && client.ForwardedTargets.Count == 0,
        "initially disabled event was dispatched");
    Console.WriteLine("NATIVE_ASYNC_DISPATCH_DISABLED_INITIAL_CONTROL: no dispatch");
}

Require(staleForward && disabledForward, "expected source-linked unsafe cases were not reproduced");
Console.WriteLine("NATIVE_ASYNC_DISPATCH_SOURCE_LINKED: 4/4 diagnostic cases matched; 2 safety REDs");
if (args.Contains("--safety-gate", StringComparer.OrdinalIgnoreCase))
{
    Console.WriteLine("NATIVE_ASYNC_DISPATCH_SAFETY_RED: target/session and post-disable forwarding");
    return 2;
}
if (!args.Contains("--diagnostic", StringComparer.OrdinalIgnoreCase))
{
    Console.Error.WriteLine("INCONCLUSIVE: pass --diagnostic or --safety-gate");
    return 3;
}
return 0;

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
    }
    public sealed class FakeSerial
    {
        public int SessionGeneration { get; set; } = 1;
        public FakeDevice? ConnectedDevice { get; } = new("COM9");
    }
    public sealed record FakeDevice(string PortName);
    public sealed class FakeTimer
    {
        public void AddCoin(int seconds, string source) { }
    }
    public sealed class FakeCentralServer
    {
        private readonly TaskCompletionSource<bool> _pending =
            new(TaskCreationOptions.RunContinuationsAsynchronously);
        public int Calls { get; private set; }
        public Task<bool> CreditCurrentAsync(int seconds)
        {
            Calls++;
            return _pending.Task;
        }
        public void Complete(bool routed) => _pending.SetResult(routed);
    }
    public sealed partial class BlazePwifiClient
    {
        private readonly AppConfig _config;
        private bool _insertWindow = true;
        private string _targetNonce;
        public List<string> ForwardedTargets { get; } = new();
        public string TargetNonce { set => _targetNonce = value; }
        public BlazePwifiClient(AppConfig config, string targetNonce)
        {
            _config = config;
            _targetNonce = targetNonce;
        }
        private Task<string?> Call(string action, int pulses, string target)
        {
            if (action != "coin" || pulses != 1)
                throw new Exception("unexpected fake network action");
            ForwardedTargets.Add(target);
            return Task.FromResult<string?>("{\"ok\":true}");
        }
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
        public FakeSerial Serial => _serial;
        public AppController(AppConfig config, FakeCentralServer central, BlazePwifiClient client)
        {
            Config = config;
            _centralServer = central;
            _blazePwifi = client;
        }
        public Task InvokeCoinPulseAsync() => HandleCoinPulse();
    }
}
