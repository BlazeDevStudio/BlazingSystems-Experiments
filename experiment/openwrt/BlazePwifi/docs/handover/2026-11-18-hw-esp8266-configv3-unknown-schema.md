# PHX-HARDWARE handover — ESP8266 ConfigV3 unknown-schema preservation

**Task:** #177 / PR #323 — instrument and correct the ESP8266 ConfigV3 boot-latch failure  
**Role:** PHX-HARDWARE  
**Branch:** `phoenix/hardware-poll-fault-dual-store-20261118`  
**Parent:** PR #322 at `50d93e0de3d682550b6f02fb43484e76ad9c7e08`  
**Current code/test commit:** `e1c9016e6fac0fbfcd9c92dfd27ba129f8219d2a`  
**Current PR head before this handover:** `359bd8f685a2a464f4a77b84501fcf4055944d5c`

## Confirmed root cause

Master's UTC15 audit correctly requested instrumentation because the prior generic `journalRecoveryRequired` assertion did not identify which scenario failed. The generated C++ line map and new fake-EEPROM/source-function trace showed that the ordinary injected commit-failure path was already correct; the failing assertion was the preceding unknown/future-schema case.

At test-only commit `d4e9abd5bb313dac8f53a6e5857281e6906d8f67`, the harness proved:

- `EEPROM.failCommit=true` reaches `EEPROM.commit()` exactly once.
- The fake commit returns false.
- Extracted `saveCfg()` propagates the failed commit.
- The extracted production `latchConfigPersistenceFailure()` body runs once.
- `journalRecoveryRequired` remains true.

The same test then failed with `TRACE_FAIL: unrecognized EEPROM schema must not call commit`. The prior diagnosis that the commit-failure latch itself was missing was therefore not supported by the trace.

## Source correction

At `e1c9016e6fac0fbfcd9c92dfd27ba129f8219d2a`:

- Added `configRecordErased(const Config &)`, which accepts first-boot defaults only when the entire Config-sized EEPROM record is erased (`0xFF`).
- After valid ConfigV3, ConfigV2 and ConfigV1 paths, `loadCfg()` now rejects any non-erased unknown/corrupt record through `latchConfigPersistenceFailure()`.
- The failure path returns before `defaults()`, `EEPROM.put()` or `EEPROM.commit()`.
- Unknown future-schema bytes are preserved; unreadable fake-EEPROM data is not treated as blank storage.
- Valid V1/V2 migration paths and genuinely erased first-boot initialization remain separate.

This is a local config-schema downgrade/preservation guard. It is **not** the independent anti-rollback witness required for production.

## Test-first and exact-head evidence

| Evidence | Result | Meaning |
|---|---|---|
| [RED run #44346145812](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44346145812), job `134948939624` | Expected failure | Commit-failure trace passed; unknown-schema rewrite assertion failed before the source fix |
| [Focused run #44346860798](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44346860798), job `134951465465` | SUCCESS | ESP8266 boot-polarity lab, commit-failure trace, unknown-schema preservation, poll-fault, poll-window and deny-only response regressions |
| Same run, job `134951464980` | SUCCESS | ESP32 local-polarity boot gate and unknown/legacy INPUT-only checks |
| [Quarantine run #44346860795](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44346860795), job `134951465403` | SUCCESS | Quarantine byte-readback lab |
| [Full run #44346860829](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44346860829), validation job `134951658251` | FAILURE | Inherited QA assertion `Missing poll signature check`; firmware default-deny was not weakened |

The first post-fix focused run also exposed a separate stale mutation in `output_enable_sequence_lab.py`: it assumed both boards used two identical `!outputPolarityKnown ||` guards. The ESP32 uses one early INPUT-only block. Commit `359bd8f685a2a464f4a77b84501fcf4055944d5c` updates that test mutation to remove the actual board-specific guard; the final focused relay workflow then passed for both boards.

The full workflow [#44346860829](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44346860829) completed with overall conclusion **CANCELLED** after validation failed. Completed target jobs: ESP8266, ESP32, x86_64, Ruijie? No — the Ruijie target job was cancelled; Orange Pi PC, PC2, One, Zero3, and optional PC+, Zero, Zero2, Zero2W and One+ jobs passed. Android was cancelled. Validation failed at the inherited `Missing poll signature check`; update bundle, browser/ESP simulations, release publishing, signing handoff and candidate gate were skipped/cancelled. The target matrix is therefore partial and the full workflow is not accepted.

## Exact blobs

- ESP8266 firmware: `312884c534637a3179180b432b9e345b36dc6af9`
- ESP8266 boot lab: `db0ac51115638d567d73e0dbfdff1129ef5efd3d`
- Board-specific output-enable mutation lab: `37363690c8a092331487b46bd1b4d1e02e3ab2f7`

## Safety and disposition

- PR #323 remains OPEN / DRAFT / UNMERGED; no force-push or merge.
- ESP32 parity evidence remains host-simulated only.
- Physical relay polarity, GPIO electrical behavior, coin ingress, power cuts and device soak: NOT TESTED.
- No positive poll/coin admission, live finance, signer provisioning, production migration, flashing or deployment.
- Production remains NO-GO.

## Next exact action

PHX-QA must replace the inherited positive poll-signature assertion with negative deny-behavior tests after CORE publishes the canonical authenticated response contract. PHX-MASTER must independently review the ConfigV3 preservation change and keep #323 candidate-only until the canonical stack and release gates are reconciled.
