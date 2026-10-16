using System.Net;
using System.Text;
using System.Text.Json;
using BlazePisonet.SoftTimer;

static void Check(bool value, string name)
{
    if (!value) throw new Exception("FOG contract failed: " + name);
}

static async Task Reject(Func<Task> action, string name)
{
    try { await action(); }
    catch (InvalidOperationException) { return; }
    throw new Exception("FOG contract admitted: " + name);
}

var binding = new FogInventoryBinding();
Check(!binding.ReadyFor(binding.Generation), "no inventory before a refresh");
var firstRefresh = binding.BeginRefresh();
binding.ConnectionEdited();
Check(!binding.CompleteRefresh(firstRefresh), "connection edit discards in-flight inventory");
var olderRefresh = binding.BeginRefresh();
var latestRefresh = binding.BeginRefresh();
Check(!binding.CompleteRefresh(olderRefresh), "later refresh supersedes earlier response");
Check(binding.CompleteRefresh(latestRefresh) && binding.ReadyFor(latestRefresh),
    "current connection inventory admitted");
binding.ConnectionEdited();
Check(!binding.ReadyFor(latestRefresh), "connection edit prevents stale deployment");
var taskBinding = new FogInventoryBinding();
var staleTaskView = taskBinding.BeginRefresh();
taskBinding.ConnectionEdited();
Check(!taskBinding.CompleteRefresh(staleTaskView), "connection edit discards in-flight task view");
var olderTaskView = taskBinding.BeginRefresh();
var currentTaskView = taskBinding.BeginRefresh();
Check(!taskBinding.CompleteRefresh(olderTaskView) && taskBinding.CompleteRefresh(currentTaskView),
    "newer task inspection supersedes older response");

await Reject(() =>
{
    using var _ = new FogManagementClient("http://shop.example/fog",
        new FogCredentials("fog_token", "", ""));
    return Task.CompletedTask;
}, "plain HTTP token transport");
await Reject(() =>
{
    using var _ = new FogManagementClient("https://shop.example/fog",
        new FogCredentials("", "", ""));
    return Task.CompletedTask;
}, "missing credential");

var boot = DisklessBootProfile.Create("pc-01", "10.20.30.40",
    "iqn.2026-10.local.blaze:target-pc-01", "iqn.2026-10.local.blaze:pc-01");
Check(boot.DhcpRootPath == "iscsi:10.20.30.40::::iqn.2026-10.local.blaze:target-pc-01",
    "per-client DHCP option 017 root path");
Check(boot.IpxeScript == "#!ipxe\nset initiator-iqn iqn.2026-10.local.blaze:pc-01\n" +
    "sanboot iscsi:10.20.30.40::::iqn.2026-10.local.blaze:target-pc-01\n",
    "per-client iPXE SAN boot script");
foreach (var (label, address, target, initiator, name) in new[]
{
    ("pc-01\nboot", "10.20.30.40", "iqn.2026-10.local.blaze:target-pc-01", "iqn.2026-10.local.blaze:pc-01", "label injection"),
    ("pc-01", "10.20.30.40; reboot", "iqn.2026-10.local.blaze:target-pc-01", "iqn.2026-10.local.blaze:pc-01", "address injection"),
    ("pc-01", "224.0.0.1", "iqn.2026-10.local.blaze:target-pc-01", "iqn.2026-10.local.blaze:pc-01", "multicast target"),
    ("pc-01", "127.0.0.1", "iqn.2026-10.local.blaze:target-pc-01", "iqn.2026-10.local.blaze:pc-01", "loopback target"),
    ("pc-01", "10.20.30.40", "iqn.2026-10.local.blaze:target-pc-01${bad}", "iqn.2026-10.local.blaze:pc-01", "IQN script injection"),
    ("pc-01", "10.20.30.40", "iqn.2026-10.local.blaze:pc-01", "iqn.2026-10.local.blaze:pc-01", "same target and initiator")
})
    await Reject(() =>
    {
        DisklessBootProfile.Create(label, address, target, initiator);
        return Task.CompletedTask;
    }, name);

