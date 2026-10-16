using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

namespace BlazePisonet.SoftTimer;

public sealed record FogCredentials(string BearerToken, string GlobalToken, string UserToken)
{
    public bool UseBearer => !string.IsNullOrWhiteSpace(BearerToken);
    public void Validate()
    {
        if (UseBearer) return;
        if (string.IsNullOrWhiteSpace(GlobalToken) || string.IsNullOrWhiteSpace(UserToken))
            throw new InvalidOperationException("Enter a FOG 1.6 Bearer token or both FOG 1.5 API tokens.");
    }
}

public sealed record FogHost(int Id, string Name, int ImageId)
{
    public override string ToString() => $"{Name} · host #{Id} · image #{ImageId}";
}

public sealed record FogImage(int Id, string Name, bool Enabled)
{
    public override string ToString() => $"{Name} · image #{Id}" + (Enabled ? "" : " · disabled");
}

public sealed record FogServerInfo(string Version)
{
    public int Major => int.TryParse(Version.Split('.')[0], out var value) ? value : 0;
    public int Minor => Version.Split('.').Length > 1 && int.TryParse(Version.Split('.')[1], out var value) ? value : -1;
}

// A POST can be accepted even when its response is lost. Callers must check
// FOG's active tasks before retrying or assuming the client's disk is safe.
public sealed class FogDeploymentUncertainException : InvalidOperationException
{
    public FogDeploymentUncertainException(Exception cause)
        : base("FOG may have accepted the deployment. Inspect its active tasks before retrying or booting the client.", cause) { }
}

// Management API only. FOG imaging is not a live Windows diskless boot service.
public sealed class FogManagementClient : IDisposable
{
    private readonly Uri _api;
    private readonly FogCredentials _credentials;
    private readonly HttpClient _http;

    public FogManagementClient(string serverUrl, FogCredentials credentials, HttpMessageHandler? handler = null)
    {
        if (!Uri.TryCreate(serverUrl, UriKind.Absolute, out var server) ||
            !string.IsNullOrEmpty(server.UserInfo) || !string.IsNullOrEmpty(server.Query) ||
            !string.IsNullOrEmpty(server.Fragment) ||
            !(server.Scheme == Uri.UriSchemeHttps ||
              (server.Scheme == Uri.UriSchemeHttp && server.IsLoopback)))
            throw new InvalidOperationException("FOG server must use HTTPS (HTTP is allowed only for local testing).");
        credentials.Validate();
        var path = server.AbsolutePath.TrimEnd('/');
        if (path != "" && path != "/" && path != "/fog")
            throw new InvalidOperationException("Enter the FOG server origin or its /fog path.");
        _api = new Uri(server.GetLeftPart(UriPartial.Authority) + "/fog/");
        _credentials = credentials;
        _http = new HttpClient(handler ?? new HttpClientHandler { AllowAutoRedirect = false }, disposeHandler: true)
        {
            Timeout = TimeSpan.FromSeconds(12),
            MaxResponseContentBufferSize = 2_000_000
        };
    }

    public async Task<FogServerInfo> GetServerInfoAsync(CancellationToken cancellationToken = default)
    {
        using var json = await GetJsonAsync("system/info", cancellationToken);
        var version = ReadText(json.RootElement, "version");
        if (version.Length == 0 && TryProperty(json.RootElement, "system", out var system))
            version = ReadText(system, "version");
        return new FogServerInfo(version);
    }

    public async Task<IReadOnlyList<FogHost>> GetHostsAsync(CancellationToken cancellationToken = default)
    {
        var rows = await GetInventoryAsync("host", "hosts", cancellationToken);
        var hosts = rows.Select(x => new FogHost(ReadId(x, "id"), ReadText(x, "name"), ReadId(x, "imageID"))).ToArray();
        if (hosts.Any(x => x.Id <= 0 || x.Name.Length == 0) ||
            hosts.Select(x => x.Id).Distinct().Count() != hosts.Length)
            throw new InvalidOperationException("FOG host inventory has missing or duplicate identities.");
        return hosts;
    }

    public async Task<IReadOnlyList<FogImage>> GetImagesAsync(CancellationToken cancellationToken = default)
    {
        var rows = await GetInventoryAsync("image", "images", cancellationToken);
        var images = rows.Select(x => new FogImage(ReadId(x, "id"), ReadText(x, "name"),
                ReadBool(x, "isEnabled",
                    ReadBool(x, "imageEnabled", ReadBool(x, "enabled", false))))).ToArray();
        if (images.Any(x => x.Id <= 0 || x.Name.Length == 0) ||
            images.Select(x => x.Id).Distinct().Count() != images.Length)
            throw new InvalidOperationException("FOG image inventory has missing or duplicate identities.");
        return images;
    }

