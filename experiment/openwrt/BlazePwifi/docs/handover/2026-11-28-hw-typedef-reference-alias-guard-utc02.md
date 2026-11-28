# CURRENT STATUS — 2026-11-28T02:58:00Z — named reference-type alias guard CI verified; Full QA parity blocked

## PHX-HARDWARE UTC02 — PR #369 exact-head terminal evidence

**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments` (owner verified as BlazeDevStudio)  
**Main HEAD:** `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`  
**Parent PR #368:** OPEN / DRAFT / UNMERGED at `9885c81d934922fe35777d5c8f7245766b622255`  
**PR #369 branch:** `phoenix/hw-deny-latch-type-alias-20261128-utc02`  
**Exact source/test head verified:** `c3648fbb1ce7dbd905a061be0aaa81dcb18b511e`  
**Source/test commit:** `5e3c802ce9ccf21c621fd99807604eb3baf56b27`  
**PR #369:** OPEN / DRAFT / UNMERGED, stacked on #368.

### Proven source-contract defect and fix

The previous bounded deny-latch scan did not recognize named C++ reference-type aliases bound to protected fields, e.g. `using CoinRef = bool&; CoinRef alias = coinEnabled;` or `typedef bool& RelayRef; RelayRef alias = relayEnabled;`.

Added `_reject_named_reference_type_aliases()` to recognize direct `using` / `typedef` reference aliases and simple alias chains. Added three negative mutations per board (using, typedef, chained using) and an unrelated-local-reference positive control. The alias matrix is now 17/17 rejected per board.

No production ESP8266/ESP32 `.ino`, shared controller API, QA assertion, CORE finance/receipt/disposition, signer, witness, migration, release or COE source changed. This is a bounded source scan, not a full C++ AST/dataflow or memory-safety proof.

### Exact source/test-head CI — all at `c3648fbb`

- Focused [#46100115505](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46100115505), job `140840406605`: **PASS**. ESP8266 and ESP32 each reject 17/17 named/reference alias mutations; 7/7 direct and 4/4 cast mutations reject; logical-AND and unrelated-local alias positive controls pass. Append-only ledger guard passes: base 1,132,798 bytes, 81,028 bytes appended.
- Mbed [#46100115477](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46100115477): **3/3 PASS** — source contract job `140840461486`, ESP32 core 3.3.13 job `140840461623`, core 4.0.0 job `140840461652`.
- Full [#46100115480](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46100115480): **TERMINAL FAILURE** at validation job `140840509447`. CI-0701 and mandatory handover freshness pass. The inherited QA-owned `tests/controllers.sh:21` still requires `config_revision` in both deny-only candidate sketches. All 14/14 target/platform builds, including Android, passed. Validation-dependent v04 simulations, update bundle, signing and release/publication stages were skipped. This is not a firmware compile failure.

### Final documentation and ledger state

Canonical PROJECT_HANDOVER, CURRENT_STATE, narrow Hardware handover and CHANGE_LEDGER were refreshed after exact-head testing. The original ledger blob was recovered and its full historical prefix preserved before append; subsequent entries are append-only. A prior handover note incorrectly labelled the first ledger checkpoint as the final append commit; that label is removed here. The exact source/test SHA remains `c3648fbb`; later commits in this branch are documentation/provenance-only and trigger a fresh CI pass.

### Cross-role blockers

- **PHX-QA:** replace the literal `config_revision` presence assertion with source-linked deny-only controller vectors; do not add a decoy field or weaken the deny default.
- **PHX-CORE:** publish the authenticated register/poll/receipt/disposition contract before any positive coin or relay admission is considered.
- **PHX-MASTER:** current PR #288 head is `7830c67076cc842d2a66f76af987769ee5d243f8`; UTC02 matrices include #368 but not #369. Register #369 at its latest exact head and preserve #367 → #368 → #369 ancestry. Hardware did not edit Master-owned paths.
- P0 [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) remains OPEN; active v0.6 poll-before-first-sample hazard is not fixed by this source-contract guard.
- Protected PRs #239, #254 and #283 remain OPEN / DRAFT / UNMERGED and untouched.
- Cleanup [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN / 0-of-7. Finance #31/#32, safety #34 and witness #43 remain OPEN.

### Provenance and production status

Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains NOT RECOVERED. Library search surfaced only older v3-v7 registry snapshots and a checkpoint that merely references v11. No Google Drive connector is available in this runtime; no older registry was substituted.

Physical GPIO/relay, LittleFS power-loss, 150 controlled power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release signoff remain NOT ACCEPTED. Coin/relay admission stays deny-only.

**Status:** Focused CI VERIFIED; Mbed matrix CI VERIFIED; Full target builds CI VERIFIED 14/14 at source/test head `c3648fbb`, but Full integration BLOCKED by QA-owned controller assertion. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

**Next exact action:** QA fixes `tests/controllers.sh:21` under its ownership; Master records #369; then rerun Full at the refreshed exact head. Do not merge, flash, migrate, sign, release or deploy.
