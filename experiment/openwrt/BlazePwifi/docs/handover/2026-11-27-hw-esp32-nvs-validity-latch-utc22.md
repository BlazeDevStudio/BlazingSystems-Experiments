# PHX-HARDWARE UTC22 — ESP32 Preferences interrupted-save validity latch

**Observed UTC:** 2026-11-26T22:50Z  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/hw-poll-preflight-lab-modules-20261127-utc18  
**Parent PR:** [#354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354), fc842342596786e072630179acfbbc4feeb2ba02  
**Current PR:** [#355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355), OPEN / DRAFT / UNMERGED  
**Firmware logic commit:** cadf8605ba8cfc9ed64fb0ff96dba34c3d739105  
**Test-harness mutation correction:** 909bbf9699f156f9687d7deb49e4aa79fe1c099f  
**Exact focused source/test SHA:** ba24c44144a6b367c12b716944d1957f20003b3f  
**Pre-documentation branch HEAD:** ba24c44144a6b367c12b716944d1957f20003b3f

## Proven defect

ESP32 saveConfig() writes configuration through 13 independent Preferences keys. Earlier code checked each return value and returned failure if any write failed, but a failed save could still leave earlier keys persisted. On the next boot, loadConfig() read the mixed set without knowing the prior save had been interrupted. The in-memory HTTP 500/deny response did not protect the next boot from consuming partial configuration.

## Hardware-owned correction

- Added cfgvalid as a fail-closed write-sequence marker.
- saveConfig() sets configStoreValid=false, retries Preferences.begin() if setup recovery needs it, and persists cfgvalid=false before changing any configuration key.
- It checks all **14** configuration writes (the previous 13 plus the setup AP password), attempts every field write, and only writes cfgvalid=true after all field writes succeed.
- Failure to invalidate the old marker, any field write failure, or failure to publish the final true marker returns false. The setup handler keeps outputs denied, returns HTTP 500, and does not reboot.
- loadConfig() checks Preferences.begin() and the explicit marker before reading any configuration fields. If begin fails or an existing marker is false, it discards partial values, uses documented default setup configuration plus a fresh temporary AP password, leaves configStoreValid=false, and returns.
- A **missing** marker remains accepted as a pre-latch legacy store for compatibility. New saves introduce the marker.
- connectSta() and the main loop refuse station connection/reconnect/controller polling while configStoreValid is false. The setup portal continues to handle configuration recovery.
- ESP8266 EEPROM behavior was not changed by this task.

## Exact-source evidence

- Expected test-first RED: [#45906591317](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45906591317), job 140204687313, exact test-only head 669167c17a15c17435b61551df0bb82cc735a5b9. It failed because the old ESP32 sketch had no configuration-validity state; the unsafe baseline was rejected before the firmware correction.
- Focused GREEN: [#45907063693](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45907063693), job 140206222638, exact checkout ba24c44144a6b367c12b716944d1957f20003b3f: **PASS**.
- Focused log markers:
  - ESP8266_EEPROM_COMMIT_FAILURE_PROPAGATED_PASS
  - ESP32_INVALID_CONFIG_MARKER_DEFAULTS_PASS
  - ESP32_LEGACY_CONFIG_WITHOUT_MARKER_COMPAT_PASS
  - ESP32_PREFERENCES_BEGIN_FAILURE_RETRY_PASS
  - ESP32_CONFIG_VALIDITY_LATCH_FAILURE_MATRIX_PASS fields=14 marker_failures=2
  - Seven unsafe mutations rejected, including invalid-marker bypass, unguarded network connection, and removal of the main-loop invalid-config return.
  - CONFIG_PERSISTENCE_WRITE_RESULT_PASS ESP8266+ESP32
- Mbed TLS matrix [#45907063709](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45907063709): source-contract job 140206339633, core 3.3.13 job 140206339513, and core 4.0.0 job 140206339110 all PASS (3/3) at source/test SHA ba24c441.
- Full [#45907350862](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45907350862) at docs HEAD 9956befb: CI-0701 job 140207225999 PASS; mandatory handover freshness passed; all 14/14 target/platform build jobs passed; validation job 140207288314 FAIL at QA-owned tests/controllers.sh:21 (config_revision). Production import, simulations, update bundle, signing and publication were skipped. This final evidence refresh is documentation-only; source/test SHA remains ba24c441.
- Native synthetic [#45907063717](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45907063717), job 140206229703, FAIL at QA-owned PAY-0745 active clearPending(true/false) assertion. No pending-disposition callsite was added.

## Limitations and safety boundaries

- This is a **software validity latch**, not an atomic multi-key NVS transaction, rollback journal, protected signer, or proof of NVS single-key power-loss behavior.
- The host fake-Preferences harness is SIMULATED / CI VERIFIED only. Real NVS power-cut behavior is NOT TESTED.
- On an explicit invalid marker, custom pin/polarity values are discarded and stock defaults are used for setup recovery. This is a deliberate refusal to consume partial state, but physical OFF behavior with custom wiring remains unverified. Verify the board's external fail-safe bias and stock pin/polarity assumptions before any noncustomer hardware trial.
- The temporary setup AP password is not persisted while the configuration marker is invalid. A successful save persists it as part of the 14-field sequence.
- No coin, finance, relay, replay, witness, or downgrade admission was enabled. No physical flash, reset, live money, migration, deployment, merge, force-push, signing, or release tag occurred.

## Cross-role blockers

- PHX-QA still owns the inherited config_revision and PAY-0745 pending-disposition assertions.
- PHX-CORE still owns the authenticated register/poll receipt and pending-disposition contract.
- PHX-MASTER owns the global assignment/integration matrix and release gate.
- Active v0.6 P0 #177 synchronous poll-before-sample pulse loss remains unresolved.
- Cleanup-first #266 remains OPEN / 0-of-7; financial #31/#32, safety #34, and witness #43 remain open.

**Next exact action:** finish the exact-head Mbed/Full target results; rerun Full after this handover freshness sync; obtain QA/CORE reconciliation before any shared receipt, poll, or pending-disposition behavior changes.
