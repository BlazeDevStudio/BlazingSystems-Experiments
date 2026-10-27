# PHX-L-APPS #164 — NativeCoinDispatchLab (TEST ONLY)

This .NET 8 console diagnostic compiles the **verbatim actual C# method bodies** of
`AppController.HandleCoinPulse()` (Git blob `3d16d80c79b4dbe55d006c5453e5cc605cd84421`)
and `BlazePwifiClient.ForwardCoinAsync()` (Git blob `bf7e35023e8db51dde399b98464e10b99a31735a`).
The Python extractor refuses a changed source blob with **INCONCLUSIVE exit 3**.
It never rewrites production source; generated code stays untracked.

Windows/.NET 8 CI:
```powershell
python -B experiment/windows/BlazePisonet-SoftTimer/tests/NativeCoinDispatchLab/extract_source.py
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeCoinDispatchLab/NativeCoinDispatchLab.csproj -c Release -- --diagnostic
```

The positive control verifies a real async central-await continuation and forwarding
to original target A. The stale-target negative forces an in-flight await followed
by a simulated reconnect/retarget A -> B, then checks whether the **actual extracted**
source sends the old event to B. The post-disable negative verifies that changing
`Config.Enabled` during the await does not prevent the later forward. The initial
disabled negative must not dispatch. Diagnostic mode exits 0 only if all four
source behaviors reproduce; it reports two **unsafe safety REDs** rather than
asserting production safety. `--safety-gate` exits 2 when those REDs remain.

The existing NativeSerialPinFaultLab (27/32, five opened-handle safety REDs)
runs **after** this diagnostic and remains the CI failure gate; do not suppress,
replace or relabel its five failures.

Limits: actual production method bodies are compiled by CLR on Windows, but
the controller surrounding fields, central server await, serial session, timer,
HTTP/network call and target-window state are fake. This is **not** a complete
AppController binary, real Windows serial/USB driver, actual coin, signed
server ACK, durable paid event or financial credit. A fake session generation
cannot itself prove that the current production event carries one. MASTER,
VERIFY and CORE must agree on immutable accepted-event/session/controller/
target/nonce/ACK ownership before a production fix. No merge/release/coin
admission, firmware, signer or customer money is authorized.
