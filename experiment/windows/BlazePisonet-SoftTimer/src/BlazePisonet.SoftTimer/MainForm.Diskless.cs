namespace BlazePisonet.SoftTimer;

public sealed partial class MainForm
{
    private readonly TextBox _fogUrl = NewText();
    private readonly TextBox _fogBearer = new() { UseSystemPasswordChar = true };
    private readonly TextBox _fogGlobal = new() { UseSystemPasswordChar = true };
    private readonly TextBox _fogUser = new() { UseSystemPasswordChar = true };
    private readonly ListBox _fogHosts = new() { Height = 190, Width = 850 };
    private readonly ListBox _fogImages = new() { Height = 155, Width = 850 };
    private readonly Label _fogStatus = new() { AutoSize = true, ForeColor = BlazeTheme.Muted };
    private readonly ListBox _fogTaskHosts = new() { Height = 100, Width = 850 };
    private readonly Label _fogTaskStatus = new() { AutoSize = true, ForeColor = BlazeTheme.Muted };
    private readonly FogInventoryBinding _fogInventoryBinding = new();
    private readonly FogInventoryBinding _fogTaskBinding = new();
    private readonly TextBox _targetdUrl = NewText();
    private readonly TextBox _targetdUser = NewText();
    private readonly TextBox _targetdPassword = new() { UseSystemPasswordChar = true };
    private readonly ListBox _targetdExports = new() { Height = 115, Width = 850 };
    private readonly ListBox _targetdMaps = new() { Height = 95, Width = 850 };
    private readonly Label _targetdStatus = new() { AutoSize = true, ForeColor = BlazeTheme.Muted };
    private readonly FogInventoryBinding _targetdBinding = new();
    private TargetdSnapshot? _targetdSnapshot;
    private long _targetdSnapshotGeneration = -1;
    private long _targetdSnapshotTick = -1;
    private readonly TextBox _disklessClient = NewText();
    private readonly TextBox _disklessTargetIp = NewText();
    private readonly TextBox _disklessTargetIqn = NewText();
    private readonly TextBox _disklessInitiatorIqn = NewText();
    private readonly ListBox _disklessProfiles = new() { Height = 115, Width = 850 };
    private readonly TextBox _disklessRootPath = new() { ReadOnly = true, Width = 850 };
    private readonly TextBox _disklessScript = new()
    {
        ReadOnly = true, Multiline = true, Width = 850, Height = 105, ScrollBars = ScrollBars.Vertical
    };
    private readonly Label _disklessProfileStatus = new() { AutoSize = true, ForeColor = BlazeTheme.Muted };

