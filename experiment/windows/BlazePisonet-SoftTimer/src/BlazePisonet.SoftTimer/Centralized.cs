using System.Collections.Concurrent;
using System.Net;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace BlazePisonet.SoftTimer;

public sealed record StationRequest(string StationId, string Address, int CallbackPort, DateTimeOffset RequestedUtc);
public sealed record QueueState(string CurrentStation, int Position, int QueueLength, long ExpiresUnix);
public sealed record CreditPayload(string EventId, long Seconds, string StationId, long Timestamp);

public static class PeerAuth
{
    public static Dictionary<string, string> BuildHeaders(string key, string station, string method, string path, string body)
    {
        var timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString();
        var nonce = Convert.ToHexString(RandomNumberGenerator.GetBytes(12)).ToLowerInvariant();
        var bodyHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(body))).ToLowerInvariant();
        var canonical = $"{method.ToUpperInvariant()}|{path}|{timestamp}|{nonce}|{bodyHash}";
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(key));
        var sig = Convert.ToHexString(hmac.ComputeHash(Encoding.UTF8.GetBytes(canonical))).ToLowerInvariant();
        return new()
        {
            ["X-Blaze-Station"] = station,
            ["X-Blaze-Timestamp"] = timestamp,
            ["X-Blaze-Nonce"] = nonce,
            ["X-Blaze-Signature"] = sig
        };
    }

    public static bool Validate(string key, HttpListenerRequest request, string body, NonceCache nonces, out string station)
    {
        station = request.Headers["X-Blaze-Station"] ?? string.Empty;
        var tsText = request.Headers["X-Blaze-Timestamp"] ?? string.Empty;
        var nonce = request.Headers["X-Blaze-Nonce"] ?? string.Empty;
        var sig = request.Headers["X-Blaze-Signature"] ?? string.Empty;
        if (station.Length is < 1 or > 64 || nonce.Length is < 8 or > 64 || sig.Length != 64 || !long.TryParse(tsText, out var ts)) return false;
        if (Math.Abs(DateTimeOffset.UtcNow.ToUnixTimeSeconds() - ts) > 120) return false;
        if (!nonces.TryUse(nonce)) return false;
        var bodyHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(body))).ToLowerInvariant();
        var canonical = $"{request.HttpMethod.ToUpperInvariant()}|{request.Url?.AbsolutePath}|{tsText}|{nonce}|{bodyHash}";
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(key));
        var expected = hmac.ComputeHash(Encoding.UTF8.GetBytes(canonical));
        try
        {
            var got = Convert.FromHexString(sig);
            return got.Length == expected.Length && CryptographicOperations.FixedTimeEquals(got, expected);
        }
        catch { return false; }
    }
}

public sealed class NonceCache
{
    private readonly ConcurrentDictionary<string, DateTimeOffset> _used = new(StringComparer.OrdinalIgnoreCase);
    public bool TryUse(string nonce)
    {
        var now = DateTimeOffset.UtcNow;
        foreach (var item in _used.Where(x => now - x.Value > TimeSpan.FromMinutes(5)).ToArray()) _used.TryRemove(item.Key, out _);
        return _used.TryAdd(nonce, now);
    }
}

public sealed class CentralizedServer : IDisposable
{
    private readonly HttpListener _listener = new();
    private readonly NonceCache _nonces = new();
    private readonly AppConfig _config;
    private readonly TimerEngine _timer;
    private readonly CancellationTokenSource _cts = new();
    private readonly object _queueGate = new();
    private readonly List<StationRequest> _queue = new();
    private StationRequest? _current;
    private DateTimeOffset _currentExpires;
    private Task? _loop;

    public event Action? QueueChanged;
    public string LastStatus { get; private set; } = "Stopped";

    public CentralizedServer(AppConfig config, TimerEngine timer)
    {
        _config = config;
        _timer = timer;
    }

    public void Start()
    {
        if (_listener.IsListening) return;
        try
        {
            _listener.Prefixes.Clear();
            _listener.Prefixes.Add($"http://+:{_config.CentralListenPort}/softtimer/");
            _listener.Start();
            LastStatus = $"Listening on TCP {_config.CentralListenPort}";
            _loop = Task.Run(ListenLoop);
        }
        catch (Exception ex)
        {
            LastStatus = "Central server failed: " + ex.Message;
            Storage.Log(LastStatus);
        }
    }

