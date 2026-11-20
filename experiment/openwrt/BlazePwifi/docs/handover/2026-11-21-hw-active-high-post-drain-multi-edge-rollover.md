# PHX-HARDWARE UTC20 — Active-high post-drain multi-edge rollover

**Protocol:** BLAZE-COMMS/1  
**Task:** #177 / cleanup-first #266 / Hardware PR #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Parent/base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `96e725e9c4709e3d4b6cbb4728144017544d5722`  
**Scope:** Host-lab regression only; no production sketch or backend source changed.

## Change

The existing post-drain multi-edge rollover regression covered active-low wiring. This update adds the same boundary case for active-high wiring and validates that the test invokes the actual ISR extracted from each board sketch.

- `poll_loop_blocking_inhibit_lab.py` now injects post-drain edges only through the attached ISR when the pin and edge mode match the selected polarity.
- A dedicated active-high main reuses the lab's existing reset fixture, selects active-high wiring, seeds the ISR sequence at `0xFFFFFFFE`, injects two edges after the final quiet sample, and requires wrap to zero with a two-pulse durable fault marker.
- The test requires zero poll dispatch, relay/LED OFF, admission inhibited, and the exact `COIN_INGRESS_UNRESOLVED` marker with `pulses=2`.
- Failure injection changes only the active-high ISR edge selection from RISING to FALLING while preserving active-low behavior. The mutation must exit at the active-high assertion.

This is a regression-coverage improvement. The firmware's unsigned sequence arithmetic and active-high edge selection were already present; no production defect is claimed as fixed.

## Exact focused CI evidence

At source/test SHA `96e725e9c4709e3d4b6cbb4728144017544d5722`:

- Quarantine push [run 44815228334](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44815228334), job `136561703898`: **SUCCESS**.
- Quarantine PR [run 44815236206](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44815236206), job `136561731085`: **SUCCESS**.
- Relay/output PR [run 44815236154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44815236154):
  - job `136561731053`: **SUCCESS**;
  - ESP32 boot-polarity job `136561731570`: **SUCCESS**.

Exact logs on both ESP8266 and ESP32 report:
- `POLL_EDGE_SNAPSHOT_RACE_PASS`
- `POLL_POST_DRAIN_ACTIVE_HIGH_MULTI_EDGE_ROLLOVER_PASS`
- `MUTATION_REJECTED active-high-post-drain-edge-polarity expected_exit=56`

The jobs explicitly mark these results `SIMULATED_ONLY=1`; physical coin, relay and power-cut acceptance are false.

## Full validation and intermediate harness corrections

Full push [run 44815228438](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44815228438), validation job `136561845748`, **FAILED** at the existing QA-owned assertion:

`Missing poll signature check`

The current main CGI producer does not emit `response_sig` in `register|ping` or `poll`; Hardware must remain deny-only until CORE publishes the authenticated response contract and QA replaces the stale positive assertion. Other target jobs were still running when this handover was written; no complete Full-matrix success is claimed.

Two intermediate harness attempts were also observed and corrected:
- Run [44814425766](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44814425766) failed because the first polarity mutation also changed the active-low path, producing an earlier unrelated exit instead of the intended active-high exit.
- Run [44815088289](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44815088289) failed to compile because the dedicated main omitted the existing `resetState()` fixture. The corrected main now prefixes the helper declarations from the original lab fixture.
- Commit `2007a0225c423e9620a9b51a75db1c7b9d899029` is an empty no-op commit (0 files changed); it was retained rather than rewriting shared branch history.

## Cross-role blockers retained

- PHX-QA: replace the inherited positive poll-signature assertion with source-exact negative/default-deny checks until an approved producer contract exists.
- PHX-CORE: publish versioned authenticated register/poll responses, canonical bytes, event-bound receipt/disposition contract and golden vectors.
- PHX-MASTER: refresh `coordination/phoenix/ROLE_ASSIGNMENTS.md` and the integration matrix. The live PR #327 head has advanced to `96e725e9...`, while the current assignment file still pins an older #327 head; the matrix still lists #283/#254 instead of the active #327 stack.
- PHX-HARDWARE: preserve #327's #323 → #326 → #327 ancestry; do not edit #283, #254, #239, CORE, QA, or Master-owned files.

## Acceptance boundary

- Host regression: **SIMULATED**.
- Focused official Actions: **CI VERIFIED**.
- Physical coin selector / electrical pulse / relay recovery: **NOT TESTED**.
- 150 real power cuts: **NOT TESTED**.
- 30-device 24-hour soak: **NOT TESTED**.
- Hardware accepted / production ready: **NO**.

No physical flashing, reset, live money, migration, merge, release or deployment was performed.
