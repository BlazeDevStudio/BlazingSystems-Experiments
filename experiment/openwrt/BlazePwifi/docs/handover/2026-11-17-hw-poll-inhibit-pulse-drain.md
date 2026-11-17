# PHX-HARDWARE — poll-inhibit pulse-drain guard

**Date:** 2026-11-17 UTC16  
**Task:** [P0 issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hardware-clear-pending-marker-match-20261117`  
**PR:** [#317 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/317)  
**PR base:** `phoenix/hardware-quarantine-append-failclosed-20261117` @ `84fe6b790139d147f330f13a40b3ae3e89a7042d`

## Finding

The existing `beginPollWindow()` inhibited the relay and LED before synchronous HTTP polling, but `coinLineQuietAfterInhibit()` waited only for `runDebounceMs`. With a 40 ms debounce setting, a 30–100 ms coin pulse beginning 100 ms after inhibit could occur after the quiet check had already returned. The poll could then block the loop for approximately 3.5 seconds while the pulse input was not sampled.

This is a software timing gap in the pre-poll drain interval. It is not proof that the physical acceptor or relay is correctly wired.

## Test-first reproduction

- Test-only commit: [`a48c2dd4`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a48c2dd4a8a77e5003a265d18c778b2b5fcda559).
- Expected RED: [focused run #44129524067](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44129524067), job `134202405008`.
- Both board extractions rejected the 100 ms delayed pulse case because the old helper returned at 40 ms: `poll=1 expected=0 elapsed=40`.

## Firmware correction

Source commit: [`c883ea92`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c883ea9228b93553515ab79c5096d539133da59b).

Both ESP8266 and ESP32 `coinLineQuietAfterInhibit()` now use:

`quietMs = max(runDebounceMs, 250 ms)`

The larger configured debounce is preserved. After output inhibit, the helper requires a continuous quiet interval. If a pulse is observed during the drain, `beginPollWindow()` cancels the poll window, restores normal intake, and returns to the loop so the pulse can be sampled and journaled before a blocking request. No interrupt-only RAM pulse counter was imported from child PR #318.

## Test fixture correction

Test/fixture commit: [`d5add094`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/d5add0949e6613b7a1b22a7c0ebd1a9adba8f7c5).

The inherited `poll_response_failclosed_lab.py` now expects the 250 ms minimum quiet interval. Its synchronous-HTTP fixture was corrected to inject the later unexpected pulse at 300 ms (after the 250 ms drain) and observe the 3.5 s wait through 3750 ms. This removes the previous fake-clock rewind, which had placed the supposed in-flight pulse before poll admission.

A new `poll_window_drain_lab.py` extracts the production `coinLineIdle()`, `canStartPoll()`, `applyOutputs()`, `coinLineQuietAfterInhibit()`, and `beginPollWindow()` from both sketches and compiles them with deterministic fake GPIO/time.

## Exact-head evidence

At source/test SHA `d5add0949e6613b7a1b22a7c0ebd1a9adba8f7c5`:

- Test-first RED [#44129524067](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44129524067), job `134202405008`: **FAILED as expected** on the 100 ms delayed pulse before the firmware fix.
- Focused quarantine/poll-window [#44129971884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44129971884), job `134204032543`: **SUCCESS**.
  - ESP8266: poll drain 8/8; short-debounce mutation rejected.
  - ESP32: poll drain 8/8; short-debounce mutation rejected.
  - Inherited poll lab on both boards: debounce 8/8, poll-window 9/9, blocking-poll relay inhibit 1/1.
  - Inherited quarantine 33/33 per board; pending journal 16/16; pending clear 17/17; pending write/readback 22/22; coin POST gate 10/10 per board.
- Relay output [#44129971858](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44129971858), job `134204037457`: **SUCCESS**; 48/48 per board, active-high/active-low mapping and output-gate mutations rejected.
- Full build [#44129957587](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44129957587):
  - Validation job `134204160548`: **FAILED** at QA-owned `tests/controllers.sh`, exact error `Missing poll signature check`. The firmware remains default-deny pending the CORE-authored canonical poll contract; PHX-HARDWARE did not restore an unapproved `response_sig`.
  - All 14/14 target build jobs completed **SUCCESS**, including ESP8266, ESP32, Android, x86_64, Ruijie and all returned Orange Pi targets.
  - Production import/signing, update bundle and release/simulation promotion jobs were skipped.
- Every hardware lab explicitly reports physical relay/coin/power-cut verification as zero.

## Stack and coordination

- PR #317 remains OPEN / DRAFT / UNMERGED; current source/test head is `d5add0949e6613b7a1b22a7c0ebd1a9adba8f7c5`.
- Child PR #318 remains OPEN / DRAFT and divergent at `a497403bd3886caf105585c0da997a100ad61dc3`, based on stale `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`; GitHub reports no mergeable result. It includes additional ISR work not copied here. PHX-MASTER must reconcile the child stack and refresh the role index, which still carries older #317 pins and omits #318.
- PRs #239, #254 and #283 were revalidated and left untouched.
- No shared API, financial schema, migration, QA-owned source, signer, witness or release workflow was changed.

## Evidence limits and next action

This is **SIMULATED / CI VERIFIED**, not HARDWARE ACCEPTED. No physical relay contact, coin acceptor pulse waveform, electrical recovery, power interruption or device was exercised. The 250 ms floor is a firmware guard to validate on noncustomer hardware; it is not a substitute for the 150 power-cut sequence, 30-device 24-hour soak or electrical pulse/recovery acceptance.

PHX-QA must repair its owned legacy positive poll-signature assertion/extractor against the approved default-deny contract and rerun Full validation. PHX-MASTER must reconcile #317/#318 and update the control-plane assignment pins. PHX-CORE must publish the authenticated poll/receipt/disposition/replay contract before any positive admission.

The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available in the accessible Library/connector surface. No older registry was substituted and no Drive artifact was created or promoted.

**Production status: NO-GO.**

## UTC18 addendum — wrap-safe poll-drain timing regression

The production coinLineQuietAfterInhibit() already uses unsigned elapsed-time subtraction (millis() - started < quietMs), which is the correct rollover-safe form for this bounded interval. The prior host lab only started its fake clock at zero, so it did not protect that property against a future absolute-deadline rewrite.

The existing exact-source lab now:
- accepts an arbitrary initial fake millis() value and compares elapsed time using unsigned subtraction;
- checks the 250 ms quiet floor starting at 0xFFFFFF80, crossing the 32-bit millisecond rollover;
- checks a larger configured 300 ms debounce across the same rollover;
- deliberately mutates the extracted production helper to use millis() < started + quietMs and requires the rollover case to fail;
- retains the short-debounce mutation and all previous pulse-window scenarios.

At source/test commit 1f263114fe003a930028b7fa9610655b03336614 (the code/test head before the handover-only documentation commit 366a975b26abff196ca002af88bda6f8124676b5):

- Focused quarantine/poll-drain run #44145794015, job 134260428980: SUCCESS.
- ESP8266: poll-window drain 10/10; short-debounce mutation rejected; unsafe absolute-deadline rollover mutation rejected.
- ESP32: poll-window drain 10/10; short-debounce mutation rejected; unsafe absolute-deadline rollover mutation rejected.
- The same focused job also passed the inherited source-extracted quarantine, pending-marker, journal-recovery, write/readback and coin-POST-deny labs. It explicitly reports SIMULATED_ONLY=1, physical relay acceptance 0, physical coin pulse acceptance 0 and physical power-cut acceptance 0.
- Relay output run #44145794054: SUCCESS.
- Full build run #44145794034, validation job 134260616058: FAILED at QA-owned tests/controllers.sh with “Missing poll signature check”. This remains the inherited positive poll-signature assertion mismatch; preserve Master §6.3/§6.7 default-deny. Target-matrix jobs were incomplete/cancelled after validation failed; no 14/14 claim is made for this head. Production signing/import and release jobs were skipped.

This is a test-coverage improvement only; no firmware runtime source, poll contract, finance schema, migration, QA-owned test, signer, witness or release workflow changed. It is SIMULATED / CI VERIFIED, not HARDWARE ACCEPTED.

PR #318 remains a separate divergent child with the poll-edge ISR snapshot work. The UTC18 PHX-HARDWARE checkpoint records that further child-stack integration is held pending PHX-MASTER reconciliation. No rebase, cherry-pick, merge or force-push was performed.

**Production status: NO-GO.**

### Exact PR-head workflow reconciliation after handover update

At the subsequent documentation-only PR head 366a975b26abff196ca002af88bda6f8124676b5 (source/test SHA remains 1f263114fe003a930028b7fa9610655b03336614):

- Focused quarantine/poll-drain [run #44146113898](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44146113898), job 134261558308: **SUCCESS**; ESP8266 10/10 and ESP32 10/10; both injected mutations rejected.
- Relay output [run #44146113794](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44146113794), job 134261558036: **SUCCESS**.
- Full build [run #44146113976](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44146113976), validation job 134261751855: **FAILED** at QA-owned tests/controllers.sh with “Missing poll signature check”. At 2026-11-17T18:20Z, 13 target jobs had passed and Android remained in progress; no complete target-matrix result is claimed. Production import/signing and release jobs were skipped.

This addendum corrects the distinction between the exact source/test SHA and the documentation-only PR head. No production firmware runtime changed.