var first = new DisklessClientAssignment("pc-01", "10.20.30.40",
    "iqn.2026-10.local.blaze:target-pc-01", "iqn.2026-10.local.blaze:pc-01");
var second = new DisklessClientAssignment("pc-02", "10.20.30.40",
    "iqn.2026-10.local.blaze:target-pc-02", "iqn.2026-10.local.blaze:pc-02");
var emptyProfiles = new List<DisklessClientAssignment>();
var saved = DisklessProfileRegistry.Add(DisklessProfileRegistry.Add(emptyProfiles, first), second);
Check(saved.Count == 2 && emptyProfiles.Count == 0, "client registry addition does not mutate prior config");
var restored = JsonSerializer.Deserialize<List<DisklessClientAssignment>>(JsonSerializer.Serialize(saved));
Check(DisklessProfileRegistry.Validate(restored).Count == 2, "saved client registry round trip");
Check(saved[1].BootProfile().IpxeScript.Contains("target-pc-02"), "saved profile produces boot text");
foreach (var (candidate, name) in new[]
{
    (first with { ClientLabel = "PC-01", TargetIqn = "iqn.2026-10.local.blaze:new-target", InitiatorIqn = "iqn.2026-10.local.blaze:new-client" }, "duplicate client label"),
    (first with { ClientLabel = "pc-03", TargetIp = "10.20.30.41", InitiatorIqn = "iqn.2026-10.local.blaze:pc-03" }, "duplicate target IQN"),
    (first with { ClientLabel = "pc-03", TargetIqn = "iqn.2026-10.local.blaze:target-pc-03" }, "duplicate initiator IQN")
})
    await Reject(() => { DisklessProfileRegistry.Add(saved, candidate); return Task.CompletedTask; }, name);
Check(saved.Count == 2, "rejected duplicate does not mutate saved profiles");
await Reject(() => { DisklessProfileRegistry.Validate(null); return Task.CompletedTask; }, "missing saved registry");
await Reject(() => { DisklessProfileRegistry.Add(new[] { first with { TargetIqn = null! } }, second); return Task.CompletedTask; }, "corrupt saved record");
await Reject(() => { DisklessProfileRegistry.Remove(saved, "missing"); return Task.CompletedTask; }, "remove unknown client");
var removed = DisklessProfileRegistry.Remove(saved, "PC-01");
Check(removed.Count == 1 && removed[0].ClientLabel == "pc-02" && saved.Count == 2,
    "local removal preserves previous registry");

var fake = new FakeFog();
using (var fog = new FogManagementClient("https://fog.example/fog",
           new FogCredentials("fog_test", "", ""), fake))
{
    var info = await fog.GetServerInfoAsync();
    Check(info.Version == "1.6.0", "version");
    var hosts = await fog.GetHostsAsync();
    var images = await fog.GetImagesAsync();
    Check(hosts.Count == 1 && hosts[0].Name == "pc-01" && hosts[0].ImageId == 5, "host inventory");
    Check(images.Count == 1 && images[0].Enabled, "image inventory");
    Check(fake.BearerRequests == 5 && fake.PairRequests == 0, "Bearer preferred");
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-02 Win11"), "wrong confirmation");
    Check(fake.Deployments == 0, "wrong confirmation no POST");
    fake.HostImageId = 6;
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11"), "stale host image assignment");
    Check(fake.Deployments == 0, "stale assignment no POST");
    fake.HostImageId = 5;
    await fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11");
    Check(fake.Deployments == 1 && fake.LastBody.Contains("\"taskTypeID\":\"1\""), "FOG 1.6 deploy body");
}

var legacy = new FakeFog { Version = "1.5.9" };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("", "global", "user"), legacy))
{
    await fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11");
    Check(legacy.PairRequests == 8 && legacy.BearerRequests == 0, "legacy token pair and active task checks");
    Check(legacy.LastBody.Contains("\"taskTypeID\":\"1\""), "FOG 1.5 deploy body");
}

var unknown = new FakeFog { Version = "unknown" };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), unknown))
{
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11"), "unknown version deploy");
    Check(unknown.Deployments == 0, "unknown version no POST");
}

