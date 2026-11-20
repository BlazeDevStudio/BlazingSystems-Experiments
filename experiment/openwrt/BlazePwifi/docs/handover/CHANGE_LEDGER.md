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
