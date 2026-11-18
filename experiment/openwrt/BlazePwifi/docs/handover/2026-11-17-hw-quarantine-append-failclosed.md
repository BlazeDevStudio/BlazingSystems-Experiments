# PHX-HARDWARE handover: quarantine failure blocks same-boot coin retries

- Role: PHX-HARDWARE
- Scope: ESP32 and ESP8266 quarantine failure gating only
- Parent: DRAFT [PR #314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/314), exact head `556adc20ef0cfd355089aff3b979c0169af79bdd`
- Branch: `phoenix/hardware-quarantine-append-failclosed-20261117`
- Status at handoff: source change committed; exact-head CI pending; **NOT HARDWARE ACCEPTED**

## Proven defect

`appendQuarantineRecord()` can refuse an append before writing when the quarantine log is over its size limit or LittleFS cannot open it for append. In those cases `journalRecoveryRequired` was not set. `quarantinePending()` correctly retained the pending record and returned false, but `canAttemptCoinPost()` remained true while the filesystem and pending flags otherwise looked healthy. The loop could therefore resend the same event after the controller had already rejected it and local quarantine persistence had failed.

## Change

Both board sketches now:
- return without latching when there is no pending pulse event;
- latch `journalRecoveryRequired` on every failed quarantine commit, including pre-write open/capacity refusals;
- preserve pending RAM and filesystem evidence and prevent further same-boot coin POST attempts through the existing `canAttemptCoinPost()` gate;
- rely on the existing caller's `applyOutputs()` to keep the relay/LED admission path disabled.

The exact-source quarantine lab now extracts the real `canAttemptCoinPost()` function for both boards. Existing scenarios 4 (append-open failure) and 10 (capacity exceeded) now require an explicit recovery latch, unchanged quarantine bytes, no clear call, no POST eligibility, and a hard stop after simulated reboot while the underlying failure persists. The suite remains 17 scenarios per board / 34 total.

## Important limitation requiring cross-role decision

`journalRecoveryRequired` is RAM-only. This patch prevents repeat POSTs during the current boot; it does **not** add a durable marker for a rejected event whose quarantine append failed. If a transient append failure clears across reboot, the still-valid pending record may again become POST-eligible before a new quarantine write. No pending-record schema, receipt, API, finance, or migration change was made. PHX-CORE/MASTER must define a durable rejected-event/reconciliation contract with PHX-QA before claiming reboot-safe handling of this case.

## Boundaries and next action

No controller API, response-signature formula, receipt schema, finance, migration, release workflow, flashing, reset, physical test, or production state changed. DRAFT remains stacked on #314 and must not merge independently. PHX-QA should independently reproduce open-failure and capacity-exhaustion behavior at the exact head; PHX-CORE/MASTER should decide the durable reboot marker contract. Physical LittleFS power interruption, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, signer/witness, migration, and independent release acceptance remain NOT TESTED / BLOCKED.


## Follow-up: malformed quarantine timestamps cannot authorize dedupe (2026-11-17 UTC07)

**New source-confirmed defect:** inspectQuarantineLog previously checked that a line began with TIME= and contained the other field labels, but did not validate the timestamp token. A complete-looking line with TIME=not-a-number and the current event PULSES/NONCE/TARGET/REASON prefix could be treated as an already-persisted quarantine record. quarantinePending would then call clearPending without a firmware-generated valid record.

**Test-first RED:** focused run #44041100586, job 133895620908, exact test head af0ee82becb2a005c9a2ffc16d8d79e7c6a91b5b, failed at SOURCE_QUARANTINE_FAIL scenario=17 on the ESP32 extracted source. This is a C++17 host/fake-LittleFS reproduction, not a physical flash test.

**Fix on both sketches:** inspectQuarantineLog now accepts only canonical decimal uint32 millisecond timestamps (1–10 digits, no leading zero except 0, overflow checked). Malformed and overflowed timestamps make the existing log invalid; append is denied, journalRecoveryRequired is latched, and the pending record remains untouched. No signature, receipt, API, finance, or migration contract was changed.

**Regression expansion:** the hardware-owned source-extracted lab now has 19 scenarios per board / 38 total, including nonnumeric and uint32-overflow timestamps. The board runner reports both board results. Exact-head GREEN CI is pending; the prior RED remains preserved.

**Limits:** fake LittleFS readback is not proof of flash power-loss durability. Physical coin/relay, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, signer/witness, durable accounting/replay, migration, independent QA and release acceptance remain NOT TESTED/BLOCKED. PR #315 remains DRAFT / UNMERGED / PRODUCTION NO-GO.


## Exact-head evidence — malformed timestamp regression (2026-11-17 UTC07)

The test-first commit af0ee82becb2a005c9a2ffc16d8d79e7c6a91b5b added malformed and overflow timestamp cases. [Focused RED run #44041100586](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44041100586), job 133895620908, failed at scenario 17 as intended.

Source commit efe8ee83d521139a3e3f0c8eaf60b29a9f9e4d75 corrected both board parsers. [Focused exact-head run #44041398477](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44041398477), job 133896584393, **SUCCESS**: 19/19 quarantine scenarios per board / 38/38 total, plus inherited source-extracted suites.

[Full run #44041398463](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44041398463) validation job 133896701236 **FAILED** in QA-owned poll-loop extraction because it omits five current production dependencies. The QA files were not modified. The focused fake-LittleFS result is SIMULATED/CI VERIFIED only; physical power-cut durability is NOT TESTED.


## Follow-up: quarantine disposition requires the matching attempt marker (2026-11-17 UTC09)

**Defect:** quarantinePending() relied on its current loop caller to have created /pending.attempt. The helper itself did not enforce that prerequisite. A future call path could append a quarantine line and clear the pending event without proving that the exact event had passed the durable one-shot POST-attempt gate.

**Correction:** both ESP sketches now implement pendingAttemptMarkerMatches(). It requires a ready, unambiguous pending event, a set one-shot attempted flag, bounded identity lengths, and a successfully read/validated /pending.attempt whose pulse count, nonce and target exactly match RAM. quarantinePending() denies and latches recovery before any quarantine append or pending clear if this check fails. The existing marker remains until clearPending() removes pending evidence first and the marker last.

**Regression:** hardware-owned quarantine_readback_lab.py now extracts the production helper and quarantine function. New scenarios 19–22 cover absent attempted state, absent marker, invalid marker and mismatched nonce; they require unchanged log bytes, no clear, and a hard stop after simulated loss of the RAM recovery latch. The fixture nonce was corrected to a firmware-valid 16-character value. Existing pending_attempt_marker_lab.py separately extracts the real boot loader/marker functions and verifies matching markers block reboot replay.

- Test-first RED: [run #44053916296](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44053916296), job 133938244153, failed on scenario 19 for both boards.
- Final focused GREEN: [run #44054509206](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054509206), job 133940278029, exact SHA 4602386add8150b37fdcf8252b68bf27d95bb3d9, quarantine 23/23 per board plus inherited focused suites passed.
- Full workflow: [run #44054501269](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054501269), validation job 133940390771 FAILED in PHX-QA-owned tests/controllers.sh because it requires an active poll signature check while Master §6.3 requires default-deny until the contract is approved. No QA-owned file was changed.

**Limit:** all evidence is source-extracted C++ host/fake-LittleFS simulation. The current coin receipt verifier remains default-deny; this change does not enable coin admission. Physical flash power-cut durability and all Phoenix release gates remain NOT TESTED/BLOCKED.


## PHX-HARDWARE — clearPending requires exact durable event evidence (2026-11-17 UTC09)

**Defect reproduced at parent PR #315 HEAD `84fe6b790139d147f330f13a40b3ae3e89a7042d`:** `clearPending()` allowed `candidateCount == 0`. With a valid `/pending.attempt` marker but no `/pending.dat`, `/pending.new`, or `/pending.bak`, it returned success, removed the only remaining attempt evidence, and reset the RAM event. This is unsafe: a marker-only state is ambiguous evidence and must require operator reconciliation.

**Correction:** both ESP sketches now require (1) a valid attempt marker matching the current RAM pulse count/nonce/target, (2) exactly one durable pending-journal candidate, and (3) a valid candidate whose complete record matches the marker, including checksum, before deleting anything. Missing, duplicate, corrupt, or mismatched candidates latch `journalRecoveryRequired` and preserve all files/RAM. Pending journal removal is verified before the attempt marker is removed last.

**Test-first evidence (local C++ host harness; not CI):**
- RED against the exact parent `clearPending()`: `cleared=1 marker_exists=0 pending_pulses=0 recovery=0` for an orphan-marker-only state.
- GREEN against the patched guard: 7/7 scenarios passed — orphan marker retained; valid single matching journal clears; duplicate journals retained; mismatched journal retained; mismatched marker retained; failed pending removal retains marker/RAM; failed marker removal latches recovery.
- The initial harness fixture was corrected to a firmware-valid 16-character nonce before GREEN; no production source was relaxed.

**Cross-role request:** PHX-QA owns `experiment/openwrt/BlazePwifi/tests/`. Please add the orphan-marker-only, missing-candidate, duplicate-candidate, mismatched-record, and both removal-failure cases to the canonical pending-clear exact-source lab and independently run it at this PR's exact head. PHX-HARDWARE did not edit QA-owned tests or workflows.

**Evidence classification:** local failure injection is SIMULATED. New PR exact-head CI is pending. This does not enable coin disposition; `coinPostDispositionVerified()` and `acceptPollResponse()` remain default-deny. Physical flash durability, 150 power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain NOT TESTED/BLOCKED. **PRODUCTION NO-GO.**


## Follow-up: strict quarantine-record grammar (2026-11-17 UTC12)

**Source-confirmed defect:** `inspectQuarantineLog()` previously required a canonical `TIME=` token and merely searched for the strings `PULSES=`, `NONCE=`, `TARGET=`, and `REASON=`. It did not validate the field values or exact order. A pre-existing line with a valid timestamp but `PULSES=not-a-number`, pulse count 21, empty nonce/target/reason, or a duplicate `PULSES` field could pass the prior-log scan. The new event could then be appended and its pending journal cleared despite malformed older quarantine evidence.

**Test-first RED:** test-only commit [05526c5](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/05526c5223cafdb3cbccb831ffd0884c809f363d) added six malformed-log cases (non-numeric pulses, out-of-range pulses, empty nonce, empty target, empty reason, duplicate field). Exact-source [run #44085874657](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44085874657), job `134048035810`, checked out SHA `05526c5223cafdb3cbccb831ffd0884c809f363d` and failed as expected at `SOURCE_QUARANTINE_FAIL scenario=23` on both ESP32 and ESP8266.

**Fix:** both sketches now share byte-identical `quarantineLogRecordValid()` and `inspectQuarantineLog()` logic. Every prior line must have canonical uint32 millisecond time, exactly ordered fields, pulse count 1–20, nonempty token-safe nonce (8–16 bytes) and target (8–32 bytes), and a nonempty printable reason no longer than 128 bytes. Invalid or ambiguous prior evidence blocks append, latches `journalRecoveryRequired`, and preserves the pending record. The append/readback and pending-clear sequence remains unchanged; no receipt, API, finance, replay, migration, or key contract was introduced.

**Final focused exact-source evidence:** PR #317 source/test head [`47af3a2f86b9e37a7a7855c50406a36014c30fcb`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/47af3a2f86b9e37a7a7855c50406a36014c30fcb). Quarantine [run #44086572438](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44086572438), job `134050443171`, **SUCCESS**: 29/29 scenarios per board (58/58 total), plus the inherited attempt-marker, mount, recovery, pending-clear, write/readback and coin POST-deny labs. Relay-output [run #44086572453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44086572453), job `134050443226`, **SUCCESS**; child-only poll-window checks were correctly skipped on the parent SHA. The full BlazePwifi build [run #44086572446](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44086572446) was still pending at this handover update.

**Evidence limit:** these are C++17 source-extracted host tests with fake LittleFS. They do not prove flash durability, flush/close behavior across a physical power cut, relay contacts, or coin pulse capture. Physical acceptance, 150 power cuts, 30-device/24-hour soak, electrical recovery, protected signer/witness, durable accounting/replay, v1-to-v2 migration and independent release approval remain **NOT TESTED / BLOCKED**. Production remains **NO-GO**.


## Follow-up: quarantine identity delimiter ambiguity (2026-11-17 UTC13)

**Source-confirmed P0 evidence-preservation defect:** the quarantine log is space-delimited. The prior encoder escaped control characters but left reserved field markers intact. A pending target containing ` REASON=` could be split as a reason delimiter; a prior record for a different target/reason tuple could then prefix-match the current identity. `inspectQuarantineLog()` could report `alreadyRecorded`, causing `appendQuarantineRecord()` to return success and `quarantinePending()` to clear the current pending journal without a distinct record.

**Test-first RED:** [commit 51528cc](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/51528cc3782cc64380196550ff2b213541a212f6) adds collision, whitespace-token, reserved-reason-marker and ambiguous-existing-log cases. [Run #44096424039](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44096424039), job `134084616687`, checked out the exact test SHA and failed at scenario 29 on both ESP32 and ESP8266 as expected.

**Correction on both sketches:** `quarantineLogTokenValid()` rejects whitespace/control characters in nonce/target before any append; `quarantineLogField()` escapes the leading space of reserved ` TARGET=` / ` REASON=` markers as literal `\\x20`; the parser rejects a nested raw ` REASON=` in the reason tail so ambiguous legacy records fail closed; and `appendQuarantineRecord()` validates its complete generated record with the production parser before touching LittleFS. Any invalid token or ambiguous old log latches recovery and preserves pending evidence. No receipt/API, finance, replay, migration or controller-auth contract changed.

**Exact-source GREEN:** final source/test head [`2bdf494`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/2bdf4945ec043a4493b33334b136d34662c97aee). [Quarantine run #44096806381](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44096806381), job `134085961421`, **SUCCESS**: 33/33 scenarios per board (66/66 total), including all four new delimiter/ambiguity cases; inherited attempt-marker 28/28 per board, mount 14/14, boot recovery 32/32, pending-clear 34/34, write/readback 22/22 per board and coin POST-deny 20/20 also passed. [Relay-output run #44096806289](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44096806289), job `134085966578`, **SUCCESS**: 48/48 per board; both polarity and poll-inhibit mutations rejected on both boards.

**Evidence limit:** source-extracted C++17 host tests with fake LittleFS only. `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `FINANCIAL_PRODUCTION_AUTHORIZED=0`. Physical flash durability, relay contact polarity, coin pulses, 150 power cuts, 30-device/24-hour soak and electrical recovery remain NOT TESTED. Full BlazePwifi build/validation is tracked separately; no release claim is made. Production remains NO-GO.


## UTC15 — ESP32/ESP8266 pending and quarantine safety-helper parity

**DRAFT PR #317 remains OPEN / UNMERGED / NO-GO.** Branch phoenix/hardware-clear-pending-marker-match-20261117. Source/test SHA: f74cd39aaf9045258f5374dd39b1542a142a8424.

### Change

The hardware-owned quarantine_readback_lab.py now extracts 11 safety-critical production helpers from both sketches and requires byte-for-byte parity before compiling either board:

- readPendingFile
- markPendingPostAttempt
- pendingAttemptMarkerMatches
- clearPending
- canAttemptCoinPost
- quarantineLogField
- quarantineLogTokenValid
- quarantineLogRecordValid
- inspectQuarantineLog
- appendQuarantineRecord
- quarantinePending

This prevents a later board-only edit from weakening pending evidence, POST gating, quarantine validation, or disposition semantics without a focused CI failure. The test includes a deliberate fail-open mutation (return verified; → return true;) in the ESP8266 append helper; the parity guard must reject it.

No firmware runtime source, shared API/schema, QA-owned tests, finance, migration, signer, or release file changed.

### Exact-head CI

- Focused quarantine [run #44117721021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44117721021), job 134160276258: **SUCCESS** at exact source/test SHA f74cd39aaf9045258f5374dd39b1542a142a8424.
- Exact log markers: BOARD_QUARANTINE_PARITY_PASS 11/11 helpers byte-identical; BOARD_PARITY_MUTATION_REJECTED fail-open append verification bypass; SOURCE_QUARANTINE_PASS 33/33 on each board; pending-attempt marker 28/28 each; mount 7/7 each; boot recovery 16/16 each; pending-clear 17/17 each; write/readback 22/22 each; coin POST gate 10/10 each.
- Relay-output [run #44117721018](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44117721018), job 134160275795: **SUCCESS** at the same exact SHA; 48/48 scenarios per board; inverted-polarity and removed-poll-inhibit mutations rejected on both boards.
- Full BlazePwifi push run [#44117698099](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44117698099): validation job 134160203209 **FAILED** at QA-owned tests/controllers.sh with Missing poll signature check. The run ended CANCELLED after the validation failure: 13/13 non-Android firmware/platform jobs completed SUCCESS, Android was CANCELLED, and downstream production/sign/publish jobs were cancelled or skipped. PR-triggered Full run [#44117721088](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44117721088) also ended CANCELLED after the same validation failure; six target jobs passed and the remaining target jobs were cancelled. Full is not green. Do not claim a complete target matrix or Full success.

### Evidence classification and coordination

All quarantine and parity evidence is **SIMULATED / CI VERIFIED** with source-extracted C++17 and fake LittleFS. Physical flash durability, real relay contacts, actual coin acceptor pulses, 150 controlled power cuts, 30-device 24-hour soak, and electrical pulse/recovery remain **NOT TESTED**. Protected witness, durable accounting/replay, v1→v2 migration and independent release approval remain BLOCKED. **Production NO-GO.**

Master's latest draft role assignment at #288 head 5e11daf8d9a65659e92030df94b212eb9e28d21f still lists #239/#254/#283 but does not list the active #317/#318 stack (rechecked after the UTC15 Master update). PR #318 remains a separate divergent child at a497403bd3886caf105585c0da997a100ad61dc3, mergeable=false, based on stale merge base 3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3. No rebase, cherry-pick, merge or force-push was performed.

**Next:** PHX-MASTER reconciles #317/#318 in ROLE_ASSIGNMENTS and resolves the child stack; PHX-QA replaces the obsolete positive poll-signature assertion with source-linked default-deny cases and reruns Full; PHX-HARDWARE preserves the deny state and awaits approved noncustomer physical acceptance.


## UTC19 — first-ever quarantine log creation and absent-file append failure

**Coverage gap:** the source-extracted fake LittleFS always reported /quarantine.log as existing. The production path where no quarantine log exists had not been exercised, even though first-ever quarantine is a normal lifecycle path.

**Test-only correction in the existing hardware-owned PR #317:**

- Fake LittleFS now models logExists independently from its byte contents.
- exists("/quarantine.log") is false until append mode creates the file.
- Read-open refuses an absent file; append-open creates it only when the injected open failure is not active.
- Scenario 33 starts with no log, performs the first append, verifies the new record bytes, and requires successful disposition only after readback.
- Scenario 34 starts with no log and injects append-open failure; it requires no file creation, no byte mutation, no pending clear, a same-boot recovery latch, no POST eligibility, and a hard stop when the simulated volatile latch is lost while the open failure persists.
- Existing scenarios continue to cover existing-log append-open failure, short write, verification-open failure, same-size corruption, readback mutation, over-capacity logs, malformed prior records, identity mismatch, and pending-clear refusal.

No production .ino, financial contract, controller API, receipt, migration, or release workflow was changed. This is a test-harness coverage improvement, not a claim that physical LittleFS durability is proven.

**Intermediate test-run correction:** initial test commit c4b09646d662c6b6972266ee37d887c3324b7d49 passed the new 35/35 source-extracted scenarios per board, but its additional mutant-harness assertion failed to detect the injected unconditional-clear mutant. That extra assertion was removed in 3c7d770845388b12f37072d6ced80a1a7561aae6; the actual append-open failure scenarios remain in the normal matrix and directly require clearCount==0 and unchanged pending evidence. The failed intermediate run is preserved, not represented as a green run.

**Final focused exact-source evidence at 3c7d770845388b12f37072d6ced80a1a7561aae6:**

- Quarantine/readback [run #44161916932](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44161916932), job 134317697702: **SUCCESS**. Both ESP32 and ESP8266 report SOURCE_QUARANTINE_PASS 35/35; aggregate 70/70. The same workflow also passed pending-attempt marker 28/28 per board, mount 7/7 per board, boot recovery 16/16 per board, pending-clear 17/17 per board, write/readback 22/22 per board, coin POST gate 10/10 per board, and poll-window 11/11 per board. Logs explicitly report SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_VERIFIED=0, and FINANCIAL_PRODUCTION_AUTHORIZED=0.
- Relay-output [run #44161916911](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44161916911), job 134317697668: **SUCCESS**, 48/48 per board; inverted-polarity and removed-poll-inhibit mutations rejected. Child-only poll-window steps were skipped on this parent stack.
- Full validation [run #44161916884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44161916884), validation job 134317874964: **FAILED** in QA-owned tests/controllers.sh with Missing poll signature check. At the last observation, Android, ESP32/ESP8266 and several target-image jobs were still in progress/queued. No complete target-matrix result is claimed; production import/signing/update/release steps were skipped.

**Limits and next action:** focused evidence is source-extracted C++17 with fake LittleFS/GPIO only. First-file creation semantics are modeled, not measured on physical LittleFS. Physical coin/relay/electrical acceptance, 150 controlled power cuts, 30-device 24-hour soak, signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain NOT TESTED/BLOCKED. Keep poll and coin admission default-deny. PHX-QA owns the stale controller assertion; PHX-MASTER owns role-index and #317/#318 stack reconciliation. **PR #317 remains DRAFT / UNMERGED / PRODUCTION NO-GO.**


## UTC19 — PHX-HARDWARE stack proposal for #317 / #318

**Live comparison at proposal time:** #317 HEAD 13dab88d443a5b9432f6cd46292af5a5df742204 versus #318 HEAD be371b03a36306a7691b411bf1b29da60b916646. GitHub compare reports **DIVERGED, 49 ahead / 48 behind**, merge base 3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3; PR #318 is mergeable=false. The #318 current-head Actions query returned one Full build only; no current-head PHX-HARDWARE child poll-window run was present.

**Proposal — preserve #317 as canonical parent; do not integrate #318 wholesale.**

1. Keep #317 as the canonical safety parent. It contains the newer pending-attempt marker, quarantine append/readback, pending-clear protections, default-deny behavior and current exact-source focused evidence. It remains DRAFT and unmerged.
2. Keep #318 as a separate experimental child candidate. Do not rebase, cherry-pick, force-push, merge, close, or copy its whole sketches/test tree without Master approval.
3. If PHX-MASTER and PHX-QA approve the concept, create a fresh child from the then-current #317 head and reimplement only the reviewed ISR edge-snapshot/fault-latch delta. Do not transplant the child firmware sketches or its older poll-response lab wholesale; they overlap the parent sketches and would reintroduce stale source.
4. Before any such child is considered integration-ready, add exact-source tests for: marker-open failure followed by reboot; short-write/readback failure followed by reboot; pulse between final drain sample and loop sampling; pulse after drain but before poll snapshot; interrupt attachment on every allowed runtime coin pin; and proof that an edge fault never authorizes POST, clear, or positive poll admission.
5. The current child implementation has a specific durability limit: latchPollPulseFault sets journalRecoveryRequired in RAM, but if writePollPulseFaultMarker cannot open/create the file, the fault marker is absent after reboot. Its existing lab scenario 21 verifies same-boot denial only; it does not verify reboot recovery after marker-open failure. The marker is also a diagnostic edge-count/millis record, not an event-bound pending coin journal or financial receipt. These are unresolved acceptance questions, not claims that the child is safe to integrate.

**Requested Master decision:** confirm #317 as parent and authorize (or reject) a new minimal #317-based child for the ISR edge snapshot. Until that decision and independent QA review, #318 remains isolated and #317 remains the only candidate to continue validating. No stack rewrite was performed in this activation.
