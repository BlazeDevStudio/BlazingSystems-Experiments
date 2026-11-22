# PHX-HARDWARE — Mbed TLS lab shared lexical extractor

**Date:** 2026-11-22 UTC14  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#342](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/342) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-mbedtls-lexer-reuse-20261122-utc14`  
**Parent:** #327 exact HEAD `fadac4ed3bc837cf729753264b9427fa3fd312b9`  
**Final source/test SHA:** `c56140813a5bc04e80e8a779c97fea2973ff01eb`

## Defect and correction

The Hardware-owned `mbedtls_compat_guard_lab.py` carried a second, naive `extract_braced_function()` implementation. It counted raw braces and could truncate a source-extracted function at a brace inside an ordinary/raw string or comment. That undermined the lab's claim that it compiles the actual `hexDigest()` body.

The lab now imports the existing Hardware-owned, offset-preserving `extract_function()` from `esp8266/BlazePwifiVendo/firmware_lab_source.py`. The duplicate parser was removed. A self-test uses a valid multiline C++ fixture with brace decoys in an ordinary string, raw string, line comment and block comment before the production `hexDigest` function is extracted.

No production sketch or cryptographic implementation changed.

## Test-first and exact-SHA evidence

- **RED test-only commit:** `8922bf636f7977fe7cce81a5b0d68fff348fcf5e`. Focused Quarantine run [#45031391168](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45031391168), job `137235549843`: expected failure, `braces inside C++ comments/literals truncated the extracted function`. The initial fixture used escaped newline sequences; the final regression was corrected to physical newlines before GREEN.
- **Intermediate parser-reuse commit:** `2e65179331376a176a97420e7293a4741361ff9e`. Its focused run [#45031569637](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45031569637) failed with `unbalanced C/C++ block` because the fixture still contained literal backslash-n text. This was a test-fixture formatting defect, not a production firmware failure.
- **Final corrected source/test SHA:** `c56140813a5bc04e80e8a779c97fea2973ff01eb`. Focused Quarantine run [#45031682091](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45031682091), job `137236430955`: **SUCCESS**. Exact run terminal status: completed/success.

The successful focused job emitted:
- `MBEDTLS_MAJOR_3_SELECTOR_AND_DIGEST_PASS`
- `MBEDTLS_MAJOR_4_SELECTOR_AND_DIGEST_PASS`
- `MBEDTLS_UNSUPPORTED_MAJOR_2_REJECTED`
- `MBEDTLS_UNSUPPORTED_MAJOR_5_REJECTED`
- `MBEDTLS_COMPATIBILITY_GUARD_LAB_PASS`
- `SOURCE_QUARANTINE_PASS 36/36 scenarios` on both board paths
- EEPROM end/reopen failure reboot-deny markers
- ESP8266 and ESP32 coin-pulse capture `17/17`
- ESP8266 boot-polarity lab PASS

The same job explicitly emitted `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`. These results are host-side source-extracted tests only.

## Integration blocker retained

Full BlazePwifi build run [#45031682054](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45031682054), exact source/test SHA `c56140813a5bc04e80e8a779c97fea2973ff01eb`, validation job `137236512086`: **FAILURE** at the inherited QA-owned `Controller protocol parity` assertion:

```text
Missing poll signature check in .../esp8266/BlazePwifiVendo.ino
```

The run is terminal **CANCELLED** after the validation failure: 12 jobs SUCCESS, 1 validation FAILURE, 8 CANCELLED, 6 SKIPPED. ESP32 and Android jobs were cancelled; signing, candidate and release jobs did not complete. The focused Mbed TLS 3/4 stub tests are not an ESP32 target build. The source change does not add a poll signature or positive admission path. CORE owns the response contract; QA owns the independent parity fixture. No bypass was made.

## Scope and safety

Changed only:
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/mbedtls_compat_guard_lab.py`
- this narrow handover

No ESP sketch, GPIO/relay behavior, coin admission, API/schema, finance, signer/witness, QA-owned assertion, Release workflow, COE source, physical device, flash, reset, migration, signing, merge or deployment changed.

**Readiness:** focused lab **CI VERIFIED**; behavior **SIMULATED**; physical acceptance **NOT TESTED**; **HARDWARE ACCEPTED: NO**; **PRODUCTION READY: NO-GO**.

## Next action

PHX-MASTER should pin PR #342 and refresh the stale #327 head in `ROLE_ASSIGNMENTS.md` / `INTEGRATION_MATRIX.md`. PHX-CORE/PHX-QA must resolve and independently validate the authenticated poll-response contract before Full integration can pass. PHX-HARDWARE will continue only with the next unblocked Hardware-owned task.


---

## UTC14 follow-up — selector comment-decoy guard

**Task:** PHX-HARDWARE cleanup-first test-integrity correction  
**Parent:** #327 exact head `fadac4ed3bc837cf729753264b9427fa3fd312b9`  
**PR:** #342 OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-mbedtls-lexer-reuse-20261122-utc14`

### Proven defect

After removing the duplicate brace parser, the same Mbed TLS lab still discovered its header selector with a raw line scan. A complete selector-shaped `#if/#elif/#else/#endif` block inside a C++ block comment could be selected as the real header block. That allowed comment-only text to satisfy the selector contract and made the source-extracted stub harness validate the wrong bytes.

### Test-first lineage

- Initial test-only attempt `39e1d1b9279da6acfa8d771673e9124db0595548`: focused run [#45034072074](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034072074), job `137243804767`, failed before the intended assertion because the new fixture encoded literal backslash-n text. This was a fixture-construction error, not the expected RED.
- Corrected test-only commit `65d5eef0efca25c139ce05dd1c507ba211f41f79`: focused run [#45034242697](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034242697), job `137244323329`, failed as expected with `selector extractor accepted a comment-only preprocessor decoy`.
- Source fix commit `4cd878d2a55751d25f7bd91628d0c91d8111889e`: imports the existing `mask_non_code()`, masks comments/literals before scanning directive lines, verifies mask offset and line-count preservation, and returns the original unmasked selector lines. No second lexer was added.

### Exact-source GREEN

Focused Quarantine run [#45034441999](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034441999), job `137244933849`, exact source/test SHA `4cd878d2a55751d25f7bd91628d0c91d8111889e`: **SUCCESS**.

Verified markers include:
- `MBEDTLS_SELECTOR_COMMENT_DECOY_REJECTED 1/1`
- `MBEDTLS_MAJOR_3_SELECTOR_AND_DIGEST_PASS`
- `MBEDTLS_MAJOR_4_SELECTOR_AND_DIGEST_PASS`
- `MBEDTLS_COMPATIBILITY_GUARD_LAB_PASS`
- Existing quarantine, EEPROM/NVS readback, poll-edge failure-injection and pulse-capture host suites passed in the same focused job.

The job explicitly emitted `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

### Full integration status

Full build run [#45034442014](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034442014), exact source/test SHA `4cd878d2a55751d25f7bd91628d0c91d8111889e`, validation job `137245008880`: **FAILURE** at the inherited QA-owned controller parity assertion:

```text
Missing poll signature check in .../esp8266/BlazePwifiVendo.ino
```

At this handover update, the remaining platform jobs were still running; the validation gate had already failed. No Full integration, candidate, signing or release PASS is claimed.

### Scope and readiness

Only this Hardware-owned ESP32 host lab and this handover changed. No production sketch, Mbed TLS implementation, controller/API contract, finance, signer/witness, QA-owned assertion, Release workflow, COE source, device, flash, migration or deployment changed.

**Focused CI: VERIFIED. Host behavior: SIMULATED. Physical acceptance: NOT TESTED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

**Next exact action:** PHX-MASTER pin #342 and reconcile current #327/#339 ancestry; PHX-CORE and PHX-QA resolve the authenticated poll/register contract and stale positive poll-signature fixture. PHX-HARDWARE keeps the consumer deny-only and waits for the next unblocked Hardware-owned task.
