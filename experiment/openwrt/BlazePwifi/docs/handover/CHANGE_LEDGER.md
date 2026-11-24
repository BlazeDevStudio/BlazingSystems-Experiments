# PHX-HARDWARE change ledger — 2026-11-20 UTC05

- PR #254 branch `phoenix/hardware-core252-deny-consumer-20261030`.
- Test-first RED: `26fae74219c505e5c9119ca4ca33de0eac039183`; focused run [44682886902](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44682886902), job 136110238848, ASan/UBSan stack-buffer-overflow at hex64 parser-span read.
- Implementation: `45f5c27db23e423acaf94d2522634536d734b4d2`; length-aware digest/signature/canonical spans; no strlen on parser-owned input; admission helpers remain false.
- Focused exact-head run [44683172568](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683172568) was IN_PROGRESS when this entry was written. Full runs 44683172700 and 44683165768 were PENDING.
- Lab/CI only. No application integration, hardware acceptance, signing, financial or production authority.

## UTC05 exact-head follow-up

- Narrow handover successor: `b541db182c2bba9d7b8cec17147e4d9cf0050577`.
- Focused [44683293103](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683293103), job 136111544480: PASS at source/docs anchor 9657280; ASan/UBSan; 5/5 synthetic checks; Phase A deny guard.
- Full [44683292995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683292995), validation job 136112096462: FAILED mandatory handover freshness because canonical handovers predated the narrow handover. ESP8266 passed; other jobs were running at last read. No Full PASS.
- Canonical handovers updated after narrow handover; new exact-head Full run must confirm freshness.
- LAB ONLY / HARDWARE NOT TESTED / PRODUCTION NO-GO.


## 2026-11-24 UTC07 — #348 zero-length controller-auth span coverage