var disabled = new FakeFog { ImageEnabledRaw = "0" };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), disabled))
{
    Check(!(await fog.GetImagesAsync())[0].Enabled, "FOG isEnabled=0 must be disabled");
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11"), "disabled image");
    Check(disabled.Deployments == 0, "disabled image no POST");
}

var missing = new FakeFog { IncludeImageEnabled = false };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), missing))
{
    Check(!(await fog.GetImagesAsync())[0].Enabled, "missing image enablement fails closed");
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11"), "unknown enablement");
    Check(missing.Deployments == 0, "unknown enablement no POST");
}

var redirect = new FakeFog { Redirect = true };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), redirect))
    await Reject(() => fog.GetHostsAsync(), "redirect to alternate origin");

var large = new FakeFog { PagedHostCount = 101 };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), large))
{
    var hosts = await fog.GetHostsAsync();
    Check(hosts.Count == 101 && hosts[0].Id == 7 && hosts[^1].Id == 200,
        "FOG 1.6 inventory walks all bounded pages");
    Check(large.HostPages == 2, "FOG 1.6 paged rather than unbounded response");
}
foreach (var fault in new[] { "empty", "count", "duplicate", "changing-total" })
{
    var broken = new FakeFog { PagedHostCount = 101, PageFault = fault };
    using var fog = new FogManagementClient("https://fog.example",
        new FogCredentials("fog_test", "", ""), broken);
    await Reject(() => fog.GetHostsAsync(), "FOG 1.6 " + fault + " inventory page");
    Check(broken.Deployments == 0, fault + " inventory never deploys");
}

foreach (var (tasks, name) in new[]
{
    ("{\"count\":1,\"tasks\":[{\"hostID\":\"7\"}]}", "active task on selected host"),
    ("{\"count\":1,\"tasks\":[{}]}", "active task with unknown host"),
    ("{\"count\":1,\"tasks\":[{\"hostID\":\"bad\",\"host\":{\"id\":\"8\"}}]}", "invalid active task host"),
    ("{\"count\":1,\"tasks\":[{\"hostID\":\"7\",\"host\":{\"id\":\"8\"}}]}", "conflicting active task host"),
    ("{\"count\":2,\"tasks\":[{\"hostID\":\"8\"}]}", "incomplete active task list"),
    ("{\"tasks\":{}}", "malformed active task list")
})
{
    var guarded = new FakeFog { ActiveTasksJson = tasks };
    using var fog = new FogManagementClient("https://fog.example",
        new FogCredentials("fog_test", "", ""), guarded);
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11"), name);
    Check(guarded.Deployments == 0, name + " no POST");
}

var otherTask = new FakeFog { ActiveTasksJson = "{\"count\":1,\"tasks\":[{\"host\":{\"id\":\"8\"}}]}" };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), otherTask))
{
    await fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11");
    Check(otherTask.Deployments == 1, "other host task permits deployment");
}

var taskView = new FakeFog { ActiveTasksJson =
    "{\"count\":2,\"tasks\":[{\"hostID\":\"7\"},{\"host\":{\"id\":\"8\"}}]}" };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), taskView))
    Check((await fog.GetActiveTaskHostIdsAsync()).SequenceEqual(new[] { 7, 8 }),
        "read-only active task view preserves both host identities");
Check(taskView.Deployments == 0, "active task inspection makes no deployment POST");
foreach (var malformed in new[]
{
    "{\"count\":2,\"tasks\":[{\"hostID\":\"7\"}]}",
    "{\"count\":1,\"tasks\":[{\"hostID\":\"bad\"}]}"
})
{
    var badTaskView = new FakeFog { ActiveTasksJson = malformed };
    using var fog = new FogManagementClient("https://fog.example",
        new FogCredentials("fog_test", "", ""), badTaskView);
    await Reject(() => fog.GetActiveTaskHostIdsAsync(), "malformed read-only active task view");
}

var activeForbidden = new FakeFog { ActiveTaskStatus = HttpStatusCode.Forbidden };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), activeForbidden))
{
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11"), "active task permission denied");
    Check(activeForbidden.Deployments == 0, "active task permission no POST");
}

