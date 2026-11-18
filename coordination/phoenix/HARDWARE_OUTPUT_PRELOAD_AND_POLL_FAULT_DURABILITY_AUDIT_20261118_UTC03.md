# PHX-MASTER audit — Hardware output preload, poll-fault durability and COE Release gates

**Date:** 2026-11-18  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** #172 / #266 / #288  
**Status:** Coordination PR ready for review; subsystem owners retain all source implementation. **PRODUCTION NO-GO.**

## 1. Exact repository state

- Experiments `main`: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`
- Experiments development `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`
- COE `main`: `a6513ab4412b4c014eee2863e45cbe32d06cb243`
- Existing Master branch before this update: `phoenix/master-coordination@292832d76aabde74a1437ef439fb7f7e3dd037a6`
- Existing PR #288: OPEN / DRAFT, base `main@f4e8a891...`; 68 existing changed paths, all under `coordination/phoenix/`.
- `OWNERSHIP_ROUTES.json`: blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`; PHX-MASTER destination remains `null`.

The Experiments root `AGENTS.md` at main blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`, uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`, uploaded `README_FIRST(9).md`, and Library `COMMUNICATION_PROTOCOL.md` were read. COE root `AGENTS.md` returned 404. The AGENTS-linked cloud policy/handover could not be retrieved through the current GitHub connector.

## 2. New Hardware child #322 — output-enable latch ordering

Current PR #322 is OPEN / DRAFT / UNMERGED at `50d93e0de3d682550b6f02fb43484e76ad9c7e08`, based exactly on #320 head `b2b41a3d6ce7887b9624137c966f58462895d3fa`. Its source/test SHA is `7ba56c1ba92dcffa2555e4cce10d3010c3afaf5b`; the current PR head adds a documentation-only handover update.

Both ESP32 and ESP8266 `configureRuntimePins()` now:
1. Deassert old relay/LED pins using their old polarity.
2. Assign the new pin numbers.
3. Preload the new relay/LED logical OFF level before OUTPUT mode.
4. Enable OUTPUT mode.
5. Attach the coin interrupt after output configuration.
6. Reassert OFF after output enable.

This prevents an active-low relay from seeing the default LOW output latch during a pin-mode transition. No poll, coin admission, receipt, ledger, API, migration, signing or release behavior changed.

**Exact-head CI:**
- [44232877611 — Relay Output Polarity LAB](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877611): SUCCESS. Job log reports `OUTPUT_SEQUENCE_PASS` for ESP8266 and ESP32; active-high/active-low ordering and the missing-preload mutation are covered.
- [44232877649 — Quarantine/readback](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877649): SUCCESS.
- [44232877624 — Full build](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877624): validation FAILED at QA-owned `Missing poll signature check`. At last read, 13 target/platform jobs had completed successfully and Android remained in progress; downstream simulations/update/publish jobs were skipped. This is not a Full CI pass.

The test-first RED was [44226524555](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44226524555). The first #322 harness attempt [44232408796](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232408796) failed because Arduino interrupt stubs were missing; the test harness was corrected before the green exact-head focused run. Host call-order simulation is not GPIO voltage or relay acceptance.

## 3. Hardware candidate lineage and poll-fault durability

Master continues to accept the proposed review lineage **#314 → #315 → #317 → #320 → #322** only. Exact #317→#320 compare is 11 ahead / 0 behind; #322 base SHA equals #320 head. #321 remains a separate test-only RED candidate; it was not rebased or merged into #322. #283 remains a separate main-based candidate; #318 remains divergent (51 ahead / 71 behind #317), nonmergeable and without current-head CI.

#320 exact-head focused quarantine/relay runs [44225714826](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225714826) and [44225714732](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225714732) passed. Its push Full run [44225708501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225708501) failed validation at the stale poll-signature assertion while 14 target builds passed; downstream simulations/release jobs were skipped. Its PR-triggered Full run [44225714932](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225714932) was cancelled. The focused poll-edge run [44225475672](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225475672) used predecessor source/test SHA `b6e9cfa75105e6cd29c29b93266255d3110c8296`, not final #320 HEAD.

**Durability gap confirmed by exact source inspection:** both #320 sketches readback-check `/pollpulse.fault`; `latchPollPulseFault()` sets the RAM `journalRecoveryRequired` latch and disables outputs before attempting persistence. If marker open/write/readback fails, the source promises fail-closed behavior only this boot. `loadPollPulseFaultLatch()` restores the hold only when the marker exists. The `fakeOpenFail` lab case checks current-boot denial but does not simulate reboot after the marker was not created. No durable reboot fallback is proven for that case.

