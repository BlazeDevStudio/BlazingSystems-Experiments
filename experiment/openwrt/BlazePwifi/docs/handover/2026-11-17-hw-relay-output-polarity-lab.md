# PHX-HARDWARE — relay output polarity source-extracted lab

**Date:** 2026-11-17 UTC11  
**Task:** #177 / #266; existing DRAFT PR #317 reused  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/hardware-clear-pending-marker-match-20261117  
**PR base:** phoenix/hardware-quarantine-append-failclosed-20261117  
**Parent PR base SHA:** 84fe6b790139d147f330f13a40b3ae3e89a7042d

## Finding

The existing poll-response source lab substitutes a host writeLogical() stub that records a logical boolean and ignores the production activeHigh argument. That proves the admission gate's boolean state, but it does not exercise the actual HIGH/LOW mapping used for active-high versus active-low relay and LED outputs.

This is a **test-coverage gap**, not a newly claimed firmware defect. The current production mapping is retained unchanged.

## Change

Added esp8266/BlazePwifiVendo/relay_output_polarity_lab.py. It extracts the actual writeLogical() and applyOutputs() functions from both sketches and compiles them with a host GPIO-level recorder.

The lab covers:
- both active-high and active-low relay polarity;
- both active-high and active-low LED polarity;
- positive admission;
- all nine independent output-denial conditions, including pollIntakeSuspended;
- independent relay and LED disable switches;
- two mutation injections per board: inverted GPIO mapping and removal of the poll-intake inhibit.

A dedicated .github/workflows/phx-hardware-relay-output-polarity.yml pins checkout to the PR event SHA and prints explicit simulation-only / no-hardware flags.

## Boundaries

- No production firmware source or runtime behavior changed.
- No shared API, receipt, finance, migration, QA-owned test path, release signer or destination repository changed.
- This lab checks software GPIO level mapping only. It cannot establish the physical relay module's active polarity, de-energized contact state, driver transistor behavior, pulse capture or electrical recovery.
- An exploratory child PR #319 was closed as superseded so the existing owner-controlled #317 branch remains the single hardware review surface. No commits were merged.

## Evidence

