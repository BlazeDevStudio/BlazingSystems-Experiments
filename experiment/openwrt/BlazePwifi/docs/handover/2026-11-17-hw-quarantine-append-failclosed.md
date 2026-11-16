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
