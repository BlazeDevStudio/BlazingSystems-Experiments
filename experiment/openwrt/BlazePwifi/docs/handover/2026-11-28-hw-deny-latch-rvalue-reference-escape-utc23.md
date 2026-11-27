# PHX-HARDWARE UTC23 — deny-latch rvalue/decltype reference-escape coverage

## PHX-HARDWARE UTC23 — deny-latch rvalue/decltype reference-escape coverage

**Recorded:** 2026-11-27T23:34:21Z (2026-11-28 07:34:21 Asia/Manila)  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Main HEAD:** `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`  
**Branch:** `phoenix/hw-deny-latch-monotonicity-20261127-utc21`  
**PR #367:** OPEN / DRAFT / UNMERGED; stacked on #366 at `07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9`  
**Source/test SHA:** `1922dcba792aad40e576583db43de0d066522bf6`  
**Clarifying source-contract comment commit:** `d3fc76d76b97e8586837aaf70bb35fe602acc5d0`  
**Status:** COMMITTED_UNTESTED; isolated regex smoke SIMULATED; exact-head CI NOT RUN.

### Actual change

The deny-latch source contract previously missed reference-producing expressions whose source field was wrapped or parenthesized. It now rejects:
- `decltype(auto) alias = (coinEnabled)` lvalue-reference deduction;
- `auto&& alias = std::move(controllerEnabled)`;
- `std::forward<T&>(protectedField)`;
- `static_cast<T&&>(protectedField)` and `const_cast<T&>(protectedField)`;
- parenthesized lvalue-reference initializers.

The existing pointer/address, ordinary reference and `std::ref`/`std::cref`/`std::addressof` checks remain. The contract comment now documents the rvalue/decltype/cast coverage. The per-board alias mutation matrix is expanded from 5 to 10 cases; five new patterns are injected per board (10 new injections total). Read-only positive controls for logical `&&`, a local `std::move`, and a local `decltype(auto)` remain accepted.

**Changed files:**  
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab_contract.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab_cases.py`

No production ESP8266/ESP32 sketch, CORE API, QA-owned test, finance, COE, signer, witness, migration or release file changed. The contract remains syntactic source analysis, not a complete C++ AST or memory-safety proof.

### Verification

- Isolated Python regex smoke: **10/10 unsafe alias patterns rejected**.
- Positive controls: **3/3 accepted** (logical `&&`, unrelated local `std::move`, unrelated local `decltype(auto)`).
- New regex block Python syntax parse: PASS.
- Full repository Python lab: NOT RUN.
- GitHub Actions for exact source/test SHA `1922dcba...`: NOT RUN; no PR-triggered run was returned for that SHA. The available GitHub connection exposes run inspection/retry, not workflow dispatch.
- Previous #367 Focused/Mbed results remain historical on earlier SHAs; the previous Full run failed at the QA-owned `config_revision` parity assertion. None is transferred to this new source SHA.
- Physical pulse/relay, electrical recovery and power-cut acceptance: NOT TESTED.

### Coordination / blockers

- PHX-QA: independently review the five new alias injections and the existing deny-only controller parity assertion.
- PHX-MASTER: refresh `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md`; their current #367 row still references an older head.
- PHX-CORE: authenticated register/poll/receipt/disposition contract remains unapproved.
- P0 #177 poll-before-first-sample on active v0.6 remains unresolved; coin/relay admission remains denied.
- PRs #239, #254 and #283 remain OPEN / DRAFT / UNMERGED and untouched.
- #283 audit lead revalidation: the original unconditional-clear pattern is not present at #283 HEAD `4dd0b01b`, but `quarantinePending()` is definition-only with no active callsite; physical LittleFS/torn-write acceptance remains absent. Current main register/poll/coin producer still does not supply the expected controller `response_sig`; do not invent one or infer authority from `ok:true`.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json`: NOT RECOVERED; no Google Drive connector is exposed and exact-name Library search did not surface it.

### Rollback and next exact action

Rollback is a normal forward revert of source/test commit `1922dcba...` (no force-push). Keep PR #367 DRAFT. Next: obtain approved exact-head Focused/Mbed/Full Actions for `1922dcba...` or current docs head; if no workflow trigger is available, ask repository administration to run the repository-owned workflows on the exact SHA. QA review and Master matrix refresh remain required before considering integration.

**Sequencing deviation:** the pre-change `IN_PROGRESS` marker was not committed before the source edit in this activation. This is disclosed, not backdated; this checkpoint records the actual post-change state.


## Exact files and commits

