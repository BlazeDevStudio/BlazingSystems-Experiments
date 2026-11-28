# PHX-MASTER migration gate — ambiguous quarantine append (2026-11-15 UTC19)

Status: **DRAFT / PRODUCTION NO-GO**. Coordination only; no runtime file migration, merge, release, financial admission or hardware flash.

## Reproducible evidence anchors
- Experiments default `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; separate development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- PHX-MASTER draft [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288), pre-change `c6a536d1c44d4525b202ca0a267724f2cb203aca`; route manifest `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`.
- PHX-HARDWARE stacked draft [#310](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/310) exact head `da18da4c2afc3f42037ee3ac4cfa48bdba4f4f01`, based on #309. It latches recovery-required state when quarantine append is partial or cannot be verified. Exact-head Actions [43748385389](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43748385389) and [43748385357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43748385357) report completed/success; software evidence only.
- Destination COE `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; existing [draft integration #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) exact head `b382d233ff06c8791b1028bed3c617cc7b670d12`. Five associated workflows were **queued**, not passed, at inspection.

## Exact Git tree comparison — two NONIDENTICAL firmware blobs

| Firmware | PHX-HARDWARE #310 source Git blob | COE #26 staged Git blob | Result |
|---|---|---|---|
| `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` → `Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` | `c12d37ee4e68082d97b4d72cf997aa14f19b6ea4` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | DIFFERENT |
| `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` → `Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` | `0e0bc19fbdbbecabcd1a0072db0584a2b9fa61e2` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | DIFFERENT |

All four entries have Git mode `100644`. Git tree metadata comparison **does not prove** whether the specific quarantine recovery fix is absent in the destination; inspect exact contents/diff before any claim of behavioral equivalence or import. The staged `Hardware/tests/test_firmware_hardening.sh` blob is `f921c56cecc19cab1989507b9b4ade1f45dac54e` (mode `100755`); no source-linked test identity or license/dependency parity has been established.

## Required owner-routed acceptance matrix
1. **PHX-HARDWARE:** enumerate all quarantine append paths for ESP32 and ESP8266; inject short append, failed verification, partial record, retry after clearing injected fault, reboot, and pending journal replay. Assert no additional bytes, no clearing pending evidence, no relay/credit enable while ambiguous.
2. **PHX-QA:** independently rerun negative cases at exact proposed source and destination SHA. Inspect and compare tests by Git blob, compilation flags, library versions, third-party licenses, target board configurations, and firmware behavior; record any deliberate differences rather than replacing staged safety fixes with older code.
3. **PHX-MASTER:** receive signed-off per-file provenance and owner/QA approval, then update migration matrix. Do not use this document as approval for copying either firmware blob.
4. **PHX-RELEASE:** maintain protected signing/independent anti-rollback, crash-atomic financial migration, native hardware acceptance, 150 real power cuts, and 30-device 24-hour soak as hard NO-GO gates.

## Execution and rollback
This activation performed **GitHub metadata/tree inspection and private registry JSON parsing** only. No firmware tests or full Master 18-test suite were executed locally; the two green HARDWARE Actions runs are independent remote CI results and not physical evidence. Private registry was read from the restricted Drive project folder and not copied here. Rollback is a single revert of this coordination-only document commit on draft #288. No product or payment state changed.
