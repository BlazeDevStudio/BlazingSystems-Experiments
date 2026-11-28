# PHX-HARDWARE UTC13 — centralize the deny-only synchronous poll boundary

**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hw-poll-deny-wrapper-20261128-utc13`  
**Parent:** PR #366 at `07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9`  
**Stack:** #375 (new child of #366; OPEN/DRAFT after creation)  
**Status at source commit:** implementation committed; exact-head CI pending.

## Selected task

Reduce the chance that a future loop edit bypasses the pre/post intake-deny sequence around the blocking 3.5-second controller poll. The prior sketches duplicated the deny, discarded POST, and second deny inline in the loop. The new `pollDenyOnly()` wrapper is the sole owner of that boundary on both ESP8266 and ESP32.

## Source changes

- Both sketches now call `pollDenyOnly()` from the existing bounded Wi-Fi poll condition.
- The helper resets the Wi-Fi failure counter, applies the deny latch, explicitly discards `post("poll")`, applies the deny latch again, then records `lastPoll`.
- No poll response is returned, parsed, or applied. The helper does not clear or rewrite pending journal evidence.
- The source contract now requires exactly one helper call inside the bounded loop block and exactly one poll POST inside the helper. It rejects direct loop poll calls, duplicate poll callsites, response consumption, remote-config application, conditional/bypassable deny calls, missing timestamp update, and coin/pending disposition regressions.
- The existing source-extracted C++ harness now receives the helper body and continues to exercise the actual 3,500 ms wait, six pulse windows, four relay/LED polarity combinations, pending identity preservation, and transport outcome matrix.

## Safety boundary

This is a behavior-preserving source-structure change on the already deny-only v0.6 candidate stack. It does **not** restore coin admission, re-enable relay/LED, authenticate controller replies, or claim the active unmerged v0.6 baseline is fixed. PR #354 and its descendants remain unmerged. The source simulation cannot establish acceptor electrical behavior or pulse retention when the enable relay is removed mid-cycle.

CORE still owns authenticated register/poll/receipt/disposition authority; QA owns independent semantic assertions; MASTER owns cross-role integration pins. No shared schema or finance path was changed.

## Validation

Exact-head Poll, Mbed TLS 3/4 and Full workflows are requested through the branch's path-filtered Actions. Results and job IDs must be recorded in the PR and the UTC13 BLAZE-COMMS/1 checkpoint after completion. Local repository runner was not available in this execution environment; do not describe a local pass.

**Not tested:** physical coin acceptor/relay polarity, pulse retention, electrical recovery, EEPROM/NVS brown-out, 150 power cuts, 30-device 24-hour soak, migration, signer/witness and production accounting/replay.

**Disposition:** SIMULATED/CI only when exact-head workflows pass; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
