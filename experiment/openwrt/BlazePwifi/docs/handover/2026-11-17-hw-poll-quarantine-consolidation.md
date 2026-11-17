# PHX-HARDWARE handover: consolidated poll and quarantine fail-closed stack

- Role: PHX-HARDWARE
- Tasks: #172 / #177 / #266
- Repository: BlazeDevStudio/BlazingSystems-Experiments
- Branch: `phoenix/hardware-quarantine-append-failclosed-20261117`
- Existing draft PR: #315 (reused; no new PR opened)
- Linear parent before consolidation: #315 head `d771e78f23b6304945e0fdd466b2d52c46c2a33a`
- Initial consolidation commit: `d771e78f23b6304945e0fdd466b2d52c46c2a33a`
- Current follow-up: hardware-owned host-lab stubs now declare the active target required by the stronger output gate
- Status: DRAFT / CI RECHECK REQUIRED / NOT HARDWARE ACCEPTED / PRODUCTION NO-GO

## Consolidated firmware scope

The existing #315 quarantine behavior is retained on both ESP8266 and ESP32:
- failed quarantine append latches `journalRecoveryRequired` while a pending event exists;
- same-boot coin POST eligibility remains denied;
- pending evidence is not cleared after an unsuccessful append.

The #316 poll-response behavior is now applied on top of that same linear #315 stack:
- poll intake remains suspended while the synchronous reply is checked;
- empty, denied, malformed-by-current-check, or unauthenticated responses clear stale positive `insertMode` and `activeTarget`;
- only an accepted positive response with a nonempty target nonce can restore admission;
- `applyOutputs()` independently requires a nonempty active target before energizing relay/LED;
- a fresh negative insert response remains disabled.

The hardware-owned poll lab compiles the actual `acceptPollResponse()` and `applyOutputs()` functions from both sketches and now includes eight source-extracted scenarios per board, including targetless positive-response denial and output-gate defense in depth.

## Test integration and first RED

At initial consolidation commit `d771e78f23b6304945e0fdd466b2d52c46c2a33a`:
- quarantine source lab completed 17/17 per board (34/34 total);
- focused workflow `43981880216`, job `133700135785`, failed in `journal_mount_failclosed_lab.py` because its test-only C++ stub did not declare the newly referenced `activeTarget`;
- this was a genuine fixture compile failure, not hidden or reclassified.

This follow-up adds `activeTarget` to the two hardware-owned host fixtures that compile `applyOutputs()`: `journal_mount_failclosed_lab.py` and `pending_journal_recovery_lab.py`. No QA-owned `tests/` or RELEASE-owned `.github/workflows/` files were changed. Exact-head reruns are required.

The existing #294 validation extractor still does not include `acceptPollResponse()`; #316 full validation run `43972511250`, job `133668043447`, failed with an undeclared-function diagnostic. That shared extractor is PHX-QA-owned. The new poll lab remains hardware-owned and is not yet wired into the canonical validation workflow.

## Cross-role contract blockers

1. Main at `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` returns poll JSON with `ok`, `insert`, `target_nonce`, `expires`, and `controller`, but no `response_sig`. With a configured key, the current firmware denies this unsigned poll response. Do not weaken that denial. PHX-CORE/MASTER must define the authenticated poll-response producer/consumer contract.
2. The current helper still treats an empty controller key as no signature requirement. Master §6.1 proposes default-deny for keyless poll admission; PHX-CORE and PHX-HARDWARE must agree the bootstrap/provisioning boundary before changing this behavior. It is not production-safe evidence.
3. The quarantine failure latch remains RAM-only. A durable rejected-event marker/reconciliation contract is required before reboot-safe non-replayability can be claimed.

## Ownership and acceptance boundaries

- #315 remains the single owner-controlled linear hardware stack, based on #314.
- #316 remains an open parallel DRAFT for Master to mark superseded/close only after reviewing the consolidated head; do not merge #316 independently.
- PHX-QA must update its canonical source extractor to include `acceptPollResponse()`, independently run the eight poll scenarios per board and the quarantine/mount/recovery labs at the consolidated exact SHA.
- No API, receipt schema, finance, migration, witness, release workflow, or production code outside ESP firmware and hardware-owned lab stubs was changed.
- Physical relay polarity/timing, coin waveform, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected signer/witness, v1-to-v2 migration, and independent release acceptance remain NOT TESTED / BLOCKED.

No flashing, reset, live money, production migration, release, or deployment occurred.


## 2026-11-16 UTC23 exact-head CI recheck and follow-up RED

At `08f5e7e25a3012fbca7a57c1674e6853304c592b`:
- Focused run [43982182229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43982182229), job `133701149610`: **PASS** — quarantine 34/34, mount/output 14/14, pending boot recovery 32/32, pending-clear 22/22, pending write/readback 44/44, coin POST gate 18/18.
- Full run [43982182265](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43982182265): validation job `133701275035` **FAILED** because the QA-owned #294 source extractor does not extract `acceptPollResponse()`. ESP8266 compile job `133701275574` also **FAILED** on an incorrectly escaped JSON literal in the new helper; this was a real production-source compile error and is corrected in the following commit. ESP32 compile and several target jobs were still running at handover time.
- The poll-response lab itself remains **NOT RUN** in CI; QA must wire it into the canonical extractor/workflow. No local C++ execution is claimed because this container could not resolve GitHub DNS.

The follow-up source patch changes only the JSON string-literal escaping in both board helpers and the matching targetless-response lab fixture. It does not change authentication policy, API bytes, financial state, or the fail-closed target requirement.

## 2026-11-17 UTC00 — keyless poll authority RED probe

