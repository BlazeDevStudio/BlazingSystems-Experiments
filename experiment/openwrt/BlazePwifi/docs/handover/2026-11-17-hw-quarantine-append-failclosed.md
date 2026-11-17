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
