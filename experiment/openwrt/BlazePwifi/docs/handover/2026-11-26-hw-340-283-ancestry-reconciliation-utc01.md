# PHX-HARDWARE UTC01 — PR #340 / #283 ancestry reconciliation

**Date:** 2026-11-26  
**Role:** PHX-HARDWARE  
**Tasks:** #172 / #177 / #266 / #283 / #340  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR #340:** OPEN / DRAFT / UNMERGED  
**Child branch:** `phoenix/hardware-prepoll-intake-deny-20261122-utc01`  
**Parent PR #283 branch:** `cleanup/esp-firmware-hardening-and-quarantine-20261111`

## Reconciliation performed

Before this activation, #340 and its #283 parent had diverged from merge base `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`:

- Parent #283 head: `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30` (4 commits beyond the merge base).
- Child #340 head: `547148eeb4384df7971d17d762e3f12bc5dcab3c` (43 commits beyond and 4 behind the current parent).
- Parent-side tree delta was exactly two paths: the ESP32 quarantine append/readback lab and its narrow dormancy handover.

The parent lab is a strict superset of the child copy for this purpose: it retains the 13/13 append/readback and existing clear/commit failure-injection scenarios, and adds a source guard requiring `quarantinePending()` to remain definition-only plus an injected unapproved-callsite mutation that must be rejected on both boards.

A two-parent merge commit was created with the child as first parent and current parent as second parent:

- **Merge commit / source-test head:** `a32c02311e4837669124c5b4b54fb1dfceed94fc`
- First parent: `547148eeb4384df7971d17d762e3f12bc5dcab3c`
- Second parent: `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`
- Tree: `e170e946f9737dc5f71cd726d6c9b31c9e30d944`

The #340 branch ref was advanced with a non-force fast-forward update guarded by expected old SHA `547148e...`. No force-push, rebase, retarget, PR merge, or source overwrite was used.

Post-update comparison: **44 ahead / 0 behind**, merge base equals current #283 head `4dd0b01...`. The two parent-side paths now resolve to the exact parent blobs:

- `quarantine_append_readback_lab.py`: `90fd651934bda7ac1c15476731b70752ccdb19c8`
- `2026-11-22-hw-quarantine-pending-dormancy-guard.md`: `d6354b5073450b2fbe56afd47706d28d9f63f363`

## Exact-head CI evidence — `a32c02311e4837669124c5b4b54fb1dfceed94fc`

| Workflow | Run / job | Result |
|---|---|---|
| Quarantine append/readback + clear/commit + clear denial | [#45737591625](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737591625), job `139634465431` | PASS |
| Poll preflight intake inhibit | [#45737591455](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737591455), job `139634464765` | PASS |
| Mbed TLS provider / fail-closed guard | [#45737591573](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737591573), job `139634465148` | PASS |
| ESP8266 Arduino core 3.1.2 compile | [#45737591568](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737591568), job `139634465565` | PASS |
| ESP32 Arduino core 3.3.13 compile | [#45737591440](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737591440), job `139634465064` | PASS |

Focused log evidence:

- Quarantine append/readback: 13/13 per board.
- Pending-journal boot fail-closed: 14/14 per board.
- Unapproved `quarantinePending()` callsite mutation rejected on ESP32 and ESP8266.
- Clear/commit: 10/10 per board; ignored `clearPending()` result mutation rejected.
- Quarantine-clear endpoint: six repeated POST attempts denied per board; evidence file unchanged.
- Poll response-consumption and remote-config mutations rejected on both boards; logs explicitly report physical coin/relay acceptance = 0 and power-cut acceptance = 0.
- ESP8266 core 3.1.2 binary SHA-256: `e4af65d3070a061827f9c4c03470687bfe9aa4998c85f5f5a22764d6ec7d3e81`.
- ESP32 core 3.3.13 binary SHA-256: `bf395b61e038b382041286f966e16689bb421033d328ce4fe7b893adc81a982f`.

Full BlazePwifi push [#45737585073](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737585073) and PR [#45737591616](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737591616) were still in progress at handover creation. Their validation jobs passed, including Controller protocol parity, accounting integration x3 and persistence/replay stress x3; target/platform, Android and simulation matrices had not all reached terminal state. **No aggregate Full PASS is claimed.** The production signed-import job was skipped.

## Scope and safety

This reconciliation changed only the Hardware-owned host lab and added/retained Hardware handover evidence. No production `.ino`, CGI producer, CORE API/schema, financial backend, replay authority, signer/witness, updater, release workflow, or COE destination changed.

- `quarantinePending()` remains definition-only; no runtime callsite was introduced.
- Coin/relay admission remains deny-only.
- The active v0.6 audit-foundation branch remains separate and still has the known synchronous poll-before-coin-sample P0; this PR is not integrated into that active branch.
- CORE's authenticated register/poll/configuration and event-bound receipt/disposition contract remains required. No signature or key behavior was invented.

## Evidence classification

- Focused source-extracted tests: **CI VERIFIED / SIMULATED**.
- Pinned ESP8266 and ESP32 builds: **CI VERIFIED**.
- Full integration: **IN PROGRESS at handover creation; no aggregate result**.
- Physical coin pulse, relay/electrical recovery and LittleFS power-loss: **NOT TESTED**.
- 150 controlled power cuts and 30-device / 24-hour soak: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

## Next exact action

1. Read terminal results for Full runs #45737585073 and #45737591616 at exact SHA `a32c023...`; do not transfer results to a later docs SHA without revalidation.
2. PHX-MASTER records the reconciled #283 → #340 ancestry in the integration matrix; keep both PRs OPEN / DRAFT / UNMERGED.
3. PHX-CORE publishes the approved authenticated response/key-provisioning and event-bound disposition contract; PHX-QA independently verifies positive and negative vectors.
4. PHX-HARDWARE then revalidates #349 → #352 and #352 → #353 ancestry as the next separate task. Do not touch those branches in this activation.

No Codex, flash/reset, live-money operation, production migration, signer provisioning, tag, publication, PR merge, or deployment occurred.
