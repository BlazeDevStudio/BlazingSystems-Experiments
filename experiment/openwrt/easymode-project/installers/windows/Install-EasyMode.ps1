param([string]$Router="192.168.1.1",[string]$User="root",[ValidateSet("auto","cellular","ap","router","switch","pc","generic")][string]$Edition="auto")
$ErrorActionPreference="Stop"
Write-Host "EasyMode Installer 5.0.0-alpha.1"
$ssh=Get-Command ssh -ErrorAction SilentlyContinue; $scp=Get-Command scp -ErrorAction SilentlyContinue
if(-not $ssh -or -not $scp){ throw "Windows OpenSSH Client (ssh/scp) is required. Enable the built-in Windows optional feature, then rerun." }
$bundle=Join-Path $PSScriptRoot "easymode-upload.tar.gz"
if(-not (Test-Path $bundle)){ throw "Missing $bundle." }
Write-Host "Testing SSH connection to $User@$Router..."
& $ssh "$User@$Router" "ubus call system board"; if($LASTEXITCODE){ throw "SSH/ubus test failed" }
Write-Host "Uploading..."; & $scp $bundle "$User@${Router}:/tmp/easymode-upload.tar.gz"; if($LASTEXITCODE){ throw "SCP upload failed" }
$cmd="rm -rf /tmp/easymode-upload; mkdir -p /tmp/easymode-upload; tar -xzf /tmp/easymode-upload.tar.gz -C /tmp/easymode-upload; /tmp/easymode-upload/installers/openwrt/install.sh $Edition"
& $ssh "$User@$Router" $cmd; if($LASTEXITCODE){ throw "Router installer failed or rolled back" }
Write-Host "EasyMode installation completed."