    private void BuildDiskless()
    {
        foreach (var field in new[] { _fogUrl, _fogBearer, _fogGlobal, _fogUser })
            field.TextChanged += (_, _) => InvalidateFogInventory();
        var root = NewPage("Diskless & Imaging",
            "Manage Windows client images through a self-hosted FOG server. Live diskless boot requires separately validated iSCSI and PXE infrastructure.");
        var connection = Card("FOG connection",
            "Use HTTPS. FOG 1.6 Bearer is preferred; FOG 1.5 accepts the global and user token pair. Tokens stay in this session and are never saved.");
        connection.Controls.Add(Field("FOG server HTTPS URL", _fogUrl));
        connection.Controls.Add(Field("FOG 1.6 Bearer token (preferred)", _fogBearer));
        connection.Controls.Add(Field("FOG global API token (legacy pair)", _fogGlobal));
        connection.Controls.Add(Field("FOG user API token (legacy pair)", _fogUser));
        connection.Controls.Add(Button("CONNECT & REFRESH INVENTORY", async (_, _) => await RefreshFogAsync()));
        connection.Controls.Add(_fogStatus);
        root.Controls.Add(connection);

        var inventory = Card("Windows client inventory", "A FOG host must already be registered and assigned an enabled image before deployment.");
        inventory.Controls.Add(_fogHosts);
        inventory.Controls.Add(_fogImages);
        inventory.Controls.Add(PrimaryButton("SCHEDULE SELECTED IMAGE DEPLOYMENT", async (_, _) => await DeployFogAsync()));
        root.Controls.Add(inventory);

        var tasks = Card("Active FOG task inspection",
            "Read-only task hosts from this server. Use after an uncertain deployment response; confirm the task type and client in FOG before retrying or booting.");
        tasks.Controls.Add(Button("INSPECT ACTIVE TASKS", async (_, _) => await InspectFogTasksAsync()));
        tasks.Controls.Add(_fogTaskHosts);
        tasks.Controls.Add(_fogTaskStatus);
        root.Controls.Add(tasks);

        foreach (var field in new[] { _targetdUrl, _targetdUser, _targetdPassword })
            field.TextChanged += (_, _) => InvalidateTargetdInspection();
        var storage = Card("Linux iSCSI storage inspection (targetd)",
            "Read-only targetd exports and access-group mappings. HTTPS and a trusted server certificate are required. Credentials stay in this session. A listed mapping does not prove ACL isolation or Windows boot.");
        storage.Controls.Add(Field("targetd HTTPS URL", _targetdUrl));
        storage.Controls.Add(Field("targetd username", _targetdUser));
        storage.Controls.Add(Field("targetd password", _targetdPassword));
        storage.Controls.Add(Button("INSPECT STORAGE MAPPINGS", async (_, _) => await InspectTargetdAsync()));
        storage.Controls.Add(Button("CHECK SELECTED CLIENT MAPPING", (_, _) => CheckSelectedTargetdMapping()));
        storage.Controls.Add(_targetdExports);
        storage.Controls.Add(_targetdMaps);
        storage.Controls.Add(_targetdStatus);
        root.Controls.Add(storage);

        var readiness = Card("Live diskless boot readiness",
            "FOG deployment writes an image to a client disk. True diskless Windows boot needs an iSCSI target, per-client writable image, PXE/iPXE boot, network isolation and real client validation.");
        readiness.Controls.Add(new Label
        {
            Text = "Diskless boot: NOT CONFIGURED · no iSCSI target or client boot evidence",
            ForeColor = BlazeTheme.Muted,
            AutoSize = true
        });
        readiness.Controls.Add(Field("Client label", _disklessClient));
        readiness.Controls.Add(Field("iSCSI target IPv4 address", _disklessTargetIp));
        readiness.Controls.Add(Field("Per-client target IQN", _disklessTargetIqn));
        readiness.Controls.Add(Field("Per-client initiator IQN", _disklessInitiatorIqn));
        readiness.Controls.Add(Button("SAVE NEW CLIENT PROFILE", (_, _) => SaveDisklessProfile()));
        readiness.Controls.Add(_disklessProfiles);
        readiness.Controls.Add(Button("SHOW SELECTED PROFILE", (_, _) => ShowDisklessProfile()));
        readiness.Controls.Add(Button("REMOVE SELECTED PROFILE", (_, _) => RemoveDisklessProfile()));
        readiness.Controls.Add(Field("DHCP option 017 root path", _disklessRootPath));
        readiness.Controls.Add(Field("iPXE boot script", _disklessScript));
        readiness.Controls.Add(_disklessProfileStatus);
        root.Controls.Add(readiness);
        _pages["Diskless"] = root;
    }

    private FogManagementClient NewFogClient() => new(_fogUrl.Text.Trim(),
        new FogCredentials(_fogBearer.Text, _fogGlobal.Text, _fogUser.Text));

    private void InvalidateTargetdInspection()
    {
        _targetdBinding.ConnectionEdited();
        _targetdSnapshot = null;
        _targetdSnapshotGeneration = -1;
        _targetdSnapshotTick = -1;
        _targetdExports.Items.Clear();
        _targetdMaps.Items.Clear();
        _targetdStatus.Text = "Storage connection changed. Inspect this server again.";
    }

