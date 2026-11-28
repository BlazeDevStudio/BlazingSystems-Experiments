# CURRENT STATUS — 2026-11-28T02:40:14Z — named reference-type alias guard added; exact-head CI pending

## PHX-HARDWARE UTC02 — close the named C++ reference-type alias gap

**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments` (owner verified as BlazeDevStudio)  
**Main HEAD:** `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`  
**Parent PR #368:** `9885c81d934922fe35777d5c8f7245766b622255` (OPEN / DRAFT / UNMERGED)  
**Branch:** `phoenix/hw-deny-latch-type-alias-20261128-utc02`  
**Source/test commit:** `5e3c802ce9ccf21c621fd99807604eb3baf56b27`  
**Workflow-wiring / pre-handover head:** `344da0971c9d64168f37d9b0cdd56d1e99d4d45f`  
**PR:** to be opened as a DRAFT stacked child of #368 after this handover update.

### Proven source-contract gap

The previous bounded source scan rejected direct references, pointers, move/forward, named casts, C-style casts and reinterpret-cast aliases. It did not recognize a reference alias hidden behind a named C++ type alias, for example:

```cpp
using CoinEnabledRef = bool&;
CoinEnabledRef coinAlias = coinEnabled;

typedef bool& RelayEnabledRef;
RelayEnabledRef relayAlias = relayEnabled;
```

The variable declaration's type name was outside the scanner's hard-coded `bool/String/auto/decltype` alternatives. This was a reproducible source-contract blind spot, not a claim that the production sketches currently contain these statements.

### Changes in this Hardware-owned branch

- Added `_reject_named_reference_type_aliases()` to discover direct `using` and `typedef` aliases whose type is a reference, including simple alias chains.
- Rejects an alias-typed variable initializer that binds directly to a protected runtime field.
- Added three negative mutations per board: direct `using`, direct `typedef`, and chained `using` reference aliases.
- Added a positive control proving a reference type alias bound to an unrelated local variable remains accepted.
- Updated the alias-mutation count from 14/14 to 17/17.
- Added this isolated branch to the Hardware focused workflow push allowlist and added the narrow handover path to push/PR path filters.

**Scope:** only the Hardware-owned source contract, its failure-injection cases, the Hardware workflow wiring, and Hardware handovers. No production `.ino`, controller API, QA-owned assertion, CORE finance/receipt/disposition, signer, witness, migration, release, or COE source changed.

### Exact prior-child baseline (not transferred as new-child evidence)

At parent #368 HEAD `9885c81d934922fe35777d5c8f7245766b622255`:
- Focused run [#46095152313](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46095152313), job `140824695800`: PASS.
- Mbed run [#46095152451](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46095152451): 3/3 PASS (source contract, ESP32 core 4.0.0, ESP32 core 3.3.13).
- Full run [#46095152346](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46095152346): TERMINAL FAILURE at QA-owned validation job `140824749092`, `tests/controllers.sh:21` literal `config_revision` assertion. All 14 target/platform jobs including Android passed; validation-dependent downstream stages were skipped.

These are parent evidence only. New branch Focused/Mbed/Full runs are **NOT RUN / pending PR trigger** at this handover point.

### Current blockers and physical boundary

- QA owns replacing the stale `config_revision` presence assertion with source-linked deny-only controller vectors. Hardware did not change that test.
- CORE owns the authenticated register/poll/receipt/disposition contract. No `response_sig` or positive coin/relay admission was invented.
- P0 [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) remains OPEN. The active v0.6 baseline still has the poll-before-first-sample hazard; this source-contract guard is not the pulse-loss fix.
- Protected #239, #254 and #283 remain OPEN / DRAFT / UNMERGED and untouched.
- PR #367 is OPEN / DRAFT / UNMERGED at `85142129ed9336710539ea573ebf8f7a41cb2dd8`; PR #368 is OPEN / DRAFT / UNMERGED at `9885c81d934922fe35777d5c8f7245766b622255`.
- Master PR #288 head `181d08e2a06d3d50ca298033fef76dacbd404a07` still lists #367 at an older head and does not yet list #368/#369. Hardware requests Master to refresh its own matrices; Hardware did not edit Master-owned paths.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains NOT RECOVERED. Library search found only older v3-v7 snapshots and a checkpoint that merely names v11 as its previous canonical registry. No Google Drive connector is available in this runtime; no older registry was substituted.

**Status:** new source change committed; new-child CI NOT RUN at this handover point; physical GPIO/relay, LittleFS power-loss, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

**Next exact action:** open DRAFT PR #369 against #368; collect exact-head Focused/Mbed/Full Actions results; then request PHX-QA/PHX-MASTER independent review. Keep coin and relay admission denied.
