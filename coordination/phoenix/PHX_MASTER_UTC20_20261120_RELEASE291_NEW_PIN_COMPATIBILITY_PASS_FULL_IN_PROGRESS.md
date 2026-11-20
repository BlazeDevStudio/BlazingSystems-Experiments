# PHX-MASTER UTC20 — RELEASE #291 new-pin compatibility PASS / Full still running

**Updated:** 2026-11-20T20:19:08Z  
**Role:** PHX-MASTER — exact-head CI reconciliation  
**Disposition:** PR #288 OPEN/DRAFT · RELEASE #291 OPEN/DRAFT · PRODUCTION NO-GO

## 1. Exact RELEASE #291 identity

- Current PR/docs head: 4f6d2371cafa2d7e80f1aa3e37e9744ad6b01ddf.
- Source/workflow-fix commit: 5188d1a1cfb5f96462a5ec24941fe35530944f68.
- Test/static-guard commit: 5c5001d43e173463024c3c790bead406fa8c90c3.
- Base #242: 734b89d9e7792247e8376335c3f3685500ab3f89.
- Accumulated PR diff: 26 paths, still 21 RELEASE / 3 CORE / 2 PISONET.
- The new compatibility test and workflow pin HARDWARE #327 source/test SHA 1a631567eb0c14c12a114f592685f44cc414466f and ESP32 sketch blob ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7. Exact file readback shows the old 76eca091 pin is absent from both the test and workflow.

## 2. Current exact-head Actions readback

The post-checkpoint Actions readback supersedes RELEASE's earlier “exact-head CI not observed” note.

| Workflow | Run | Current result |
|---|---:|---|
| ESP32 core compatibility | [#44809606421](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44809606421) | SUCCESS, 3/3 jobs |
| BlazePwifi Full | [#44809606527](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44809606527) | IN_PROGRESS; no terminal result |
| Windows SoftTimer | [#44809606428](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44809606428) | FAILURE |

Compatibility exact jobs:

- Provenance regression suite 136542675863: SUCCESS.
- ESP32 core 3.3.13 / source 1a631567eb0c 136542676483: SUCCESS.
- ESP32 core 4.0.0 / source 1a631567eb0c 136542676949: SUCCESS.

This verifies the exact pinned ESP32 sketch/source under both listed cores and the provenance regression suite. It is scoped compatibility evidence, not production release acceptance.

Full exact jobs at latest readback:

- Validation 136542799908, ESP8266 136542799950, ESP32 136542799970 and Android 136542800113: SUCCESS.
- All currently started firmware target jobs: SUCCESS.
- Update bundle 136544529667 and ESP32/ESP8266 simulations 136544529741 / 136544529778: SUCCESS.
- Browser, Android emulator, x86 and several Orange Pi/Ruijie simulations remained IN_PROGRESS.
- Production import/sign/publish jobs were SKIPPED. No terminal Full PASS is claimed.

Windows:

- Build-windows job 136542584711: FAILURE.
- PISONET-owned negative-selftest.ps1 still reads $buildWorkflow before initialization.
- Publisher job 136543116646: SKIPPED.

## 3. Owner routing remains unchanged

- RELEASE owns the new compatibility test/workflow and its handover.
- PISONET owns the Windows negative-selftest failure.
- CORE owns the three inherited handover/ledger/state paths in the accumulated #291 diff.
- HARDWARE owns firmware and the source/test baseline.
- QA retains independent review.
- Master only records the exact pin and CI state; no source ownership or route changes.

The prior compatibility PASS #44799798721 at source label 76eca0915943 is historical only. The current exact-pin PASS is #44809606421 at source 1a631567eb0c and sketch blob ae0da8e2.

## 4. Other blockers remain

HARDWARE #327 remains at docs head 4d651e918f71de2e69d1f3bcfe627c4f944c9c39 / source-test 1a631567eb0c14c12a114f592685f44cc414466f. Focused quarantine/relay PASS; Full #44805905622 fails at QA's inherited positive poll-signature fixture. RENTAL #328 remains at 0e0da62acd47c6a1ce287f8a30fc700d603fa070 and inherits the older Mbed TLS 4-incompatible ESP32 sketch blob from #289; its shared build fails at CORE handover freshness and missing header.

COE #26 remains frozen at b382d233ff06c8791b1028bed3c617cc7b670d12. The complete tree comparison, source/destination firmware and test blob mismatches, 25-vs-0 board-local Python lab gap, three-vs-one workflow gap, incomplete NOTICE/Hardware license scope, and five queued destination workflows remain unchanged. No migration or staging.

Master PR #288 at audit start was e45ed9f555817b7ab24e699d7e5ba9788bc31fea; its coordination-only UTC20 audit branch remains open/draft. Ownership manifest remains DRAFT_REVIEW_ONLY with Master destination null.

## 5. Evidence and limitations

The current exact-pin compatibility run is a real GitHub Actions PASS on the pinned source and both ESP32 core jobs. The Full run remains in progress; no terminal result is inferred. The Windows failure remains open. Full Master Python suite remains NOT RUN because local GitHub DNS resolution failed. Private canonical registry v11 and newer corrections remain inaccessible through the exposed Library/connector surface.

No merge, release, signing, secret provisioning, hardware flash, payment operation, migration, physical acceptance or production action was performed.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates have independently verified evidence.
