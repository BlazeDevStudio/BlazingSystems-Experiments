# PAY-0716 Windows process-restart fixture: no production app / keys.
$ErrorActionPreference = 'Stop'
$proj = Join-Path $PSScriptRoot 'V2PendingSequenceLab.csproj'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('blaze-v2-pending-' + ([Guid]::NewGuid().ToString('N')).Substring(0,12))
New-Item -ItemType Directory -Path $temp -Force | Out-Null
try {
  [IO.File]::WriteAllText((Join-Path $temp '.blaze-v2-pending-synthetic-only'), ('BLAZE-V2-PENDING-SYNTHETIC-ONLY' + [char]10), [Text.Encoding]::ASCII)
  dotnet build $proj -c Release -warnaserror --nologo
  if ($LASTEXITCODE -ne 0) { throw 'PAY-0716 .NET8 compilation failure' }
  $dll = Join-Path $PSScriptRoot 'bin/Release/net8.0/V2PendingSequenceLab.dll'
  function Run([string[]]$items) {
    $output = & dotnet $dll @items
    if ($LASTEXITCODE -ne 0) { throw ('PAY-0716 Windows failure: ' + ($items -join ' ')) }
    return ($output | Out-String).Trim()
  }
  function Reject([string[]]$items) {
    $null = & dotnet $dll @items 2>$null
    if ($LASTEXITCODE -eq 0) { throw 'PAY-0716 Windows unexpectedly accepted invalid authority' }
  }
  Reject -items @('--pending', $temp)
  if ((Run -items @('--init', $temp, 'ctrlOne')) -ne 'INITIALIZED') { throw 'init' }
  Reject -items @('--init', $temp, 'ctrlOne')
  $initial = (Get-FileHash (Join-Path $temp 'sequence.state') -Algorithm SHA256).Hash
  $env:BLAZE_V2_PENDING_FAULT = 'before-rename'
  Reject -items @('--reserve', $temp, 'AM', 'alice', '-', '40', '1000')
  Remove-Item Env:BLAZE_V2_PENDING_FAULT
  if ((Get-FileHash (Join-Path $temp 'sequence.state') -Algorithm SHA256).Hash -ne $initial) { throw 'precommit mutated authority' }
  $env:BLAZE_V2_PENDING_FAULT = 'after-rename'
  Reject -items @('--reserve', $temp, 'AM', 'alice', '-', '40', '1000')
  Remove-Item Env:BLAZE_V2_PENDING_FAULT
  $command = 'ctrlOne 1 AM alice - 40 1000'
  if ((Run -items @('--pending', $temp)) -ne $command) { throw 'restart pending identity' }
  if ((Run -items @('--reserve', $temp, 'AM', 'alice', '-', '40', '1000')) -ne $command) { throw 'duplicate seq' }
  Reject -items @('--reserve', $temp, 'AM', 'alice', '-', '41', '1000')
  # PAY-0718: separate fixture server ACK trust, no controller-key fallback.
  $controllerKey = '3333333333333333333333333333333333333333333333333333333333333333'
  $serverKey = '5555555555555555555555555555555555555555555555555555555555555555'
  $revokedKey = '6666666666666666666666666666666666666666666666666666666666666666'
  $rotatedKey = '7777777777777777777777777777777777777777777777777777777777777777'
  $signer = Join-Path $PSScriptRoot '../V2NativeEnvelopeContract/V2NativeEnvelopeContract.csproj'
  dotnet build $signer -c Release -warnaserror --nologo
  if ($LASTEXITCODE -ne 0) { throw 'PAY-0718 signer fixture build' }
  $signerDll = Join-Path $PSScriptRoot '../V2NativeEnvelopeContract/bin/Release/net8.0/V2NativeEnvelopeContract.dll'
  $trust = Join-Path $temp 'trusted-server-ack-keys.tsv'
  $registry = "serverA`tctrlOne`tactive`t$serverKey`nserverOld`tctrlOne`trevoked`t$revokedKey`n"
  [IO.File]::WriteAllText($trust, $registry, [Text.Encoding]::ASCII)
  $reply = & dotnet $signerDll --server-ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 serverA $serverKey
  if ($LASTEXITCODE -ne 0) { throw 'PAY-0718 server ACK fixture generation' }
  $legacy = & dotnet $signerDll --ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 $controllerKey
  Reject -items @('--ack', $temp, '1', 'AM', 'alice', '-', '40', '1000', ("COMMIT`t140"))
  Reject -items @('--ack-auth', $temp, '1', 'AM', 'alice', '-', '40', '1000', $legacy, $controllerKey)
  Reject -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $legacy)
  $forged = & dotnet $signerDll --server-ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 serverA $controllerKey
  Reject -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $forged)
  Reject -items @('--ack-server', $temp, '2', 'AM', 'alice', '-', '40', '1000', $reply)
  $other = & dotnet $signerDll --server-ack-fixture ctrlOther 1 AM alice - 40 1000 COMMIT 140 serverA $serverKey
  Reject -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $other)
  $wrongAmount = & dotnet $signerDll --server-ack-fixture ctrlOne 1 AM alice - 41 1000 COMMIT 140 serverA $serverKey
  Reject -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $wrongAmount)
  $revoked = & dotnet $signerDll --server-ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 serverOld $revokedKey
  Reject -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $revoked)
  $unknown = & dotnet $signerDll --server-ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 serverMissing $serverKey
  Reject -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $unknown)
  [IO.File]::WriteAllText($trust, "serverA`tctrlOne`trevoked`t$serverKey`nserverNew`tctrlOne`tactive`t$rotatedKey`n", [Text.Encoding]::ASCII)
  Reject -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $reply)
  [IO.File]::WriteAllText($trust, "serverA`tctrlOne`tactive`t$serverKey`nserverNew`tctrlOne`tactive`t$rotatedKey`n", [Text.Encoding]::ASCII)
  Reject -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $reply)
  [IO.File]::WriteAllText($trust, $registry, [Text.Encoding]::ASCII)
  # Temporary synthetic-only reason categories; never print key or raw ACK.
  $env:BLAZE_V2_LAB_DIAG = 'synthetic-only'
  $before = (Get-FileHash (Join-Path $temp 'sequence.state') -Algorithm SHA256).Hash
  if ((Run -items @('--ack-server', $temp, '1', 'AM', 'alice', '-', '40', '1000', $reply)) -ne 'ACKED') { throw 'independent server ACK result' }
  if ((Get-FileHash (Join-Path $temp 'sequence.state') -Algorithm SHA256).Hash -eq $before) { throw 'ACK did not update state' }
  if ((Run -items @('--pending', $temp)) -ne 'EMPTY') { throw 'cleared pending' }
  if ((Run -items @('--reserve', $temp, 'TM', 'alice', 'bob', '30', '1000')) -ne 'ctrlOne 2 TM alice bob 30 1000') { throw 'sequence reuse' }
  $file = Join-Path $temp 'sequence.state'
  [IO.File]::AppendAllText($file, 'TAMPER' + [char]10)
  Reject -items @('--pending', $temp)
  Reject -items @('--reserve', $temp, 'AM', 'alice', '-', '3', '1000')
  Write-Output 'PAY-0718 Windows independent server ACK rotation/revocation + restart fixture PASS (not production)'
}
finally {
  Remove-Item Env:BLAZE_V2_PENDING_FAULT -ErrorAction SilentlyContinue
  Remove-Item Env:BLAZE_V2_LAB_DIAG -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