    private async Task<IReadOnlyList<JsonElement>> GetInventoryAsync(string resource,
        string legacyName, CancellationToken cancellationToken)
    {
        var info = await GetServerInfoAsync(cancellationToken);
        if (info.Major != 1 || info.Minor < 5)
            throw new InvalidOperationException("FOG version is unknown; inventory is disabled.");
        if (info.Minor == 5)
        {
            using var legacy = await GetJsonAsync(resource, cancellationToken);
            return Array(legacy.RootElement, legacyName).Select(x => x.Clone()).ToArray();
        }

        const int pageSize = 100;
        const int maxInventory = 10_000;
        var result = new List<JsonElement>();
        int? expectedTotal = null;
        int? expectedFiltered = null;
        while (true)
        {
            using var page = await GetJsonAsync($"{resource}?length={pageSize}&start={result.Count}", cancellationToken);
            var root = page.RootElement;
            if (root.ValueKind != JsonValueKind.Object ||
                !TryProperty(root, "data", out var data) || data.ValueKind != JsonValueKind.Array ||
                !TryCount(root, "recordsTotal", out var total) ||
                !TryCount(root, "recordsFiltered", out var filtered) ||
                !TryCount(root, "recordsReturned", out var returned) ||
                filtered > total || filtered > maxInventory ||
                (expectedTotal is not null && expectedTotal != total) ||
                (expectedFiltered is not null && expectedFiltered != filtered) ||
                returned != data.GetArrayLength() || returned > pageSize ||
                result.Count + returned > filtered ||
                (returned == 0 && result.Count < filtered))
                throw new InvalidOperationException("FOG inventory page is incomplete or inconsistent.");
            expectedTotal = total;
            expectedFiltered = filtered;
            result.AddRange(data.EnumerateArray().Select(x => x.Clone()));
            if (result.Count == filtered) return result;
        }
    }

    private static bool TryCount(JsonElement root, string name, out int value)
    {
        value = 0;
        return TryProperty(root, name, out var field) &&
            int.TryParse(field.ToString(), out value) && value >= 0;
    }

    public async Task QueueDeploymentAsync(int hostId, int imageId, string confirmation,
        CancellationToken cancellationToken = default)
    {
        // Refresh both records immediately before scheduling. The image must already be
        // assigned to the host; this action never silently changes host configuration.
        var host = (await GetHostsAsync(cancellationToken)).SingleOrDefault(x => x.Id == hostId);
        var image = (await GetImagesAsync(cancellationToken)).SingleOrDefault(x => x.Id == imageId);
        if (host is null || image is null || !image.Enabled || host.ImageId != image.Id ||
            confirmation != $"DEPLOY {host.Name} {image.Name}")
            throw new InvalidOperationException("Select an enabled image already assigned to this host and confirm its exact names.");
        var info = await GetServerInfoAsync(cancellationToken);
        string property = info.Major switch
        {
            1 when info.Minor >= 5 => "taskTypeID",
            _ => throw new InvalidOperationException("FOG version is unknown; deployment is disabled.")
        };
        if (await HasActiveTaskAsync(hostId, cancellationToken))
            throw new InvalidOperationException("FOG already has an active task for this host.");
        using var request = NewRequest(HttpMethod.Post, $"host/{hostId}/task");
        request.Content = new StringContent(JsonSerializer.Serialize(new Dictionary<string, string> { [property] = "1" }),
            Encoding.UTF8, "application/json");
        try
        {
            using var response = await _http.SendAsync(request, cancellationToken);
            EnsureResponse(response);
        }
        catch (Exception ex) when (ex is HttpRequestException or OperationCanceledException or InvalidOperationException)
        {
            throw new FogDeploymentUncertainException(ex);
        }
        // FOG's successful POST body is an empty string. Check its active-task
        // view before reporting a queued deployment; a delayed/missing task is
        // uncertain and requires operator inspection rather than a blind retry.
        try
        {
            if (!await HasActiveTaskAsync(hostId, cancellationToken))
                throw new InvalidOperationException("FOG did not show the deployment in active tasks.");
        }
        catch (Exception ex) when (ex is HttpRequestException or OperationCanceledException or InvalidOperationException or JsonException)
        {
            throw new FogDeploymentUncertainException(ex);
        }
    }

    private async Task<bool> HasActiveTaskAsync(int hostId, CancellationToken cancellationToken) =>
        (await GetActiveTaskHostIdsAsync(cancellationToken)).Contains(hostId);

