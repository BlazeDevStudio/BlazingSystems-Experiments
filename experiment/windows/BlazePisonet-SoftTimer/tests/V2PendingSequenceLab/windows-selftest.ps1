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
  # PAY-0717: Retire bare textual ACK entirely, even in this fixture.
  $key = '3333333333333333333333333333333333333333333333333333333333333333'
  $wrongKey = '4444444444444444444444444444444444444444444444444444444444444444'
  $signer = Join-Path $PSScriptRoot '../V2NativeEnvelopeContract/V2NativeEnvelopeContract.csproj'
  dotnet build $signer -c Release -warnaserror --nologo
  if ($LASTEXITCODE -ne 0) { throw 'PAY-0717 fixture signer build' }
  $signerDll = Join-Path $PSScriptRoot '../V2NativeEnvelopeContract/bin/Release/net8.0/V2NativeEnvelopeContract.dll'
  $reply = & dotnet $signerDll --ack-fixture ctrlOne 1 AM alice - 40 1000 COMMIT 140 $key
  if ($LASTEXITCODE -ne 0) { throw 'PAY-0717 signed fixture ACK generation' }
  Reject -items @('--ack', $temp, '1', 'AM', 'alice', '-', '40', '1000', ('COMMIT' + [char]9 + '140'))
  Reject -items @('--ack-auth', $temp, '1', 'AM', 'alice', '-', '40', '1000', ('COMMIT' + [char]9 + '140'), $key)
  Reject -items @('--ack-auth', $temp, '1', 'AM', 'alice', '-', '40', '1000', $reply, $wrongKey)
  Reject -items @('--ack-auth', $temp, '2', 'AM', 'alice', '-', '40', '1000', $reply, $key)
  $other = & dotnet $signerDll --ack-fixture ctrlOther 1 AM alice - 40 1000 COMMIT 140 $key
  if ($LASTEXITCODE -ne 0) { throw 'PAY-0717 wrong controller fixture' }
  Reject -items @('--ack-auth', $temp, '1', 'AM', 'alice', '-', '40', '1000', $other, $key)
  $wrongAmount = & dotnet $signerDll --ack-fixture ctrlOne 1 AM alice - 41 1000 COMMIT 140 $key
  if ($LASTEXITCODE -ne 0) { throw 'PAY-0717 amount collision fixture' }
  Reject -items @('--ack-auth', $temp, '1', 'AM', 'alice', '-', '40', '1000', $wrongAmount, $key)
  $before = (Get-FileHash (Join-Path $temp 'sequence.state') -Algorithm SHA256).Hash
  if ((Run -items @('--ack-auth', $temp, '1', 'AM', 'alice', '-', '40', '1000', $reply, $key)) -ne 'ACKED') { throw 'authenticated ack result' }
  if ((Get-FileHash (Join-Path $temp 'sequence.state') -Algorithm SHA256).Hash -eq $before) { throw 'ACK did not update state' }
  if ((Run -items @('--pending', $temp)) -ne 'EMPTY') { throw 'cleared pending' }
  if ((Run -items @('--reserve', $temp, 'TM', 'alice', 'bob', '30', '1000')) -ne 'ctrlOne 2 TM alice bob 30 1000') { throw 'sequence reuse' }
  $file = Join-Path $temp 'sequence.state'
  [IO.File]::AppendAllText($file, 'TAMPER' + [char]10)
  Reject -items @('--pending', $temp)
  Reject -items @('--reserve', $temp, 'AM', 'alice', '-', '3', '1000')
  Write-Output 'PAY-0716/PAY-0717 Windows authenticated ACK + process-restart fixture PASS (not production)'
}
finally {
  Remove-Item Env:BLAZE_V2_PENDING_FAULT -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