- Starting PR #317 HEAD: 3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3
- Expected normal result: 48 scenarios per board.
- Expected mutation evidence: both injected regressions must be rejected for both boards.
- Exact reused-branch HEAD tested: `9f12e9658797dbd92d09525acba6d8c6803880bf`.
- Focused polarity [run #44072123813](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44072123813), job `134000692913`: **SUCCESS**; ESP8266 and ESP32 each passed 48/48 normal scenarios, and both injected regressions were rejected on both boards.
- Inherited quarantine [run #44072123802](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44072123802), job `134000693140`: **SUCCESS**; quarantine 38/38 total, pending-attempt marker 56/56, and inherited mount/recovery/write/readback/coin-gate suites passed.
- Full [run #44072123887](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44072123887), validation job `134000833456`: **FAILED** at the inherited QA-owned `tests/controllers.sh` check, which still requires an active poll signature contrary to Master Architecture Contracts §6.7. Target jobs were still running at last observation; production import/signing and release bundle were skipped.
- The exploratory #319 branch was closed unmerged; these are fresh exact-head #317 results, not carried across branches.
- Physical relay/coin acceptance: **NOT TESTED**.
- 150 power cuts / 30-device 24-hour soak / electrical pulse recovery: **NOT TESTED**.

## Next action

PHX-QA independently review the host extraction and mutation checks and reconcile the stale poll-signature assertion; PHX-MASTER preserve the existing #314 → #315 → #317 stack and reconcile the stale §2.2 wording with the later §6.7 default-deny decision.


## PHX-HARDWARE — parent/child poll-window workflow scope guard (2026-11-17 UTC12)

**Task:** #177 / #172 / #266 · **Role:** PHX-HARDWARE · **Branch:** `phoenix/hardware-clear-pending-marker-match-20261117` · **Starting HEAD:** `8bde0c268b76fe5578b7cba5c29e402c6d7582f2`

At exact parent PR #317 HEAD `8bde0c268b76fe5578b7cba5c29e402c6d7582f2`, focused run [#44077597223](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44077597223), job `134019532118`, compiled the relay-output lab successfully: ESP8266 and ESP32 each passed 48/48 scenarios and both injected regressions were rejected. The next step failed because the workflow invoked `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_window_timeline_guard_lab.py`, which is intentionally present on child PR #318 but absent from the parent #317 tree. This was a workflow/stack-scope failure, not a firmware compile or relay-lab failure.

The same parent SHA's Full run [#44077597179](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44077597179), validation job `134019533307`, failed at QA-owned `tests/controllers.sh` with the legacy “Missing poll signature check” assertion. Master Architecture Contracts §6.7 keeps poll admission default-deny; PHX-HARDWARE did not change QA-owned files or restore the unapproved `response_sig` candidate.

**Change:** the workflow now runs both child-only poll-window labs only when the timeline-guard file exists in the exact checked-out SHA. On a parent-only SHA, it emits `CHILD_POLL_WINDOW_TESTS=NOT_PRESENT_ON_THIS_SHA` and `NO_CHILD_POLL_WINDOW_CI_CLAIM=1`; it does not silently claim those tests passed. Child PR #318 currently contains the corrected timeline guard and poll lab, but remains 17 commits ahead / 8 behind #317 with no PR-triggered run on its literal head. Do not rebase or compose it without Master stack reconciliation.

**Validation:** exact-head Actions after this workflow change are pending; no GREEN is claimed yet. This commit changes CI wiring and handovers only, not firmware runtime. Host simulations remain SIMULATED; relay polarity, coin waveform, electrical recovery, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. Production remains NO-GO.


## PHX-HARDWARE — UTC12 final parent/child CI reconciliation

**Parent PR #317:** exact HEAD `a29c51b8066095cf1a19a8847849f6da3c344ae7`, still OPEN / DRAFT / UNMERGED.

- Focused relay-output [run #44081886930](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44081886930), job `134034277849`: **SUCCESS**. ESP8266 and ESP32 each passed 48/48 GPIO polarity/output-gate scenarios; both mutation injections were rejected on both boards. Because the parent SHA does not contain the child-only timeline guard, the job explicitly printed `CHILD_POLL_WINDOW_TESTS=NOT_PRESENT_ON_THIS_SHA` and `NO_CHILD_POLL_WINDOW_CI_CLAIM=1`.
- Quarantine [run #44081886965](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44081886965), job `134034277275`: **SUCCESS**; source-extracted quarantine, pending-attempt, journal recovery, clear and write/readback suites passed.
- Full [run #44081886887](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44081886887), validation job `134034278243`: **FAILED** at QA-owned `tests/controllers.sh` with “Missing poll signature check”. Master Architecture Contracts §6.7 keeps poll admission default-deny; PHX-HARDWARE did not restore the unapproved `response_sig` candidate or edit QA-owned files. All 14 listed target jobs completed SUCCESS (ESP8266, ESP32, Android, x86_64, Ruijie and 9 Orange Pi targets). Production import/signing, update bundle and release/simulation gates were SKIPPED.

**Child PR #318:** current head `90262e4677638b01d18a8eb348efdc3cbeff6202`. Exact child poll-window [run #44083290324](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44083290324), job `134039102435`: **SUCCESS**. The corrected timeline guard passed; both boards passed 13/13 poll-window scenarios, 8/8 debounce-floor scenarios and 1/1 blocking-poll relay-inhibit scenario. The injected removal of the final `coinLineIdle()` sample was rejected on both boards at expected exit 25. Both boards also passed 11/11 poll-response default-deny, 13/13 strict-root-JSON, 4/4 coin-POST ACK-root and 4/4 coin-disposition default-deny cases. The lab prints `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0` and `PHYSICAL_POWER_CUT_VERIFIED=0`.

Current child compare against parent #317 `a29c51b8066095cf1a19a8847849f6da3c344ae7`: **25 ahead / 9 behind, diverged, mergeable=false**, merge base `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`. No rebase, cherry-pick, merge or force-push was performed. Child Full build [run #44083290724](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44083290724) has validation job `134039104956` **FAILED** on the same QA-owned stale poll-signature assertion; at this handover update 11/14 target jobs were SUCCESS and ESP32, Android and x86_64 were still running. The prior child build [#44082711402](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44082711402) at `9154e3f744035265f58e9f5278ea196fe601072e` completed all 14 target jobs SUCCESS but its validation failed. ESP8266 and ESP32 firmware blob SHAs are unchanged between that source-build head and child head `90262e...`; the later commits changed test/CI/handovers, not firmware runtime.

This activation changed CI wiring, host tests and handovers only. All host tests are SIMULATED / CI VERIFIED. Physical relay/coin waveform, electrical pulse/recovery, 150 power cuts, 30-device/24-hour soak, protected signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release approval remain NOT TESTED/BLOCKED. **PRODUCTION NO-GO.**


## PHX-HARDWARE — final child target-build recheck (2026-11-17 UTC12)

The interim note above recorded 11/14 child target jobs complete while three were still running. Final readback of child Full build [#44083290724](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44083290724) at test/firmware head `90262e4677638b01d18a8eb348efdc3cbeff6202` supersedes that interim count: **all 14/14 target jobs completed SUCCESS** (ESP8266, ESP32, Android, x86_64, Ruijie and 9 Orange Pi targets). Validation job `134039104956` remains **FAILED** at the QA-owned legacy “Missing poll signature check” assertion. Production import/signing, update bundle and v0.4 simulation/publication gates were SKIPPED.

The child PR #318 branch subsequently advanced only with its handover documentation to `c840e76e437344920a2a1720d457e93c348b3ad9`; firmware blobs and poll-lab source are unchanged from the exact tested `90262e...` head. Current compare to this parent branch before this documentation follow-up was 26 ahead / 10 behind and diverged; no rebase or merge was performed. Preserve the default-deny contract and keep production NO-GO.
