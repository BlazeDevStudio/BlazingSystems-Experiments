# PHX-HARDWARE UTC00 — modularize the deny-latch source contract

**Recorded:** 2026-11-28T00:41:06Z
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
**Branch:** `phoenix/hw-deny-latch-monotonicity-20261127-utc21`
**PR:** [#367 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/367)
**Base:** #366 at `07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9`
**Source/test commit:** `985a54c289b8e3c796c2bcc977f652b178b293c0`

## Scope

One Hardware-owned Python host-test contract was refactored into named checks for protected-field enumeration, direct address escapes, ordinary/move/forward/cast aliases, `decltype(auto)` aliases, standard reference wrappers, and runtime assignment ownership. The main `deny_latch_assignment_contract()` now calls these helpers in the original order. No predicate, protected field, or denial rule was intentionally changed.

No production `.ino`, CORE API, QA-owned assertion, finance, COE, signer, witness, migration or release file changed.

## Exact evidence

- Focused [#46089157326](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46089157326), job `140805735661`: PASS. 7/7 direct and 10/10 alias mutations rejected per board; logical-AND and comment/string decoys accepted; poll matrix 20 cases per board.
- Mbed [#46089157351](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46089157351): source contract PASS; ESP32 core 3.3.13 PASS; core 4.0.0 was in progress at readback.
- Full push [#46089151346](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46089151346) validation job `140805785941` and Full PR [#46089157387](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46089157387) validation job `140805804838` failed the handover-freshness gate because the code change had not yet been recorded in the canonical handover. This is not a controller-parity result.
- Previous Full [#46084788285](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084788285) on `778220aa...` terminally failed at QA-owned `tests/controllers.sh:21` (`config_revision` absent by deny-only design); all 14 target/platform jobs passed there.

## Remaining blockers

- P0 #177 synchronous poll-before-first-sample remains unresolved; no physical pulse-loss fix is claimed.
- QA owns the deny-only controller parity assertion; CORE owns the authenticated register/poll/receipt/disposition contract. Do not invent `response_sig` or `config_revision` or re-enable coin/relay.
- 150 controlled power cuts, 30-device/24-hour soak, electrical recovery, protected witness, durable accounting/replay, v1-to-v2 migration and independent QA/release signoff remain NOT TESTED / NOT ACCEPTED.
- Private BLAZE_PROJECT_REGISTRY_v11_20261027.json remains unavailable through exposed connectors; no older snapshot substituted.

**Next:** recheck exact-head workflows after this canonical handover commit; PHX-QA/CORE resolve their owned contract; PHX-MASTER refresh role/integration pins. Keep PR #367 DRAFT.


## UTC00 final exact-head recheck — 2026-11-28T00:46:07Z

The handover-freshness gate now passes on docs head `ea6a16506b2e1f7d421de6d5a9599fd3225e73f1`; Full validation proceeds to QA-owned `tests/controllers.sh` and fails at line 21 because the test requires `config_revision` in both deny-only candidate sketches, which do not contain it.

Exact run: [Full #46089588999](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46089588999), validation job `140807165566`; synthetic merge ref `abbaf991c42137f8eb0014a3551c970e40b923e2`. CI-0701 and handover history tests pass. Target jobs were partially in progress at readback. Focused [#46089589007](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46089589007) job `140807120453` PASS. Mbed [#46089589064](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46089589064) source-contract and core 3.3.13 PASS; core 4.0.0 still in progress.

The controller mismatch is a QA/MASTER contract reconciliation, not a Hardware-owned reason to add an unauthenticated field. P0 #177 remains unresolved; no production sketch or shared API changed. Coin/relay stay denied.