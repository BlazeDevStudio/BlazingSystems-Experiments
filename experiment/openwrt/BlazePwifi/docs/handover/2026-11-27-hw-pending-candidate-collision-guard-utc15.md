# PHX-HARDWARE — Pending journal candidate collision guard

**Date:** 2026-11-27 UTC15  
**PR:** [#362](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/362), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-pending-candidate-collision-guard-20261127-utc15`  
**Parent:** [#361](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/361) at `8a1999ccdcab02445ef93c153316e519d9476210`; #361 is stacked on #359.  
**Firmware/test commit:** `a45b2491f312f1d66e70f8caef5b55f49dec60bb`  
**Harness assertion correction:** `2768bf701945401aa6efed9c7c2573ed08b2b8cb`  
**Workflow synchronization/current branch HEAD:** `7536b6568c186a35bcbde0cddff1c6774bfe6c6d`  
**Role:** PHX-HARDWARE · **Tasks:** #31 / #32 / #177 / cleanup-first #266.

## Finding

The sequence writer stages and flushes `/pending.new` before moving the previous `/pending.dat` to `/pending.bak`. A power loss between those operations can leave a valid old canonical record and a valid newer fallback. The previous loader preferred the canonical path and ignored the fallback, which could recover an older sequence while leaving a newer pending reservation unprocessed.

## Firmware correction

Both ESP8266 and ESP32 now count the three candidate paths before reading any of them. More than one present candidate latches `pendingReady=true`, sets `fsReady=false`, returns false, and preserves all candidate files. A single candidate retains the existing validation and promotion behavior. No automatic coin retry, pending clear, replay, positive relay enable, receipt/disposition, finance or shared API change was added.

## Host regression coverage

The extracted C++ harness now adds four coexistence cases:
1. valid canonical + `pending.new`;
2. valid canonical + `pending.bak`;
3. `pending.new` + `pending.bak`;
4. all three candidates present.

Every case requires fail-closed state, no rename, no published identity and preservation of every file. The Python source-contract lab requires the multi-candidate guard to precede candidate reads and rejects a mutation that raises the allowed candidate count.

## Exact CI evidence

- Focused push [#46028930317](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46028930317), job `140607427614`: PASS.
- Focused PR [#46028937563](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46028937563), job `140607451486`: PASS.
- Both exact-head runs report 15 scenarios per board, 2 rename failures, 6 ambiguous-preservation scenarios and 18/18 source mutations rejected.
- Mbed source-contract [#46028930281](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46028930281), job `140607427755`: PASS; target builds pending at sync.
- Full [#46028937549](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46028937549): handover freshness failed because this record was not yet appended; post-sync rerun required.
- Native [#46028937565](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46028937565): QA-owned PAY-0745 assertion mismatch (`if(any) return false;` expected literally); source remains fail-closed.

The initial focused run [#46028536467](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46028536467) exposed a test-only ordering assertion bug (searching a masked buffer for a call containing a string literal). Commit `2768bf7` corrected it; subsequent exact-head focused runs pass.

## Coordination / blockers

- PHX-MASTER: add #362 to role assignment and integration matrices; preserve #361 → #359 → #355/#354 ancestry.
- PHX-QA: replace PAY-0745's literal `if(any) return false;` expectation with an assertion over the fail-closed block and independent state-preservation semantics.
- PHX-CORE: publish the authenticated register/poll and receipt/disposition contract before any future positive coin path.
- PHX-HARDWARE: keep admission denied; do not auto-select a journal candidate when multiple files exist.

**Status:** SIMULATED / CI VERIFIED for host-only recovery checks. Physical LittleFS, electrical, relay, 150 power-cut, 30-device/24-hour soak acceptance NOT TESTED. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO. No flash, reset, live money, production migration, merge, release or deployment.
