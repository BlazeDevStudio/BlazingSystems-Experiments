param([string]$Router="192.168.1.1",[string]$User="root",[ValidateSet("auto","cellular","ap","router","switch","pc","generic")][string]$Edition="auto")
$ErrorActionPreference="Stop"
$ssh=Get-Command ssh -ErrorAction SilentlyContinue; $scp=Get-Command scp -ErrorAction SilentlyContinue
if(-not $ssh -or -not $scp){ throw "Windows OpenSSH Client (ssh/scp) is required." }
$bundle=Join-Path $PSScriptRoot "easymode-upload.tar.gz"; if(-not(Test-Path $bundle)){throw "Missing easymode-upload.tar.gz"}
& $ssh "$User@$Router" "ubus call system board"; if($LASTEXITCODE){throw "SSH/ubus test failed"}
& $scp $bundle "$User@${Router}:/tmp/easymode-upload.tar.gz"; if($LASTEXITCODE){throw "SCP upload failed"}
& $ssh "$User@$Router" "rm -rf /tmp/easymode-upload; mkdir -p /tmp/easymode-upload; tar -xzf /tmp/easymode-upload.tar.gz -C /tmp/easymode-upload; /tmp/easymode-upload/installers/openwrt/install.sh $Edition"
if($LASTEXITCODE){throw "Router installer failed or rolled back"}