var lostAck = new FakeFog { LostDeploymentResponse = true };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), lostAck))
{
    try
    {
        await fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11");
        throw new Exception("FOG contract admitted lost deployment response");
    }
    catch (FogDeploymentUncertainException ex)
    {
        Check(ex.Message.Contains("Inspect its active tasks"), "lost response demands task inspection");
    }
    try
    {
        await fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11");
        throw new Exception("FOG contract admitted retry after lost response");
    }
    catch (FogDeploymentUncertainException)
    {
        throw new Exception("preflight refusal misclassified as an uncertain POST");
    }
    catch (InvalidOperationException) { }
    Check(lostAck.Deployments == 1, "lost response never schedules twice");
}

foreach (var (activeAfterPost, name) in new[]
{
    ("{\"count\":0,\"tasks\":[]}", "HTTP success with no active task"),
    ("{\"count\":1,\"tasks\":[{\"hostID\":\"8\"}]}", "HTTP success with another host task"),
    ("{\"count\":1,\"tasks\":[]}", "HTTP success with incomplete active task list")
})
{
    var unconfirmed = new FakeFog { ActiveAfterPostJson = activeAfterPost };
    using var fog = new FogManagementClient("https://fog.example",
        new FogCredentials("fog_test", "", ""), unconfirmed);
    try
    {
        await fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11");
        throw new Exception("FOG contract falsely confirmed: " + name);
    }
    catch (FogDeploymentUncertainException) { }
    Check(unconfirmed.Deployments == 1, name + " reports uncertainty after one POST");
}

await Reject(() => { using var _ = new TargetdInspectionClient("http://storage.example", "operator", "secret");
    return Task.CompletedTask; }, "targetd HTTP rejected");
await Reject(() => { using var _ = new TargetdInspectionClient("https://operator:secret@storage.example", "operator", "secret");
    return Task.CompletedTask; }, "targetd URL credentials rejected");
await Reject(() => { using var _ = new TargetdInspectionClient("https://storage.example/other", "operator", "secret");
    return Task.CompletedTask; }, "targetd path rejected");
await Reject(() => { using var _ = new TargetdInspectionClient("https://storage.example", "operator", "");
    return Task.CompletedTask; }, "targetd missing password rejected");
foreach (var fault in new[] { "", "redirect", "mismatch", "rpc-error", "bad-json", "duplicate-export",
    "unknown-group", "duplicate-group", "bad-initiator", "bad-map", "partial" })
{
    var server = new FakeTargetd { Fault = fault };
    using var client = new TargetdInspectionClient("https://storage.example/targetrpc", "operator", "secret", server);
    if (fault == "")
    {
        var snapshot = await client.InspectAsync();
        Check(snapshot.Exports.Count == 1 && snapshot.Groups.Count == 1 && snapshot.Maps.Count == 1,
            "targetd read-only complete snapshot");
        Check(snapshot.Exports[0].InitiatorIqn == "iqn.2026-10.local.blaze:pc-01",
            "targetd export initiator retained");
        Check(server.Methods.SequenceEqual(new[] { "export_list", "access_group_list", "access_group_map_list" }),
            "targetd never invokes a mutating method");
    }
    else await Reject(() => client.InspectAsync(), "targetd fault: " + fault);
}
var targetBinding = new FogInventoryBinding();
var oldStorage = targetBinding.BeginRefresh();
targetBinding.ConnectionEdited();
Check(!targetBinding.CompleteRefresh(oldStorage), "targetd connection edit discards stale inspection");
var supersededStorage = targetBinding.BeginRefresh();
var latestStorage = targetBinding.BeginRefresh();
Check(!targetBinding.CompleteRefresh(supersededStorage) && targetBinding.CompleteRefresh(latestStorage),
    "targetd later inspection supersedes earlier response");
var clientExport = new TargetdExport(first.InitiatorIqn, 0, "pool1", "pc01", "uuid-pc01");
var uniqueDirect = new TargetdSnapshot(new[] { clientExport },
    Array.Empty<TargetdAccessGroup>(), Array.Empty<TargetdAccessMap>());
Check(TargetdProfileMappingCheck.Assess(first, uniqueDirect).Status ==
    TargetdMappingStatus.ReportedSingleClient, "one reported dedicated LUN 0 export");
