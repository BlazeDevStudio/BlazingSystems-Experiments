# PHX-HARDWARE UTC19 — Master canonical #380 pin and exact-head revalidation

**Updated:** 2026-11-28T19:36:48Z  
**Task:** `PHX-HW-177-HW380-MASTER-PIN-20261128T19Z`  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#380](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/380), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-gpio-writer-reconcile-20261128-utc17`  
**Parent:** #377 at `95ace1236c2b3e4816515c372edd4853ceeed064`  
**Pre-update branch HEAD:** `a4ec03835fb8ad3483d0447d105436f0f38071e3`  
**Source/test SHA:** `83fc27e474064f2ed429332b8a14fa8ffb66784c`

## Master decision and stack disposition

The live PHX-MASTER branch `phoenix/master-coordination` is `aa3d8a3214311fef8a3705e41b5e0aeac47e75f1`. Its current `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md` pin #380 as the canonical combined DRAFT child of current #377.

- #380 carries #378's post-deny GPIO escape regression and #379's centralized writer-authority contract.
- Preserve #378 and #379 OPEN/DRAFT/UNMERGED at their original heads; do not integrate them separately, retarget them, or rewrite them.
- #376 remains a separate storage-preflight line.
- Master owns the integration pin; Hardware does not edit Master-owned role assignments or matrix.

This supersedes the earlier #380 body wording that asked Master to decide whether #380 should be pinned.

## Exact-head CI revalidated on `a4ec03835fb8ad3483d0447d105436f0f38071e3`

