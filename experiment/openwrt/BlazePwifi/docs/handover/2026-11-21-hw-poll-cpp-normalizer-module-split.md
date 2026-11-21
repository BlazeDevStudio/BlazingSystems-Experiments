# PHX-HARDWARE — poll-loop C++ normalizer module split (UTC22)

**Disposition:** PR_READY · FOCUSED CI VERIFIED at source/test SHA · Full integration blocked · SIMULATED ONLY · PRODUCTION NO-GO  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments (repository ID 1389289885)  
**PR:** [#338](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/338) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-poll-normalizer-module-20261121-utc22`  
**Parent:** PR #337 at `378fc605673b43d34e6bb43642c8405e31f43840`  
**Source/test SHA:** `237169157dffc0843767d3be8ddbf57580fee33f`  
**Base:** #337 branch `phoenix/hardware-poll-lab-parity-module-20261121-utc21`

## One bounded cleanup task

The 332-line `poll_loop_blocking_inhibit_lab_parity.py` mixed:
1. C++ token-aware whitespace normalization and its 10-case self-test.
2. ESP32/ESP8266 shared-helper parity and fail-open mutation guards.

The source/test commit moved `normalize_cpp_function_body()` and `verify_cpp_parity_normalizer()` into the adjacent `poll_loop_blocking_inhibit_lab_normalizer.py`. The parity module now imports only the normalization primitive it needs; the runner imports and executes the normalizer self-test separately before board parity and scenario tests.

- Runner: 388 lines (unchanged).
- Parity module: 332 → 206 lines.
- New normalizer module: 133 lines.
- The 10 normalization cases, 23 shared-helper parity checks, six quarantine-helper parity checks, two drain-abort polarity cases and existing mutation/failure-injection paths are retained.
- Only the host-lab runner/parity modules changed. No ESP sketch, controller/API, finance/ledger, signer/witness, GPIO/relay runtime, QA-owned assertion, workflow policy or Release path changed.

## Exact-source focused CI at `237169157dffc0843767d3be8ddbf57580fee33f`

- Quarantine Byte Readback [run #44958345073](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44958345073), job `137011359018`: **SUCCESS**.
- Relay Output Polarity [run #44958345168](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44958345168), job `137011359291`: **SUCCESS**.
- Relay ESP32 boot-polarity job `137011359000`: **SUCCESS**.

Observed exact-source markers:
- C++ normalizer self-test: 10/10.
- Shared ESP32/ESP8266 helper parity: 23/23.
- Quarantine helper parity: 6/6.
- Drain-abort polarity fixture: 2/2.
- Poll/coin mutation probes reject removal of pre-poll inhibit, edge-count/wrap guards, ISR attachment, active-high/active-low polarity, journal recovery deny, pending marker checks, quarantine append/readback, coin disposition and positive poll admission.
- Both board coin-pulse capture suites report 17/17.
- Poll response fail-closed fixtures report 11/11 per board; strict root JSON 13/13 per board; coin POST ACK root status 4/4 per board; poll response fixture boundary 4/4.
- The 1501/1600/1680 ms #177 timeline and 3500 ms blocking timeout guard remain present.

These are source-extracted host simulations and CI checks, not physical coin/relay/flash evidence.

## Full integration disposition

- Push Full [run #44958326800](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44958326800), validation job `137011306511`: **FAILURE** at inherited `tests/controllers.sh` assertion `Missing poll signature check` for the ESP8266 sketch.
- PR Full [run #44958344981](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44958344981), validation job `137011358905`: same **FAILURE**.
- The target matrix was still queued/in progress when this handover was written; do not claim 14/14 target completion from these runs.
- Downstream browser/candidate/signing/publication jobs are skipped after validation failure.

The current main CGI producer does not emit `response_sig` in `register|ping` or `poll` replies. PHX-CORE owns the canonical response contract and PHX-QA owns the stale positive presence assertion. Do not invent a signature or weaken default-deny admission to make Full green.

## Current #283 audit reconciliation

At live PR API head `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`, both sketches now guard `clearPending()` behind successful `appendQuarantineRecord()`; the append checks write length and readback; `POST /quarantine/clear` returns 403. `quarantinePending()` is definition-only with no active callsite. These source findings do not prove reboot durability or an active lifecycle. The PR body head pin is stale and Master was asked to reconcile it.

## Remaining gates and blockers

- Physical 150 power cuts, 30-device/24-hour soak, electrical pulse and relay recovery: NOT TESTED.
- Protected anti-rollback signer/witness: NOT ESTABLISHED.
- v1→v2 financial migration, durable accounting and replay: NOT TESTED / NOT ESTABLISHED.
- Independent QA and Release signoff: PENDING.
- Master role map/integration matrix/#172 still omit the current #335→#336→#337→#338 cleanup child chain and contain stale PR head pins; Master was asked to refresh them.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not returned by Library search and no Google Drive connector was exposed. Older registry snapshots were not substituted.

No physical flash/reset, live coin/money operation, production migration, signing, merge, release tag or deployment occurred.
