# PHX-L-VERIFY UTC07 — off-device coin waveform raw-byte provenance QA (2026-10-26)

**Scope:** synthetic QA-only enhancement of conversation-local UTC06 waveform checker. NO CODEX, no firmware or financial source edit, no customer device/coin, no flash, no signing, no merge, no release. **PRODUCTION NO-GO.**

## Exact GitHub state and CI
- Draft PR #193 (stacked on draft #179) HEAD `7832f992eb580d499645954896a6bf741efeb208`; Full [#40283088143](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40283088143) **COMPLETED FAILURE**: 15 success, 13 skipped, 1 failed. Validate job `121440563993` has 13/15 source-linked GPIO checks per board with two genuine RED cases: `untrusted_positive_revision_cannot_enable_coin`, `cold_reboot_older_positive_revision_cannot_enable_coin`. Handover and ESP8266/ESP32 Arduino builds PASS.
- Native [#40283088181](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40283088181) **COMPLETED SUCCESS**. These are source/CI observations, not hardware acceptance.
- Default `main@9596fc6a9f8a6a42bc252019c24ca1f38d96dd7a`; comparison-only development `blazepwifi-v0.6.0-audit-foundation@5a8fe3efbc4afb9ecf1260c4f09cf6903c26795a`. PRs #179/#193/#150/#183 draft and unmerged. PR #30 closed unmerged; no approved integration base.

## One bounded executed independent provenance audit
The prior UTC06 V2 checker validates `metadata.capture_sha256` as 64 hexadecimal characters only. It never hashes actual raw capture bytes or checks that JSON events match those bytes. In a disposable Python harness, four otherwise-safe synthetic mutations per board (coin timestamp, poll timestamp, raw CSV sample, claimed digest) remained **V2 FORMAT PASS** despite inconsistent capture identity. This is a **test/evidence false-pass**, not a production firmware exploit.

V3 test-only checker adds independently supplied raw CSV byte hashing, digest comparison, strict CSV schema and parsed-sample equality. `python3 -m py_compile` PASS; `python3 -m unittest -v test_trace_gate_v2.py test_trace_gate_v3.py` **7/7 methods PASS**, 2/2 board positive controls, **8/8** V2 false-passes reproduced and rejected by V3, **8** malformed raw inputs rejected, and CLI exit codes 0 (format pass), 2 (format fail), 3 (invalid setup) exercised. Reproducible conversation-local ZIP SHA-256 `3286fa7bc492b2971f648e52ab34f5e1c3d726e210048e94f124cd61420864fc` (not a GitHub artifact).

**Limits:** Raw CSV and JSON were both locally synthesized; a party able to rewrite both can still create a consistent false trace. Self-asserted `capture_origin`, clock, board, and resolution are NOT authenticated. V3 is a byte-consistency **format preflight only**, not signed independent measurement, actual electrical relay acceptance, hardware power-cut evidence, or firmware durability. MASTER/CORE must approve independently retained raw analyzer bytes, calibrated channel wiring, capture custody and signed manifest before any owner-authorized isolated hardware test.

## Next exact action
MASTER/CORE review raw-capture custody/attestation and authenticated firmware config-revision/cold-start antirollback; VERIFY retains draft #193 and real-source security REDs. Do not merge, flash, sign, migrate, release, or accept payment until #31/#32/#34/#43 and physical 150 cuts/30-device soak/witness gates are satisfied.
