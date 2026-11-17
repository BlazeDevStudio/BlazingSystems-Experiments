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
