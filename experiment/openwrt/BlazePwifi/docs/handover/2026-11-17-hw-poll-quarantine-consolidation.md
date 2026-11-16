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
