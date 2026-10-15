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
        try
        {
            _fogStatus.Text = "Connecting to FOG...";
            using var fog = NewFogClient();
            var info = await fog.GetServerInfoAsync();
            var hosts = await fog.GetHostsAsync();
            var images = await fog.GetImagesAsync();
            _fogHosts.Items.Clear();
            _fogImages.Items.Clear();
            _fogHosts.Items.AddRange(hosts.Cast<object>().ToArray());
            _fogImages.Items.AddRange(images.Cast<object>().ToArray());
            _fogStatus.Text = $"FOG {info.Version} · {hosts.Count} hosts · {images.Count} images · imaging management ready";
        }
        catch (Exception ex)
        {
            _fogHosts.Items.Clear();
            _fogImages.Items.Clear();
            _fogStatus.Text = "FOG connection failed: " + ex.Message;
        }
    }

    private async Task DeployFogAsync()
    {
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
        try
        {
            using var fog = NewFogClient();
            await fog.QueueDeploymentAsync(host.Id, image.Id, $"DEPLOY {host.Name} {image.Name}");
            _fogStatus.Text = $"FOG deployment queued for {host.Name}. Check FOG active tasks before booting that client.";
        }
        catch (Exception ex)
        {
            _fogStatus.Text = "Deployment was not queued: " + ex.Message;
        }
    }
}
