# PHX-HARDWARE UTC05 — active v0.6 poll intake deny

**Task:** P0 coin-pulse loss during synchronous poll — [Issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Control plane:** [Issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Cleanup gate:** [Issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**Draft:** [PR #354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354)  
**Role:** PHX-HARDWARE  
**Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`  
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**Source implementation commit:** `dc619870a096f01d0d1cba24f0bf3c0c981a08d2`  
**Test-matcher correction:** `f381f6d38699e953b32e1d0c603524bc6da86541`

## Why this is a separate active-branch PR

Existing [PR #340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/340) already contains a deny-only poll candidate, but it is a child of #283. The active v0.6 branch remains separate and still had synchronous poll-before-sample, unsigned register/poll consumption, and automatic pending coin POST/clear. This PR applies the bounded deny-only mitigation directly to the active branch without changing or rebasing #239, #254, #283, #340, #352 or #353.

## Test-first evidence

- Test-only PR head `95a32f53824591ceacfbc6317b3f80c95a883b75`: [run #45764293566](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45764293566), job `139721362633`, expected RED. The corrected source guard rejected the active loop because pending coin disposition (`clearPending`) was still present. The response-use and remote-config mutation checks ran first and were rejected.
- Earlier run #45764106355 is **not counted**: its harness had an invalid regex escape.
- Intermediate source-head run #45764829147 is **not counted as product failure**: the new global definition-only matcher had an invalid regex escape; corrected in `f381f6d...`.

## Firmware changes on both boards

- Added `denyRemoteControl()`: disable controller, coin, relay and LED flags; clear only the active target; force logical outputs OFF using existing board polarity handling.
- Invoke deny before and after each synchronous `post("poll")`; explicitly discard the poll response.
- Ignore register response and deny after registration; setup denies immediately after pin configuration.
- Retain `applyRemoteConfig()` only as a deny-only compatibility sentinel.
- Remove unused unauthenticated `jsonString/jsonTrue/jsonInt` parsers and `remoteRevision`.
- Remove automatic `post("coin")`, retry and `clearPending()` from the loop. Existing unresolved pending journal state is retained; the deny helper does not modify `pendingPulses`, `pendingNonce`, `pendingTarget` or the durable sequence record.

**Operational consequence:** this is deliberately deny-only. Coin acceptance and automatic event disposition remain unavailable until PHX-CORE publishes the authenticated controller/configuration and event receipt/disposition contracts and PHX-QA independently validates them. This is safer than reopening the relay based on unsigned legacy fields.

## Focused regression scope

The source-extracted host lab checks both board sketches and:
- pre-poll deny, blocking poll, post-poll deny ordering;
- discarded poll response and no unauthenticated remote config use;
- GPIO OFF behavior under both relay polarities;
- pending pulse/nonce/target preservation when deny is applied;
- failure injection for missing deny assignments, missing pre-poll guard, unguarded second poll, response consumption, remote config application, automatic coin POST and pending clear.

The companion remote-config lab verifies the compatibility sentinel remains deny-only. The workflow asserts that the checked-out SHA equals the event SHA.

## Acceptance boundaries

- Host C++ and source-extracted tests: **SIMULATED / CI VERIFIED only**.
- Physical relay polarity, coin acceptor cutoff timing, electrical pulse/recovery, power-loss behavior and actual coin-slot acceptance: **NOT TESTED**.
- 150 controlled power cuts, 30-device/24-hour soak, protected anti-rollback witness, financial migration, durable accounting/replay and independent release signoff remain open.
- No shared API/schema was changed. No finance backend or COE file was modified.
- No physical flash, device reset, live money, signing, migration, merge, deployment or release tagging occurred.

## Review requests

- **PHX-QA:** independently review the source-extracted deny/polarity/pending-preservation tests and mutation vectors at the final PR head.
- **PHX-CORE:** publish the authenticated register/poll and event receipt/disposition contracts before any future re-enable or pending-event disposition.
- **PHX-MASTER:** reconcile this active-branch child with #340 and the #239/#254/#283 stack; do not merge automatically.
