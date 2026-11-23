# PHX-HARDWARE handover — poll-drain polarity fixture lexical guard

**Date:** 2026-11-22 UTC05  
**Role:** PHX-HARDWARE  
**Task:** #177 / #266 / #327  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test fix:** [`d76523b877308b6b5a84e4bf85cd986de7da605d`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/d76523b877308b6b5a84e4bf85cd986de7da605d)

## Bounded Hardware-owned defect

`verify_drain_abort_polarity_fixture_is_shared()` used whitespace-only normalization over a C++ scenario fixture. It counted call-shaped text inside comments and string literals as real C++ callsites. A removed active-low or active-high drain invocation could therefore be hidden by a decoy comment/string, leaving that polarity scenario unexecuted while the static guard reported it present.

This was a verification-infrastructure defect, not a demonstrated firmware runtime defect.

## Test-first reproduction

- First harness-construction attempt [`73a3e30f137112318214d167dd51eba6217eeb09`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/73a3e30f137112318214d167dd51eba6217eeb09) failed with a Python string-escaping SyntaxError. This is recorded as a failed harness attempt, not as the defect reproduction.
- Corrected test-only mutation [`bc1a310ff440859e228cc4b329c9d37d6091f9ef`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/bc1a310ff440859e228cc4b329c9d37d6091f9ef) reproduced the false positive. The active-low invocation was replaced by a comment containing the call text; the guard failed with `POLL_DRAIN_ABORT_POLARITY_COMMENT_DECOY_SURVIVED`.
- Exact RED evidence: [Relay/output run #44990908019](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44990908019), job `137111527674`; [Quarantine run #44990908014](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44990908014), job `137111527631`. Both reached the intended decoy-survived assertion after the existing source labs, not a compiler/harness error.

## Correction

Only the Hardware-owned `poll_loop_blocking_inhibit_lab.py` changed:

- Import the already-tested shared `mask_non_code()` helper from `firmware_lab_source.py`.
- Normalize only remaining C++ code when checking the shared helper definition and its active-low/active-high callsites.
- Add two self-mutations: replace the active-low call with a comment decoy and the active-high call with a string-literal decoy. Both must be ignored by the lexical mask.
- Preserve the existing scenario body, helper implementation, firmware sketches, runtime APIs and financial behavior.

## Exact-source GREEN evidence — `d76523b877308b6b5a84e4bf85cd986de7da605d`

- Quarantine/readback [run #44990983968](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44990983968), job `137111762309`: **SUCCESS**. Logs contain `POLL_DRAIN_ABORT_POLARITY_DECOY_REJECTED 2/2` and `POLL_DRAIN_ABORT_POLARITY_BUILDER_PASS 2/2`; the existing source-extracted quarantine, journal, poll-loop and coin-post suites also completed.
- Relay/output [run #44990983935](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44990983935), jobs `137111762262` and `137111762380`: **SUCCESS**. Logs contain the same 2/2 decoy rejection markers and existing active-high/active-low output-gate checks.
- Full BlazePwifi [run #44990983975](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44990983975), validation job `137111815977`: **FAILURE** at the inherited QA-owned `Missing poll signature check` in both sketches. Other target jobs were still in progress at this handover readback; no Full integration pass is claimed.

## Classification and limits

- **SIMULATED:** C++ fixture callsite decoys and source-extracted board scenarios.
- **CI VERIFIED:** the two focused exact-source workflows above.
- **Full integration:** FAILED at the separate CORE/QA controller-response contract gate.
- **HARDWARE ACCEPTED:** NO. Physical relay/coin selector behavior, electrical recovery, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.
- **PRODUCTION READY:** NO.

No ESP32/ESP8266 production sketch, controller API, finance, witness, QA-owned assertion, Release workflow, COE destination or production state was changed. No flash, device reset, coin transaction, migration, signing, merge, tag or deployment occurred.

## Next exact action

PHX-MASTER should refresh the #327 pin in `ROLE_ASSIGNMENTS.md` / `INTEGRATION_MATRIX.md` to the new exact head after this handover commit. PHX-CORE and PHX-QA still own the authenticated register/poll response contract and its positive/negative vectors. PHX-HARDWARE will continue the #177 source audit only after revalidating those live heads; no positive coin admission is authorized by these host tests.