Check(TargetdProfileMappingCheck.Assess(first, new TargetdSnapshot(
    Array.Empty<TargetdExport>(), Array.Empty<TargetdAccessGroup>(),
    Array.Empty<TargetdAccessMap>())).Status == TargetdMappingStatus.Missing,
    "missing initiator mapping is not reported ready");
Check(TargetdProfileMappingCheck.Assess(first, uniqueDirect with
{
    Exports = new[] { clientExport, clientExport with { Lun = 1, Volume = "other" } }
}).Status == TargetdMappingStatus.Ambiguous,
    "multiple client LUNs are ambiguous");
Check(TargetdProfileMappingCheck.Assess(first, uniqueDirect with
{
    Exports = new[] { clientExport, clientExport with { InitiatorIqn = second.InitiatorIqn } }
}).Status == TargetdMappingStatus.Shared,
    "another initiator's export of same writable volume is refused");
Check(TargetdProfileMappingCheck.Assess(first, uniqueDirect with
{
    Exports = new[] { clientExport with { Lun = 1 } }
}).Status == TargetdMappingStatus.WrongLun,
    "saved blank-LUN SAN URI selects LUN 0");
var groupOnly = new TargetdSnapshot(Array.Empty<TargetdExport>(),
    new[] { new TargetdAccessGroup("pc01", new[] { first.InitiatorIqn }) },
    new[] { new TargetdAccessMap("pc01", 0, "pool1", "pc01") });
Check(TargetdProfileMappingCheck.Assess(first, groupOnly).Status ==
    TargetdMappingStatus.UnverifiableGroupMap,
    "group-only map lacks volume UUID and cannot prove same-name replacement identity");
Check(TargetdProfileMappingCheck.Assess(first, groupOnly with
{
    Groups = new[] { new TargetdAccessGroup("pc01", new[] { first.InitiatorIqn, second.InitiatorIqn }) }
}).Status == TargetdMappingStatus.Shared,
    "access-group volume shared with another initiator is refused");
Check(TargetdProfileMappingCheck.Assess(first, new TargetdSnapshot(
    new[] { clientExport }, groupOnly.Groups, groupOnly.Maps)).Status ==
    TargetdMappingStatus.Ambiguous, "direct and group map ambiguity is refused");
targetBinding.ConnectionEdited();
Check(!targetBinding.ReadyFor(latestStorage), "server edit invalidates selected client mapping");
Check(TargetdSnapshotAge.IsRecent(1_000, 61_000) &&
    !TargetdSnapshotAge.IsRecent(1_000, 61_001) &&
    !TargetdSnapshotAge.IsRecent(-1, 2_000) &&
    !TargetdSnapshotAge.IsRecent(2_000, 1_000),
    "expired or uncertain targetd report is refused");

Console.WriteLine("PISONET-0017 FOG, targetd and saved-client mapping contracts PASS");

