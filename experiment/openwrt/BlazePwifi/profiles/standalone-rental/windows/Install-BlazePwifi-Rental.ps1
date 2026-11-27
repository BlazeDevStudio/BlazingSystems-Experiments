$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName Microsoft.VisualBasic

function Show-Error([string]$Message) {
    [System.Windows.Forms.MessageBox]::Show($Message, "BlazePwifi Rental Installer", "OK", "Error") | Out-Null
}
function Show-Info([string]$Message) {
    [System.Windows.Forms.MessageBox]::Show($Message, "BlazePwifi Rental Installer", "OK", "Information") | Out-Null
}

# Windows PowerShell 5.1 can promote stderr from a native program into a
# NativeCommandError when the script-wide ErrorActionPreference is Stop.
# PuTTY intentionally writes first-connection host-key information to stderr,
# so every PuTTY call goes through these wrappers.
function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(Mandatory=$true)][string[]]$Arguments
    )

    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        $lines = & $FilePath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        $text = (($lines | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine)
        return [pscustomobject]@{
            ExitCode = $exitCode
            Output   = $text
        }
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }
}

function Invoke-NativeVisible {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(Mandatory=$true)][string[]]$Arguments
    )

    $oldPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $FilePath @Arguments 2>&1 | ForEach-Object {
            Write-Host $_.ToString()
        }
        return $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }
}

function Prompt-Password {
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "BlazePwifi Rental - SSH Password"
    $form.Width = 420
    $form.Height = 175
    $form.StartPosition = "CenterScreen"
    $form.TopMost = $true

    $label = New-Object System.Windows.Forms.Label
    $label.Text = "Enter the SSH/root password. It is used only for this install."
    $label.AutoSize = $true
    $label.Left = 18
    $label.Top = 18
    $form.Controls.Add($label)

    $box = New-Object System.Windows.Forms.TextBox
    $box.Left = 18
    $box.Top = 50
    $box.Width = 365
    $box.UseSystemPasswordChar = $true
    $form.Controls.Add($box)

    $ok = New-Object System.Windows.Forms.Button
    $ok.Text = "Continue"
    $ok.Left = 218
    $ok.Top = 86
    $ok.Width = 80
    $ok.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.Controls.Add($ok)

    $cancel = New-Object System.Windows.Forms.Button
    $cancel.Text = "Cancel"
    $cancel.Left = 303
    $cancel.Top = 86
    $cancel.Width = 80
    $cancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $form.Controls.Add($cancel)

    $form.AcceptButton = $ok
    $form.CancelButton = $cancel
    $form.Add_Shown({$box.Focus()})
    $result = $form.ShowDialog()
    if ($result -ne [System.Windows.Forms.DialogResult]::OK) { return $null }
    return $box.Text
}

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Plink = Join-Path $Here "plink.exe"
$Pscp = Join-Path $Here "pscp.exe"
$BundleName = "BlazePwifi-Rental-Standalone-OpenWrt-v0.5.0-rental-rc.3.tar.gz"
$Bundle = Get-ChildItem -Path $Here -Filter $BundleName -ErrorAction SilentlyContinue | Select-Object -First 1

if (!(Test-Path $Plink) -or !(Test-Path $Pscp)) {
    Show-Error "The installer package is incomplete. plink.exe and pscp.exe must be beside this script."
    exit 2
}
if (!$Bundle) {
    Show-Error "The OpenWrt Rental Standalone bundle was not found beside this script."
    exit 3
}

$gateway = ""
try {
    $gateway = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction Stop |
        Where-Object {$_.NextHop -and $_.NextHop -ne "0.0.0.0"} |
        Sort-Object RouteMetric |
        Select-Object -First 1 -ExpandProperty NextHop)
} catch {}

$HostName = [Microsoft.VisualBasic.Interaction]::InputBox(
    "Router IP or hostname:`r`n`r`nExample: 192.168.1.1",
    "BlazePwifi Rental - Target",
    $gateway
).Trim()
if (!$HostName) { exit 1 }

$SshUser = [Microsoft.VisualBasic.Interaction]::InputBox(
    "SSH username:",
    "BlazePwifi Rental - SSH User",
    "root"
).Trim()
if (!$SshUser) { exit 1 }

$PortText = [Microsoft.VisualBasic.Interaction]::InputBox(
    "SSH port:",
    "BlazePwifi Rental - SSH Port",
    "22"
).Trim()
[int]$Port = 22
if (![int]::TryParse($PortText, [ref]$Port) -or $Port -lt 1 -or $Port -gt 65535) {
    Show-Error "Invalid SSH port."
    exit 4
}

$Password = Prompt-Password
if ($null -eq $Password -or $Password.Length -eq 0) { exit 1 }

$PwFile = Join-Path $env:TEMP ("blazepwifi-rental-" + [Guid]::NewGuid().ToString("N") + ".pw")
[System.IO.File]::WriteAllText($PwFile, $Password, [System.Text.Encoding]::ASCII)
$Password = $null

