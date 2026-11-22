# PHX-HARDWARE — shared active C++ preprocessing mask (UTC20)

**Disposition:** focused Quarantine CI VERIFIED at the exact source/test SHA; Full integration run is queued/pending with no jobs returned; SIMULATED ONLY; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.

- Role: PHX-HARDWARE
- Repository: `BlazeDevStudio/BlazingSystems-Experiments` (repository ID `1389289885`)
- Child PR: [#344](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/344) — OPEN / DRAFT / UNMERGED
- Parent PR: [#341](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/341), exact parent HEAD `4368435ad762d507a907e72a9c739c7bddbc3a81`
- Parent lineage: #338 `1a6a7cacf95722a78330d70de057e858143520f2` → #339 `b3e1558845ae2cd508e42d0d4722fdcd28293e32` → #341
- Branch: `phoenix/hardware-shared-preprocessor-mask-20261122-utc20`
- Test-only RED commit: `4c396537615a97cb6332372c5856e1fe6d592d7c`
- Shared helper implementation commit: `8f1b4ca6f099eab744b57e73e9c1059140a671ee`
- Fixture refactor commit: `e944f77b70071dfc5613d65d03867684cfc4fb56`
- Final source/test SHA before this handover: `f9a18ea3ba7fe37a490f93eaa12525e97ac0331a`

## Decision and scope

This is a cleanup-first, behavior-preserving consolidation of a duplicated bounded C/C++ preprocessor mask in the Hardware host-test infrastructure. The prior #341 fixture module carried its own phase-2 logical-line and literal inactive-branch parser. The same responsibility now lives in the shared `firmware_lab_source.py` module, so future Hardware labs can reuse one reviewed implementation.

No ESP32/ESP8266 sketch, runtime GPIO, relay, coin admission, pending journal, controller/API contract, finance, migration, signer, witness, QA-owned assertion, Release workflow, or COE destination file changed.

## Test-first RED

- Test-only commit: `4c396537615a97cb6332372c5856e1fe6d592d7c`.
- Quarantine run [#45067790629](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45067790629), job `137347739306`: expected FAILURE at the new shared-helper assertion:
  `AttributeError: module 'firmware_lab_source' has no attribute 'mask_active_cpp_code'`.
- This is the intended RED against the parent #341 source tree, not a runner/infrastructure failure.

## Source correction

The shared module now owns:
- `_literal_preprocessor_condition()` for literal `#if/#elif 0/1` recognition;
- `_logical_preprocessor_lines()` for LF, CRLF and CR phase-2 line-splicing while retaining physical offsets;
- `_mask_inactive_preprocessor_branches()` for known-inactive literal branches;
- public `mask_active_cpp_code()`, which composes `mask_non_code()` with the bounded preprocessor mask and verifies exact source offsets and newline positions.

The fixture module now imports `mask_active_cpp_code()` and no longer carries a second copy of the preprocessor parser. Unknown macro expressions remain conservatively visible; this helper is not a complete C/C++ compiler preprocessor.

The dual-store runner adds direct checks for:
- exact offset/newline preservation across LF, CRLF and CR: 3/3;
- conservative visibility of unknown macro branches: 1/1;
- failure injection replacing the shared active mask with the lexical-only mask, which must re-expose an inactive declaration: mutation rejected 1/1.

## Exact-source GREEN

- Source/test SHA: `f9a18ea3ba7fe37a490f93eaa12525e97ac0331a`.
- Quarantine run [#45067887389](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45067887389), job `137348038635`: **SUCCESS**.
- Logs:
  - `POLL_FAULT_SHARED_ACTIVE_MASK_NEWLINE_PRESERVATION_PASS 3/3`
  - `POLL_FAULT_SHARED_ACTIVE_MASK_UNKNOWN_MACRO_CONSERVATIVE_PASS 1/1`
  - `POLL_FAULT_SHARED_ACTIVE_MASK_MUTATION_REJECTED 1/1`
  - existing comment/raw-string/identifier/inactive-branch/phase-2/digraph extraction checks also passed.
- The same job completed the existing quarantine, EEPROM/NVS, poll-window, pulse-capture and boot-polarity source-extracted suites. Its explicit end markers remain `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

Full integration run [#45067887363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45067887363) was still pending with no jobs returned at handover time. Do not claim a current-head Full result from the parent #341 run; the parent Full run [#45060591630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060591630) failed its QA-owned `Missing poll signature check` validation assertion.

## Ownership and safety boundaries

- #344 is a child of #341, which is itself a child of #339/#338. It is **not** a continuation of the separate #327 → #342 → #343 stack. Keep both lineages separate until PHX-MASTER selects and records a canonical composition plan.
- Preserve independent drafts #239 (Phase A deny), #254 (ControllerAuthV1Lab), and #283 (both sketches, fail-closed).
- Current register/poll signature and event-bound coin receipt contract remains CORE/QA-owned and unapproved. Do not add synthetic signatures or enable positive admission to satisfy the inherited Full validation fixture.
- No merge, rebase, retarget, force-push, flashing, device reset, signer provisioning, financial migration, release tag, deployment or cutover occurred.

## Remaining blockers / next action

1. PHX-MASTER to record the #338 → #339 → #341 → #344 cleanup lineage and exact heads in Master-owned role/integration documents without collapsing it into #327 → #342 → #343.
2. PHX-QA to reconcile the stale positive poll-signature assertion with independently reviewed negative deny-behavior tests at pinned SHAs.
3. PHX-CORE to publish the canonical authenticated register/poll/configuration and event-bound receipt contract.
4. PHX-HARDWARE keeps coin admission and remote configuration deny-only; continue only after revalidating current heads and role assignments.
5. Hardware acceptance remains NOT TESTED: 150 physical power cuts, 30-device/24-hour soak, electrical pulse/recovery and independent monotonic witness remain outstanding.
