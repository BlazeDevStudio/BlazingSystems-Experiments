# PHX-HARDWARE UTC23 — C++ CRLF line-splice parity guard

Observed: 2026-11-25T23:50Z
Role: PHX-HARDWARE
Repository: BlazeDevStudio/BlazingSystems-Experiments
PR: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349
Branch: phoenix/hw-json-array-primitive-guard-20261124-utc00
Base branch: phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13
Captured base SHA: 960184670379f01e20f0e7e8bc23b3e5eedacd3f

## Selected task and defect

This is a host-side C++ token-normalizer correction used by the ESP8266/ESP32 bounded-response source-parity lab. The scanner previously recognized backslash-LF line splices in // comments but not backslash-CRLF. A CRLF-continued comment could therefore be normalized as if the following source line were ordinary code, allowing two semantically different function bodies to compare equal.

A local C++17/GCC runtime fixture confirmed the semantic difference: in the backslash-CRLF case, the first return remains in the continued line comment; in the ordinary CRLF case, it executes. The pre-fix normalizer produced identical token sequences for both.

## Exact source and test commits

- Test-only RED commit: 62f7813ef482e7ac9bc0d2010f8f7e2113cf29ef.
- Source correction commit: 9dc0ae39832e5fe7db79694b670a841f0c90ffe0.
- The new regression is test_crlf_line_splice_continues_line_comment in cpp_token_normalizer_contract_lab.py.
- The source adds _has_backslash_line_splice_before_lf(), recognizing both backslash-LF and backslash-CRLF, and uses it in the // comment scanner.
- Existing literal, preprocessing-number, raw-string, and punctuation token rules remain unchanged.

## Test-first RED

- Relay run: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45723546132
- Job: 139587561096, exact test SHA 62f7813ef482e7ac9bc0d2010f8f7e2113cf29ef.
- Expected failure: test_crlf_line_splice_continues_line_comment. The two token tuples were equal before the fix; 14 other tests passed.
- The assertion failure was the intended reproduction, not an unrelated compile failure.

## Exact-source GREEN

All following runs checked out source/test SHA 9dc0ae39832e5fe7db79694b670a841f0c90ffe0:

- Quarantine Byte Readback: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45723944288 — job 139588898662 PASS.
- Relay Output Polarity: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45723944279 — jobs 139588898747 and 139588899114 PASS.
- Logs report CPP_TOKEN_NORMALIZER_CONTRACT_PASS 15/15 and BOUNDED_HTTP_RESPONSE_TOKEN_NORMALIZER_PASS 8/8. Existing both-board source/polarity mutation checks passed.
- Local mirror of the 15-test contract suite: 15/15 PASS; Python bytecode compilation PASS; C++17 CRLF semantic fixture PASS.

## Full integration status

- Full BlazePwifi run: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45723944321.
- Validation job 139589011037 FAILS at the inherited “Missing poll signature check” in the active ESP8266 sketch.
- All 14 listed firmware target jobs and Android PASS on this SHA.
- Production import/sign handoff, simulations, candidate gate, prerelease and release publication were skipped. No Full integration PASS is claimed.

## Scope and safety

Only the Hardware-owned host normalizer, its contract lab, and this handover plus PROJECT_HANDOVER.md changed. No production .ino sketch, CGI producer, shared CORE API, financial state, key provisioning, signer, witness, migration, COE destination or release artifact changed. No secrets, live money, physical flash, device reset, production migration, merge or deployment.

Evidence classification: SIMULATED / CI VERIFIED only. Physical coin pulse, relay/electrical recovery, LittleFS power-cut durability, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.

## Cross-role blockers revalidated

- Master UTC23 report: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/223f7fdcfc15849a97bf54d25cb87875fd7248d6/coordination/phoenix/PHX_MASTER_UTC23_20261125_HW348_MBEDTLS4_COE35_EXACT_HEAD_AUDIT.md
- The active v0.6 audit branch remains 2fbd2475e9f54878c316fa7cea2f228386b0e859. Its ESP8266 and ESP32 poll paths still consume unsigned insert/target_nonce and call applyRemoteConfig; the current producer response lacks an approved response_sig. Master also identified the empty-key verification skip and default-enabled top-level config as a P0 trust-boundary issue. This host normalizer task does not fix that.
- CORE must publish the versioned authenticated response schema, standard HMAC construction, canonical serialization, controller/target binding, nonce/freshness rules and key-provisioning contract. HARDWARE must then implement the approved mandatory-key and full-envelope deny path; QA must supply independent negative vectors.
- Master UTC23 separately assigned Hardware to synchronize #348 canonical handovers (PROJECT_HANDOVER.md, CURRENT_STATE.md, CHANGE_LEDGER.md) with #348 head ed172016 and runs #45716221522/#45716221609. That is a separate pending task; no #348 files were modified here.
- #266 remains OPEN / 0-of-7. #239/#254/#283 and the #340/#352/#353 ancestry constraints remain unmerged and owner-controlled.

## Registry and next action

Private Google Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json was not recovered; no Google Drive connector is exposed. Older Library snapshots were not substituted.

Next exact action: synchronize #348's three canonical handovers per Master UTC23, then coordinate the mandatory-key/authenticated-envelope implementation with CORE and QA before touching production firmware. Master must retain stack ancestry decisions.