    // Read-only view for operators reconciling an uncertain POST. FOG's list
    // exposes task hosts, but does not prove which request created a task.
    public async Task<IReadOnlyList<int>> GetActiveTaskHostIdsAsync(
        CancellationToken cancellationToken = default)
    {
        using var json = await GetJsonAsync("task/active", cancellationToken);
        var root = json.RootElement;
        var tasks = Array(root, "tasks").ToArray();
        if (root.ValueKind == JsonValueKind.Object &&
            (!TryProperty(root, "count", out var countValue) ||
             !int.TryParse(countValue.ToString(), out var count) ||
             count != tasks.Length))
            throw new InvalidOperationException("FOG active task list is incomplete; deployment is disabled.");

        var hostIds = new List<int>();
        foreach (var task in tasks)
        {
            if (task.ValueKind != JsonValueKind.Object)
                throw new InvalidOperationException("FOG active task is malformed.");
            var ids = new List<int>();
            foreach (var field in task.EnumerateObject())
                if (field.Name.Equals("hostID", StringComparison.OrdinalIgnoreCase))
                {
                    if (!int.TryParse(field.Value.ToString(), out var id) || id <= 0)
                        throw new InvalidOperationException("FOG active task has an invalid host identity.");
                    ids.Add(id);
                }
            if (TryProperty(task, "host", out var host))
            {
                var nestedId = ReadId(host, "id");
                if (nestedId <= 0)
                    throw new InvalidOperationException("FOG active task has an invalid host identity.");
                ids.Add(nestedId);
            }
            if (ids.Count == 0 || ids.Any(id => id != ids[0]))
                throw new InvalidOperationException("FOG active task host identity is missing or inconsistent.");
            hostIds.Add(ids[0]);
        }
        return hostIds;
    }

    private async Task<JsonDocument> GetJsonAsync(string path, CancellationToken cancellationToken)
    {
        using var request = NewRequest(HttpMethod.Get, path);
        using var response = await _http.SendAsync(request, cancellationToken);
        EnsureResponse(response);
        return JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
    }

    private HttpRequestMessage NewRequest(HttpMethod method, string path)
    {
        var request = new HttpRequestMessage(method, new Uri(_api, path));
        if (_credentials.UseBearer)
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _credentials.BearerToken.Trim());
        else
        {
            request.Headers.TryAddWithoutValidation("fog-api-token", _credentials.GlobalToken.Trim());
            request.Headers.TryAddWithoutValidation("fog-user-token", _credentials.UserToken.Trim());
        }
        return request;
    }

    private static void EnsureResponse(HttpResponseMessage response)
    {
        if ((int)response.StatusCode is >= 300 and < 400)
            throw new InvalidOperationException("FOG redirected the request; verify the HTTPS server address.");
        if (response.StatusCode == HttpStatusCode.Unauthorized || response.StatusCode == HttpStatusCode.Forbidden)
            throw new InvalidOperationException("FOG rejected the API credentials or permissions.");
        if (!response.IsSuccessStatusCode)
            throw new InvalidOperationException($"FOG API returned HTTP {(int)response.StatusCode}.");
    }

    private static IEnumerable<JsonElement> Array(JsonElement root, string name)
    {
        if (root.ValueKind == JsonValueKind.Array) return root.EnumerateArray().ToArray();
        if (TryProperty(root, name, out var value) && value.ValueKind == JsonValueKind.Array)
            return value.EnumerateArray().ToArray();
        throw new InvalidOperationException("FOG returned an unexpected inventory response.");
    }

    private static bool TryProperty(JsonElement value, string name, out JsonElement property)
    {
        property = default;
        if (value.ValueKind != JsonValueKind.Object) return false;
        foreach (var item in value.EnumerateObject())
            if (item.Name.Equals(name, StringComparison.OrdinalIgnoreCase))
            {
                property = item.Value;
                return true;
            }
        return false;
    }

    private static string ReadText(JsonElement value, string name)
    {
        return TryProperty(value, name, out var p) && p.ValueKind is JsonValueKind.String or JsonValueKind.Number
            ? p.ToString() : "";
    }

    private static int ReadId(JsonElement value, string name) =>
        int.TryParse(ReadText(value, name), out var id) ? id : 0;

    private static bool ReadBool(JsonElement value, string name, bool fallback)
    {
        if (!TryProperty(value, name, out var p)) return fallback;
        return p.ToString().Equals("1", StringComparison.OrdinalIgnoreCase) ||
               p.ToString().Equals("true", StringComparison.OrdinalIgnoreCase);
    }

    public void Dispose() => _http.Dispose();
}
