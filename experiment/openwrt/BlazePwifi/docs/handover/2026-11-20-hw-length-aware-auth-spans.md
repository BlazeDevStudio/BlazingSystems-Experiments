# PHX-HARDWARE narrow handover — length-aware ControllerAuthV1Lab spans

- Role: PHX-HARDWARE
- Task: #266 cleanup-first; #254 lab-only helper
- Repository: BlazeDevStudio/BlazingSystems-Experiments
- Branch: `phoenix/hardware-core252-deny-consumer-20261030`
- PR: [#254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/254), OPEN / DRAFT / UNMERGED
- Base: #239 at `d83b715b116185107737fef721c2eece8feebf39`
- Sanitizer workflow: `6cf18b913a72090df728f7030ef07c41aae95c1e`
- Test-first RED: `26fae74219c505e5c9119ca4ca33de0eac039183`
- Implementation: `45f5c27db23e423acaf94d2522634536d734b4d2`
- Status at checkpoint: exact-head focused CI PASS; Full validation FAILED handover freshness before canonical-doc successor; HARDWARE NOT TESTED; PRODUCTION NO-GO

## Finding

The previous `hex64(const char *)` bounded scan still read `p[64]`. A parser-owned 64-byte non-NUL-terminated span caused a real stack-buffer-overflow under AddressSanitizer/UndefinedBehaviorSanitizer.

## Correction

- `hex64(p, length)` requires exactly 64 bytes and never scans for a terminator.
- `matches_policy_digest` takes explicit digest length.
- `verify_mac` takes explicit canonical-message and signature lengths; it no longer uses `strlen` on parser-owned input.
- Tests exercise nonterminated digest/canonical/signature spans and malformed lengths/case/null, plus tamper, wrong-device, wrong-nonce, empty-key, digest mismatch and fixed lowercase formatting.
- Focused workflow compiles with ASan+UBSan.
- Coin admission and relay authorization helpers remain hard-coded false.

## Exact evidence

- RED [run 44682886902](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44682886902), job 136110238848: expected ASan/UBSan failure at old `hex64` byte-65 read.
- Implementation commit: [45f5c27](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/45f5c27db23e423acaf94d2522634536d734b4d2).
- Full [run 44683292995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683292995) reached validation job 136112096462 and failed the mandatory handover freshness gate because the canonical handovers were committed before this narrow handover. ESP8266 build passed; ESP32, Android and platform jobs were still running at the last read. This is not Full PASS. Canonical handovers are being refreshed after this narrow handover so the next exact-head run can re-evaluate the gate.

## Limits

This remains an isolated, non-actuating helper. It is not integrated into the .ino parser or coin intake. Mbed TLS 4 remains intentionally rejected by this lab helper; no PSA adapter was added. No CORE contract, wire format, key, finance, GPIO, relay, physical hardware, power-cut, signer/witness, migration, flash, or release behavior changed.
