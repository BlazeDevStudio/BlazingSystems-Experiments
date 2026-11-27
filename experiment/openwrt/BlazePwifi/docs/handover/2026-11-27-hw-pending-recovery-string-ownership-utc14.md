# PHX-HARDWARE — Pending-recovery host String ownership regression

**Date:** 2026-11-27 UTC14  
**PR:** [#361](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/361), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-pending-recovery-harness-module-split-20261127-utc13`  
**Parent:** #359 at `47357aab2ff7910b38ca538a46dfa01bdbca01e8`  
**Source/test commit:** `4a85070a1f6a1caa417570a91dcdf355ff072fcc`  
**Role:** PHX-HARDWARE

## Finding

The source-extracted `loadPending()` declares `BpPendingSequence r{}` locally, then copies `r.nonce` and `r.target` into Arduino `String` values. The host harness's fake `String` stored only the incoming pointer. After `loadPending()` returned, that pointer referenced expired stack storage. Existing tests checked sequence/filesystem state but did not read the nonce/target after return, so this harness-fidelity defect was invisible.

## Change

In `pending_recovery_promotion_lab_harness.hpp`:

- Replaced the borrowed `const char *` fake with an owning `std::string` value.
- Added `c_str()` and `length()` accessors matching the operations needed by the extracted function and assertions.
- Added identity assertions to all existing scenarios: successful canonical/new/backup recovery must preserve the expected nonce and target; ambiguous candidates, failed rename, invalid-only and empty-journal paths must not publish identity; legacy migration write failure retains the loaded identity while keeping `fsReady=false` and `pendingReady=true`.

No scenario count, extracted firmware body, production sketch, or firmware behavior changed.

## Exact-source CI

- Focused run [#46016953274](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953274), job `140566402392`: PASS.
- Mbed run [#46016953049](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953049): source-contract job `140566402516` PASS; core 3.3.13 job `140566402198` PASS; core 4.0.0 job `140566402334` in progress at checkpoint.
- Pre-sync Full run [#46016953164](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953164): mandatory handover freshness job `140566586511` failed because this source commit was not yet documented; CI-0701 passed and target jobs were still running. Post-sync Full rerun required.

## Ownership and safety

No production sketch/runtime, shared API, QA-owned assertion, finance, signer/witness, migration, COE source, or release workflow changed. Parent #359 remains deny-only. CORE owns authenticated register/poll and receipt/disposition; QA owns independent semantic assertions; MASTER owns stack integration and release gates.

**Evidence classification:** host-only SIMULATED / CI VERIFIED. Physical LittleFS, GPIO/relay/electrical acceptance, 150 controlled power cuts, and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.

No flash, reset, live money, production migration, merge, signing, release tag, or deployment.


## PHX-HARDWARE UTC14 — append-only ledger restoration correction

The first docs-sync commit `f1a4e36010572b59ce5576724dd18af480087e60` did not preserve the large `CHANGE_LEDGER.md`: the repository file-content response was empty for that oversized blob, and the commit temporarily replaced it with a 1,375-character append. The focused workflow caught this before merge at [#46017446457](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46017446457), job `140568087908` (`CHANGE_LEDGER_APPEND_ONLY_FAIL`, base 1,132,798 bytes vs candidate 1,377 bytes).

The complete ledger was recovered by exact blob SHA `19778170a05b3a71194ee29b23176ac398f28a29` from parent source/test commit `4a85070a1f6a1caa417570a91dcdf355ff072fcc`. Its text starts with the full base ledger from #354 at fc842342596786e072630179acfbbc4feeb2ba02 (blob `b950f7be47f79d71e6cb8b721801c1bae128df45`); prior #359 and #361 entries remain intact. A correction entry is appended to the recovered ledger. Exact byte-prefix verification is pending the new focused run.

The actual host-fixture correction at `4a85070a1f6a1caa417570a91dcdf355ff072fcc` remains unchanged. Focused source run #46016953274 PASS; Mbed run #46016953049 3/3 PASS. Pre-sync Full #46016953164 terminally failed at handover freshness (13 succeeded, 6 skipped, 9 cancelled, 1 validation failure); no Full PASS is claimed. Physical acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.


## PHX-HARDWARE UTC14 — terminal docs-head CI and append-only restoration proof

**Docs/evidence head tested:** `8b687a0407d8b53e8ae7213c7db05c7d89778501`  
**Source/test SHA:** `4a85070a1f6a1caa417570a91dcdf355ff072fcc`  
**PR #361:** OPEN / DRAFT / UNMERGED; child of #359 at `47357aab2ff7910b38ca538a46dfa01bdbca01e8`.

- Focused [#46017755525](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46017755525), job `140569149552`: **PASS**. Exact append-only proof: `CHANGE_LEDGER_APPEND_ONLY_PASS base_bytes=1132798 appended_bytes=24007`. Both ESP8266 and ESP32 source-extracted pending recovery harnesses report 11 scenarios, two rename-failure cases and ambiguous-candidate preservation. The host fake `String` now owns the nonce/target copy; identity assertions run after `loadPending()` returns. All emitted guard/source-mutation probes in the focused job passed.
- ESP32 Mbed TLS [#46017755424](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46017755424): **3/3 PASS** — source contract job `140569702266`, Arduino core 3.3.13 job `140569702224`, Arduino core 4.0.0 job `140569702049`.
- Full [#46017755412](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46017755412): **FAIL** at QA-owned Controller protocol parity, validation job `140569371672`, `tests/controllers.sh:21`, which requires the literal `config_revision` token in both sketches. CI-0701 job `140569287228` PASS; all 13 firmware target jobs and Android PASS; 13 downstream production/import/update/simulation/publication jobs SKIPPED. This is the existing token-presence assertion, not cryptographic response verification. No decoy token was added.
- The earlier docs sync `f1a4e36010572b59ce5576724dd18af480087e60` was rejected by the append-only guard because the oversized ledger file-content response was empty. The full original ledger was restored by exact blob read and the focused run above now proves the complete 1,132,798-byte base prefix is preserved with 24,007 appended bytes. The intermediate failure [#46017446457](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46017446457) remains transparently recorded; no merge occurred.
- Parent #359 Native [#45997708911](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708911) remains failed at QA-owned PAY-0745. No Native run was triggered for this test-harness-only increment.

**Scope:** host-test fixture only; no production sketch, shared API, QA-owned test, finance, signer/witness, migration, COE source, flash, reset, release or deployment changed. Physical LittleFS/electrical acceptance, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
