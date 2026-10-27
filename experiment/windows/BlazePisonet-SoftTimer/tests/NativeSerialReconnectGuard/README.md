# PHX-L-APPS #164 — bounded native Windows/.NET 8 CTS reconnect race diagnostic

**TEST ONLY.** Authorized by PHX-L-MASTER's conditional decision [#172 / 6405148364](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/172#issuecomment-6405148364). Stacked on DRAFT #197. Does NOT modify the installed SoftTimer application code, financial authority, modem driver, firmware, actual coin acceptor, customer money, signing or release.

## Exact-source guards and evidence quality

The workflow uses Windows `windows-latest`, .NET 8, and Python 3.12 only to prepare the source copy. Before any compilation, `prepare_guarded_copy.py` executes literal `git hash-object` on the checked-out **production** `SerialHardware.cs` (must equal `487eea1729b86cf463ffae6c7393ecb8ccbe809f`) and **existing TEST-ONLY** `FakeOsAndAppTypes.cs` (must equal `db0ec9f4a4a82c3524e13197f86f01a733e0b3e6`). A different SHA/missing file/repeated instrument anchor returns explicit **INCONCLUSIVE exit 3** before native testing. This is exact source revision custody; it does NOT imply physical adapter provenance.

The preparer creates only ignored/disposable `Generated/ActualSerialHardware.cs` by changing ONE expression in a COPY: split the original `if (!TryReadCoinActive(cfg, out var active))` into `sampleOk`, invoke `TestOnlyHooks.ObserveSample` immediately after the `TryReadCoinActive` call releases its lock, then check the same Boolean. Original application `SerialHardware.cs` is not changed. The actual C# source is compiled and executed with fake System.IO.Ports and WMI APIs in a real Windows .NET CLR, not merely modeled in Python or C++.

## Nonvacuous positive + two forced races

- First a **real source-linked C# valid CTS pulse positive control**: one accepted `CoinPulseAccepted`, two observed successful CTS samples. Otherwise explicit exit **3**.
- **V4**: old A active-high CTS status read returns a valid asserted level. Barrier then forces `Connect(B)` with new idle active-low CTS before old A callback updates pulse state; old callback resumes and subsequent idle B notification must **NOT** count a coin. Unsafe pre-fix source yields **1 false callback** vs **0 required**.
- **V5**: old A CTS status read THROWS and returns untrusted. Barrier forces `Connect(B)` in active-high mode; a **valid B pulse starts**; old A callback then resumes its error handler, which must NOT corrupt B pulse state. Unsafe pre-fix source yields **0 delivered callbacks** vs **1 legitimate new-session callback required**. This tests source-level event-loss/liveness, not physical pulses or actual paid balance.
- Instrumented callback CTS-sample hooks and barriers must actually fire and release. Timeout, missing old/new distinct port, unexpected hook count or wrong CTS status => **INCONCLUSIVE exit 3**, not fabricated RED or GREEN.
- `--invalid-setup` runs a deliberately invalid control whose native .NET process **must exit 3** before the normal diagnostic; the latest workflow adds this extra verification.

### Exit classifications

| Native exit | Meaning |
|---|---|
| `2` | Both source-level V4/V5 unsafe outcomes reproduced under controlled fake OS; workflow records `NATIVE_CSHARP_EXPECTED_SOURCE_RED_CONFIRMED` and exits successfully **only as an expected diagnostic RED**, not safety GREEN |
| `0` | Both instrumented cases met their expected safe outcomes; not hardware/production proof, requires independent review |
| `1` | Unexpected mixed result, compiler/suite mismatch; not a meaningful safety RED |
| `3` | Invalid/untestable setup, guard/sentinel/positive control failure; **INCONCLUSIVE**, no safety claim |

## Actual verified prior run

[Windows Actions #40447487104](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40447487104), literal workflow SHA `a6a41c84cab99e6731e99920e0637071f9cf7ee8`: **completed SUCCESS as diagnostic wrapper**, both exact Git-blob guards PASSED, disposable copy generated, actual C# positive accepted **1** with 2 CTS samples, V4 FALSE credit **1** vs required 0, V5 legitimate B credit **0** vs required 1, native exit `2` observed. No physical adapter or Windows COM driver used. This run did **not** yet exercise the separate deliberately-invalid exit-3 control. Latest source+workflow successor adding this negative control needs its own exact-head Windows conclusion. Prior #197 five separate opened-handle safety RED remain preserved (27/32 expected matching), not corrected by this test.

## Mandatory open gates

Real Windows driver callbacks, USB serial device-interface HANDLE identity, stale/reentrant callbacks, paid event/session/target immutable identity, Ring width capture, delayed pulses, signer/witness/migration, 150 physical power cuts and 30-device/24h soak are **NOT verified**. MASTER and VERIFY review before any app source change, cross-worker API contract or integration; financial coin admission **NO-GO**. No PR merges/releases from this lab.