    private async Task ListenLoop()
    {
        while (!_cts.IsCancellationRequested && _listener.IsListening)
        {
            try
            {
                var ctx = await _listener.GetContextAsync().WaitAsync(_cts.Token);
                _ = Task.Run(() => Handle(ctx));
            }
            catch (OperationCanceledException) { break; }
            catch (Exception ex)
            {
                if (!_cts.IsCancellationRequested) Storage.Log("Central listen error: " + ex.Message);
            }
        }
    }

    private async Task Handle(HttpListenerContext ctx)
    {
        string body = string.Empty;
        try
        {
            using (var reader = new StreamReader(ctx.Request.InputStream, ctx.Request.ContentEncoding ?? Encoding.UTF8))
                body = await reader.ReadToEndAsync();

            if (!PeerAuth.Validate(_config.CentralSharedKey, ctx.Request, body, _nonces, out var caller))
            {
                await Json(ctx, 401, new { ok = false, error = "unauthorized" });
                return;
            }

            var path = ctx.Request.Url?.AbsolutePath ?? string.Empty;
            if (path.EndsWith("/api/request", StringComparison.OrdinalIgnoreCase) && ctx.Request.HttpMethod == "POST")
            {
                var payload = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(body, Storage.JsonOptions) ?? new();
                var station = payload.TryGetValue("station_id", out var sid) ? sid.GetString() ?? caller : caller;
                var port = payload.TryGetValue("callback_port", out var cp) && cp.TryGetInt32(out var p) ? p : _config.CentralListenPort;
                var remote = ctx.Request.RemoteEndPoint?.Address.ToString() ?? string.Empty;
                Enqueue(new StationRequest(station, remote, port, DateTimeOffset.UtcNow));
                await Json(ctx, 200, new { ok = true, queue = GetQueueState(station) });
                return;
            }

            if (path.EndsWith("/api/queue", StringComparison.OrdinalIgnoreCase))
            {
                var station = ctx.Request.QueryString["station_id"] ?? caller;
                await Json(ctx, 200, new { ok = true, queue = GetQueueState(station) });
                return;
            }

            if (path.EndsWith("/api/credit", StringComparison.OrdinalIgnoreCase) && ctx.Request.HttpMethod == "POST")
            {
                var credit = JsonSerializer.Deserialize<CreditPayload>(body, Storage.JsonOptions);
                if (credit is null || credit.Seconds <= 0 || !credit.StationId.Equals(_config.CentralStationId, StringComparison.OrdinalIgnoreCase))
                {
                    await Json(ctx, 400, new { ok = false, error = "invalid credit" });
                    return;
                }
                var applied = _timer.AddSeconds(credit.Seconds, credit.EventId, true, $"Centralized credit from {caller}");
                await Json(ctx, 200, new { ok = true, duplicate = !applied, remaining_seconds = _timer.RemainingSeconds });
                return;
            }

            if (path.EndsWith("/api/status", StringComparison.OrdinalIgnoreCase))
            {
                await Json(ctx, 200, new { ok = true, station = _config.CentralStationId, remaining_seconds = _timer.RemainingSeconds, active = _timer.IsActive });
                return;
            }

            await Json(ctx, 404, new { ok = false, error = "not found" });
        }
        catch (Exception ex)
        {
            try { await Json(ctx, 500, new { ok = false, error = ex.Message }); } catch { }
        }
    }

    public void Enqueue(StationRequest request)
    {
        lock (_queueGate)
        {
            ExpireCurrentIfNeeded();
            if (_current?.StationId.Equals(request.StationId, StringComparison.OrdinalIgnoreCase) == true)
            {
                _current = request;
                _currentExpires = DateTimeOffset.UtcNow.AddSeconds(_config.CentralCoinWindowSeconds);
                return;
            }
            _queue.RemoveAll(x => x.StationId.Equals(request.StationId, StringComparison.OrdinalIgnoreCase));
            _queue.Add(request);
            PromoteIfNeeded();
        }
        QueueChanged?.Invoke();
    }

    public QueueState GetQueueState(string stationId)
    {
        lock (_queueGate)
        {
            ExpireCurrentIfNeeded();
            PromoteIfNeeded();
            if (_current?.StationId.Equals(stationId, StringComparison.OrdinalIgnoreCase) == true)
                return new QueueState(_current.StationId, 0, _queue.Count + 1, _currentExpires.ToUnixTimeSeconds());
            var idx = _queue.FindIndex(x => x.StationId.Equals(stationId, StringComparison.OrdinalIgnoreCase));
            return new QueueState(_current?.StationId ?? string.Empty, idx < 0 ? -1 : idx + 1, _queue.Count + (_current is null ? 0 : 1), _currentExpires.ToUnixTimeSeconds());
        }
    }

