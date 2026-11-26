2026-11-27 UTC19 | PHX-HARDWARE | PR #355 | test-first RED 39aa77e56806df3c1febae0f0a097b0f661ca2c6 (run #45886210859/job 140137430702: both boards rejected unsafe startup order); firmware correction 6bb8eafe03e5a2548524b7c693a37a95638c140e moves ESP8266 initPendingStore and ESP32 LittleFS mount/recovery after configured pin OFF preload + denyRemoteControl. Exact-head GREEN pending; physical acceptance NOT TESTED; PRODUCTION NO-GO.

## 2026-11-27 UTC19 — exact-head startup output latch evidence

- Source/test HEAD: `6b4f7a873dd72663c00c4e08f23131d58e662584`; firmware correction: `6bb8eafe03e5a2548524b7c693a37a95638c140e`.
- Expected RED: run `45886210859`, job `140137430702`, both boards rejected the unsafe pre-fix order.
- Focused GREEN: run `45886748490`, job `140139222908`, both boards pass startup output-before-LittleFS and reject the early-mount mutation.
- ESP32 Mbed TLS matrix: run `45886748407`; source-contract `140139828100`, core 3.3.13 `140139827987`, core 4.0.0 `140139827660` all PASS.
- Full run `45886748466`: CI-0701 `140140022161`, ESP8266 `140140135665`, ESP32 `140140135695`, and 13 OpenWrt/target jobs PASS; Android `140140135671` in progress at last check. Validation `140140135720` failed only because this ledger lacked the required dated `## 2026-` heading. Fresh Full required after this documentation commit.
- Native synthetic `45886748463` remains FAIL on QA-owned active-`clearPending` assertion; no QA source changed.
- Physical acceptance remains NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## 2026-11-27 UTC19 — post-sync Full gate and QA contract result

- Final docs head before this update: `d4a35e5e12b8abd85b6a45fa6902d09471c84e4d`; exact source/test SHA: `6b4f7a873dd72663c00c4e08f23131d58e662584`.
- Focused docs-head run `45887618603`, job `140142163199`: PASS.
- Mbed exact-source run `45886748407`: source-contract `140139828100`, core 3.3.13 `140139827987`, core 4.0.0 `140139827660`: PASS.
- Full run `45887618795`: CI-0701 `140142273647` and mandatory handover freshness/history gates PASS; QA-owned `tests/controllers.sh:21` fails because the deny-only sketches intentionally have no `config_revision` response consumer. ESP8266 and 13 OpenWrt target jobs PASS; ESP32/Android still running at last check.
- Native run `45887618600` fails QA-owned active-`clearPending` assertion; current sketches have definition-only clear helper and no disposition callsite.
- Production/HARDWARE ACCEPTED = NO; physical acceptance NOT TESTED; PRODUCTION READY = NO-GO.
