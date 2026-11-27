# PHX-HARDWARE handover — poll transport outcome matrix (UTC19)

- **Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
- **Role:** PHX-HARDWARE
- **PR:** [#365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/365), OPEN / DRAFT / UNMERGED
- **Branch:** `phoenix/hw-poll-boundary-pulse-matrix-20261128-utc18`
- **Parent:** #364 at `ea765fb822e1c517db4e61c103b86d8eb2c66c92`
- **Pre-task head:** `7c4ca74838be3d4469bef6acc2c2209849f30869`
- **Status:** IN PROGRESS — documentation staged before source edits

## One bounded task

Extend the existing poll-boundary harness with transport return outcomes: immediate begin failure, empty timeout response, malformed response, server-error body, and a non-empty untrusted `insert=true` response. Run each across four independent relay/LED active-level combinations. Inject a source mutation that consumes the untrusted positive response and briefly re-enables outputs before the final deny call; the harness must reject that transient actuation.

## Safety boundary

This is host simulation of the candidate deny-only poll block. It does not modify either production sketch or the active v0.6 branch. It does not establish physical coin retention when the acceptor is inhibited, relay polarity, electrical recovery, 150 power cuts, or 30-device/24-hour soak. No coin admission, relay re-enable, finance, replay, witness, downgrade, migration, signing, flashing, reset, merge, release or deployment.

## Next exact action

Implement the transport-outcome harness and mutation in the existing Hardware-owned #365 branch, run focused exact-SHA CI and Mbed matrix, then record terminal evidence. Full integration is expected to retain the inherited v0.6/current-main controller parity blocker unless Master/QA reconcile it.
