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

The existing #294 validation extractor still does not include `acceptPollResponse()`; #316 full validation run `43972511250`, job `133668043447`, failed with an undeclared-function diagnostic. That shared extractor is PHX-QA-owned. The hardware-owned poll lab is now invoked by the existing focused quarantine workflow through `quarantine_readback_lab.py`; it remains absent from PHX-QA's canonical `Controller protocol parity` extractor in `blazepwifi-build.yml`.

## Cross-role contract blockers

1. Main at `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` returns poll JSON with `ok`, `insert`, `target_nonce`, `expires`, and `controller`, but no `response_sig`. With a configured key, the current firmware denies this unsigned poll response. Do not weaken that denial. PHX-CORE/MASTER must define the authenticated poll-response producer/consumer contract.
2. Keyless poll admission was changed to default-deny in the UTC01 follow-up below: `signatureOk` starts false and only a nonempty provisioned key plus a matching `response_sig` can authorize. Setup/bootstrap remains non-authorizing. PHX-CORE/MASTER still must approve the provisioning and signed-response contract; no keyless admission is allowed.
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

## 2026-11-17 UTC01 — strict root-only poll status parsing

At the pre-fix exact head \`f99dc2bd4ff28efec73f8da6e188bae514147c72\`, both sketches gated poll acceptance with \`response.indexOf("\\"ok\\":true")\`. That searches the entire byte string rather than the root JSON object, so a nested \`controller.ok\` field or quoted text could satisfy the status check. The poll signature binds \`insert\`, \`target_nonce\`, and \`expires\`, but not the separate \`ok\` status field; the root status therefore must be unambiguous.

Both ESP8266 and ESP32 now use a bounded \`pollJsonTopLevelTrue(response,"ok")\` scanner:
- requires one unescaped root-level \`ok:true\`;
- ignores nested object/array keys and string-content decoys;
- rejects duplicate root \`ok\` keys, escaped property names, invalid scalar values, top-level trailing commas, unbalanced nested values, and trailing bytes;
- caps nested composite depth at 16 and uses fixed stack storage;
- changes no controller schema, response-signature formula, provisioning path, or financial behavior.

The hardware poll lab now extracts the actual scanner helpers from each sketch as well as \`acceptPollResponse()\` and \`applyOutputs()\`. It adds 13 root-parser cases and a ninth end-to-end poll-denial case. The existing PHX-HARDWARE focused workflow already invokes \`quarantine_readback_lab.py\`; that lab now invokes the poll lab, so the new tests run without modifying RELEASE-owned workflow files or PHX-QA-owned \`tests/controllers.sh\`.

The general \`jsonString\`, \`jsonTrue\`, and \`jsonInt\` helpers remain unchanged; this is a narrow root-\`ok\` parser, not a claim that the entire firmware JSON parser has been replaced. The main-branch controller poll still omits \`response_sig\`, so configured-key admission remains default-deny pending the CORE/Master producer-consumer contract. The RAM-only quarantine latch and durable rejected-event marker also remain unresolved.

Exact-head focused CI is required before this change can be called CI VERIFIED. The full BlazePwifi workflow remains separately blocked by the QA-owned controller-parity extractor that does not yet include \`acceptPollResponse()\`.

No physical relay, coin, power-cut, electrical, finance, migration, flashing, reset, release, or deployment operation occurred.


## 2026-11-17 UTC01 — legacy brace-check compatibility correction

The first exact-head full workflow after the root-status parser change reached the existing v05_firmware_hardening_test.sh brace counter and failed at ESP8266 source line 600. That legacy check counts raw opening and closing brace characters without lexing character literals. The new parser had used brace character constants, so the checker reported a false-positive unmatched delimiter at the helper close.

The hardware-owned parser now uses the equivalent ASCII delimiter values 123 and 125 instead of brace character literals. This preserves the scanner's behavior while remaining compatible with the repository's existing raw brace counter. No QA-owned test or RELEASE-owned workflow was edited.

Exact failing evidence: full run [43995933844](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43995933844), validation job 133747891212, Controller protocol parity step. The focused hardware run at the first head 64b9683cbabcd329dadee11ed974e6102f8710e4 was still queued when this note was written; it is not counted as passing. Re-run both focused and full workflows at the new exact head and inspect any subsequent QA extractor result separately.

No physical, financial, migration, flashing, reset, release, or deployment operation occurred.


## 2026-11-17 UTC01 — poll lab fixture repair and keyless regression

At the pre-fix PR #315 head \`d5bb5d482f96c3ed1829a74fcaf2bb1c404a70df\`, the exact-head focused workflow [43996442006](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43996442006), job \`133749556034\`, executed the quarantine source lab successfully (17/17 per board, 34/34 total), then failed while compiling the hardware-owned poll lab. Its C++ stub did not declare \`pinConfigSafe\`, which the actual extracted \`applyOutputs()\` function reads. This was a test-fixture compile failure, not a firmware target compile failure.

The full BlazePwifi run [43996442210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43996442210) also completed with validation job \`133749557166\` failed at the QA-owned Controller protocol parity extractor: it extracts \`loop()\` but not \`acceptPollResponse()\`, so the generated host source reports the helper undeclared for ESP8266 and ESP32. Actual ESP8266 compile job \`133749557234\` and ESP32 compile job \`133749557313\` both passed. Target image builds completed successfully; production sign/import/publish jobs were skipped.

This follow-up makes only hardware-owned lab/handover changes:
- Adds \`pinConfigSafe\` to the host stub so the actual output gate compiles without weakening it.
- Adds an empty-key positive-response regression with a nonempty \`response_sig\`-shaped value; both board-shaped runs must reject it, clear stale target/insert state, and leave relay/LED OFF after poll suspension is released.
- Raises the poll-lab result from 9/9 to 10/10 scenarios per board; the strict root-JSON parser remains 13/13.
- The existing focused hardware workflow already reaches this lab through \`quarantine_readback_lab.py\`; no RELEASE-owned workflow or QA-owned \`tests/\` file was changed.

The firmware's keyless default-deny fix was already present at the parent head: \`signatureOk=false\`, and only a nonempty provisioned key plus a matching response signature can authorize a positive poll. This commit adds exact-source regression coverage; it does not change runtime firmware or the controller API.

Outstanding:
- PHX-QA must update its canonical Controller protocol parity extractor to include \`acceptPollResponse()\` and independently run the poll lab at the new exact head.
- PHX-CORE/MASTER must approve the signed poll producer/consumer contract. Main still does not emit \`response_sig\`; configured-key responses therefore remain fail-closed.
- The quarantine \`journalRecoveryRequired\` latch is RAM-only; durable rejected-event/replay disposition still needs a CORE/MASTER contract and QA reboot-failure proof.
- Physical relay polarity/timing, coin waveform, 150 real power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected signer/witness, v1-to-v2 migration, durable accounting/replay and independent release signoff remain NOT TESTED / BLOCKED.

No QA-owned tests, RELEASE-owned workflows, shared API, finance source, migration, signing, physical hardware, flashing, reset, merge, release or deployment were changed or performed.


## 2026-11-17 UTC02 — enforce minimum debounce and exercise the poll-intake guard

**Source finding at parent `b21d05822772e7c07299331d2a6a1670da2b077e`:** Master Architecture Contracts §2.1 requires a minimum 20 ms stable signal before an edge is recognized, but the ESP8266 remote configuration and ESP32 persisted, remote, and setup-portal configuration paths accepted values as low as 1 ms. Because `beginPollWindow()` also uses `runDebounceMs` for its post-inhibit quiet interval, a 1 ms configuration could shorten both pulse debounce and the poll check-to-inhibit guard below the existing architecture requirement.

**Hardware-owned repair:**
- Added `boundedCoinDebounceMs()` to both sketches; all owned configuration ingress paths now clamp to 20–2000 ms.
- ESP8266 remote poll configuration uses the helper.
- ESP32 NVS load, controller configuration, and local setup portal all use the same helper.
- No controller schema, response signature, receipt, finance, or provisioning API changed.
- Expanded the existing hardware-owned `poll_response_failclosed_lab.py` to compile the actual debounce clamp, `coinLineIdle()`, `canStartPoll()`, `coinLineQuietAfterInhibit()`, `beginPollWindow()`, and `applyOutputs()` from both sketches.
- The new lab checks the clamp boundary, active line at poll entry, pending pulse/group, pending journal, unavailable filesystem, a 30 ms pulse beginning 19 ms after inhibit, stable quiet-line admission, active-high polarity, and source ordering that places `beginPollWindow()` before the blocking poll and response validation before inhibit release.

**Evidence state at commit preparation:** source change and hardware-owned test extension prepared; exact-head GitHub Actions result pending. All host scenarios are simulated. Physical coin waveform, relay polarity, mechanical coin transit, electrical recovery, 150 power cuts and 30-device soak remain NOT TESTED.

**Next:** inspect the exact-head focused run; preserve any RED, then request independent PHX-QA reproduction and PHX-MASTER review of the 20 ms contract alignment. No flash, reset, live money, migration, merge, release or deployment.


## 2026-11-17 UTC02 — first exact-head regression RED and harness correction

At source commit `5d8776be4fc6bf915bf52f463224a130703f666c`, focused run [44006268728](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44006268728), job `133782278742`, executed the inherited quarantine suites (34/34) and poll-response suites (10/10 per board) successfully, then failed in the new poll-window extension because its Python source extractor was called with a full C++ signature rather than the function name and did not yet recognize the `uint16_t` return type. This is a genuine test-harness RED; no firmware runtime failure was reported by that step.

The full build [44006269369](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44006269369) separately failed in the existing PHX-QA-owned Controller protocol parity extractor (job `133782280822`) because it still does not extract `acceptPollResponse()`. That is the known QA-owned integration blocker; PHX-HARDWARE did not edit `tests/controllers.sh`.

Follow-up corrects the hardware-owned extractor to accept `uint16_t` functions and pass function names, then re-runs the actual debounce/poll-window bodies. ESP32/ESP8266 compile jobs from the full run were still in progress at this checkpoint; no compile result is inferred.

No physical coin acceptor, relay, power-cut or financial operation was performed.


## 2026-11-17 UTC02 — Arduino prototype-order RED and correction

The first full build at source commit `b30bbee26c29fbc30cc02ef8ba6ff9864c23d5a0` exposed a genuine ESP8266 compile failure: the new `boundedCoinDebounceMs()` definition sat before `struct PendingRecord`, and Arduino's prototype generation emitted later `PendingRecord` function declarations before the type. Full run [44006532865](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44006532865), ESP8266 job `133783230092`, failed with `PendingRecord does not name a type` at `pendingChecksum` / `readPendingFile`. This is retained as a real RED; it was not a test-only issue.

The focused run at the same commit [44006532858](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44006532858), job `133783130977`, passed the new poll-window/debounce lab after the earlier extractor correction:
- debounce floor 8/8;
- poll-window guard 8/8 per board;
- poll-response 10/10 and strict root JSON 13/13 per board;
- quarantine 34/34, mount/output 14/14, boot recovery 32/32, pending-clear 22/22, pending write/readback 44/44, coin POST gate 18/18.

This follow-up moves the helper below `PendingRecord` in both sketches to preserve Arduino prototype ordering. The existing full validation still independently fails in the PHX-QA-owned `tests/controllers.sh` Controller protocol parity extractor because it omits `acceptPollResponse()`; PHX-HARDWARE did not edit that QA-owned file. ESP32 compilation from the prior full run was still in progress at this checkpoint and is not counted.

No physical coin, relay, power-cut, electrical or financial operation occurred.


## 2026-11-17 UTC03 — separate poll admission from remote configuration

At parent `919c1fd96144a2ee0ef59fbaab8cab767f9f6034`, source review found that both `acceptPollResponse()` implementations verified an admission signature over only the poll tuple (controller ID, request nonce, insert bit, target nonce and expiry), then passed the same response to `applyRemoteConfig()`. That function can change controller/coin/relay/LED enable flags, GPIO pins and polarity, debounce, pulse grouping and Wi-Fi retry settings. Those configuration fields are not included in the approved admission-signature expression.

Exact producer readback:
- Experiments main poll body (blob `2e3a1430d08cc6606429a042df3b5848f53c7267`) returns `ok/insert/target_nonce/expires/controller`, without a response signature or config fields.
- COE PR #26 candidate poll body (blob `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e`) adds `response_sig` for the poll tuple, but still does not provide a separately authenticated configuration object or `config_revision`.

A LAN/on-path response modifier could append configuration fields while preserving a valid admission signature, and the firmware would apply those fields as if authenticated. This is a source-confirmed consumer trust-boundary defect; no physical actuation was attempted.

**Fix:** both ESP consumers now stop after applying the authenticated admission state. They no longer call `applyRemoteConfig(response)` from the poll response. The existing remote-config helper remains dormant until PHX-CORE/MASTER define a separate authenticated configuration contract and PHX-QA verifies its exact canonical bytes. This does not change the current producer API or the admission signature algorithm.

**Regression:** the hardware-owned source-extracted poll lab now injects a valid signed positive admission response carrying hostile extra config fields. The test requires relay/LED admission to follow the valid poll tuple while all local GPIO, polarity, debounce and revision sentinels remain unchanged; the stub fails the test if `applyRemoteConfig()` is called. The poll matrix is now 11 cases per board; exact-head CI is pending.

**Coordination required:** PHX-CORE/MASTER should decide whether remote configuration is needed and, if so, define a separate config signature over every applied field (including revision, enable flags, pins, polarities and timing bounds). PHX-QA should independently reproduce the config-injection regression at this exact head. No shared API, finance code, QA-owned tests, release workflow, migration or destination repository was changed.

No physical coin acceptor, relay, power-cut, electrical or financial operation occurred.


## 2026-11-17 UTC03 — focused poll/config lab fixture RED and correction

The first exact-head focused run after the config-isolation change, [44008391400](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44008391400), job `133789169313`, correctly executed both quarantine source suites (34/34 total) and then failed to compile the poll lab host stub: `runRelayActiveHigh` was declared twice in the test-only C++ fixture. The production sketches compiled separately in the full build; this RED is isolated to the hardware-owned test fixture.

Correction: the fixture now declares only the new `runCoinActiveLow` sentinel and reuses its existing `runRelayActiveHigh` variable. The stub still mutates both values if the forbidden `applyRemoteConfig()` call occurs, so the regression remains sensitive to the original trust-boundary defect.

The full build at this source head [44008391473](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44008391473) also has the known PHX-QA-owned validation failure: `tests/controllers.sh` extracts `loop()` without `acceptPollResponse()`, causing an undeclared-helper compile error on both board harnesses. PHX-HARDWARE did not edit QA-owned tests. Target builds were still running at the time of this handover update.

No physical coin acceptor, relay, power-cut, electrical or financial operation occurred.


## 2026-11-17 UTC03 — exact-head poll/config regression result

After correcting the test-only duplicate declaration in `853d2ada6d7111cfdc044fb73475ffb2d90c9085`, focused workflow [44008556093](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44008556093), job `133789714381`, completed **SUCCESS** at that exact source head:
- Poll-response/config-isolation: **11/11 per board**.
- Strict root JSON: **13/13 per board**.
- Debounce floor: **8/8 per board**.
- Poll-window guard: **8/8 per board**.
- Quarantine: **34/34 total**.
- Fake-LittleFS mount/output: **14/14 total**.
- Boot recovery: **32/32 total**.
- Pending-clear protection: **22/22 total**.
- Pending write/readback: **44/44 total**.
- Coin POST gate: **18/18 total**.

All are source-extracted host/fake-filesystem simulations. The workflow explicitly reports physical coin acceptor and production financial authorization as false.

Full BlazePwifi run [44008556084](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44008556084) had validation job `133789824548` **FAILED** because the PHX-QA-owned `tests/controllers.sh` extractor still omits `acceptPollResponse()` from the extracted `loop()` harness. ESP8266 target compile `133789824864` **PASS**; ESP32 compile `133789824811` and several optional target/Android jobs were still in progress at the `2026-11-17T03:14:00Z` observation. No overall full-workflow success is claimed.

The prior test-only RED at [44008391400](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44008391400) is retained above: it was caused by a duplicate `runRelayActiveHigh` declaration in the hardware-owned C++ stub and was corrected in `853d2ada`. No production firmware failure was reported by that run.

**Next:** PHX-QA must independently repair and rerun the canonical extractor at the current exact PR head; PHX-CORE/MASTER must approve a separate authenticated remote-config contract before any remote config is re-enabled. Physical pulse/relay behavior, 150 power cuts, 30-device 24-hour soak and electrical recovery remain NOT TESTED.


## 2026-11-17 UTC03 — register-response configuration authority denied

PHX-MASTER's current DRAFT #288 contract at `fc9ba1391908f8d49d8f9e9c578e43b49e21417`, §6.4, identified a separate residual trust boundary after the poll-path configuration isolation: both `connectSta()` implementations still called `applyRemoteConfig(r)` on a positive register response. The register signature binds the register tuple only; it does not bind the returned controller configuration. With an empty key, the old `sigOk=true` default also treated the response as accepted.

**Test-first evidence:** test-only commit `b4b46452b9f17acb8bd5e4347322f10874ec9b6f`, focused workflow [44012633615](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44012633615), job `133803015218`, **COMPLETED FAILURE as the expected source RED**. The new source-extracted register lab compiled both production `connectSta()` bodies and observed the unsafe configuration mutator on both ESP8266 and ESP32 (scenario 1, exit 11). All preceding quarantine, poll, strict JSON, debounce and poll-window suites in that same job passed. This is host simulation, not a network or hardware test.

**Source correction in this follow-up:** both `connectSta()` functions retain the register/status request but discard its response. The helper `applyRemoteConfig()` remains present for future use but is explicitly documented as dormant. There is no remaining call site from either register or poll admission. No shared API, crypto algorithm, configuration schema, GPIO default, finance/ledger, QA-owned test directory or release workflow was changed.

**Acceptance boundary:** remote configuration stays disabled until PHX-CORE defines a separate domain-separated configuration envelope and PHX-QA independently verifies canonical positive/negative golden vectors, identity/nonce/revision/freshness binding and atomic persistence behavior. This is not an assertion that remote configuration has been replaced or that the controller is production interoperable.

**Remaining blockers:** canonical QA `tests/controllers.sh` still omits `acceptPollResponse()`; configured-key poll producer/consumer compatibility and the shared signature golden vector remain unverified; quarantine failure disposition is still RAM-only across reboot; protected signer/witness, durable accounting/replay, v1-to-v2 migration, physical 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery and independent QA/release acceptance remain open. No flashing, reset, live money, migration, merge, release or deployment.


## 2026-11-17 UTC03 — register tuple verification retained; config mutation remains denied

The first source correction removed the register response parser entirely. Exact full workflow [44012826068](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44012826068), validation job `133803739259`, then failed in the pre-existing QA-owned `tests/v05_firmware_hardening_test.sh` because it requires the register signature construction marker `|register|`. This was a compatibility/test-contract RED; the focused hardware-owned lab at [44012826028](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44012826028), job `133803638627`, had already passed all source-extracted suites including register-config denial 7/7 per board.

The corrected implementation **retains verification of the register tuple** when a provisioned key exists, but does not use that result to authorize any configuration mutation. Empty key, missing signature or invalid signature are logged as unauthenticated; even a valid register-tuple signature cannot call `applyRemoteConfig()`. The test lab now also asserts that the register signature verifier runs for provisioned keys and is skipped for keyless bootstrap, while configuration state remains unchanged in every case.

The `applyRemoteConfig()` helper remains explicitly dormant. The canonical QA test directory and workflow were not modified. A new exact-head focused and full CI result is required after this follow-up.


## 2026-11-17 UTC03 — exact-head register-config denial evidence

**Source behavior commit:** `f4cf215300c432f989b4f806594e7c963b2764ed`.

**Focused exact-head workflow:** [44013023461](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44013023461), job `133804269560`, **COMPLETED SUCCESS**:
- register-response config denial: 7/7 per board (keyless positive, valid register-tuple signature with hostile config, invalid signature, missing signature, nested positive marker under top-level denial, disconnected Wi-Fi, empty SSID);
- poll/config isolation: 11/11 per board;
- strict root JSON: 13/13 per board;
- debounce floor: 8/8 per board;
- poll-window guard: 8/8 per board;
- quarantine failure injection: 34/34 total;
- mount/output: 14/14 total;
- boot recovery: 32/32 total;
- pending-clear: 22/22 total;
- pending write/readback: 44/44 total;
- coin POST gate: 18/18 total.
All are source-extracted host/fake-filesystem simulations; physical acceptance is not inferred.

**Full workflow:** [44013023437](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44013023437) remains **IN PROGRESS** at the latest snapshot, but validation job `133804366550` is **FAILED**. Its raw log shows PHX-QA-owned `tests/v060_esp_poll_intake_guard.py` compiles the production `loop()` without extracting `acceptPollResponse()`, causing an undeclared-function compile error for both board harnesses. ESP8266 job `133804366196` PASS; ESP32 and several remaining target/Android jobs were still running. Production signing/import/publish and v0.4 candidate/simulation jobs are skipped. No overall full-workflow success is claimed.

The earlier full-validation compatibility RED at `882407d5...` was due the static hardening test requiring the register signature marker; the final source retains provisioned-key register-tuple verification while keeping configuration application disabled. The new hardware-owned lab additionally checks the whole sketch has exactly one `applyRemoteConfig(` occurrence (the dormant function definition only), preventing any poll/register call site from silently returning.

**Ownership:** no QA-owned tests, shared API/schema, CORE financial source, Master coordination files, release workflow, or other role's source was changed. PHX-QA must repair its extractor. Remote config remains disabled until PHX-CORE defines a separate domain-separated config envelope and PHX-QA approves exact golden vectors.


## 2026-11-17 UTC05 — durable one-shot coin POST attempt marker

See [the narrow PHX-HARDWARE handover](2026-11-17-hw-pending-post-attempt-marker.md). The current #315 source writes and verifies `/pending.attempt` before a coin POST, blocks same-boot retries, and makes any marker a boot-time reconciliation stop. The durable pending record is removed before the marker. The source-extracted lab is wired into the existing focused quarantine workflow via `quarantine_readback_lab.py`. This is a proposed hardware-journal implementation of Master Architecture Contracts §6.2, pending PHX-CORE / PHX-MASTER agreement and independent PHX-QA exact-head verification. Physical flash durability remains NOT TESTED.
