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