- Poll Intake Deny [#46173865754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865754), job `141068074645`: **PASS**. The log confirms `GPIO_WRITE_AUTHORITY_MUTATIONS_REJECTED=8` (four mutations per board), the post-deny direct-GPIO re-enable mutation marker, and the broader 14/14 injected-regression result. Output explicitly identifies simulation-only evidence.
- ESP32 Mbed TLS [#46173865768](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865768): **3/3 PASS** — source-contract job `141068074872`, core 3.3.13 job `141068074661`, core 4.0.0 job `141068074935`. Logs retain `SIMULATED_ONLY=1`, `TARGET_BUILD_REQUIRED=1`, and `COIN_ADMISSION_ENABLED=0`.
- Full BlazePwifi [#46173865781](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865781): **FAIL** at QA-owned `experiment/openwrt/BlazePwifi/tests/controllers.sh:21`, the `config_revision` parity assertion. Both #377-based sketches lack the field. All 14/14 target/platform jobs completed successfully; update bundle, simulations, candidate, signing and publication were skipped.
- Native Synthetic Journal: **NOT RUN** for this PR because its path filters do not include the two Hardware host-lab Python files or this handover. The workflow has `workflow_dispatch`, but the available GitHub integration exposes no workflow-dispatch write action. No Native PASS is claimed.

These are exact-head CI results, not hardware acceptance. The Full failure remains a CORE/QA contract issue; Hardware did not add a decoy `config_revision` token or invent `response_sig`.

## Scope and ownership

The source/test SHA remains `83fc27e474064f2ed429332b8a14fa8ffb66784c`; only two Hardware-owned host-lab Python files changed in that source increment. No production sketch, CGI producer, CORE API, QA-owned test, finance, signer, witness, migration runtime or COE destination source changed.

- PHX-QA owns PAY-0745 semantics and controller-parity assertions in `tests/controllers.sh`.
- PHX-CORE owns the canonical authenticated register/poll/receipt/disposition envelope and golden vectors.
- PHX-MASTER owns role/integration pins.
- PHX-HARDWARE owns firmware, Hardware host labs, stack sequencing and Hardware handovers.

## P0 #177 and safety disposition

The active `blazepwifi-v0.6.0-audit-foundation` branch remains `2fbd2475e9f54878c316fa7cea2f228386b0e859`. Its ESP8266 sketch still executes synchronous `post("poll")` before the first coin sample (lines 354/357); ESP32 does the same (314/318). #380 is a candidate test/guard stack and is not integrated into active v0.6. P0 pulse-loss risk remains OPEN.

Keep coin, relay, finance, replay, witness and downgrade fail-closed. Do not change the active production sketches or add positive admission until CORE publishes the approved authenticated contract and QA independently verifies its semantic vectors, with Master sequencing confirmed.

Physical GPIO/relay polarity, coin-pulse retention, EEPROM/NVS brown-out, LittleFS torn-write recovery, 150 controlled power cuts, 30-device/24-hour soak and electrical pulse/recovery are **NOT TESTED**. Protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff are **NOT ACCEPTED**. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

No merge, force-push, flash, device reset, live money, production migration, key provisioning, signing, release tag or deployment occurred.

## Next exact actions

1. PHX-CORE publishes the versioned authenticated controller envelope and canonical golden vectors.
2. PHX-QA replaces/reconciles the current literal controller-parity check with independent semantic positive/negative tests without weakening deny-default.
3. PHX-MASTER keeps #380 as the canonical combined DRAFT child and refreshes any remaining integration references.
4. PHX-HARDWARE resumes the active v0.6 P0 intake-inhibit work only after the shared contract and integration order are explicit.


 
## PHX-HARDWARE UTC20 — alternate GPIO writer bypass guard

**Updated:** 2026-11-28T20:36Z  
**Task:** PHX-HW-177-GPIO-OUTPUT-API-AUTHORITY-20261128T20Z  
**PR:** [#380](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/380), OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hw-gpio-writer-reconcile-20261128-utc17  
**Base:** #377 at 95ace1236c2b3e4816515c372edd4853ceeed064  
**Source/test commit:** 0c09d8ed5927bac037f01a2649d0d332c5717a38  
**Prior intermediate commit:** c5a9f666ddb016ed6df43ed73756696b3db3c824 (corrected immediately; its regex/newline escaping is not the final implementation).

### Proven gap and correction

The previous writer-authority guard enforced one digitalWrite() implementation inside writeLogical(), but it did not reject alternate output APIs or direct output-register assignments. A future analogWrite, ESP32 LEDC/DAC, ESP-IDF GPIO-level call, tone/shiftOut, or direct GPIO register write could bypass that contract while the original digitalWrite count remained unchanged.

The source contract now explicitly rejects 11 alternate output APIs:
analogWrite, digitalWriteFast, ledcWrite, ledcWriteChannel, dacWrite, gpio_set_level, gpio_ll_set_level, gpio_hal_set_level, tone, noTone, and shiftOut.

It also rejects ESP8266 GPOS/GPOC and ESP32 GPIO.out* output-register assignments. The existing single digitalWrite() inside writeLogical(), six startup logical-OFF writes, four accepting-gated output writes, and polarity rules remain unchanged.

### Failure-injection coverage

The host source-contract lab now injects 19 mutations per board (4 existing writer-authority mutations, 11 alternate output API calls, and 4 direct register assignments), for 38 total expected rejections across ESP8266 and ESP32. Comment/string decoys are also checked to avoid false positives.

These are static/source-extracted regression tests only. They do not establish physical GPIO voltage, relay polarity, coin-acceptor behavior, pulse retention, or hardware acceptance.

### CI status at this checkpoint

GitHub Actions workflow runs for source/test SHA 0c09d8ed5927bac037f01a2649d0d332c5717a38 were not returned by the commit-run lookup at the time of this handover. Poll Intake Deny, Mbed TLS, Full, and Native must be re-read on their exact tested heads after the append-only handover update. Do not transfer earlier #380 runs to this new source SHA. Native remains subject to its existing path filter; no manual workflow-dispatch write action is exposed.

### Release and ownership disposition

- CORE still owns the canonical authenticated controller/financial envelope.
- QA still owns PAY-0745 and controller parity semantics.
- HARDWARE owns this firmware host-lab source contract and the #380 stack handovers.
- Active v0.6 P0 #177 poll-before-first-sample remains unresolved; no coin/relay re-enable was introduced.
- #239, #254, and #283 remain separate protected DRAFTs; no edits or retargeting.
- Physical relay/acceptor polarity, EEPROM/NVS brown-out, LittleFS recovery, 150 power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected signer/witness, v1-to-v2 migration, durable accounting/replay, and independent QA/release signoff remain NOT TESTED / NOT ACCEPTED.

**HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.**

 
## PHX-HARDWARE UTC20 — GPIO output-register bank and compound-assignment coverage

**Updated:** 2026-11-28T20:48Z  
**Task:** PHX-HW-177-GPIO-OUTPUT-API-AUTHORITY-20261128T20Z  
**PR:** #380, OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hw-gpio-writer-reconcile-20261128-utc17  
**Source/test + handover commit:** the commit containing this append-only entry (the exact resulting SHA is pinned in the PR body and PHX-HARDWARE UTC20 checkpoint).

### Additional failure-injection coverage

Expanded the direct-register mutation matrix beyond simple assignment to cover ESP8266 GPOS/GPOC compound OR assignment and ESP32 GPIO.out_w1ts/out_w1tc plus GPIO.out1_w1ts/out1_w1tc .val and compound-assignment forms.

The final source-contract matrix now contains 27 mutations per board: 4 existing logical-writer mutations, 11 alternate output API calls, and 12 direct register writes/assignments. Expected rejection count: 54 total across ESP8266 and ESP32. Comment/string decoys remain a positive control.

The source contract itself is unchanged in this follow-up; the mutation matrix now exercises the already-defined register patterns. This remains static/source-extracted CI evidence only, not electrical or physical acceptance. Poll, Mbed TLS, and Full exact-head Actions results must be read after this commit; prior runs are not transferable.

**HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.**

 
## PHX-HARDWARE UTC20 — exact-head terminal CI and P0 source revalidation

**Updated:** 2026-11-28T20Z  
**Exact tested source/test head:** b355d92b392c81b539e3f4e80b7839b186ef74ab  
**Branch:** phoenix/hw-gpio-writer-reconcile-20261128-utc17  
**PR:** #380 OPEN / DRAFT / UNMERGED; canonical child of #377@95ace1236c2b3e4816515c372edd4853ceeed064.

### Exact-head workflow results

- Poll Intake Deny [#46187906137](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46187906137), job 141111859740: PASS. The log records 54/54 GPIO writer/register mutations rejected across ESP8266 and ESP32 (27 per board), comment/string decoys ignored, both board guards PASS, and POLL_INTAKE_GUARD_SIMULATED_ONLY=1.
- Mbed TLS [#46187906203](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46187906203): 3/3 PASS (source contract, ESP32 core 3.3.13 and 4.0.0). Within-core clean A/B outputs match: 3.3.13 SHA256 51c1cad7743336db806bddf05b1e6d08ab769f9b077246804010c7e52fee16aa; 4.0.0 SHA256 258a9701cf4ad6f0767242cd9583a39f5185ee48d4bee2dd0e4ae8a3975cd358. Artifacts 15280626741 and 15281115206.
- Full [#46187906187](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46187906187): FAIL at QA-owned tests/controllers.sh:21 literal config_revision requirement. Both #377-based ESP sketches lack that field. All 14/14 target/platform jobs completed PASS (ESP8266, ESP32, Android, and 11 OpenWrt targets). CI-0701 and mandatory handover freshness passed; update bundle, simulations, candidate, signing and publication were skipped.
- Native Synthetic Journal: NOT RUN; path filters exclude these Hardware host-lab Python files and no manual workflow-dispatch action is exposed.

### Source and correction history

- Contract change commit: 0c09d8ed5927bac037f01a2649d0d332c5717a38.
- Final test expansion and handover sync commit: b355d92b392c81b539e3f4e80b7839b186ef74ab.
- Intermediate c5a9f666ddb016ed6df43ed73756696b3db3c824 had an escaping defect in regex/newline fixtures and was corrected by 0c09d8; do not use its failed Poll run as final evidence.
- No production ESP8266/ESP32 .ino, CORE API, QA-owned controller test, finance, signer, witness, migration or COE destination source was changed.

### Live blockers and ownership

- Active v0.6 remains at 2fbd2475e9f54878c316fa7cea2f228386b0e859: ESP8266 poll 354 -> first coin sample 357; ESP32 poll 314 -> first sample 318. P0 #177 remains OPEN; this PR does not fix the race.
- CORE #252 v1 config_auth is a DENY-only lab proposal with admission_allowed=false and does not bind immutable owner/window-kind identity. CORE owns the versioned authenticated producer/contract; HARDWARE consumes only after review; QA owns semantic fail-closed vectors.
- #283 source audit: failed quarantine append returns false before clearPending; quarantinePending is definition-only at the inspected head; current main register/poll has no approved response_sig. Do not guess or wire a positive response.
- Master #288 UTC20 head 0d8a48b908078663eeadf283cb33a9541785e9be still pinned the prior #380 head 5297760322c3752878087d38b784ee8c715db6f2; HARDWARE requested a Master-owned ROLE_ASSIGNMENTS/INTEGRATION_MATRIX refresh to b355d92.
- Private BLAZE_PROJECT_REGISTRY_v11_20261027.json NOT RECOVERED; no Google Drive connector/action is exposed. No older registry substituted.

### Release classification

GPIO writer authority guard and 54 mutation cases: CI VERIFIED / SIMULATED.  
Controller Full integration: FAILED. Native: NOT TESTED.  
Physical relay/acceptor polarity, EEPROM/NVS brown-out, LittleFS recovery, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery: NOT TESTED.  
Protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff: NOT ACCEPTED.

**HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.**