$HostKeyArgs = @()
try {
    Write-Host ""
    Write-Host "Checking SSH connection to $SshUser@$HostName`:$Port ..." -ForegroundColor Cyan

    $base = @("-ssh","-P",$Port.ToString(),"-batch","-pwfile",$PwFile)
    $probeArgs = $base + @("$SshUser@$HostName","echo BLAZE_SSH_OK")
    $probe = Invoke-NativeCapture -FilePath $Plink -Arguments $probeArgs

    if ($probe.ExitCode -ne 0) {
        # Typical PuTTY first-connection output contains:
        # ssh-ed25519 255 SHA256:...
        # ecdsa-sha2-nistp256 256 SHA256:...
        # ssh-rsa 2048 SHA256:...
        $match = [regex]::Match(
            $probe.Output,
            '(?im)(ssh-[A-Za-z0-9@._+-]+|ecdsa-[A-Za-z0-9@._+-]+)\s+\d+\s+SHA256:[A-Za-z0-9+/=]+'
        )

        if (!$match.Success) {
            Write-Host $probe.Output
            Show-Error "SSH connection failed. Check the router IP, SSH service, username and password."
            exit 5
        }

        $fingerprint = $match.Value.Trim()
        $choice = [System.Windows.Forms.MessageBox]::Show(
            "First connection to this router.`r`n`r`nSSH host key:`r`n$fingerprint`r`n`r`nTrust this router and continue the installation?",
            "BlazePwifi Rental - Verify Router",
            [System.Windows.Forms.MessageBoxButtons]::YesNo,
            [System.Windows.Forms.MessageBoxIcon]::Question
        )
        if ($choice -ne [System.Windows.Forms.DialogResult]::Yes) { exit 6 }

        # Pin the accepted fingerprint for every remaining SSH/SCP operation.
        # This avoids a second interactive PuTTY host-key prompt and does not
        # require the user to open PuTTY or pre-cache anything manually.
        $HostKeyArgs = @("-hostkey",$fingerprint)
        $probeArgs = $base + $HostKeyArgs + @("$SshUser@$HostName","echo BLAZE_SSH_OK")
        $probe = Invoke-NativeCapture -FilePath $Plink -Arguments $probeArgs

        if ($probe.ExitCode -ne 0 -or $probe.Output -notmatch "BLAZE_SSH_OK") {
            Write-Host $probe.Output
            Show-Error "SSH authentication failed after router host-key verification."
            exit 7
        }
    }
    elseif ($probe.Output -notmatch "BLAZE_SSH_OK") {
        Write-Host $probe.Output
        Show-Error "SSH connected but the router did not return the expected validation response."
        exit 7
    }

    Write-Host "SSH connection OK." -ForegroundColor Green
    Write-Host "Uploading Rental Standalone package..." -ForegroundColor Cyan

    $scpArgs = @("-scp","-P",$Port.ToString(),"-batch","-pwfile",$PwFile) + $HostKeyArgs +
        @($Bundle.FullName,"$SshUser@$HostName`:/tmp/$BundleName")
    $scp = Invoke-NativeCapture -FilePath $Pscp -Arguments $scpArgs
    if ($scp.ExitCode -ne 0) {
        Write-Host $scp.Output
        Show-Error "Package upload failed."
        exit 8
    }

    $remote = @'
set -e
rm -rf /tmp/blazepwifi-rental-install
mkdir -p /tmp/blazepwifi-rental-install
tar -xzf /tmp/BlazePwifi-Rental-Standalone-OpenWrt-v0.5.0-rental-rc.3.tar.gz -C /tmp/blazepwifi-rental-install --strip-components=1
cd /tmp/blazepwifi-rental-install
sh ./install.sh --target=auto
'@

    Write-Host ""
    Write-Host "Installing on OpenWrt..." -ForegroundColor Cyan
    $installArgs = @("-ssh","-P",$Port.ToString(),"-batch","-pwfile",$PwFile) + $HostKeyArgs +
        @("$SshUser@$HostName",$remote)
    $rc = Invoke-NativeVisible -FilePath $Plink -Arguments $installArgs

    if ($rc -ne 0) {
        Show-Error "The router-side installer failed. Review the console output above. Existing network/Wi-Fi/firewall settings were not intentionally changed."
        exit $rc
    }

    Write-Host ""
    Write-Host "Installation complete." -ForegroundColor Green
    Write-Host "Rental console: https://$HostName/rental/" -ForegroundColor Green
    Write-Host "Android server: http://$HostName" -ForegroundColor Green

    Show-Info "BlazePwifi Rental Standalone was installed.`r`n`r`nRental console:`r`nhttps://$HostName/rental/`r`n`r`nAndroid server:`r`nhttp://$HostName`r`n`r`nThe console window contains the generated bootstrap password if this was a first install."
    try { Start-Process "https://$HostName/rental/" } catch {}
}
finally {
    if (Test-Path $PwFile) {
        try { [System.IO.File]::WriteAllText($PwFile, ("0" * 128)) } catch {}
        Remove-Item -Force $PwFile -ErrorAction SilentlyContinue
    }
}
