# PHX-L-VERIFY 2026-10-26 UTC08 — synthetic capture temporal-resolution false-pass

**Scope:** isolated firmware QA / off-device evidence-format preflight, not firmware source, payment logic, production release, hardware flashing or customer equipment. **NO CODEX. PRODUCTION NO-GO.**

## Live refs / previous exact-head CI
- Default `main@9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`; development comparison-only `blazepwifi-v0.6.0-audit-foundation@5a8fe3efbc4afb9ecf1260c4f09cf6903c26795a`. No MASTER-approved integration base. #30 CLOSED UNMERGED.
- Draft #179 `e5a9781ea5234b09501d5356cf966f9237ac8172` OPEN; draft #193 prior `776cb58aef16c39455bfad38ffcd2eb722738c19` OPEN stacked on #179; #150 `867cbbac952ffb24414635a6178021b7371ac123` and #183 `3b892c67655ffda0b5adc0fc034a60e368254e17` OPEN, unmerged.
- Exact #193 `776cb58aef16c39455bfad38ffcd2eb722738c19`: [Full #40289438712](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40289438712) COMPLETED FAILURE, 15 success/13 skipped/1 failed. Handover and ESP8266/ESP32 Arduino compilers PASS; validate job `121460804189` reports two genuine security RED per board: `untrusted_positive_revision_cannot_enable_coin`, `cold_reboot_older_positive_revision_cannot_enable_coin`. [Native #40289438763](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40289438763) COMPLETED SUCCESS. Signing and release SKIPPED.

## Executed bounded QA
- Independently re-ran previous V3 checker from UTC07 conversation-local evidence ZIP, with raw CSV and JSON SHA-256 kept self-consistent. For each of ESP8266 and ESP32, four synthetic mutants with **1 microsecond transitions** and declared `sample_resolution_us=10` passed V3: coin pulse, poll start/end, relay supply off/on bounce and coin bounce. **8/8 V3 false-passes reproduced.**
- Disposable V4 adds conservative same-channel transition interval >= **declared** sampling resolution. **8/8 V4 rejects**, two positive board fixtures pass, two exact-resolution boundary controls pass, previous byte-binding negative controls retained, CLI exit 0/2/3 verified; `python3 -m py_compile` PASS, `python3 -m unittest -v test_trace_gate_v4` **5/5 PASS**. No firmware sketch, workflow or source change.
- Conversation-local reproducible ZIP SHA-256: `1c3d8a4c535d2e8d44d22e748936c6d60db3dfd755adac2eeafb1bfef70383fd`.

## Limits / decision
- V4 is a **format** check, not proof of actual sampling frequency, analyzer bandwidth, trigger completeness, power rail voltage, physical polarity, independent signed acquisition, or custody. Self-declared `sample_resolution_us` can be falsified. An operator-controlled capture can still pass. Do not treat V4 green as hardware or release acceptance.
- MASTER/CORE must approve independent analyzer capability and signed off-device custody, as well as authenticated config revision/ACK contracts, before physical trials or source correction. Keep #31/#32/#34/#43, 150 physical power cuts, 30-device 24-hour soak, independent witness, reversible migration and permanent signing blocked.
- **NEXT:** classify exact successor Full/Native at new docs HEAD; no merge, flashing, production signing, customer data, or commercial release.