    public async Task<bool> CreditCurrentAsync(long seconds)
    {
        StationRequest? target;
        lock (_queueGate)
        {
            ExpireCurrentIfNeeded();
            PromoteIfNeeded();
            target = _current;
            if (target is not null) _currentExpires = DateTimeOffset.UtcNow.AddSeconds(_config.CentralCoinWindowSeconds);
        }
        if (target is null) return false;
        var eventId = $"central:{_config.CentralStationId}:{Guid.NewGuid():N}";
        var payload = new CreditPayload(eventId, seconds, target.StationId, DateTimeOffset.UtcNow.ToUnixTimeSeconds());
        var url = $"http://{target.Address}:{target.CallbackPort}/softtimer/api/credit";
        var ok = await PeerClient.PostJsonAsync(url, _config.CentralSharedKey, _config.CentralStationId, payload);
        if (ok) Storage.Log($"Central coin routed to {target.StationId}; +{seconds}s; {eventId}");
        return ok;
    }

    public void ReleaseCurrent()
    {
        lock (_queueGate)
        {
            _current = null;
            PromoteIfNeeded();
        }
        QueueChanged?.Invoke();
    }

    private void ExpireCurrentIfNeeded()
    {
        if (_current is not null && DateTimeOffset.UtcNow > _currentExpires) _current = null;
    }

    private void PromoteIfNeeded()
    {
        if (_current is not null || _queue.Count == 0) return;
        _current = _queue[0];
        _queue.RemoveAt(0);
        _currentExpires = DateTimeOffset.UtcNow.AddSeconds(_config.CentralCoinWindowSeconds);
    }

    private static async Task Json(HttpListenerContext ctx, int status, object payload)
    {
        var bytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(payload, Storage.JsonOptions));
        ctx.Response.StatusCode = status;
        ctx.Response.ContentType = "application/json; charset=utf-8";
        ctx.Response.ContentLength64 = bytes.Length;
        await ctx.Response.OutputStream.WriteAsync(bytes);
        ctx.Response.Close();
    }

    public void Dispose()
    {
        _cts.Cancel();
        try { _listener.Stop(); } catch { }
        try { _listener.Close(); } catch { }
        _cts.Dispose();
    }
}

public static class PeerClient
{
    private static readonly HttpClient Http = new() { Timeout = TimeSpan.FromSeconds(4) };

    public static async Task<bool> RequestCoinAsync(AppConfig cfg)
    {
        var url = new Uri(new Uri(EnsureSlash(cfg.CentralCoordinatorUrl)), "softtimer/api/request");
        var payload = new { station_id = cfg.CentralStationId, callback_port = cfg.CentralListenPort };
        return await PostJsonAsync(url.ToString(), cfg.CentralSharedKey, cfg.CentralStationId, payload);
    }

    public static async Task<QueueState?> GetQueueStateAsync(AppConfig cfg)
    {
        var baseUri = new Uri(EnsureSlash(cfg.CentralCoordinatorUrl));
        var path = $"/softtimer/api/queue";
        var url = new Uri(baseUri, $"softtimer/api/queue?station_id={Uri.EscapeDataString(cfg.CentralStationId)}");
        using var req = new HttpRequestMessage(HttpMethod.Get, url);
        foreach (var kv in PeerAuth.BuildHeaders(cfg.CentralSharedKey, cfg.CentralStationId, "GET", path, string.Empty)) req.Headers.TryAddWithoutValidation(kv.Key, kv.Value);
        try
        {
            using var resp = await Http.SendAsync(req);
            var text = await resp.Content.ReadAsStringAsync();
            if (!resp.IsSuccessStatusCode) return null;
            using var doc = JsonDocument.Parse(text);
            if (!doc.RootElement.TryGetProperty("queue", out var q)) return null;
            return JsonSerializer.Deserialize<QueueState>(q.GetRawText(), Storage.JsonOptions);
        }
        catch { return null; }
    }

    public static async Task<bool> PostJsonAsync<T>(string url, string key, string station, T payload)
    {
        var body = JsonSerializer.Serialize(payload, Storage.JsonOptions);
        var uri = new Uri(url);
        using var req = new HttpRequestMessage(HttpMethod.Post, uri)
        {
            Content = new StringContent(body, Encoding.UTF8, "application/json")
        };
        foreach (var kv in PeerAuth.BuildHeaders(key, station, "POST", uri.AbsolutePath, body)) req.Headers.TryAddWithoutValidation(kv.Key, kv.Value);
        try
        {
            using var resp = await Http.SendAsync(req);
            return resp.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    private static string EnsureSlash(string value) => value.EndsWith('/') ? value : value + "/";
}
