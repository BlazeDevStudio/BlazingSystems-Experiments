# PHX-HARDWARE — ESP8266 strap-pin guard and shared revision-fixture reconciliation

**Date:** 2026-11-27 UTC09  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#358](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/358) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-esp8266-strap-pin-guard-20261127-utc08`  
**Parent:** PR #353 at `f527b33c9e391a9a66490388d96f06d6c8761dfa`  
**Source implementation commit:** `617d5673b4852750e59d0c7cdb90aa7823dcf6ad`  
**Source/test head before this handover:** `af3ed03db1c07a950ad27adc3e18f27a1afc1ec6`

## Scope and ownership

This is a bounded ESP8266 Hardware task on the existing #358 child branch. The production guard was already added in commit `617d5673`; this activation corrected a Hardware-owned host-test fixture that still used the newly prohibited ESP8266 ROM strap pins as its positive test tuple. No CORE/QA/Master-owned source, shared API, finance, migration, signer, witness, or COE files were changed.

## Proven defect and correction

The ESP8266 `runtimePinsSafe()` guard rejects GPIO0, GPIO2, and GPIO15 for coin, relay, and LED roles because those pins are sampled by the ROM at reset. The shared `remote_config_revision_lab.py` still used the tuple GPIO2/14/15 in its stale, equal, zero-initial, newer-revision, and unknown-polarity fixtures. The newer-revision positive case therefore failed with exit 13 after the correct safety guard was added.

The shared fixture now uses GPIO4/13/14, a tuple accepted by the current ESP8266 and ESP32 validators. Expected runtime pin identities and pin-mode assertions were updated accordingly. The test still covers stale/equal/zero revision denial, a valid strictly newer revision, and unknown-polarity output denial. The ESP8266-specific boot-polarity lab separately tests all nine GPIO0/GPIO2/GPIO15 role combinations and removes the guard in memory to prove the mutation is rejected.

**This activation changed only** `esp8266/BlazePwifiVendo/remote_config_revision_lab.py`. It did not change the firmware behavior introduced by `617d5673`.

## Exact-head CI evidence — source/test SHA `af3ed03db1c07a950ad27adc3e18f27a1afc1ec6`

- Relay Output Polarity LAB [run #45975867767](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45975867767), job `140427309661`: **PASS**. ESP8266 strap policy reports 10/10; guard-removal mutation rejected. Shared remote-config revision lab reports 5/5 on both ESP8266 and ESP32. Existing poll/JSON/UTF-8 and bounded-response source labs pass. Log explicitly reports `SIMULATED_ONLY=1`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.
- Quarantine Byte Readback LAB [run #45975867690](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45975867690), job `140427309756`: **PASS**. Exact-source quarantine/readback, EEPROM recovery, pulse-capture, JSON/UTF-8, cold-boot polarity, strap-policy 10/10 and mutation checks pass. Log reports `SIMULATED_ONLY=1` and `PHYSICAL_POWER_CUT_VERIFIED=0`.
- Full [run #45975867669](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45975867669): **FAIL** only at validation job `140427311339`, `Controller protocol parity`, with `Missing poll signature check` in the ESP8266 sketch. All 14 firmware target/platform jobs and Android passed. Production import, signing, publication, update-bundle, candidate and simulation stages were skipped. This inherited authenticated poll-contract blocker is not owned by this GPIO fixture change.
- An earlier push Full [run #45975860516](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45975860516) also failed the same validation assertion; all target jobs and Android passed.

## Boundaries and remaining blockers

- ESP32 source was not changed; no ESP32 strapping policy was inferred from this ESP8266 finding.
- No authenticated register/poll/receipt/disposition contract was invented. Current controller responses remain deny-only.
- No pending records were cleared, no coin admission was enabled, and no relay actuation path was added.
- No physical boot, coin-slot, relay, electrical pulse, brownout, LittleFS power-cut, or soak test was performed.
- PR #358 remains stacked on #353 → #352 → #349; no retarget, rebase, force-push, merge, or release was performed.
- This branch does not contain `docs/handover/CURRENT_STATE.md` or `docs/handover/CHANGE_LEDGER.md`; no substitute ledger was created. The canonical `PROJECT_HANDOVER.md` and this narrow handover are the branch-local records.

## Next exact action

PHX-QA should independently review the exact-source strap matrix and shared revision-fixture change. PHX-MASTER should add PR #358 and its parent chain to the current role/integration matrix. PHX-CORE must publish the authenticated register/poll and receipt/disposition contract before Hardware changes positive poll handling or pending disposition. Keep coin and relay admission deny-only.

**Classification:** SIMULATED / CI VERIFIED for source-extracted tests and target builds; physical acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
