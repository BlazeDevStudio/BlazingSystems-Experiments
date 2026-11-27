# PHX-HARDWARE handover — startup GPIO output-sequence lab modularization (UTC19)

- Repository: BlazeDevStudio/BlazingSystems-Experiments
- Role: PHX-HARDWARE
- PR: pending DRAFT child of #365; no merge
- Branch: phoenix/hw-output-enable-lab-modules-20261128-utc19
- Parent: #365 at e65b0b895af9c3fc5e5632f704cb67b347e69725
- Source/test SHA: ff73702adf6fb958c9f21ebe9a68c908ee829ea4

## Completed task

The existing output_enable_sequence_lab.py mixed source extraction/orchestration, mutation construction, and C++ harness compilation. It is now a small runner importing two single-purpose modules:

- output_enable_sequence_lab_contract.py — board paths, source-extractor decoy check, and the three source mutation helpers.
- output_enable_sequence_lab_harness.py — C++ event recorder, compile/run harness, and terminal result handling.

The entry point continues to extract the actual production writeLogical() and configureRuntimePins() functions from both sketches. The same four independent relay/LED polarity combinations, old-pin shutdown checks, pre-OUTPUT OFF preload checks, post-OUTPUT OFF confirmation, and 14 unsafe mutations remain the acceptance contract.

The existing Hardware workflow now watches both modules and the new role branch. The original lab command remains unchanged.

## Evidence boundary

Expected focused lab output remains 8/8 board/polarity scenarios and 14/14 injected regressions rejected. This is host simulation/CI only; it does not measure GPIO voltage, relay contacts, coin-slot behavior, or physical polarity. Physical acceptance remains NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## Exact next action

Run the existing phx-hw-active-v06-poll-intake-deny.yml on this PR's exact head, inspect terminal job logs, then update this handover with exact run/job IDs. Master retains ownership of coordination/phoenix/ and role/integration matrices.