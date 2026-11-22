# PHX-HARDWARE — shared active C++ preprocessing mask (UTC20)

**Disposition:** focused Quarantine CI VERIFIED at exact source/test SHA `07ef70b73dba128c71b2bd735a7370333a600293`; Full integration validation FAILED at the inherited QA-owned `Missing poll signature check`; SIMULATED ONLY; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.

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
- `_logical_preprocessor_lines()` for LF, CRLF and CR phase-2 line-splicing while retaining original Python string-index ranges;
- `_mask_inactive_preprocessor_branches()` for known-inactive literal branches;
- public `mask_active_cpp_code()`, which composes `mask_non_code()` with the bounded preprocessor mask and verifies Python string-index and newline-position preservation.

The fixture module now imports `mask_active_cpp_code()` and no longer carries a second copy of the preprocessor parser. Unknown macro expressions remain conservatively visible; this helper is not a complete C/C++ compiler preprocessor.

The dual-store runner adds direct checks for:
- Python string-index/newline preservation across LF, CRLF and CR: 3/3;
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

At the earlier handover, Full run [#45067887363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45067887363) had no jobs returned. The later final-docs-head Full run [#45068113012](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45068113012) completed with validation job `137349513473` **FAILURE** at the inherited QA-owned `Missing poll signature check`; its 14 configured target/platform jobs and Android build passed, while downstream simulation/signing/publication stages were skipped.

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

## UTC21 follow-up — Unicode-safe source-index contract

The previous helper docstring called its offsets “byte offsets”. That was imprecise: the implementation operates on Python `str` indices (Unicode code-point positions), which are the correct indices for its source-string slicing API; they are not UTF-8 byte offsets.

- Helper documentation correction commit: [`5020ae0786609d6b70114cabc0b799a74d4e4d1e`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5020ae0786609d6b70114cabc0b799a74d4e4d1e).
- Unicode regression test commit: [`faa81d31b8f374332667ff523ba462add0e5f37b`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/faa81d31b8f374332667ff523ba462add0e5f37b).
- Corrected real-LF fixture commit / exact source-test head: [`07ef70b73dba128c71b2bd735a7370333a600293`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/07ef70b73dba128c71b2bd735a7370333a600293).
- The new fixture places multibyte UTF-8 text (`café 🔧`) before a literal inactive branch, then checks Python string length, exact CR/LF positions and active-only constant extraction.
- Exact-source Quarantine run [#45074086697](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45074086697), job `137367313779`: **SUCCESS**. Log marker: `POLL_FAULT_SHARED_ACTIVE_MASK_UNICODE_STRING_INDEX_PRESERVATION_PASS 1/1`; prior 3/3 newline, 1/1 unknown-macro and 1/1 mutation checks also pass.
- Full run [#45074086696](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45074086696) completed **FAILURE**: validation job `137367388911` failed at the same inherited `Missing poll signature check` in the ESP8266 sketch. All 13 firmware target jobs and the Android build completed SUCCESS. Browser/device simulations, update bundle, candidate gate, signing handoff and publication stages were skipped.
- Logs retain `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

This is a host-test contract/documentation correction only. No ESP sketch or runtime behavior changed.


## UTC22 follow-up — reject malformed conditional structure in the shared source mask

**Disposition:** exact-source Quarantine CI VERIFIED; Full integration validation FAILED at the inherited QA-owned poll-signature assertion; SIMULATED ONLY; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.

- Test-only RED commit: 5abc300f5998cacc602a645615c869bb9586f47d.
- Corrected physical-newline fixtures after an initial escaped-newline draft; Quarantine run #45080270000, job 137386621656: EXPECTED FAILURE at "shared active-C++ mask must reject malformed conditional structure: orphan #elif".
- Implementation commit / exact source-test SHA: 7aea96679043a38924765cccd2efea965cc44256.
- Quarantine run #45080463303, job 137387232032: SUCCESS. New markers:
  - POLL_FAULT_SHARED_ACTIVE_MASK_MALFORMED_DIRECTIVE_STRUCTURE_REJECTED 6/6
  - POLL_FAULT_SHARED_ACTIVE_MASK_NESTED_UNKNOWN_BRANCH_CONSERVATIVE_PASS 1/1
  - Earlier newline 3/3, unknown-macro 1/1, inactive-mask mutation 1/1 and Unicode string-index 1/1 also passed.
- Full run #45080463292: FAILURE at validation job 137387307139, inherited QA-owned "Missing poll signature check" in tests/controllers.sh. All 15 configured firmware target jobs and Android completed SUCCESS; browser/device simulations, update bundle, candidate gate, signing handoff and publication were skipped.

The shared helper now rejects unmatched #elif, #else and #endif, unterminated conditional stacks, duplicate #else, #elif after #else, missing #if/#elif expressions and unexpected tokens after #else/#endif. Diagnostics include the physical source line. Unknown macro branches remain conservatively visible; this is still a bounded source-analysis helper, not a full C/C++ preprocessor.

This increment changes only the Hardware-owned Python source-analysis helper, its Hardware host-lab regression, and this handover. No ESP32/ESP8266 production sketch, runtime GPIO, relay, coin admission, pending journal, shared API, finance, migration, signer, witness, QA-owned assertion, Release workflow or COE destination file changed.

The #344 cleanup lineage remains #338 → #339 → #341 → #344 and separate from #327 → #342 → #343. Keep #239 Phase-A deny, #254 ControllerAuthV1Lab and parallel #283 fail-closed sketches open and unmerged. No rebase, retarget, force-push, merge, flashing, device reset, financial migration, signer provisioning, release tag, deployment or cutover occurred.
