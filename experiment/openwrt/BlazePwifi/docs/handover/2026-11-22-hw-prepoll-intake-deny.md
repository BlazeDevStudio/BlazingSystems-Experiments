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

## UTC02 continuation — ESP32 Mbed TLS 4 SHA-256 compatibility (2026-11-22)

**Final source/test head:** `4eefce64719f40fd30621296db7c3fa764a44f1a`  
**PR:** #340 remains OPEN / DRAFT / UNMERGED; base remains #283 at `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`.  
**Branch:** `phoenix/hardware-prepoll-intake-deny-20261122-utc01`.

### Defect and correction

The current #340 ESP32 sketch inherited an unconditional `<mbedtls/sha256.h>` include. The Full run [#44971548978](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44971548978) failed in ESP32 compilation because Mbed TLS 4 no longer exposes the legacy SHA module header/API.

The test-first source guard was added before the firmware correction:
- Test-only lab commit: `9a8655494434ea169980e0322e91e699f6971f73`.
- Exact failing guard: [#44978244522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44978244522), job `137072842418` — RED because the version-gated provider was absent.
- Firmware correction: `fac21e9591dc948ef9172e3a83507e81122a321a`.

The ESP32 sketch now:
- selects PSA Crypto (`psa_crypto_init` / `psa_hash_compute`) for Mbed TLS 4;
- selects the legacy `mbedtls_sha256_*` API for Mbed TLS 3;
- rejects unsupported major versions at compile time;
- checks provider status and exact 32-byte digest length;
- validates a 64-character hexadecimal digest before recording `lastSentNonce`;
- returns before HTTP/network I/O if signing fails or produces an invalid/empty body.

The existing POST allowlist remains register/poll only. No coin POST, positive coin admission, relay enable, replay acceptance, or response-signature contract was added.

The source guard was tightened after an intermediate over-specific function-signature extractor failed; the final test harness is at the final head above. It includes failure injection for missing PSA status/length checks, missing legacy status check, missing invalid-digest denial, and missing empty-request denial.

### Exact-head CI evidence

- Mbed TLS SHA-256 source guard: [#44978514982](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44978514982), job `137073679458` — PASS; mutation cases rejected.
- Duplicate exact-head source-guard run: [#44978512033](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44978512033), job `137073669052` — PASS.
- Poll preflight deny lab: [#44978514971](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44978514971), job `137073679224` — PASS.
- Quarantine append/readback lab: [#44978514968](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44978514968), job `137073679496` — PASS.
- Full exact-head build/validation: [#44978514967](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44978514967) — terminal SUCCESS, 26 successful jobs, 4 production import/sign/publish jobs SKIPPED, no failed jobs.
  - ESP32 compile job `137073898355` — PASS.
  - ESP8266 compile job `137073898400` — PASS.
  - Validation job `137073898443` — PASS, including accounting integration x3 and persistence/replay stress x3.
  - 14/14 target/platform build jobs — PASS.
  - Update bundle, browser, Ruijie, x86, Orange Pi and ESP simulations — PASS.
  - Candidate gate job `137075240185` — PASS.
  - Production signed-APK import, production sign handoff, prerelease publish and release publish — SKIPPED.

These results are CI/build and simulation evidence only. The focused source guard is static; it does not execute a real PSA crypto provider. The Full workflow used the current Arduino ESP32 core; a separate exact-head Mbed TLS 3.3.13 compile has not yet been run on #340.

### Parallel audit and boundaries

- #283 remains an independent parent candidate. The failed quarantine append is guarded before `clearPending()`, but `quarantinePending()` still has no active callsite; complete quarantine lifecycle is not established.
- Current main register/poll responses still do not expose the authenticated `response_sig` required by the older positive fixture. Keep coin admission deny-only; CORE owns the response/receipt contract and QA owns fixture reconciliation.
- #254 remains at its independently revalidated head `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; its Mbed TLS 4 build issue was not modified by this #340 change. Master should decide whether to port the proven provider selector or keep the lab stack isolated.
- Primary poll/edge stack #327→#339 remains separate; #340 is a child of #283, not a replacement or retarget.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains BLOCKED: no Google Drive connector is exposed and the exact v11 file is absent from the available Library listing. No older registry was substituted and no Drive upload/readback is claimed.

### Next exact action

PHX-MASTER refreshes its role/integration pins to #340 final head `4eefce64719f40fd30621296db7c3fa764a44f1a` and confirms whether the Mbed TLS selector should be ported to #254. PHX-HARDWARE's next scoped task is an exact-head ESP32 core 3.3.13 compile for #340, preserving the #283 ancestry and all deny-only behavior.


## UTC03 continuation — pinned Arduino ESP32 core 3.3.13 compile

**Final workflow commit:** `e4af707ee6774441c17b53eb4d1e6ec6fbc21f0e`  
**Final PR #340 head:** `e4af707ee6774441c17b53eb4d1e6ec6fbc21f0e`  
**PR:** #340 OPEN / DRAFT / UNMERGED; base remains #283 at `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`.  
**Branch:** `phoenix/hardware-prepoll-intake-deny-20261122-utc01`.

### Added exact-version compile workflow

Added `.github/workflows/phx-hw-esp32-core-3.3.13-compile.yml`. It:
- verifies the checked-out commit equals the event SHA;
- installs exactly `esp32:esp32@3.3.13` (the package index reported 4.0.0 as latest, but 3.3.13 was installed);
- runs the existing Mbed TLS 3/4 fail-closed source and mutation guard;
- compiles the actual ESP32 Vendo sketch for `esp32:esp32:esp32`;
- requires a nonempty `.bin` and prints its SHA-256;
- retains read-only contents permissions and does not upload or publish a release artifact.

Two early workflow attempts failed before compilation because the optional version-header probe assumed a package filesystem path/format that was not portable:
- `87cc5677b421deda8721a118961138659b48feb7`, run [#44979951013](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44979951013), job `137078057356`: header-path/version probe failed; compile skipped.
- `d1f7f1936b0e7d2f85a00f14af9b193b1f4ea199`, run [#44980120953](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44980120953), job `137078587110`: same brittle probe failed; compile skipped.

These were workflow-probe failures, not firmware compile failures. The path-specific probe was removed; the exact core install, existing dual-provider source guard, and real sketch compile remain.

### Final exact-head compile evidence

[Arduino ESP32 core 3.3.13 run #44980286970](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44980286970), job `137079089915`, **SUCCESS** on exact workflow/PR head `e4af707ee6774441c17b53eb4d1e6ec6fbc21f0e`.

- Exact checkout SHA check: PASS.
- `esp32:esp32@3.3.13` installation and installed-version assertion: PASS.
- Existing provider/failure-injection guard: PASS; mutations rejected for missing PSA status/length check, missing legacy status check, missing invalid-digest denial, and missing empty-request denial.
- Actual ESP32 Vendo sketch compile against core 3.3.13: PASS.
- Compiler size: 1,028,936 bytes (78% of 1,310,720-byte program storage); global variables 49,456 bytes (15% of 327,680-byte RAM).
- Generated CI binary SHA-256: `e1c531a7ad914f1250b509f3aa5f9d875fd7b9ba7d334cf2a005b5a4c8daab52`.
- Workflow log explicitly prints `SIMULATED_ONLY=1` and `PHYSICAL_ACCEPTANCE=0`.

The optional header-path probe was removed, so this run does **not** independently report the bundled Mbed TLS major. It does prove the current sketch compiles under the pinned Arduino ESP32 core 3.3.13. The existing static source guard checks both Mbed TLS 3 and 4 code paths; this is not a substitute for a separate real provider test or physical board acceptance.

The last completed Full integration run for the firmware source/test head `4eefce64719f40fd30621296db7c3fa764a44f1a` remains [#44978514967](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44978514967): 26 jobs successful, with four production import/sign/publish jobs skipped. A later Full run on workflow-only commit `87cc5677...` was cancelled during subsequent branch updates; no new Full integration conclusion is claimed for `e4af707...`.

### UTC03 disposition

The exact Arduino ESP32 core 3.3.13 build is **CI VERIFIED**. No firmware source, controller API, poll contract, coin admission, finance, signer/witness, QA-owned test or Release-owned workflow was changed. PR #340 remains DRAFT and unmerged. Physical coin/relay/electrical acceptance, 150 power cuts and 30-device/24-hour soak remain **NOT TESTED**; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.


## UTC03 continuation — pinned ESP8266 Arduino core 3.1.2 compile

**Updated:** 2026-11-22T03:48:56.350Z  
**PR #340 branch HEAD at source/test verification:** `e03c2347edeb2627862f9477da9db656768e9ce1`  
**PR #340 base:** #283 at `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`

### Added workflow

`.github/workflows/phx-hw-esp8266-core-3.1.2-compile.yml` pins the ESP8266 Arduino core to 3.1.2, verifies the exact PR checkout SHA, runs the source-extracted pre-poll deny/failure-injection lab for both board sketches, compiles the actual ESP8266 Vendo sketch for `esp8266:esp8266:nodemcuv2`, requires a nonempty binary, and prints its SHA-256. It has `contents: read` only and does not upload or publish artifacts. The pinned version matches the upstream ESP8266 Arduino Core 3.1.2 documentation: https://arduino-esp8266.readthedocs.io/en/3.1.2/.

An initial workflow draft contained over-escaped shell continuations; source readback caught it before a passing run was claimed. The shell escaping was corrected in the final workflow commit below.

### Exact-head CI evidence

- Workflow/source commit: `e03c2347edeb2627862f9477da9db656768e9ce1`.
- [ESP8266 core 3.1.2 run #44982146103](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44982146103), job `137084756167`: **SUCCESS**.
- Exact checkout assertion: PASS.
- Pinned `esp8266:esp8266@3.1.2` installation and version assertion: PASS.
- Source-extracted pre-poll deny lab: PASS for ESP8266 and ESP32; deny-removal and pre-poll-order mutations rejected on both boards.
- Actual ESP8266 Vendo compile: PASS.
- RAM: 31,368 / 80,192 bytes (39%).
- IRAM+reserved instruction cache: 60,535 / 65,536 bytes (92% total report; 27,767 bytes IRAM code plus 32,768 bytes cache reservation).
- Flash code: 313,872 / 1,048,576 bytes (29%).
- CI binary SHA-256: `1712b6235c7b8b96813dfc1ea49750f4c4d904b0c15fbb98ff39379fd637ddf0`.
- Log flags: `SIMULATED_ONLY=1`, `PHYSICAL_ACCEPTANCE=0`.

The core's bundled `elf2bin.py` emitted Python invalid-escape SyntaxWarnings; the build still completed successfully. No firmware source/runtime, controller contract, coin admission, finance, signer/witness, QA-owned tests, or Release-owned workflow was changed.

### Same-head companion runs

- [Poll preflight inhibit #44982146089](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44982146089): SUCCESS.
- [Mbed TLS provider guard #44982146096](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44982146096): SUCCESS.
- [ESP32 core 3.3.13 compile #44982146100](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44982146100): pending at this checkpoint.
- [Full BlazePwifi build #44982146097](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44982146097): in progress at this checkpoint; no aggregate result claimed.

### Remaining boundaries

This establishes a reproducible ESP8266 core compile, not physical board acceptance. Physical coin/relay polarity, electrical pulse/recovery, LittleFS power-loss durability, 150 power cuts, 30-device/24-hour soak, protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay, and independent QA/Release acceptance remain NOT TESTED or NOT ESTABLISHED. The main controller register/poll response contract remains CORE-owned and unresolved; coin admission remains deny-only.

**Next exact action:** PHX-HARDWARE checks the terminal state of #44982146100 and #44982146097 on the same source SHA; PHX-MASTER refreshes the role/integration matrix to include the current #340 child of #283 without conflating it with #327→#339.
