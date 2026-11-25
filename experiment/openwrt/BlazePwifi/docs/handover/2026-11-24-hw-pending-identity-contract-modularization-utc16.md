# PHX-HARDWARE — pending identity contract module extraction (2026-11-24 UTC16)

**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 / Hardware #177 / DRAFT #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Starting PR HEAD:** `7eab719485dca333f06c1cac844a3fc943564e9b`  
**Source/test commit:** [`eff6e055a62068ff3b9e3606888632388121be8e`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/eff6e055a62068ff3b9e3606888632388121be8e)  
**Status:** cleanup-only refactor; poll-loop source-extracted CI steps PASS on both focused workflows; overall focused jobs still running at this checkpoint; Full validation FAILS at the inherited poll-signature assertion; physical hardware NOT TESTED; production NO-GO.

## Selected task and concrete source change

The 871-line `poll_loop_blocking_inhibit_lab.py` still contained a cohesive pending-identity/configured-ingress scenario matrix inside its board orchestration loop.

This increment extracts the 151-line scenario block into `poll_loop_blocking_inhibit_lab_pending_identity_contracts.py` (174 lines including module documentation, imports and the explicit function signature).

The new module owns:
- unmutated pending identity and attempted-evidence baselines;
- failure injection for pendingReady loss and pending identity clearing;
- deletion attempts against each of `/pending.dat`, `/pending.new`, `/pending.bak`, and `/pending.attempt`;
- pending attempt-state clearing and multi-edge delta truncation;
- relay output-gate bypass;
- separate controller/coin/relay configured-ingress baseline and fail-open mutation checks.

The runner now invokes one `run_pending_identity_matrix(...)` function and passes the board, assembly closure, compile callback, extracted source helpers and configured-ingress predicate explicitly. The runner shrank **871 → 727 lines**. Fixture constants and helper imports moved into the new module; scenario labels, C++ payloads, expected exit codes and mutation anchors were retained.

The Relay and Quarantine workflow path filters now include this narrow handover in both push and pull-request filters. Their existing ESP8266/ESP32 directory filters already cover the new module.

No production `.ino`, CGI producer, shared protocol, financial ledger, signer, witness, migration or COE destination source changed.

## Exact source/test-head evidence — `eff6e055`

**Relay Output Polarity LAB** — [run #45434405045](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45434405045)
- Source/output job `138588168583`: still running at checkpoint time.
- The exact-source poll-loop/fault-latch step 7 completed **SUCCESS**.
- Parent pulse-capture step 8 completed **SUCCESS**.
- Child poll-window timeline step 10 completed **SUCCESS**.
- Child response/pulse-window step 11 was still running.
- ESP32 boot-polarity job `138588169232`: **SUCCESS**.

**Quarantine Byte Readback LAB** — [run #45434405129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45434405129)
- Quarantine job `138588168311`: still running at checkpoint time.
- Exact-source fault-injected LittleFS/poll-loop step 4 completed **SUCCESS**.
- ESP8266 config-read recovery step 5 completed **SUCCESS**.
- Pulse-capture step 6 was still running.

**Full BlazePwifi PR validation** — [run #45434426956](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45434426956)
- Validation job `138588251163`: **FAILURE** at `Missing poll signature check` in the ESP8266 Vendo sketch.
- The other firmware/platform jobs were still running; no Full PASS is claimed.
- Candidate, signing and publication stages are skipped after validation failure.

The current main CGI producer remains blob `2e3a1430d08cc6606429a042df3b5848f53c7267`: `register|ping` and `poll` do not emit `response_sig`; inspected signatures belong to separate member endpoints. HARDWARE did not invent a positive response vector or weaken default-deny. CORE owns the authenticated producer contract; QA owns assertion reconciliation.

## Coordination and limitations

- PR #349 remains OPEN / DRAFT / UNMERGED, stacked on #347; no rebase, retarget, merge or force-push.
- Protected #239 Phase-A deny, #254 ControllerAuthV1Lab and parallel #283 remain OPEN / DRAFT / UNMERGED and untouched.
- #177 remains P0. The poll-inhibit and quiet-drain behavior remains software/CI evidence only.
- #266 remains OPEN; Master owns the global cleanup checklist and assignment matrix.
- Local tests: **NOT RUN** (no authenticated local checkout).
- Google Drive canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json`: NOT RECOVERED through this runtime; no older Library checkpoint substituted.
- Physical relay/electrical/pulse acceptance, 150 real power cuts, 30-device/24-hour soak, protected witness, durable accounting/replay, reversible v1-to-v2 migration and independent QA/Release signoff remain NOT TESTED / NOT ACCEPTED.

**Disposition:** source refactor committed; exact-source poll-loop checks have step-level CI PASS evidence; focused workflow completion pending; Full validation FAILED at the inherited CORE/QA contract mismatch; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
