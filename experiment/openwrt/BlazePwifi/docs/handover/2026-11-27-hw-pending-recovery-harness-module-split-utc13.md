# PHX-HARDWARE UTC13 — pending-recovery C++ harness module split

**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266; Hardware-owned pending-recovery lab maintainability  
**PR:** [#361](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/361), OPEN / DRAFT / UNMERGED  
**Parent:** [#359](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/359)  
**Branch:** `phoenix/hw-pending-recovery-harness-module-split-20261127-utc13`  
**Base head:** `47357aab2ff7910b38ca538a46dfa01bdbca01e8`  
**Source/test SHA:** `13ef08db75acb5bfa609b6f0c445f35d2584a024`

## Why this cleanup

The 382-line `pending_recovery_promotion_lab.py` combined four responsibilities:
1. extract the real board `loadPending()` implementation;
2. assert source-level fail-closed contracts and inject unsafe source mutations;
3. embed a C++17 fake-LittleFS implementation as a large Python raw string;
4. compile and execute 11 deterministic recovery scenarios per board.

The embedded C++ made the Python runner difficult to navigate and made the C++ fixture harder to review as C++.

## Changes

- New `pending_recovery_promotion_lab_harness.hpp` contains the C++17 fake-LittleFS harness template.
- The template contains exactly one `/*__LOAD_PENDING_FUNCTION__*/` marker.
- The Python runner reads the adjacent template and replaces that marker with the exact source-extracted `loadPending()` function.
- The runner rejects a missing or duplicated insertion marker before compilation.
- The existing workflow now watches the new header on both push and pull-request path filters.

The template was assembled from the exact prefix and suffix of the former raw string. The placeholder splice was verified before commit. No fixture statement, scenario, mutation, expected return code, firmware sketch, or production behavior changed.

## Exact CI

Focused [#46010669158](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46010669158), job `140545038497`, **PASS** at `13ef08db75acb5bfa609b6f0c445f35d2584a024`.

Observed:
- `CHANGE_LEDGER_APPEND_ONLY_PASS base_bytes=1132798 appended_bytes=18747`
- ESP8266: 11 scenarios; two injected rename failures; canonical/fallback ambiguity preserved; invalid-only, empty-init and legacy-migration failures denied.
- ESP32: same 11 scenarios and failure paths.
- Eight unsafe source mutations rejected per board; 16 total.
- `PENDING_RECOVERY_PROMOTION_LAB_PASS boards=ESP8266,ESP32 mutations_rejected=16`.

Full [#46010669130](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46010669130) validation job `140545112859` failed at the pre-sync handover freshness gate. This run predates the documentation update in this commit; its remaining target jobs were still running at the time of this handover. No Full PASS or target count is claimed. A post-sync Full rerun is required.

## Ownership / release boundary

- HARDWARE owns this test harness and both firmware sketches.
- CORE owns the authenticated register/poll/receipt/disposition contract.
- QA owns independent semantic assertions.
- MASTER owns stack ordering, role assignments and integration approval.

No source/API, firmware, QA-owned tests, financial state, signer/witness, migration, COE, or release files outside this task were changed.

**Classification:** host-only SIMULATED / CI VERIFIED. Physical LittleFS recovery, electrical pulse/relay behavior, 150 power cuts, and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

No flash, reset, live money, production migration, merge, signing, release tag, or deployment.