- Source/test: [1922dcba792aad40e576583db43de0d066522bf6](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1922dcba792aad40e576583db43de0d066522bf6)
- Clarifying comment: [d3fc76d76b97e8586837aaf70bb35fe602acc5d0](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/d3fc76d76b97e8586837aaf70bb35fe602acc5d0)
- PR: [#367](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/367)
- Control plane: [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)
- P0 hardware issue: [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)

## Resume instruction

Continue PHX-HARDWARE on the same #367 branch. First verify current branch/PR HEAD and exact Actions. Do not modify production sketches, QA assertions, CORE APIs or Master coordination files. Do not treat local regex smoke as repository CI. Request exact-head workflow execution if the GitHub connection still cannot dispatch it. Keep coin and relay denied; no physical operations or production acceptance are authorized.


## CI follow-up — 2026-11-27T23:48:26Z

## PHX-HARDWARE UTC23 CI follow-up — exact source and docs-head Focused/Mbed PASS; Full parity blocked

**Recorded:** 2026-11-27T23:48:26Z (2026-11-28 07:48:26 Asia/Manila)  
**Role:** PHX-HARDWARE  
**Repository / branch:** `BlazeDevStudio/BlazingSystems-Experiments` / `phoenix/hw-deny-latch-monotonicity-20261127-utc21`  
**PR #367:** OPEN / DRAFT / UNMERGED; base #366 `07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9`  
**Source/test SHA:** `1922dcba792aad40e576583db43de0d066522bf6`  
**Docs head with exact Focused/Mbed/Full runs:** `4a78354c985abe26e02ac9574d70b45b6cf3f113`  
**Current source status:** CI VERIFIED (focused deny-latch contract + Mbed matrix); Full integration BLOCKED.

### Exact-source evidence

- Focused [#46083988151](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46083988151), job `140789185854`, head `1922dcba...`: **PASS**. Job log confirms both ESP8266 and ESP32 reject 7/7 direct deny mutations and 10/10 pointer/reference/decltype/move/forward/cast alias mutations; logical-AND positive control and comment/string decoys accepted; poll transport matrix 20 cases per board.
- Mbed [#46083988148](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46083988148), head `1922dcba...`: **3/3 PASS** — source-contract `140789186405`, ESP32 core 3.3.13 `140789186261`, ESP32 core 4.0.0 `140789186428`.
- Focused [#46084256327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084256327), job `140790012861`, head `4a78354c...`: **PASS**, same 10/10 alias matrix per board.
- Mbed [#46084256398](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084256398), head `4a78354c...`: **3/3 PASS** — source-contract `140790018452`, core 3.3.13 `140790018772`, core 4.0.0 `140790018749`.

### Full integration result

- Source-head Full [#46083988182](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46083988182), head `1922dcba...`: CANCELLED after validation failed the handover freshness gate; not a full pass.
- Docs-head Full [#46084256341](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084256341), head `4a78354c...`: overall workflow still IN_PROGRESS at this checkpoint; validation job `140790134787` is **FAILURE** at `tests/controllers.sh`. Exact source check confirms that script requires `config_revision` in both sketches; the deny-only candidate sketches omit it while current main sketches contain it. Do not insert an unauthenticated placeholder or edit QA-owned assertions.
- At last job read, 13 target/platform jobs PASS and `firmware (orangepi_pc)` remains IN_PROGRESS. Downstream simulation, update-bundle, signing and publication stages are skipped after validation failure.

### Interpretation

The new deny-latch alias tests are now actually executed by the Hardware-owned `phx-hw-active-v06-poll-intake-deny.yml` workflow; exact job logs show the 10/10 per-board results. This is host/source-contract and target-build evidence only. It does not prove arbitrary C++ memory safety, physical pulse capture, relay polarity/retention or power-loss behavior.

P0 #177 remains unresolved. CORE authenticated register/poll/receipt authority and QA controller parity remain blockers. Coin and relay admission remain denied. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

**Supersession note:** this CI follow-up supersedes the initial UTC23 handover statement that no exact-head workflow had yet appeared; it does not erase the earlier timestamped observation.



## Final exact-head recheck — 2026-11-27T23:50:04Z

## PHX-HARDWARE UTC23 final recheck — current-head Focused PASS; Mbed/Full still running; previous Full terminal failure

**Recorded:** 2026-11-27T23:50:04Z (2026-11-28 07:50:04 Asia/Manila)  
**Role:** PHX-HARDWARE  
**Repository / branch:** `BlazeDevStudio/BlazingSystems-Experiments` / `phoenix/hw-deny-latch-monotonicity-20261127-utc21`  
**PR #367:** OPEN / DRAFT / UNMERGED  
**Current PR/docs head:** `f7abed43a46f9e85976d5c2897f927609cd2f446`  
**Source/test SHA:** `1922dcba792aad40e576583db43de0d066522bf6`  
**Base (#366):** `07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9`

### Current-head exact evidence

- Focused [#46084613154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084613154), job `140791154901`, exact head `f7abed43...`: **PASS**. Job log confirms ESP8266 and ESP32 each reject 7/7 direct deny mutations and 10/10 alias mutations; logical-AND positive control and comment/string decoys accepted; poll transport matrix 20 cases per board.
- Mbed [#46084613147](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084613147), exact head `f7abed43...`: **IN PROGRESS**. Source-contract job `140791155163` PASS; target builds for ESP32 core 3.3.13 (`140791155501`) and 4.0.0 (`140791155419`) IN PROGRESS.
- Full [#46084613152](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084613152), exact head `f7abed43...`: **IN PROGRESS**; validation job `140791194190` already FAILED at the same controller parity gate. At last job read, 11/14 target/platform jobs PASS and 3 remain IN PROGRESS.

### Terminal prior docs-head Full result

- Full [#46084256341](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084256341), exact head `4a78354c...`: terminal **FAILURE**. All 14/14 target/platform jobs PASS. Validation job `140790134787` fails at `tests/controllers.sh`: it requires `config_revision` in both deny-only candidate sketches, but the candidate intentionally omits it; current main sketches contain it. Simulation, update-bundle, signing and publication stages were skipped.
- The source-head Full #46083988182 was CANCELLED after the handover-freshness gate failed; it is not a pass.

### Status

Focused deny-latch source-contract and Mbed matrix are CI VERIFIED at exact source/docs heads. Full integration remains BLOCKED by the QA-owned controller assertion and the unapproved CORE response contract. No production sketch or shared API changed. P0 #177 remains unresolved; coin/relay admission remains denied. Physical pulse/relay/electrical recovery and power-cut acceptance remain NOT TESTED. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

**Next exact action:** QA/CORE reconcile the deny-only controller parity without adding an unauthenticated `config_revision`; Master refreshes #367 matrices to `f7abed43...`; Hardware rechecks current-head Mbed and Full terminal results. Keep PR #367 DRAFT.

