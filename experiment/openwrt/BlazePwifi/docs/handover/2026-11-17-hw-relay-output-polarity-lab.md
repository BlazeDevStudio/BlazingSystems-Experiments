# PHX-HARDWARE — relay output polarity source-extracted lab

**Date:** 2026-11-17 UTC11  
**Task:** #177 / #266; child DRAFT #319 stacked on DRAFT #317  
**Base:** 3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3  
**Branch:** phoenix/hardware-relay-output-polarity-lab-20261117

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

## Evidence

- Exact parent PR #317 HEAD at start: 3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3
- Expected normal run: 48 scenarios per board.
- Expected mutation evidence: both injected regressions must be rejected for both boards.
- Initial exact-head CI at `e5c52814eb2f35c363aa4c13d36eba3dca6f86ca`: [run #44071357249](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44071357249), job `133998108886`, SUCCESS. ESP8266 and ESP32 each passed 48/48 normal scenarios; both injected regressions were rejected on both boards. A final documentation-corrected head will receive a fresh exact-SHA run.
- Physical relay/coin acceptance: **NOT TESTED**.
- 150 power cuts / 30-device 24-hour soak / electrical pulse recovery: **NOT TESTED**.

## Next action

PHX-QA independently review the host extraction and mutation checks; PHX-MASTER preserve the #317 → #319 stack. Physical polarity must remain unaccepted until owner-approved isolated hardware and independent electrical measurements are available.
