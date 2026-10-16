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

Console.WriteLine("PISONET-0003 FOG API: auth, inventory, active-task and lost-response deployment guard PASS");

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