Master's bounded static source assertions passed 15/15: both boards' output preload order, marker readback checks, failure-latch ordering, boot marker gate, and the lab's open-failure/no-reboot test boundary. These are source assertions, not runtime or hardware tests.

Required: QA adds an exact-source reboot/reset vector after marker-open and readback failures, including no surviving pending record; HARDWARE implements an owner-reviewed durable fallback; CORE reviews event/receipt/replay semantics. Keep poll/coin admission and disposition default-deny.

## 4. COE Release and integration

- COE #31 current head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`: shared run 44222517238 and case run 44222517258 SUCCESS; mandatory sandbox run 44222517263 FAILED at `bwrap: setting up uid map: Permission denied` after 8/8 host-preflight tests passed. Packaging regressions were skipped.
- COE #35 current docs head `729c3e9c622c8f13bd949aebec750567c5382ed7`, source/test head `e5fb3be13c8ae0d82e943d6d71095c9a1db8223d`, exact child of current #31 (7 ahead / 0 behind). Case 44228970740 and shared/firmware 44228970878 SUCCESS; mandatory sandbox 44228970827 failed at the same UID-map probe, so packaging regressions were skipped.
- Current #35 packager blob `0bfc6404dee2f90a0c941f8ec40f3cb59c386d01` still contains invalid ULA placeholder `fd00:db8:blaze::/48`; do not invent a replacement. CORE/COE must define durable installation-scoped ULA provisioning before RELEASE implementation.
- COE #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12` with five workflows QUEUED and zero jobs. #27 is a separate main-based candidate, 3 ahead / 83 behind #26; its firmware blobs match #26, not current source candidates. #28/#29/#30/#32 have scoped CI success, not combined #26 acceptance.
- No source/destination files were moved, copied, overwritten or deleted. No license/import/test identity is inferred from matching firmware names alone.

## 5. Other current role/CI pins

- CORE #252 `c82705f2...`: 42698139210 SUCCESS, scoped; separate hourly CORE automation retains source ownership.
- RENTAL #240 `a7d113fb...`, #287 `a4fffd01...`, #289 `68928774...`: scoped current-head runs SUCCESS.
- PISONET #255 `d01fd164...`: 42462978704 SUCCESS, scoped; native COM acceptance UNKNOWN.
- QA #267 `ff536799...` run 41452247439 SUCCESS; #290 `5c29d159...` run 43633486963 SUCCESS; #279 and #292 have no current-head runs.
- RELEASE #291 `a74b8b94...`: 44199987756 SUCCESS, scoped; signing/publishing skipped.

## 6. Registry, cleanup and execution limitations

Issue #172 remains OPEN and received the Hardware #322 UTC03 checkpoint. Cleanup issue #266 remains OPEN; no new cleanup completion evidence was found. The separate CORE automation retains CORE implementation ownership; PHX-MASTER did not modify CORE files.

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed Google Drive/connector surface. Recursive Library listing exposed registry v3–v7 plus older artifact/ledger files only; none was substituted. No private registry content was published or written.

The full Master Python suite was NOT RUN: container checkout failed because `github.com` could not be resolved. No PR-triggered Master CI run was returned. Physical GPIO/relay/coin behavior, 150 real power cuts and 30-device/24-hour soak remain NOT TESTED.

## 7. Exact next owner actions

1. **PHX-QA:** add reboot-after-marker-open-failure and short-write/readback failure vectors; replace the stale positive poll-signature fixture with default-deny behavior assertions; verify exact #322 SHA.
2. **PHX-HARDWARE / PHX-CORE:** define and implement a durable reboot-safe poll-edge fault witness without enabling automatic replay or coin disposition.
3. **PHX-RELEASE / Infrastructure:** supply an authorized disposable no-secret runner with unprivileged user namespaces; resolve site-scoped ULA provisioning.
4. **COE integration owner:** refresh #26 exact-source blob/license/import/test provenance and unblock its queued workflows only after owner review.
5. **Registry custodian:** restore authorized read-only Drive v11 and newer-correction access.

No merge, migration, release, signing, secret provisioning, flash, physical test or real-payment operation occurred. **PRODUCTION NO-GO.**
