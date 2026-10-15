using System.Net;
using System.Text;
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
    Check(fake.BearerRequests == 3 && fake.PairRequests == 0, "Bearer preferred");
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
    Check(legacy.PairRequests == 5 && legacy.BearerRequests == 0, "legacy token pair and active task preflight");
    Check(legacy.LastBody.Contains("\"taskType\":\"1\""), "FOG 1.5 deploy body");
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

foreach (var (tasks, name) in new[]
{
    ("{\"count\":1,\"tasks\":[{\"hostID\":\"7\"}]}", "active task on selected host"),
    ("{\"count\":1,\"tasks\":[{}]}", "active task with unknown host"),
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

var otherTask = new FakeFog { ActiveTasksJson = "{\"count\":1,\"tasks\":[{\"host\":{\"id\":\"8\"}]}" };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), otherTask))
{
    await fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11");
    Check(otherTask.Deployments == 1, "other host task permits deployment");
}

var lostAck = new FakeFog { LostDeploymentResponse = true };
using (var fog = new FogManagementClient("https://fog.example",
           new FogCredentials("fog_test", "", ""), lostAck))
{
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11"), "lost deployment response");
    await Reject(() => fog.QueueDeploymentAsync(7, 5, "DEPLOY pc-01 Win11"), "retry after lost response");
    Check(lostAck.Deployments == 1, "lost response never schedules twice");
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
    public bool LostDeploymentResponse { get; set; }
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
            return Json("{\"hosts\":[{\"id\":\"7\",\"name\":\"pc-01\",\"imageID\":\"" + HostImageId + "\"}]}");
        if (request.Method == HttpMethod.Get && path == "/fog/image")
            return Json("{\"images\":[{\"id\":\"5\",\"name\":\"Win11\"" +
                (IncludeImageEnabled ? ",\"isEnabled\":\"" + ImageEnabledRaw + "\"" : "") + "}]}");
        if (request.Method == HttpMethod.Get && path == "/fog/task/active")
            return Json(ActiveTasksJson);
        if (request.Method == HttpMethod.Post && path == "/fog/host/7/task")
        {
            LastBody = await request.Content!.ReadAsStringAsync(cancellationToken);
            Deployments++;
            if (LostDeploymentResponse)
            {
                ActiveTasksJson = "{\"count\":1,\"tasks\":[{\"hostID\":\"7\"}]}";
                return new HttpResponseMessage(HttpStatusCode.ServiceUnavailable);
            }
            return Json("\"\"");
        }
        throw new Exception("unexpected FOG route " + request.Method + " " + path);
    }

    private static HttpResponseMessage Json(string value) =>
        new(HttpStatusCode.OK) { Content = new StringContent(value, Encoding.UTF8, "application/json") };
}
