using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace BlazePisonet.SoftTimer;

public sealed record TargetdExport(string InitiatorIqn, int Lun, string Pool, string Volume, string VolumeUuid)
{
    public override string ToString() => $"{InitiatorIqn} · LUN {Lun} · {Pool}/{Volume} · {VolumeUuid}";
}

public sealed record TargetdAccessGroup(string Name, IReadOnlyList<string> Initiators);
public sealed record TargetdAccessMap(string Group, int Lun, string Pool, string Volume);
public sealed record TargetdSnapshot(IReadOnlyList<TargetdExport> Exports,
    IReadOnlyList<TargetdAccessGroup> Groups, IReadOnlyList<TargetdAccessMap> Maps);

// targetd has powerful write methods. This adapter deliberately exposes only
// three inventory methods, and does not infer that the target ACLs or boot work.
public sealed class TargetdInspectionClient : IDisposable
{
    private readonly Uri _endpoint;
    private readonly HttpClient _http;
    private readonly string _basicAuth;
    private int _nextId;

    public TargetdInspectionClient(string serverUrl, string username, string password,
        HttpMessageHandler? handler = null)
    {
        if (!Uri.TryCreate(serverUrl, UriKind.Absolute, out var server) ||
            server.Scheme != Uri.UriSchemeHttps || server.UserInfo.Length != 0 ||
            server.Query.Length != 0 || server.Fragment.Length != 0 ||
            server.AbsolutePath is not ("/" or "/targetrpc"))
            throw new InvalidOperationException("targetd requires a trusted HTTPS server origin or /targetrpc URL.");
        if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password) ||
            username.Contains(':') || username.Any(char.IsControl) || password.Any(char.IsControl))
            throw new InvalidOperationException("Enter a targetd username and password without control characters.");
        _endpoint = new Uri(server.GetLeftPart(UriPartial.Authority) + "/targetrpc");
        _basicAuth = Convert.ToBase64String(Encoding.UTF8.GetBytes(username + ":" + password));
        _http = new HttpClient(handler ?? new HttpClientHandler { AllowAutoRedirect = false }, true)
        {
            Timeout = TimeSpan.FromSeconds(12),
            MaxResponseContentBufferSize = 1_000_000
        };
    }

    public async Task<TargetdSnapshot> InspectAsync(CancellationToken cancellationToken = default)
    {
        using var exportsDoc = await CallAsync("export_list", cancellationToken);
        using var groupsDoc = await CallAsync("access_group_list", cancellationToken);
        using var mapsDoc = await CallAsync("access_group_map_list", cancellationToken);
        var exports = Rows(exportsDoc).Select(x => new TargetdExport(
            RequiredText(x, "initiator_wwn"), RequiredInt(x, "lun"),
            RequiredText(x, "pool"), RequiredText(x, "vol_name"), RequiredText(x, "vol_uuid"))).ToArray();
        var groups = Rows(groupsDoc).Select(x => new TargetdAccessGroup(
            RequiredText(x, "name"), RequiredInitiators(x))).ToArray();
        var maps = Rows(mapsDoc).Select(x => new TargetdAccessMap(
            RequiredText(x, "ag_name"), RequiredInt(x, "h_lun_id"),
            RequiredText(x, "pool_name"), RequiredText(x, "vol_name"))).ToArray();
        if (exports.Any(x => !IsIqn(x.InitiatorIqn) || x.Lun < 0) ||
            groups.Any(x => x.Initiators.Any(i => !IsIqn(i))) ||
            maps.Any(x => x.Lun < 0 || !groups.Any(g => g.Name == x.Group)) ||
            exports.Select(x => (x.InitiatorIqn, x.Lun)).Distinct().Count() != exports.Length ||
            groups.Select(x => x.Name).Distinct(StringComparer.Ordinal).Count() != groups.Length ||
            groups.SelectMany(x => x.Initiators).Distinct(StringComparer.Ordinal).Count() !=
                groups.Sum(x => x.Initiators.Count) ||
            maps.Select(x => (x.Group, x.Lun)).Distinct().Count() != maps.Length)
            throw new InvalidOperationException("targetd inventory has missing, duplicate or inconsistent identities.");
        return new TargetdSnapshot(exports, groups, maps);
    }

    private async Task<JsonDocument> CallAsync(string method, CancellationToken cancellationToken)
    {
        var id = Interlocked.Increment(ref _nextId);
        using var request = new HttpRequestMessage(HttpMethod.Post, _endpoint);
        request.Headers.Authorization = new AuthenticationHeaderValue("Basic", _basicAuth);
        request.Content = new StringContent(JsonSerializer.Serialize(new
        {
            jsonrpc = "2.0", method, id
        }), Encoding.UTF8, "application/json");
        using var response = await _http.SendAsync(request, HttpCompletionOption.ResponseContentRead,
            cancellationToken);
        if (response.StatusCode != HttpStatusCode.OK)
            throw new InvalidOperationException("targetd request failed (HTTP " + (int)response.StatusCode + ").");
        var raw = await response.Content.ReadAsStringAsync(cancellationToken);
        if (raw.Length > 1_000_000)
            throw new InvalidOperationException("targetd response is too large.");
        JsonDocument doc;
        try { doc = JsonDocument.Parse(raw); }
        catch (JsonException ex) { throw new InvalidOperationException("targetd returned invalid JSON.", ex); }
        var root = doc.RootElement;
        if (root.ValueKind != JsonValueKind.Object ||
            !root.TryGetProperty("jsonrpc", out var version) ||
            version.ValueKind != JsonValueKind.String || version.GetString() != "2.0" ||
            !root.TryGetProperty("id", out var returnedId) || returnedId.ValueKind != JsonValueKind.Number ||
            !returnedId.TryGetInt32(out var actualId) || actualId != id ||
            root.TryGetProperty("error", out _) ||
            !root.TryGetProperty("result", out var result) || result.ValueKind != JsonValueKind.Array)
        {
            doc.Dispose();
            throw new InvalidOperationException("targetd response has an error or an invalid request identity.");
        }
        return doc;
    }

    private static JsonElement.ArrayEnumerator Rows(JsonDocument doc)
    {
        var rows = doc.RootElement.GetProperty("result");
        if (rows.GetArrayLength() > 10_000)
            throw new InvalidOperationException("targetd inventory is too large.");
        return rows.EnumerateArray();
    }

    private static string RequiredText(JsonElement row, string name)
    {
        if (row.ValueKind != JsonValueKind.Object || !row.TryGetProperty(name, out var value) ||
            value.ValueKind != JsonValueKind.String || string.IsNullOrWhiteSpace(value.GetString()) ||
            value.GetString()!.Length > 256 || value.GetString()!.Any(char.IsControl))
            throw new InvalidOperationException("targetd inventory field is missing or invalid: " + name);
        return value.GetString()!;
    }

    private static int RequiredInt(JsonElement row, string name)
    {
        if (row.ValueKind != JsonValueKind.Object || !row.TryGetProperty(name, out var value) ||
            value.ValueKind != JsonValueKind.Number || !value.TryGetInt32(out var result))
            throw new InvalidOperationException("targetd inventory field is missing or invalid: " + name);
        return result;
    }

    private static IReadOnlyList<string> RequiredInitiators(JsonElement row)
    {
        if (row.ValueKind != JsonValueKind.Object || !row.TryGetProperty("init_ids", out var ids) ||
            ids.ValueKind != JsonValueKind.Array || ids.GetArrayLength() > 10_000)
            throw new InvalidOperationException("targetd access group has no valid initiator list.");
        return ids.EnumerateArray().Select(x => x.ValueKind == JsonValueKind.String ? x.GetString() ?? "" : "")
            .ToArray();
    }

    private static bool IsIqn(string value) =>
        value.StartsWith("iqn.", StringComparison.OrdinalIgnoreCase) && value.Length <= 256;

    public void Dispose() => _http.Dispose();
}
