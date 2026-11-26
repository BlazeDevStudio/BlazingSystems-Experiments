# PHX-HARDWARE — 2026-11-26 UTC12 poll-guard control-flow regression

**Task:** [Issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) / [DRAFT PR #354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354)  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`  
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**Source/test SHA:** `ea24229ee3b46424997fd3e68012ef50a65897f9`  
**PR state:** OPEN / DRAFT / UNMERGED; deny-only.

## Scope

One Hardware-owned test-hardening task: prove that the pre-poll and post-poll `denyRemoteControl()` calls are unconditional top-level statements, not calls hidden under a conditional, and that no control transfer can bypass the post-poll deny.

The previous source-extracted lab checked only source order. It accepted this unsafe mutation:

```cpp
if (false) {
    denyRemoteControl();
}
(void)post("poll");
```

The production sketches currently use direct unconditional pre/post deny calls. This activation changed only `poll_preflight_inhibit_lab.py`; neither production sketch was modified.

## Test-first evidence

- **RED:** [Run #45819429664](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45819429664), job `139907519235`, failed at the new braced conditional pre-poll mutation because the old guard accepted it.
- **Correction:** [Commit `ea24229ee3b46424997fd3e68012ef50a65897f9`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ea24229ee3b46424997fd3e68012ef50a65897f9).
- **Exact-source GREEN:** [Run #45819620598](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45819620598), job `139908174414`, PASS.

The corrected lab:
- requires each deny call to be a direct top-level standalone statement inside the guarded poll block;
- rejects braced and unbraced conditional pre-poll deny mutations;
- rejects braced and unbraced conditional post-poll deny mutations;
- rejects an early return before the post-poll deny;
- rejects `return`, `goto`, `break`, `continue`, or `throw` between the blocking poll and post-poll deny.

The focused log confirms five new control-flow mutations rejected on each board (10/10), plus the existing poll-response-discard, remote-config-deny, no-coin-POST, no-pending-clear, request-auth, GPIO output-order and source-extractor checks.

## Other current CI / blockers

- Native [#45819620637](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45819620637), job `139908175159`: FAIL at QA-owned PAY-0745 active `clearPending(true/false)` assertion. Do not restore active pending disposition.
- Full [#45820173237](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45820173237) was superseded after its handover-freshness failure; root handover, CURRENT_STATE and append-only CHANGE_LEDGER were refreshed afterward. A new exact-head Full run is required.
- ESP32 Mbed TLS matrix [#45819620625](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45819620625): source contract and core 3.3.13 passed; core 4.0.0 was still in progress at the last job read. No terminal result claimed here.

## Safety / acceptance status

The candidate continues to deny coin/relay/LED outputs before and after synchronous poll, discards the unauthenticated poll response, does not apply remote configuration, does not issue automatic coin POST, and does not actively clear pending evidence.

Host/source-extracted evidence is **SIMULATED / CI VERIFIED only**. Physical coin/relay acceptance, GPIO voltage/contact transient, LittleFS power-loss durability, electrical pulse/recovery, 150 controlled power cuts and 30-device/24-hour soak are **NOT TESTED**. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.

No QA/CORE/Master-owned source changed. No Codex, physical flash, device reset, live-money operation, migration, signer provisioning, merge, release tag or deployment occurred.

## Next exact action

PHX-QA reconciles the native deny-only/pending-evidence assertion; PHX-CORE publishes the authenticated register/poll and receipt/disposition contract; PHX-MASTER refreshes the #354 head pin. PHX-HARDWARE reruns Full validation on the exact current head and keeps coin/relay admission denied until the shared contract is approved.
