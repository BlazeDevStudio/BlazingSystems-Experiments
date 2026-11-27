# PHX-HARDWARE UTC22 — correct deny-latch address detector positive control

**Recorded:** 2026-11-27T22:46Z  
**PR:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/367  
**Branch:** `phoenix/hw-deny-latch-monotonicity-20261127-utc21`  
**Source/test head at this checkpoint:** `83504c222c60e823e5883f814e28f9948a1f7702`  
**Tree restoration:** `f3988697ed960294bca1c849661a53ad0355b7b3`

## Exact-head failure and cause

After the complete parent tree was restored, the exact-head focused workflow [#46078329448](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46078329448), job `140771206739`, executed the real source lab and failed at `deny_latch_assignment_contract(source)` with:

`coinEnabled: address escape can bypass the deny-latch assignment guard`

The source contains the ordinary read-only expression `controllerEnabled && coinEnabled` in `applyOutputs()`. The original regex matched the second ampersand of logical conjunction as if it were address-of. This was a false positive in the new test guard, not evidence of a firmware pointer escape.

The same run independently passed the append-only ledger check (`base_bytes=1132798`, `appended_bytes=51959`) and all seven append-only guard unit tests before reaching the source-contract failure.

## Correction

- Contract commit: `e1e333bc8b8bc53f37eb1ff62c5a94573ed31b3f` — require a single ampersand not adjacent to another ampersand: `(?<!&)&(?!&)`.
- Test commit: `83504c222c60e823e5883f814e28f9948a1f7702` — add a dedicated `coinEnabled` address-of injection and a positive-control read-only logical-AND expression. Expected alias/address mutation count is now 5/5 per board.
- Production ESP8266/ESP32 sketches remain unchanged. No shared CORE API, QA-owned assertion, financial source, signer, witness, migration, release setting or COE source changed.

## Validation status

- Exact previous-head focused run #46078329448: **FAIL**, diagnosed above.
- Full and Mbed workflows at prior docs head `6fc779a7...` were separate runs and are not transferable to the new source/test head.
- Exact current source/test head `83504c2...`: await its own focused, Mbed and Full Actions results; do not claim green before terminal logs.
- Physical pulse/relay, electrical recovery, 150 power cuts, 30-device/24-hour soak: **NOT TESTED**.

## Repository integrity

The preceding tree-repair handover records restoration of the complete #366 base tree. This correction is committed on that restored branch; do not force-push or merge. PR #367 remains OPEN / DRAFT / UNMERGED.

**Disposition:** test-guard false positive corrected; coin and relay admission remain denied; production remains NO-GO.


## Exact-head revalidation — 2026-11-27T22:55Z

- Focused [#46078860359](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46078860359), job 140772887391: PASS at docs head `638444dfa4f36a0a38cac8d06fd31f07ce9b8228`. Both boards: 7/7 direct deny mutations rejected, 5/5 pointer/reference/address mutations rejected, logical-AND positive control accepted, register 8/8, poll transport 20 cases/board, append-only ledger guard and 7 ledger unit tests PASS.
- Mbed [#46078860303](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46078860303): source-contract 140773102073 PASS; core 3.3.13/4.0.0 target jobs still in progress.
- Full [#46078860354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46078860354): handover freshness gate PASS; QA-owned `tests/controllers.sh` fails on `config_revision` missing from both deny-only sketches. Main contains the token; candidate does not. All 14 target jobs PASS at last read; Full workflow still settling. No change to QA-owned test or production sketches.
- The current source/test SHA remains `83504c222c60e823e5883f814e28f9948a1f7702`; exact docs head tested was `638444dfa4f36a0a38cac8d06fd31f07ce9b8228`. Production remains NO-GO; physical acceptance NOT TESTED.
