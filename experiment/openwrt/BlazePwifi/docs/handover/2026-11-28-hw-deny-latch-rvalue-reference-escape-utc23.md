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