sealed class FakeFog : HttpMessageHandler
{
    public string Version { get; set; } = "1.6.0";
    public int HostImageId { get; set; } = 5;
    public string ImageEnabledRaw { get; set; } = "1";
    public bool IncludeImageEnabled { get; set; } = true;
    public bool Redirect { get; set; }
    public string ActiveTasksJson { get; set; } = "{\"count\":0,\"tasks\":[]}";
    public HttpStatusCode ActiveTaskStatus { get; set; } = HttpStatusCode.OK;
    public bool LostDeploymentResponse { get; set; }
    public string ActiveAfterPostJson { get; set; } = "{\"count\":1,\"tasks\":[{\"hostID\":\"7\"}]}";
    public int PagedHostCount { get; set; } = 1;
    public string PageFault { get; set; } = "";
    public int HostPages { get; private set; }
    public int BearerRequests { get; private set; }
    public int PairRequests { get; private set; }
    public int Deployments { get; private set; }
    public string LastBody { get; private set; } = "";

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        var uri = request.RequestUri ?? throw new Exception("FOG request URI missing");
        if (uri.Scheme != "https" || uri.Host != "fog.example")
            throw new Exception("FOG contract failed: fixed HTTPS origin");
        if (request.Headers.Authorization?.Scheme == "Bearer" &&
            request.Headers.Authorization.Parameter == "fog_test")
            BearerRequests++;
        else if (request.Headers.TryGetValues("fog-api-token", out var global) &&
                 global.Single() == "global" &&
                 request.Headers.TryGetValues("fog-user-token", out var user) &&
                 user.Single() == "user")
            PairRequests++;
        else throw new Exception("missing or wrong auth header");
        if (Redirect)
            return new HttpResponseMessage(HttpStatusCode.Redirect)
                { Headers = { Location = new Uri("https://attacker.example/") } };
        var path = uri.AbsolutePath;
        if (request.Method == HttpMethod.Get && path == "/fog/system/info")
            return Json("{\"version\":\"" + Version + "\"}");
        if (request.Method == HttpMethod.Get && path == "/fog/host")
        {
            if (Version.StartsWith("1.5", StringComparison.Ordinal))
                return Json("{\"hosts\":[{\"id\":\"7\",\"name\":\"pc-01\",\"imageID\":\"" + HostImageId + "\"}]}");
            HostPages++;
            var query = uri.Query.TrimStart('?').Split('&')
                .Select(part => part.Split('=', 2))
                .ToDictionary(part => part[0], part => part.Length == 2 ? part[1] : "");
            var start = int.Parse(query.GetValueOrDefault("start", "-1"));
            var length = int.Parse(query.GetValueOrDefault("length", "-1"));
            if (length != 100 || start < 0 || start >= PagedHostCount)
                throw new Exception("FOG contract failed: bounded host page request");
            var rows = Enumerable.Range(start, Math.Min(length, PagedHostCount - start))
                .Select(i => new { id = PageFault == "duplicate" && i == 100 ? 7 :
                    i == 0 ? 7 : 100 + i,
                    name = i == 0 ? "pc-01" : "pc-" + i, imageID = HostImageId }).ToArray();
            if (PageFault == "empty" && start == 0) rows = rows.Take(0).ToArray();
            return Json(JsonSerializer.Serialize(new { recordsTotal = PagedHostCount +
                    (PageFault == "changing-total" && start > 0 ? 1 : 0),
                recordsFiltered = PagedHostCount,
                recordsReturned = rows.Length + (PageFault == "count" ? 1 : 0), data = rows }));
        }
        if (request.Method == HttpMethod.Get && path == "/fog/image")
        {
            var row = "{\"id\":\"5\",\"name\":\"Win11\"" +
                (IncludeImageEnabled ? ",\"isEnabled\":\"" + ImageEnabledRaw + "\"" : "") + "}";
            return Version.StartsWith("1.5", StringComparison.Ordinal) ?
                Json("{\"images\":[" + row + "]}") :
                Json("{\"recordsTotal\":1,\"recordsFiltered\":1,\"recordsReturned\":1,\"data\":[" + row + "]}");
        }
        if (request.Method == HttpMethod.Get && path == "/fog/task/active")
            return ActiveTaskStatus == HttpStatusCode.OK ? Json(ActiveTasksJson) :
                new HttpResponseMessage(ActiveTaskStatus);
        if (request.Method == HttpMethod.Post && path == "/fog/host/7/task")
        {
            LastBody = await request.Content!.ReadAsStringAsync(cancellationToken);
            using var body = JsonDocument.Parse(LastBody);
            if (!body.RootElement.TryGetProperty("taskTypeID", out var taskType) ||
                taskType.ValueKind != JsonValueKind.String || taskType.GetString() != "1" ||
                body.RootElement.EnumerateObject().Count() != 1)
                return new HttpResponseMessage(HttpStatusCode.NotFound);
            Deployments++;
            if (LostDeploymentResponse)
            {
                ActiveTasksJson = "{\"count\":1,\"tasks\":[{\"hostID\":\"7\"}]}";
                return new HttpResponseMessage(HttpStatusCode.ServiceUnavailable);
            }
            ActiveTasksJson = ActiveAfterPostJson;
            return Json("\"\"");
        }
        throw new Exception("unexpected FOG route " + request.Method + " " + path);
    }

    private static HttpResponseMessage Json(string value) =>
        new(HttpStatusCode.OK) { Content = new StringContent(value, Encoding.UTF8, "application/json") };
}