    private async Task InspectTargetdAsync()
    {
        var generation = _targetdBinding.BeginRefresh();
        _targetdSnapshot = null;
        _targetdSnapshotGeneration = -1;
        _targetdSnapshotTick = -1;
        _targetdExports.Items.Clear();
        _targetdMaps.Items.Clear();
        _targetdStatus.Text = "Reading targetd inventory...";
        try
        {
            using var targetd = new TargetdInspectionClient(_targetdUrl.Text.Trim(),
                _targetdUser.Text, _targetdPassword.Text);
            var snapshot = await targetd.InspectAsync();
            if (!_targetdBinding.CompleteRefresh(generation)) return;
            _targetdSnapshot = snapshot;
            _targetdSnapshotGeneration = generation;
            _targetdSnapshotTick = Environment.TickCount64;
            foreach (var export in snapshot.Exports)
                _targetdExports.Items.Add(export);
            foreach (var map in snapshot.Maps)
                _targetdMaps.Items.Add($"{map.Group} · LUN {map.Lun} · {map.Pool}/{map.Volume}");
            _targetdStatus.Text = $"{snapshot.Exports.Count} export(s), {snapshot.Groups.Count} access group(s), " +
                $"{snapshot.Maps.Count} group mapping(s) reported by {_targetdUrl.Text.Trim()}. " +
                "Confirm target ACLs, authentication, isolation and Windows boot on approved hardware.";
        }
        catch (Exception ex)
        {
            if (_targetdBinding.Generation != generation) return;
            InvalidateTargetdInspection();
            _targetdStatus.Text = "Storage inspection failed: " + ex.Message;
        }
    }

    private void CheckSelectedTargetdMapping()
    {
        try
        {
            if (_targetdSnapshot is null || !_targetdBinding.ReadyFor(_targetdSnapshotGeneration) ||
                !TargetdSnapshotAge.IsRecent(_targetdSnapshotTick, Environment.TickCount64))
                throw new InvalidOperationException("Inspect the current targetd server before checking a client.");
            var saved = DisklessProfileRegistry.Validate(_controller.Config.DisklessProfiles);
            if (_disklessProfiles.SelectedItem is not DisklessClientAssignment assignment ||
                !saved.Contains(assignment))
                throw new InvalidOperationException("Select a currently saved client profile.");
            var result = TargetdProfileMappingCheck.Assess(assignment, _targetdSnapshot);
            _targetdStatus.Text = $"{assignment.ClientLabel}: {result.Status}. {result.Detail}";
        }
        catch (InvalidOperationException ex)
        {
            _targetdStatus.Text = "Client mapping check refused: " + ex.Message;
        }
    }

    private void InvalidateFogInventory()
    {
        _fogInventoryBinding.ConnectionEdited();
        _fogHosts.Items.Clear();
        _fogImages.Items.Clear();
        _fogTaskBinding.ConnectionEdited();
        _fogTaskHosts.Items.Clear();
        _fogTaskStatus.Text = "FOG connection changed. Inspect this server's tasks again.";
        _fogStatus.Text = "FOG connection changed. Refresh inventory before scheduling a deployment.";
    }

    private async Task InspectFogTasksAsync()
    {
        var requestGeneration = _fogTaskBinding.BeginRefresh();
        _fogTaskHosts.Items.Clear();
        _fogTaskStatus.Text = "Reading active FOG tasks...";
        try
        {
            using var fog = NewFogClient();
            var hostIds = await fog.GetActiveTaskHostIdsAsync();
            if (!_fogTaskBinding.CompleteRefresh(requestGeneration)) return;
            foreach (var hostId in hostIds)
                _fogTaskHosts.Items.Add($"host #{hostId}");
            _fogTaskStatus.Text = $"{hostIds.Count} active task(s) shown for {_fogUrl.Text.Trim()}. " +
                "Task type and disk outcome require confirmation in FOG.";
        }
        catch (Exception ex)
        {
            if (_fogTaskBinding.Generation != requestGeneration) return;
            _fogTaskBinding.ConnectionEdited();
            _fogTaskHosts.Items.Clear();
            _fogTaskStatus.Text = "FOG task inspection failed: " + ex.Message;
        }
    }

