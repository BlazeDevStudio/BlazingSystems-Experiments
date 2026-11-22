# PHX-HARDWARE handover — pre-poll coin-intake deny guard

**Updated:** 2026-11-22T01:30:00Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Issue:** [#177 — preserve coin-line edges during synchronous poll](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/340) — OPEN / DRAFT / UNMERGED  
**Parent PR:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-intake-deny-20261122-utc01`  
**Base:** #283 at `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`

## Parallel-candidate hardening (not the primary #177 fix)

The current #283 candidate already denies all remote actuation and keeps coin POST/retry/clear disabled. Its `loop()` still called the synchronous `post("poll")` before reasserting `denyRemoteControl()`. The deny state was established at setup/register, but the local poll block did not explicitly enforce that invariant immediately before its bounded HTTP wait.

This child makes the precondition local and auditable on both boards. It does **not** enable coin intake or claim to preserve/credit an untrusted pulse.

**Important lineage correction:** the live Hardware child chain #327 → #329 → #335 → #336 → #337 → #338 → #339 already contains the primary source-level #177 poll-window/edge-reconciliation implementation. At current #339 head `3538ee67c55f14776c3406bdd33496f7b411b26e`, both sketches use `pollIntakeSuspended`, `beginPollWindow()`, ISR `coinEdgeSequence`, post-drain/post-poll edge reconciliation, `latchPollPulseFault()`, `sampleCoinPulseEdge()`, and deny-only `acceptPollResponse()`. The active chain's host lab executes the extracted production `loop()` and covers the original 1501/1600/1680 ms timing and unsafe-inhibit mutation; exact focused run #44968896770 / job 137044089088 passed. Its Full run #44968896799 / validation job 137044090062 remains blocked by the QA-owned `Missing poll signature check`. PR #340 is only a defense-in-depth pre-poll deny on the separate, main-based #283 deny-only candidate; it is not a replacement for, or an integration of, the #327→#339 pulse-capture work. Keep both lineages separate pending PHX-MASTER sequencing/reconciliation.


## Source changes

Both sketches now call the existing `denyRemoteControl()` immediately before `post("poll")`, while retaining the post-poll deny:

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`

The existing deny function clears controller/coin/relay/LED permission, clears `insertMode` and `activeTarget`, and calls `applyOutputs()`. The existing output function has an explicit relay-off branch for both active-high and active-low polarity. Pending journal evidence is not cleared.

Source commits:
- ESP8266 pre-poll deny: `35aded4e54f247466b7b01472a462a8f2af950eb`
- ESP32 pre-poll deny: `1909037f121b0615fd0dcfcebdd8a004b436b959`

## Source-extracted regression

Hardware-owned lab:
`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab.py`

The lab:
- extracts the actual `applyOutputs()` and `denyRemoteControl()` function bodies from both sketches;
- checks a deny call before the synchronous poll and a second deny after it;
- checks that ordinary coin sampling remains after the blocking poll call;
- compiles the extracted functions with C++17 and checks active-high/active-low relay-off behavior;
- injects a mutation removing all four actuation-deny assignments and requires the relay-state harness to reject it;
- injects a mutation removing the pre-poll deny and requires the source-order guard to reject it.

The initial parent-source RED was reproduced locally on both ESP8266 and ESP32: `coin intake is not denied before blocking poll`.

After the firmware changes, local host execution passed:
- pre-poll guard: 2/2 boards;
- active-high/active-low GPIO model: 2/2 polarities per board;
- actuation-deny mutation rejected: both boards;
- missing-pre-poll-order mutation rejected: both boards.

Observed classification: **SIMULATED / LOCAL HOST VERIFIED**. The lab explicitly prints physical coin/relay and power-cut acceptance as 0.

## Workflow

The existing Hardware-specific `.github/workflows/phx-hw-quarantine-append-readback.yml` now invokes the new lab. A separate Hardware-only exact-source workflow was also added:

`.github/workflows/phx-hw-poll-preflight-inhibit.yml`

Both workflows use read-only contents permissions and exact checkout verification. They are Hardware lab workflows, not Release build/signing workflows.

**GitHub Actions evidence:** no workflow run/job has yet been returned for PR #340's non-default stacked base. The exact source-extracted lab was executed locally against the exact relevant function and loop excerpts read back from PR #340's source commits. Do not label this CI VERIFIED until a GitHub Actions run/job reports the exact SHA.

## Contract and safety boundary

- No register/poll response signature or shared API was invented.
- No positive admission, remote configuration, coin POST, retry, replay, pending clear or quarantine lifecycle was enabled.
- CORE still owns the authenticated poll/configuration and event-bound receipt contracts; QA owns independent contract vectors.
- The pre-poll deny is fail-closed and remains in force after poll because no approved positive contract exists.

No QA-owned tests, financial backend, signer/witness, migration, Release build/signing workflow, or COE destination was changed.

## Exact PR #340 workflow evidence

At final source/docs HEAD `6ce3e9cc6f8f5f8dad76d9ec4a29bf9f15e26183`:
- Poll preflight workflow [#44970890745](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44970890745), job `137050199432`: SUCCESS; both boards passed pre-poll ordering and fail-open deny mutation rejection; SIMULATED_ONLY=1 and physical acceptance flags 0.
- Quarantine workflow [#44970890729](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44970890729), job `137050199437`: SUCCESS; existing append/readback, boot-recovery, clear/commit, clear-deny and pre-poll labs passed.
- Full BlazePwifi build [#44970890716](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44970890716): validation job `137050263334` PASS; ESP8266 job `137050263429` PASS; 13/14 target/platform jobs PASS. ESP32 job `137050263353` FAILS at the inherited missing `mbedtls/sha256.h` header. Production import/signing/publication and v0.4 ESP candidate gate were skipped. This is not a Full integration pass and is not a physical acceptance result.

## Remaining blockers

- CORE authenticated register/poll and event-bound coin receipt/disposition contract: NOT ESTABLISHED.
- Independent QA verification of positive/negative vectors: PENDING.
- Physical relay polarity and electrical pulse/recovery: NOT TESTED.
- Physical LittleFS durability and 150 controlled power cuts: NOT TESTED.
- 30-device / 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff: NOT ESTABLISHED / PENDING.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json`: not exposed by the available connector surface; no older registry substituted.

**Disposition:** bounded firmware pre-poll deny guard implemented; local source-extracted simulation passed; GitHub CI evidence pending; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.