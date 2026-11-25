# PHX-HARDWARE handover — C++ preprocessing-number normalizer extraction

**Updated:** 2026-11-25 UTC10  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Control plane:** [Issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Hardware task:** [Issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [Issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** [`fc4ce808`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/fc4ce8084c8465a75d5c3418bac5a268e49a4ae3)

## Selected task and reproduced defect

The token-aware board-parity scanner introduced at source/test `9b20d0a6e520d78423250636b3ea0fe983b35294` preserved identifiers, punctuation, ordinary/raw/escaped literals and comments, but its number scanner stopped before an exponent sign. As a result:

- `1e-3` became number `1e`, punctuation `-`, number `3`;
- `0x1.fp-2` became number `0x1.fp`, punctuation `-`, number `2`;
- `1e-3` and `1e - 3` normalized to the same token sequence, despite different C++ tokenization.

This could make the Hardware-owned ESP8266/ESP32 source-parity guard miss a real lexical difference. This is a host-test defect, not a discovered production-sketch behavior defect.

## Test-first evidence

Test-only commit [`ccdfdc45`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ccdfdc45f3fdbff326928caf2efd3bd86bc40a64) added five exponent/token-boundary contracts and wired them into the focused workflows.

- Quarantine RED [#45598286371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45598286371), job `139150080528`: expected 3 failures (decimal exponent, hexadecimal exponent, whitespace-before-sign distinction); 2 existing controls passed.
- Relay RED [#45598497125](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45598497125), job `139150814811`: same 3 expected failures.
- The first Relay push run [#45598283336](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45598283336) exposed a YAML indentation error in the newly added multiline step (zero jobs). The workflow block was corrected at [`d31fa218`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/d31fa21808c8d0b21cb1ae38359cd6f5acd06685) before the valid Relay RED run. No product source was affected by that intermediate workflow error.

## Source correction and modularization

Source/test commit [`fc4ce808`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/fc4ce8084c8465a75d5c3418bac5a268e49a4ae3):

- Added `cpp_token_normalizer.py` as a dedicated, pure lexical-normalization module.
- Moved the 139-line C++ token scanner out of `bounded_http_response_lab.py`; the runner is 139 lines shorter and now imports `tokenize_cpp()`.
- Added a bounded preprocessing-number scanner that consumes `+` / `-` only after `e/E/p/P`, keeping decimal and hexadecimal exponents atomic while preserving digit separators and ordinary arithmetic operators.
- Kept malformed block comments, quoted literals and invalid/unterminated raw strings fail-closed.
- Expanded `cpp_token_normalizer_contract_lab.py` to 11 focused contracts covering decimal/hex exponents, whitespace token boundaries, digit separators, arithmetic operators, raw-string payloads, comment boundaries, malformed literals/comments and longest-match punctuators.
- Both Quarantine and Relay workflow path filters now include the normalizer module and contract lab, and both run the contract lab before the bounded HTTP board-parity lab.

No production `.ino`, CGI producer, shared controller API, coin disposition, relay actuation, financial state, signer, witness, migration or COE destination was changed.

## Exact-source CI evidence — SHA `fc4ce8084c8465a75d5c3418bac5a268e49a4ae3`

- Quarantine [#45599003730](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45599003730), job `139152588586`: **PASS**. Markers include `CPP_TOKEN_NORMALIZER_CONTRACT_PASS 11/11`, bounded-response normalizer 8/8, board parity PASS, parity mutations 10/10, source-extracted quarantine scenarios 36/36, and append/clear failure-injection preservation on ESP8266 and ESP32.
- Relay [#45599003585](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45599003585), source/output job `139152587841` and ESP32 boot job `139152588175`: **PASS**. Normalizer 11/11, bounded-response contract 8/8, board parity 10/10 mutations rejected, bounded HTTP allowed 3 / denied 9 on both boards.
- Full BlazePwifi [#45599003619](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45599003619), validation job `139152588712`: **FAILED** at Controller protocol parity / inherited `Missing poll signature check`. All 13 firmware/platform targets plus Android completed **14/14 PASS**. Downstream simulations, update bundle, candidate, signing and publication jobs were skipped after validation failed.

These are host/source-extracted CI simulations, not physical board acceptance. Logs explicitly retain `SIMULATED_ONLY=1` and physical coin/relay/power-cut flags at zero.

## Revalidated adjacent Hardware trust-boundary leads

PR [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) remains OPEN / DRAFT / NO-GO at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`.

- On both current sketch blobs, `quarantinePending()` checks `appendQuarantineRecord(reason)`; append failure returns false before `clearPending()`. The helper is definition-only at this head (no active callsite). The earlier claim of unconditional clear after failed append is therefore **not present in the current source**, but no durable end-to-end quarantine acceptance is inferred.
- Current main CGI blob `2e3a1430d08cc6606429a042df3b5848f53c7267` emits no `response_sig` in register/ping or poll responses. Its other member endpoints do contain signature-related fields; that does not satisfy the register/poll contract.
- Both sketches continue to ignore register/poll response fields and deny remote control. No signature bypass or positive coin authority was added.

Protected draft pins revalidated: #239 `d83b715b116185107737fef721c2eece8feebf39`; #254 `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; #283 `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`; #340 `38f3e9419f37109443c806a2362577d9efc50e4d`; #347 `960184670379f01e20f0e7e8bc23b3e5eedacd3f`; Master #288 `025aadaa71aadf7fc09d53e0b623356c5550fe17`. No stack was retargeted or rebased.

## Production evidence classification and blockers

- C++ token normalizer + focused source-extracted contracts: **CI VERIFIED**.
- Board behavior in the host labs: **SIMULATED / CI VERIFIED ONLY**.
- Local independent full suite: **NOT RUN**.
- Physical coin pulse, relay contacts, electrical recovery, LittleFS/EEPROM power-loss: **NOT TESTED**.
- 150 controlled power cuts and 30-device / 24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release acceptance: **NOT ACCEPTED / PENDING**.
- P0 safety #34, finance #31/#32 and witness #43 remain OPEN.
- COE integration PR #26 remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`, based on COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`. No source promotion occurred.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed connected sources; only older Library snapshots were found. No older registry was substituted.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

## Next exact actions

1. **PHX-MASTER:** refresh the current #349 source/test and handover pins in the owner matrix; reconcile #340/#283 ancestry without unauthorized retargeting.
2. **PHX-CORE:** publish the approved authenticated register/poll response contract and canonical golden vectors.
3. **PHX-QA:** independently reconcile the Full validation signature assertion without weakening deny-default.
4. **PHX-HARDWARE:** on the next activation, revalidate live branch heads and choose one new unblocked Hardware-owned task.

No flash/reset, physical power interruption, live money, production migration, signer provisioning, merge, release tag or deployment occurred.


## Post-commit live-ref reconciliation (2026-11-25 UTC10)

A second live read after the source/test CI completed found the repository default branch had advanced beyond the historical pins in the current Master audit:

- Experiments owner is \`BlazeDevStudio\`; current \`main\` is \`6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5\` (commit time 2026-11-25T09:29:55Z).
- The named development line is \`blazepwifi-v0.5.3-development\` at \`aad3aade72c1156eecba1fed30907c6d0283b2c5\`; there is no branch literally named \`development\`.
- COE main remains \`a6513ab4412b4c014eee2863e45cbe32d06cb243\`; COE #26 remains OPEN / DRAFT at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`, base main \`a6513ab...\`.
- Hardware stack pins: #239 head \`d83b715b116185107737fef721c2eece8feebf39\`; #254 head \`84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9\` and its base equals #239 head. GitHub compare confirms #254 head is 17 commits ahead of the supplied #254 cleanup commit \`3692ddf889470da8a002e9a16bf0ac2f37f1a9d0\` with zero commits behind.
- #283 head / cleanup branch \`4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30\` still uses main base \`f4e8a891...\`, while current main is \`6be5d19b...\`.
- #340 head \`38f3e9419f37109443c806a2362577d9efc50e4d\` still declares cleanup base \`88581eef...\`, while that cleanup branch currently resolves to #283 head \`4dd0b01b...\`.
- #347 base branch currently resolves to \`ca72497ed386c9ac4e50d3f811827bef51e296ad\`, matching its declared base; #347 head \`960184670379f01e20f0e7e8bc23b3e5eedacd3f\` matches #349's declared base.
- Master #288 head is \`025aadaa71aadf7fc09d53e0b623356c5550fe17\`, but its base is still \`f4e8a891...\`, not current main \`6be5d19b...\`. Hardware did not retarget, rebase or merge any of these stacks.

The current main CGI blob is \`2e3a1430d08cc6606429a042df3b5848f53c7267\`; exact \`register|ping\` and \`poll\` response bodies still have no \`response_sig\`. This revalidates the Full integration blocker; no producer contract was changed by Hardware.

The root repository README at current main still links the old \`BlazingSystems\` organization profile/projects/labs/archives. GitHub owner and repository URLs now resolve under \`BlazeDevStudio\`; this is a Master/maintainer documentation cleanup request, not a Hardware-owned edit. The BlazePwifi README still describes a 0.3.0 production release, which must not be confused with current Phoenix production acceptance.

**Coordination request:** PHX-MASTER must reconcile the stale #288/#283 main bases and #340 cleanup base, refresh the live role matrix, and decide any authorized retarget/rebase sequence. Hardware made no such change.