    private void RefreshDisklessProfiles()
    {
        _disklessProfiles.Items.Clear();
        try
        {
            foreach (var assignment in DisklessProfileRegistry.Validate(_controller.Config.DisklessProfiles))
                _disklessProfiles.Items.Add(assignment);
            _disklessProfileStatus.Text = $"{_disklessProfiles.Items.Count} local client profiles saved. Storage and boot remain unverified.";
        }
        catch (InvalidOperationException ex)
        {
            _disklessRootPath.Clear();
            _disklessScript.Clear();
            _disklessProfileStatus.Text = "Saved profiles invalid; edits refused: " + ex.Message;
        }
    }

    private void SaveDisklessProfile()
    {
        _disklessRootPath.Clear();
        _disklessScript.Clear();
        try
        {
            var assignment = new DisklessClientAssignment(_disklessClient.Text.Trim(),
                _disklessTargetIp.Text.Trim(), _disklessTargetIqn.Text.Trim(),
                _disklessInitiatorIqn.Text.Trim());
            var next = DisklessProfileRegistry.Add(_controller.Config.DisklessProfiles, assignment);
            PersistDisklessProfiles(next);
            RefreshDisklessProfiles();
            _disklessProfiles.SelectedItem = assignment;
            DisplayDisklessProfile(assignment);
        }
        catch (Exception ex) when (ex is InvalidOperationException or IOException or UnauthorizedAccessException)
        {
            _disklessProfileStatus.Text = "Profile was not saved: " + ex.Message;
        }
    }

    private void ShowDisklessProfile()
    {
        try
        {
            DisklessProfileRegistry.Validate(_controller.Config.DisklessProfiles);
            if (_disklessProfiles.SelectedItem is not DisklessClientAssignment assignment)
                throw new InvalidOperationException("Select a saved client profile first.");
            _disklessClient.Text = assignment.ClientLabel;
            _disklessTargetIp.Text = assignment.TargetIp;
            _disklessTargetIqn.Text = assignment.TargetIqn;
            _disklessInitiatorIqn.Text = assignment.InitiatorIqn;
            DisplayDisklessProfile(assignment);
        }
        catch (InvalidOperationException ex)
        {
            _disklessRootPath.Clear();
            _disklessScript.Clear();
            _disklessProfileStatus.Text = "Profile refused: " + ex.Message;
        }
    }

    private void RemoveDisklessProfile()
    {
        try
        {
            DisklessProfileRegistry.Validate(_controller.Config.DisklessProfiles);
            if (_disklessProfiles.SelectedItem is not DisklessClientAssignment assignment)
                throw new InvalidOperationException("Select a saved client profile first.");
            var next = DisklessProfileRegistry.Remove(_controller.Config.DisklessProfiles, assignment.ClientLabel);
            if (MessageBox.Show($"Remove local profile for {assignment.ClientLabel}? This does not remove any iSCSI target, ACL or DHCP/PXE configuration.",
                    "Confirm local profile removal", MessageBoxButtons.YesNo, MessageBoxIcon.Warning,
                    MessageBoxDefaultButton.Button2) != DialogResult.Yes) return;
            PersistDisklessProfiles(next);
            _disklessRootPath.Clear();
            _disklessScript.Clear();
            RefreshDisklessProfiles();
        }
        catch (Exception ex) when (ex is InvalidOperationException or IOException or UnauthorizedAccessException)
        {
            _disklessProfileStatus.Text = "Profile was not removed: " + ex.Message;
        }
    }

