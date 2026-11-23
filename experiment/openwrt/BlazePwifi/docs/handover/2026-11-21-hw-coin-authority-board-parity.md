# PHX-HARDWARE handover — shared coin-authority board parity

**Date:** 2026-11-21 (UTC03)  
**Role:** PHX-HARDWARE  
**Task:** #266 / #327 — shared ESP8266/ESP32 coin-authority parity  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `c5cb17bfa35ea24615f53097b936c49ebe5f0104`  
**PR HEAD before this handover:** `c5cb17bfa35ea24615f53097b936c49ebe5f0104`

## Selected task and reason

The Hardware-owned poll-loop lab enforced normalized parity for 11 shared ESP8266/ESP32 poll and ingress helpers, but omitted six equally shared functions that control whether an untrusted poll response can enable intake, whether a coin POST is authorized, and whether a pending event may be marked attempted or deleted. The current implementations were byte-equivalent after whitespace normalization, so this was a coverage/maintainability gap rather than a confirmed runtime divergence.

## Change

Only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py` changed in the source/test commit.

The parity contract now covers 17 normalized shared helpers, including:

- `acceptPollResponse`
- `coinPostDispositionVerified`
- `canAttemptCoinPost`
- `markPendingPostAttempt`
- `pendingAttemptMarkerMatches`
- `clearPending`

The existing 11 poll/ISR/output/fault helpers remain covered. Six ESP32-only fail-open mutations are now injected and must be detected by the parity guard: positive poll acceptance, positive coin disposition, removal of the known-polarity POST gate, bypass of the one-shot marker, unconditional attempt identity match, and bypass of the pending-clear marker check.

No production `.ino`, API, wire format, persistence schema, accounting, witness, QA-owned assertion, release workflow, or other role's source was changed.

## Test-first evidence

**RED — expected missing-coverage failure**

- Test-only commit: `5398f1640ebcc9ec17343eca5d88ac62b93bc0f6`
- Quarantine push: [run 44863040495](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863040495)
- Job: `136720479742`
- Result: expected FAIL at `POLL_COIN_AUTHORITY_PARITY_REQUIRED_HELPERS_MISSING`, listing all six absent helpers. Existing poll, journal, coin-post and pulse labs ran before the guard and passed.

**GREEN — exact source/test SHA**

- Source/test commit: `c5cb17bfa35ea24615f53097b936c49ebe5f0104`
- Quarantine push: [run 44863161774](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863161774), job `136720861460` — PASS.
- Quarantine PR: [run 44863167396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863167396), job `136720877805` — PASS.
- Relay/output PR: [run 44863167432](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863167432), jobs `136720878016` and `136720878227` — PASS.

Exact logs report `POLL_SAFETY_BOARD_PARITY_PASS 17/17`, the existing `applyOutputs` journal-fault mutation rejected, and all six new ESP32-only coin-authority mutations rejected. The exact-head suites also retain the existing ESP8266/ESP32 pulse, journal, pending-clear, coin POST, poll-response and boot-polarity regression passes.

**Full validation remains failed, not passed**

- Full push: [run 44863161803](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863161803), validation job `136720934109` — FAIL.
- Full PR: [run 44863167502](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44863167502), validation job `136720950171` — FAIL.
- Both fail in `experiment/openwrt/BlazePwifi/tests/controllers.sh` at the inherited `Missing poll signature check`. This is QA/CORE contract coordination, not a Hardware test failure. The exact source/test change did not modify that assertion.
- Both Full runs completed 14/14 firmware-target plus Android jobs successfully; validation failed and downstream simulation/update/signing/candidate/publication gates were skipped.

## Parallel draft audit — read-only

- #239 branch HEAD: `d83b715b116185107737fef721c2eece8feebf39`; remains separate Phase-A deny draft.
- #254 branch HEAD: `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; the older cleanup commit `3692ddf889470da8a002e9a16bf0ac2f37f1a9d0` is not the live head. Focused run [44683629378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629378) passed. Full [44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) failed ESP32 compilation under `esp32:esp32@4.0.0` because `mbedtls/sha256.h` is unavailable; the validation job also failed the mandatory handover-freshness gate. No adapter was copied or applied.
- #283 branch HEAD: `830c355376380f9b5533d5cda2558beed41a593a`. Both sketches guard failed `appendQuarantineRecord()` before `clearPending()`, but `quarantinePending()` has no callsite beyond its definition; this is not end-to-end acceptance. Current main `cgi-bin/vendo` blob `2e3a1430d08cc6606429a042df3b5848f53c7267` has register/poll branches without controller `response_sig`; other member endpoints do emit signatures. The approved controller response/receipt contract remains absent.
- #322/#323/#326/#327 live branch refs at revalidation: `50d93e0d...`, `988904e8...`, `58c558fb...`, and the current Hardware branch above. The #327 → #326 base relationship is unchanged.

## Coordination and blockers

- Master PR #288 branch HEAD: `8517d6850589bb213ca1bb2b65882381ff9307ad`. Its `ROLE_ASSIGNMENTS.md` still pins #327 to `b6304208...`, #323 to `1761bf38...`, and #254 to `bea6f44e...`, which do not match live branch refs. Hardware did not edit `coordination/phoenix/`; Master must reconcile the active-head index and #172.
- #177 currently labels its body `PHX-L-VERIFY`, while Master `ROLE_ASSIGNMENTS.md` assigns #177 to PHX-HARDWARE. This ownership conflict is not silently resolved by Hardware; Master must reconcile it. No #177 body or other-role task content was edited.
- The private Drive registry v11 was not available through the connected tools in this activation. No Google Drive connector was exposed and Library search did not surface the v11 file; an older registry snapshot was not substituted.
- CoinOperatedEcosystem main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE PR #26 remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`. No migration or promotion was attempted.

## Evidence boundary and next action

**SIMULATED / CI VERIFIED only.** No physical coin acceptor, relay, electrical pulse, flash/power-cut, 150-cycle power-cut, 30-device/24-hour soak, protected witness, financial migration, durable accounting/replay, or customer-money test was performed. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.

Next:
1. PHX-MASTER reconciles #177 ownership and refreshes #172 / `ROLE_ASSIGNMENTS.md` / `INTEGRATION_MATRIX.md` to live branch refs without changing stack ancestry.
2. PHX-CORE publishes the canonical authenticated register/poll and event-bound coin receipt contract with golden vectors.
3. PHX-QA aligns the positive poll-signature assertion only after that contract is approved, preserving default-deny tests.
4. PHX-HARDWARE revalidates the live stack and selects the next unblocked firmware-owned task.

PR #327 remains OPEN / DRAFT / UNMERGED. No merge, rebase, force-push, physical flash, production migration, signer provisioning, release tag, deployment or cutover is authorized.
