# PHX-HARDWARE — ISR modulo-increment mutation fixture alignment

**Date:** 2026-11-25  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** [#352](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/352) — OPEN / DRAFT / UNMERGED  
**Parent:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED  
**Working branch:** `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`  
**Parent #349 HEAD:** `2a5c997add4f49fcd74f753101d3a9daac0040bf`  
**Current source/test HEAD before this handover:** `e28c0e462a63497c003019e93a8b0820b9003997`  
**Firmware source change:** `ec9547f8e97b815db705d5aa65382f171b5eade9`

## One defect corrected

The prior Hardware source cleanup replaced deprecated volatile-qualified `coinEdgeSequence++` with explicit unsigned modulo-`2^32` assignment:

`coinEdgeSequence = coinEdgeSequence + 1U;`

The source-extracted poll failure-injection suite still tried to inject the no-op ISR mutation by replacing the old `coinEdgeSequence++;` text. It therefore failed before testing the mutation:

- Quarantine [#45614479720](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45614479720), job `139206216249`: failed with `AssertionError: ESP8266: ISR mutation did not apply`.
- Relay [#45614479717](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45614479717), job `139206216599`: same stale mutation anchor.
- ESP8266 exact-core [#45614479608](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45614479608), job `139206216679`: stopped in the poll lab before compilation.

This was a test-harness/source-anchor mismatch, not evidence of a runtime ISR regression.

Commit [`e28c0e46`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/e28c0e462a63497c003019e93a8b0820b9003997) updates only:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_failclosed_mutation_contracts.py`

The no-op mutation now changes the exact modulo increment to an explicit zero increment. The existing guard still fails if the mutation anchor is absent. No firmware runtime, API, coin, relay, financial, signer, witness or migration behavior changed in this commit.

## Exact-head CI evidence

All following runs checked out the current PR head `e28c0e462a63497c003019e93a8b0820b9003997`.

| Workflow | Run / job | Result |
|---|---|---|
| Quarantine Byte Readback LAB | [#45622354594](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622354594), job `139233546828` | **PASS** |
| Relay Output Polarity LAB | [#45622354655](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622354655), jobs `139233546730`, `139233547452` | **PASS** |
| ESP8266 core 3.1.2 | [#45622354831](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622354831), job `139233547588` | **PASS** |
| ESP32 core 3.3.13 / 4.0.0 | [#45622354607](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622354607), jobs `139233546476`, `139233547154` | **PASS / PASS** |

The no-op ISR mutation was rejected with expected exit 12 on **both ESP8266 and ESP32** in Quarantine, Relay and the exact-source ESP8266 core workflow. The poll lab also retained edge-snapshot race and active-high/active-low multi-edge rollover checks. Coin pulse capture reported 18/18 for each board in the Quarantine workflow.

### Exact sketch image identities

| Target | Sketch image | Bytes | SHA-256 |
|---|---|---:|---|
| ESP8266 core 3.1.2 | `BlazePwifiVendo.ino.bin` | 363,728 | `cad045f77cbc9b1384d6bf10b40b10236080037c1ab015bb6a07188e59e475d5` |
| ESP32 core 3.3.13 | `BlazePwifiVendo32.ino.bin` | 1,045,808 | `b33d3ca000ddbfe55f5542a53cecd87b9e3b29014db4569bf471adcb3293a628` |
| ESP32 core 4.0.0 | `BlazePwifiVendo32.ino.bin` | 1,100,016 | `c51ff31254861a73d357e1e3e104eee3b1f2ee1ab607b12d188918e20286f9ad` |

All three workflows explicitly report `SIMULATED_ONLY=1` and `PHYSICAL_ACCEPTANCE=0`. ESP8266 compilation still emits the existing `ICACHE_RAM_ATTR` deprecation warning; it is non-fatal and is not changed here.

## Full integration remains blocked

Exact-head Full build [#45622354830](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622354830), validation job `139233548655`, **FAILS** at Controller protocol parity:

`Missing poll signature check in .../esp8266/BlazePwifiVendo.ino`

At the recorded check, ESP8266 job `139233548087`, ESP32 job `139233548507`, and optional Orange Pi One Plus job `139233548741` passed; other target jobs were still queued/in progress. No 14/14 broad target-matrix pass is claimed from this run. Candidate, signing and publication stages remain skipped.

Current main CGI producer blob `2e3a1430d08cc6606429a042df3b5848f53c7267` still has no approved `response_sig` in `register|ping` or `poll`. Signatures used by member endpoints are not interchangeable. CORE owns the producer contract and canonical vectors; QA owns independent assertion reconciliation. Hardware retains deny-default and does not invent a signature.

## Revalidated stacks and related gates

- #239: OPEN / DRAFT, head `d83b715b116185107737fef721c2eece8feebf39`.
- #254: OPEN / DRAFT, head `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, still stacked on #239. Its focused header run #44683629378 passed; Full #44683629491 failed on the ESP32 Mbed TLS header and handover-freshness gates. The source cleanup `3692ddf889470da8a002e9a16bf0ac2f37f1a9d0` remains unchanged.
- #283: OPEN / DRAFT, head `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`, base main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. Both `quarantinePending()` helpers return false on append failure and reach `clearPending()` only after successful append, but each is definition-only with no active callsite. Main register/poll still lacks the approved response signature. This is source audit, not physical LittleFS acceptance.
- #349: OPEN / DRAFT, head `2a5c997add4f49fcd74f753101d3a9daac0040bf`.
- Experiments main: `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`; development branch `blazepwifi-v0.5.3-development` at `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- CoinOperatedEcosystem main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`; PR #26 remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`. No destination write or source promotion occurred.
- Cleanup-first #266 remains OPEN; this narrow Hardware correction does not complete the seven-role cleanup gate.
- Canonical private Google Drive registry v11 was not available through the connected tools/Library in this activation; no older registry snapshot was substituted.

## Evidence classification and next exact actions

- Source/test harness: **CI VERIFIED**.
- Arduino target builds: **CI VERIFIED** on the exact PR head.
- Poll/quarantine/relay fault injection: **SIMULATED / CI VERIFIED**.
- Physical coin pulse, relay load, electrical recovery, LittleFS/EEPROM power-loss, 150 power cuts and 30-device/24-hour soak: **NOT TESTED**.
- Hardware acceptance: **NO**.
- Production readiness: **NO-GO**.

Next:
1. PHX-MASTER refreshes the current #352 exact head and stack ancestry in its owner matrix; do not retarget or merge.
2. PHX-CORE publishes the authenticated register/poll response contract and canonical vectors.
3. PHX-QA independently reconciles the Full validation assertion without weakening deny-default.
4. PHX-HARDWARE keeps #352 DRAFT and revalidates all live heads before the next owned change.

No local hardware, live money, signing, migration, flashing, reset, release tag, deployment or merge was performed.
