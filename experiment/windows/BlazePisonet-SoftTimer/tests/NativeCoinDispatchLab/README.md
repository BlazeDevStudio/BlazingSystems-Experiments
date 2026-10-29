# PHX-PISONET #216 — NativeCoinDispatchLab, actual-source correction controls

**Native Windows result:** [#40817385210](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40817385210) **SUCCESS**, exact production+fixture HEAD `ba1fa03d5952a0919daa7bb5a88c947594b8e0d1`.

## Exact-source provenance

`extract_source.py` checks literal `git hash-object` before extracting and compiling production methods into `GeneratedMethods.g.cs` (never changes product source):

- `AppController.cs` blob `f315f18826c9cb6f20bfe03dfaff8fe16ccb2b7d`, actual `HandleCoinPulse(SerialCoinAcceptance)`.
- `BlazePwifiClient.cs` blob `afa20d80f7d57ea206d4ca7051ea1011d4de31c9`, actual immutable `CoinWindowSnapshot`, capture, poll-revision check, ownership check and both forwarding methods.

## Controls (real Windows/.NET8 C# against fake network/central/serial API)

Original #216 scenarios are **preserved**: valid A during/after central await forwards A; stale original A after session1→2/target B forwards neither A nor B; disable after await forwards none; initially disabled invokes no centralized request.

Additional controls: retarget with unchanged serial session denied, mutated controller ID denied, `ok:true` with wrong/missing `target_nonce` denied, unchanged poll does not retire the in-flight A window, a retry of the *same* captured event keeps its originally minted v1 event nonce, retargeted old retry denied, and unowned legacy forwarding entry point denied. Separate workflow tests #219 CTS valid1/V4=0/V5=1, #221 failed Open, and immutable serial event reentrancy and builds app with `-warnaserror`.

```powershell
python experiment/windows/BlazePisonet-SoftTimer/tests/NativeCoinDispatchLab/extract_source.py
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeCoinDispatchLab/NativeCoinDispatchLab.csproj -c Release -- --invalid-setup
# Must exit 3 (test setup negative)
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeCoinDispatchLab/NativeCoinDispatchLab.csproj -c Release --no-build
# Must exit 0, unsafe exit 2, inconclusive exit 3
```

## Limits / release NO-GO

The actual existing OpenWrt v1 `coin` CGI response echoes `target_nonce` on new/duplicate ACK; client compares it to the original immutable snapshot. **This is a correlation check, NOT a cryptographically signed, controller/event-bound paid receipt.** The coin HTTP request contains its original stable `id`, `target`, `nonce`, `pulses`, `sig` form values; the fake handler is not a real server or signer. Lost ACK still needs durable journal/witness and operator reconciliation, not a new event. No actual Windows OS opened-HANDLE identity, physical USB/RS232 signal, customer money, signer/migration or real production traffic tested.

Parent #197 five opened-HANDLE identity safety REDs remain **separate**, so the inherited full release workflow remains unsafe. PR #238 is DRAFT, UNMERGED; no release, coin admission or deployment authorized. Original #216 test-only LIGHT PR remains unchanged.
