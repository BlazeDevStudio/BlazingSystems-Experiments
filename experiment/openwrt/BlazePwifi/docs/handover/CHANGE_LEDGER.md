

## 2026-11-27 — PHX-HARDWARE UTC14 PR #361 host String ownership regression

- Source/test SHA: `4a85070a1f6a1caa417570a91dcdf355ff072fcc`; PR #361 remains OPEN / DRAFT / UNMERGED, child of #359 at `47357aab2ff7910b38ca538a46dfa01bdbca01e8`.
- Corrected the host fake Arduino `String` in `pending_recovery_promotion_lab_harness.hpp` to own a `std::string` copy of the stack-local nonce/target fields supplied by source-extracted `loadPending()`. Added assertions across all existing 11 scenarios for recovered identity retention and fail-closed empty identity on ambiguous/failed paths.
- Focused [#46016953274](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953274), job 140566402392: PASS.
- Mbed [#46016953049](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953049): source contract and Arduino core 3.3.13 PASS; core 4.0.0 in progress at this entry.
- Pre-sync Full [#46016953164](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953164): validation failed at handover freshness before target matrix completed; post-sync exact-head Full rerun required.
- No firmware sketch, shared API, QA-owned test, financial state, signer/witness, migration, COE destination, or release operation changed. Physical acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