- **ID / scope:** PHX-HARDWARE / #172 / #177 / #266 / #254 / #348; non-actuating ESP32 ControllerAuthV1Lab native test only.
- **Status:** committed; focused CI validated; Full build pending at checkpoint. Hardware NOT TESTED; production NO-GO.
- **Branch / parent:** `phoenix/hw-controller-auth-nonempty-spans-20261123-utc15`, stacked on #254 at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, itself stacked on #239 at `d83b715b116185107737fef721c2eece8feebf39`.
- **Source/test commit:** `4ad6d202da4918ae244d5cb6f44176bf93e6fa3c`; file `experiment/openwrt/BlazePwifi/tests/v060_controller_auth_header_native.cpp`.
- **Change:** add explicit rejection assertions for zero-length hex digest, zero-length policy digest and zero-length HMAC signature spans. Actual helper/header remains the subject under test; no production sketch or shared API changed.
- **Exact CI:** focused [#45350904157](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45350904157), job `138296790332`, SUCCESS at exact source/test SHA; ASan/UBSan, `-Wall -Wextra -Werror`, Phase-A deny guard PASS. Full [#45350904159](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45350904159) was IN_PROGRESS; no Full result claimed.
- **Known blocker:** prior Full [#45207909463](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45207909463) failed at inherited ESP32 core 4.0.0 missing `mbedtls/sha256.h` in `BlazePwifiVendo32.ino:6`, plus stale handover gate. Mbed TLS 4/PSA provider decision remains a Master/Release coordination dependency; no cross-stack port performed.
- **Safety:** Phase A coin/relay admission remains DENY. No key, signer, witness, finance, migration, physical device, flash, reset, release or deployment action.
- **NEXT ACTION:** reconcile terminal Full run #45350904159, then request Master/Release decision on the ESP32 provider path; retain exact source/head evidence and independent QA review.


## 2026-11-24 UTC07 — #348 null-pointer span failure injection

- **ID / scope:** PHX-HARDWARE / #172 / #177 / #266 / #254 / #348; non-actuating ControllerAuthV1Lab native test.
- **Status:** source/test and all three canonical handovers committed together; exact-head focused/Full CI pending. Hardware NOT TESTED; production NO-GO.
- **Branch / stack:** `phoenix/hw-controller-auth-nonempty-spans-20261123-utc15`, PR #348 → #254 at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9` → #239 at `d83b715b116185107737fef721c2eece8feebf39`.
- **Source/test:** this checkpoint commit adds null-pointer rejection cases for raw policy, digest, canonical message and signature spans, including null/zero-length hex input. Prior zero-length coverage is in `4ad6d202da4918ae244d5cb6f44176bf93e6fa3c`.
- **Prior exact CI:** focused [#45350904157](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45350904157), job `138296790332`, SUCCESS at `4ad6d202da4918ae244d5cb6f44176bf93e6fa3c`; ASan/UBSan and Phase-A deny guard PASS. Full [#45350904159](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45350904159) failed the stale event SHA's handover gate: `CHANGE_LEDGER has no dated entries`; no Full PASS.
- **Handover gate correction:** added dated UTC07 entry and synchronized PROJECT_HANDOVER, CURRENT_STATE and CHANGE_LEDGER in this same source+docs commit; new Full exact-head run must independently verify.
- **Known blocker:** inherited ESP32 Arduino core 4.0.0 build cannot find `mbedtls/sha256.h` in the application sketch. Provider/PSA decision remains Master/Release coordination; no cross-stack port.
- **Safety:** Phase A coin/relay admission DENY. No application behavior, CORE contract, key, signer, witness, finance, migration, flash, reset, release or deployment changed.
- **NEXT ACTION:** verify new exact-head focused and Full runs; record terminal outcomes; request independent QA and Master/Release review.


## 2026-11-24 UTC07 — terminal exact-head CI for #348

- **Branch / final source+handover head:** `phoenix/hw-controller-auth-nonempty-spans-20261123-utc15` / `b1639bde37de704708d87a085ed0d14208594e59`; PR #348 OPEN/DRAFT/UNMERGED, base #254 `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, parent #239 `d83b715b116185107737fef721c2eece8feebf39`.
- **Source/test:** zero-length digest-hex, policy-digest and HMAC-signature assertions; null raw-policy, digest, canonical-message and signature pointer rejection. Canonical handovers were committed in the same source+docs commit to preserve freshness.
- **Focused exact-head:** [#45351486951](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45351486951), job `138298749761`: SUCCESS at `b1639bde37de704708d87a085ed0d14208594e59`; ASan/UBSan, `-Wall -Wextra -Werror`, 5/5 synthetic checks, Phase-A deny guard PASS.
- **Full exact-head:** [#45351479477](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45351479477): overall FAILURE; 23 jobs SUCCESS, 1 FAILURE, 6 SKIPPED. Validation job `138298862610` SUCCESS, including mandatory handover freshness, gate regression, controller protocol parity and financial/accounting/replay/witness host tests. ESP8266 `138298862746`, Android `138298862647`, and 11 other OpenWrt target jobs SUCCESS. ESP32 `138298862598` FAILURE: `BlazePwifiVendo32.ino:6` cannot find `mbedtls/sha256.h` on Arduino core 4.0.0. ESP32 simulation and production sign/publish/candidate jobs SKIPPED.
- **Handover gate history:** previous event SHA `4ad6d202da4918ae244d5cb6f44176bf93e6fa3c` failed because CHANGE_LEDGER lacked a dated heading; this combined commit added the dated record and synchronized all three canonical handovers. New Full exact-head gate PASS. Prior failure is preserved as history, not transferred to this head.
- **Blocker / ownership:** inherited ESP32 Mbed TLS 4 provider compatibility requires PHX-MASTER/PHX-RELEASE decision; no provider port or cross-stack cherry-pick performed. CORE response contract, coin/relay admission, finance, signer, witness and migration unchanged.
- **Safety:** Phase-A coin/relay admission DENY. No physical hardware, live money, flash, reset, migration, signing, release or deployment.
- **NEXT ACTION:** Master/Release decide the approved ESP32 provider/stack path; QA reviews span tests; Hardware reruns Full after approval.