At the consolidated firmware source 939e6ae09050e3e7244249acf9c7969301a05363, both acceptPollResponse() implementations initialize signatureOk=true and only require response_sig when cfg.key is nonempty. With an empty key, an ok:true, insert:true, nonempty target_nonce response is accepted; after the poll suspension is released, applyOutputs() can energize the relay and LED.

**Local simulated reproduction:** a host C++ harness compiled the exact acceptPollResponse() and applyOutputs() function bodies read from both sketches at that source SHA. With an empty ESP8266-shaped key and an empty ESP32 String key, the positive unsigned response was accepted and both outputs became enabled. Both board-shaped runs returned the expected RED sentinel (42). This is a source-function simulation, not Wi-Fi, GPIO, relay, coin-acceptor, or hardware evidence.

Added hardware-owned diagnostic probe:
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_keyless_authority_red.py
- Probe commit: bd67d8a7d498b0d53a7da132bff0a3a85923635d
- It extracts the production helper and output gate from both sketches and is expected to exit nonzero while the keyless gap remains. It is an audit RED probe, not a passing safety test; it is not yet wired into canonical CI and was not run as a full repository checkout in this activation.

**No firmware behavior was changed.** Master architecture contract §6.1 is explicitly provisional pending PHX-CORE / PHX-HARDWARE agreement on the keyless bootstrap/provisioning boundary. The current main controller register/poll responses also do not emit response_sig; do not weaken authentication to restore interoperability. PHX-CORE/MASTER must decide the producer/consumer contract and bootstrap path before the firmware guard is changed. PHX-QA/RELEASE should review and wire the RED probe only after the contract is accepted.

Next exact action: PHX-CORE and PHX-MASTER publish the keyless/bootstrap and signed poll-response decision; then PHX-HARDWARE implements the approved fail-closed behavior and PHX-QA independently runs the source-extracted probe plus the existing poll/quarantine suites at the new exact head.
## 2026-11-17 UTC01 — keyless poll admission default-deny fix

Master's current role-routing snapshot at PR #288 head d047c49419c920a546ff9438f2fc9e708566f78a explicitly assigns the firmware correction to PHX-HARDWARE, the signature/replay contract to PHX-CORE, and the canonical extractor/negative tests to PHX-QA. Architecture Contracts §6.1 requires that an empty key is not authentication success.

Both ESP8266 and ESP32 acceptPollResponse() helpers now initialize signatureOk=false. Only a nonempty provisioned cfg.key plus a nonempty response_sig matching the existing expected digest can set it true. Empty-key bootstrap can no longer authorize a positive poll. This changes no controller endpoint, response bytes, key provisioning, receipt schema, or finance behavior; setup/bootstrap remains non-authorizing.

Runtime-source commits:
- ESP8266: 24525767ebb8371d9a5b5460c7ae652b143a9439
- ESP32: 1ea307966979cc7ed6d67962b0e22f98cbb516c3
- Source-extracted keyless regression probe update: 44f0255ee9957ddbf3aa12d6d9b18983fcec2b6e

**Local simulated check:** a host C++ harness using the exact current acceptPollResponse() and applyOutputs() bodies/board-shaped configuration compiled with g++ for ESP8266-shaped and ESP32-shaped stubs. An unsigned ok:true/insert:true/nonempty-target response with an empty key was denied on both; simulated relay and LED remained OFF (both exit 0). This is SIMULATED control-flow evidence only. The source-extracted Python probe is updated to act as a regression check but remains NOT RUN in canonical CI.

**Exact CI at the prior branch head:** focused run 43991222383 job 133731991733 PASSes quarantine byte-readback only. Full run 43991222301 COMPLETED FAILURE at validation job 133732116541 because the QA-owned extractor omits acceptPollResponse() and generated C++ reports it undeclared for both boards. ESP8266 job 133732116666 and ESP32 job 133732116647 both PASS; all listed target/Android builds PASS. Production import/sign, publication and v0.4 candidate/simulation jobs were skipped. The new keyless probe was not executed by either workflow.

Configured-key positive authorization remains unavailable until PHX-CORE supplies the approved signed poll response producer/consumer contract; main currently returns no response_sig, so firmware continues to deny those unsigned replies. PHX-QA must update the extractor and independently execute the keyless probe plus poll/quarantine suites at the new exact head. PHX-RELEASE must wire the hardware-owned probe into a canonical workflow. The RAM-only rejected-event latch and durable reboot disposition remain open.

No physical coin/relay test, power cut, electrical pulse test, flash, reset, migration, live money, merge, release or deployment occurred.
### Keyless regression positive control and CI retry status

A second local host C++ positive-control run used a nonempty test key and matching stub response signature. Both ESP8266-shaped and ESP32-shaped builds accepted the signed positive response and enabled the simulated outputs (exit 0). Together with the empty-key negative case above, this verifies the intended local branch split: provisioned + matching signature may authorize; empty key cannot. Both are SIMULATED control-flow checks, not controller interoperability or hardware acceptance.

The first full workflow associated with the firmware commits was cancelled after later branch commits. The attempted job retry at source commit 1ea307966979cc7ed6d67962b0e22f98cbb516c3 re-ran validation job 133736710809, which again failed because the QA-owned extractor did not declare acceptPollResponse(); the remaining board/target jobs in that run were cancelled. Focused quarantine run 43992328925 job 133735792206 completed success, but it tests only quarantine byte-readback and does not compile or execute the poll helper. A final exact-head full build must be allowed to complete after the last source/test commit.

Do not describe the poll-response regression probe as CI-verified until PHX-QA/PHX-RELEASE wire it into canonical validation and an exact-head job executes it.