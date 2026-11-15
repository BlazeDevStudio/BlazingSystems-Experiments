# PHX-MASTER migration gate — invalid pending temporary journal cleanup

Date: 2026-11-15 UTC13  
Role: PHX-MASTER; coordination-only, review-only  
Source: [HARDWARE draft #304](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/304) at `d5af6f7b18fcc8043f0dcbbb05482bb630d438aa`, stacked on #303 at `1689e215e36f377ddc98c66abdee3d3dffec438f`.  
Proposed destination: [COE draft #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) at `b382d233ff06c8791b1028bed3c617cc7b670d12` (unchanged).  
Status: **REVIEW REQUIRED / PRODUCTION NO-GO**.

## Source inspection, not execution

The #304 diff replaces unchecked `LittleFS.remove("/pending.new")` after short writes or invalid readback with `removePendingCandidate("/pending.new")`, setting `journalRecoveryRequired` when cleanup cannot be proven. Both ESP32 and ESP8266 sketches are changed; the fake-LittleFS ASan/UBSan test gains two cases per board (11 to 13), asserting no primary promotion, preserved invalid temporary candidate and recovery-required on removal failure. The source-owner handover states that the active caller already denied filesystem/relay admission on save failure; this change closes a recovery-state evidence gap rather than establishing end-to-end finance correctness.

At this SHA, two GitHub Actions records report completed/success: [focused lab 43715312676](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43715312676) and [build 43715312695](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43715312695). MASTER did not independently execute those tests or physical hardware. No exact-head Master PR workflow run was returned at `884b8c206afa29d59a53fac3f01b70f2734d34c4`. COE #26's associated workflows returned queued, not completed success.

## Mandatory migration parity and QA matrix

Before any selective copy, record each exact source/destination firmware blob SHA and mode, licenses, imports/dependency closure, storage format, boot-time candidate precedence and corresponding test-file blob identity. Inspect destination code for stronger existing behavior. Do not recursively copy `Rental/`: ownership manifest explicitly blocks its parent-prefix overlap.

Independent PHX-HARDWARE and PHX-QA must exercise, separately for ESP32 and ESP8266: (1) short write plus failed temporary removal, (2) failed readback plus failed removal, (3) cleanup success, (4) old primary plus surviving invalid temporary candidate, (5) reboot/recovery with candidate conflicts, (6) fault injection in open/flush/close/remove/rename/rollback. Assert no unverified ACK, no relay/coin credit, no silent pending evidence loss, and explicit recovery/quarantine on ambiguity. Validate signed event ACK and ledger idempotency with PHX-CORE through the existing control plane, without taking over CORE code.

The host fake-filesystem suite is simulated evidence only. Require independent real LittleFS brownout, electrical and native target acceptance, protected signing/anti-rollback witness, crash-atomic durable finance, reversible migration, 150 real power cuts and 30-device 24-hour soak with owner authorization. No source migration, merge, release, flash or live financial action is approved.

Private Drive v11 registry remains unlocated via connector name searches; do not infer contents or publish private identifiers. Next human action: QA independently inspect exact #304 and destination #26 file/test identities and run fault/reboot matrix; separately locate private registry via authorized owner Drive folder navigation.