    private void PersistDisklessProfiles(IReadOnlyList<DisklessClientAssignment> next)
    {
        var previous = _controller.Config.DisklessProfiles;
        _controller.Config.DisklessProfiles = next.ToList();
        try { Storage.SaveConfig(_controller.Config); }
        catch
        {
            _controller.Config.DisklessProfiles = previous;
            throw;
        }
    }

    private void DisplayDisklessProfile(DisklessClientAssignment assignment)
    {
        var profile = assignment.BootProfile();
        _disklessRootPath.Text = profile.DhcpRootPath;
        _disklessScript.Text = profile.IpxeScript;
        _disklessProfileStatus.Text = "Profile saved for " + profile.ClientLabel +
            ". Configure target ACLs, a dedicated writable disk and DHCP/PXE separately; boot remains unverified.";
    }

    private async Task RefreshFogAsync()
    {
        var generation = _fogInventoryBinding.BeginRefresh();
        _fogHosts.Items.Clear();
        _fogImages.Items.Clear();
        try
        {
            _fogStatus.Text = "Connecting to FOG...";
            using var fog = NewFogClient();
            var info = await fog.GetServerInfoAsync();
            var hosts = await fog.GetHostsAsync();
            var images = await fog.GetImagesAsync();
            if (!_fogInventoryBinding.CompleteRefresh(generation)) return;
            _fogHosts.Items.AddRange(hosts.Cast<object>().ToArray());
            _fogImages.Items.AddRange(images.Cast<object>().ToArray());
            _fogStatus.Text = $"FOG {info.Version} · {hosts.Count} hosts · {images.Count} images · imaging management ready";
        }
        catch (Exception ex)
        {
            if (_fogInventoryBinding.Generation != generation) return;
            _fogInventoryBinding.ConnectionEdited();
            _fogHosts.Items.Clear();
            _fogImages.Items.Clear();
            _fogStatus.Text = "FOG connection failed: " + ex.Message;
        }
    }

    private async Task DeployFogAsync()
    {
        var generation = _fogInventoryBinding.Generation;
        if (!_fogInventoryBinding.ReadyFor(generation))
        {
            _fogStatus.Text = "Refresh the current FOG connection before scheduling a deployment.";
            return;
        }
        if (_fogHosts.SelectedItem is not FogHost host || _fogImages.SelectedItem is not FogImage image)
        {
            _fogStatus.Text = "Select one host and one image first.";
            return;
        }
        if (host.ImageId != image.Id || !image.Enabled)
        {
            _fogStatus.Text = "Assign an enabled image to the host in FOG before deployment.";
            return;
        }
        var answer = MessageBox.Show(
            $"Deploy image \"{image.Name}\" to \"{host.Name}\" on its next FOG boot?\n\nThis overwrites the client's disk. Verify the client and its backup first.",
            "Confirm FOG deployment", MessageBoxButtons.YesNo, MessageBoxIcon.Warning,
            MessageBoxDefaultButton.Button2);
        if (answer != DialogResult.Yes) return;
        if (!_fogInventoryBinding.ReadyFor(generation))
        {
            _fogStatus.Text = "FOG connection or inventory changed. Refresh before scheduling a deployment.";
            return;
        }
        var serverUrl = _fogUrl.Text.Trim();
        try
        {
            using var fog = NewFogClient();
            await fog.QueueDeploymentAsync(host.Id, image.Id, $"DEPLOY {host.Name} {image.Name}");
            _fogStatus.Text = $"FOG deployment queued for {host.Name} on {serverUrl}. Check FOG active tasks before booting that client.";
        }
        catch (FogDeploymentUncertainException ex)
        {
            _fogStatus.Text = $"Deployment outcome uncertain on {serverUrl}. " + ex.Message;
        }
        catch (Exception ex)
        {
            _fogStatus.Text = "Deployment was not queued: " + ex.Message;
        }
    }
}
