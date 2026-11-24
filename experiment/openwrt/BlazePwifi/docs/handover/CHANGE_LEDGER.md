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
