## PHX-HARDWARE UTC21 — deny-latch monotonicity contract

**Status:** DRAFT / source-test change committed; exact-head Actions pending.  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Role:** PHX-HARDWARE  
**Task:** #177 / cleanup-first #266  
**Branch:** phoenix/hw-deny-latch-monotonicity-20261127-utc21  
**Base:** PR #366 branch at 07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9  
**Source/test commits:** d0797078a0f41382ca3cdaeeba5c394013e59617, e7ec6494204681c4602436817acfaa14a860fd82, plus the fixture-format correction recorded in branch history.

### Actual change

Extended the existing poll-preflight source-contract lab with a whole-sketch assignment audit for the deny-only runtime fields:

- controllerEnabled
- coinEnabled
- relayEnabled
- ledEnabled
- insertMode
- activeTarget

The contract allows one global initializer for each boolean, requires insertMode=false at startup, and permits runtime writes only inside the unconditional denyRemoteControl() function. That function must set all five flags false and clear activeTarget exactly once. Any other runtime assignment, compound assignment, increment/decrement, non-empty target restoration, or re-enable write is rejected.

Added seven source mutations per board: re-enable each of the five flags outside the deny helper, restore a stale target outside the helper, and change the helper to set relay enabled. The existing poll/register, GPIO polarity, transport-outcome and pending-disposition labs remain in the same runner.

### Scope and safety

This is a source-contract / failure-injection improvement only. No ESP8266 or ESP32 production sketch, CORE API, financial logic, QA-owned assertion, COE destination, or release configuration was modified. It does not solve the active v0.6 poll-before-first-sample race and does not authorize positive coin intake. Keep coin and relay admission denied.

The audit is intentionally limited to direct C/C++ assignments visible after comment/string masking; it is not a proof against pointer aliasing, memory corruption, electrical faults, or physical coin retention.

### Tests and evidence

- GitHub Actions exact-head focused and PR runs: PENDING.
- Mbed TLS 3/4: NOT RUN for this new head.
- Full controller integration: inherited blocker; the deny-only candidate intentionally omits the unapproved controller field, while QA's current parity assertion still expects it.
- Native PAY-0745: prior QA-owned assertion mismatch remains unresolved.
- Physical relay polarity, pulse retention, electrical recovery, 150 power cuts and 30-device/24-hour soak: NOT TESTED.

### Coordination

PHX-MASTER owns the global assignment/integration matrices. PHX-QA owns PAY-0745 and controller parity assertions. PHX-CORE owns authenticated register/poll/receipt/disposition. No shared API was changed.

**Execution sequencing note:** the required pre-change IN_PROGRESS handover marker was not committed before the first source edit in this activation; this deviation is recorded after the fact rather than represented as compliant.

**Next exact action:** open/reuse the DRAFT child PR against #366, inspect exact-head focused/Mbed/Full/Native results, and ask QA to review the new deny-latch invariant without changing QA-owned files.