sealed class FakeTargetd : HttpMessageHandler
{
    public string Fault { get; set; } = "";
    public List<string> Methods { get; } = new();

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        if (request.Method != HttpMethod.Post || request.RequestUri?.AbsoluteUri !=
            "https://storage.example/targetrpc" ||
            request.Headers.Authorization?.Scheme != "Basic" ||
            Encoding.UTF8.GetString(Convert.FromBase64String(
                request.Headers.Authorization.Parameter ?? "")) != "operator:secret")
            throw new Exception("targetd contract failed: fixed HTTPS endpoint and Basic identity");
        if (Fault == "redirect")
            return new HttpResponseMessage(HttpStatusCode.Redirect)
                { Headers = { Location = new Uri("https://attacker.example/targetrpc") } };
        using var body = JsonDocument.Parse(await request.Content!.ReadAsStringAsync(cancellationToken));
        var root = body.RootElement;
        if (root.GetProperty("jsonrpc").GetString() != "2.0" ||
            root.EnumerateObject().Count() != 3)
            throw new Exception("targetd contract failed: JSON-RPC 2.0 request body");
        var method = root.GetProperty("method").GetString() ?? "";
        if (method is not ("export_list" or "access_group_list" or "access_group_map_list"))
            throw new Exception("targetd contract failed: mutation invoked");
        Methods.Add(method);
        var id = root.GetProperty("id").GetInt32();
        if (Fault == "bad-json") return Json("{" );
        if (Fault == "rpc-error")
            return Json(JsonSerializer.Serialize(new { jsonrpc = "2.0", id,
                error = new { code = -32601, message = "method unavailable" } }));
        var result = method switch
        {
            "export_list" => Fault switch
            {
                "duplicate-export" => "[{\"initiator_wwn\":\"iqn.2026-10.local.blaze:pc-01\",\"lun\":0,\"pool\":\"pool1\",\"vol_name\":\"disk1\",\"vol_uuid\":\"uuid1\"},{\"initiator_wwn\":\"iqn.2026-10.local.blaze:pc-01\",\"lun\":0,\"pool\":\"pool1\",\"vol_name\":\"disk2\",\"vol_uuid\":\"uuid2\"}]",
                "partial" => "[{\"initiator_wwn\":\"iqn.2026-10.local.blaze:pc-01\",\"lun\":0}]",
                _ => "[{\"initiator_wwn\":\"iqn.2026-10.local.blaze:pc-01\",\"lun\":0,\"pool\":\"pool1\",\"vol_name\":\"disk1\",\"vol_uuid\":\"uuid1\"}]"
            },
            "access_group_list" => Fault switch
            {
                "duplicate-group" => "[{\"name\":\"group1\",\"init_ids\":[\"iqn.2026-10.local.blaze:pc-01\"]},{\"name\":\"group1\",\"init_ids\":[]}]",
                "bad-initiator" => "[{\"name\":\"group1\",\"init_ids\":[\"not-an-iqn\"]}]",
                _ => "[{\"name\":\"group1\",\"init_ids\":[\"iqn.2026-10.local.blaze:pc-01\"]}]"
            },
            _ => Fault switch
            {
                "unknown-group" => "[{\"ag_name\":\"missing\",\"h_lun_id\":0,\"pool_name\":\"pool1\",\"vol_name\":\"disk1\"}]",
                "bad-map" => "[{\"ag_name\":\"group1\",\"h_lun_id\":\"x\",\"pool_name\":\"pool1\",\"vol_name\":\"disk1\"}]",
                _ => "[{\"ag_name\":\"group1\",\"h_lun_id\":0,\"pool_name\":\"pool1\",\"vol_name\":\"disk1\"}]"
            }
        };
        return Json("{\"jsonrpc\":\"2.0\",\"id\":" + (id + (Fault == "mismatch" ? 1 : 0)) +
            ",\"result\":" + result + "}");
    }

    private static HttpResponseMessage Json(string value) =>
        new(HttpStatusCode.OK) { Content = new StringContent(value, Encoding.UTF8, "application/json") };
}
