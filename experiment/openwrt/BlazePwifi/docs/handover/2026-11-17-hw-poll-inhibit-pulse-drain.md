# PHX-HARDWARE handover — poll inhibit pulse-train quiet guard

- Role: PHX-HARDWARE
- Task: Project Phoenix #177 / control plane #172
- Repository: `BlazeDevStudio/BlazingSystems-Experiments`
- PR: [#318](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/318), DRAFT, stacked on DRAFT #317
- Branch: `phoenix/hardware-poll-inhibit-settle-20261117`
- Base branch: `phoenix/hardware-clear-pending-marker-match-20261117`
- Base SHA: `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`
- Final source SHA: `5d3dc5547606841209ade10c888dab67e1ffcaa7`
- Current docs checkpoint (before this update): `233ad9749579d0048185eea7023878a3d628adf2`
- Status: DRAFT / FOCUSED CI VERIFIED / FULL VALIDATION FAILED / PHYSICAL ACCEPTANCE NOT TESTED / PRODUCTION NO-GO

## Confirmed source-level timing gap

Both ESP sketches originally used the configured debounce interval (20 ms minimum, 40 ms default) as the post-relay-inhibit quiet window before starting synchronous HTTP poll. Master Architecture Contracts §2.1 defines a **250 ms inter-coin quiet period** as the completion boundary for a pulse train. A 20/40 ms debounce interval can end between pulses in one coin insertion. A first 120 ms single-pulse drain improvement was also insufficient to cover the 250 ms pulse-train gap.

This is a software timing gap derived from the shared contract. It does not prove a specific acceptor emits a delayed pulse after relay de-energization; the actual output delay and relay behavior remain unmeasured on physical hardware.

## Test-first RED / refinement

1. Test-only commit [`3948b9c405c57fea6e90e610774ce956ef3a5033`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3948b9c405c57fea6e90e610774ce956ef3a5033) added a delayed pulse beginning 80 ms after inhibit. Focused [#44067323124](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44067323124), job `133984253325`, **RED** at the 120 ms expectation against the old 20 ms guard.
2. An intermediate 120 ms guard passed focused [#44067564257](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44067564257) at source `5072e8fd...`. That result was superseded after checking the 250 ms inter-coin contract.
3. Test-only refinement [`4cdeaa2f81569a95a36f8aabc6e70ca96cefbb4a`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4cdeaa2f81569a95a36f8aabc6e70ca96cefbb4a) adds an 80 ms pulse beginning 200 ms after relay inhibit. Focused [#44069089876](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44069089876), job `133990363481`, **RED** at scenario return 17 because the 120 ms interval was shorter than the 250 ms pulse-train boundary.

## Final firmware correction

- ESP8266: [`c93d836201bf851f63b1938f1fdeeb06fd4dafa2`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c93d836201bf851f63b1938f1fdeeb06fd4dafa2)
- ESP32: [`5d3dc5547606841209ade10c888dab67e1ffcaa7`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5d3dc5547606841209ade10c888dab67e1ffcaa7)

Both `coinLineQuietAfterInhibit()` implementations now wait for `max(runDebounceMs, 250 ms)` of continuous quiet after relay inhibit. A pulse observed during that interval cancels the blocking poll, releases the temporary inhibit and returns to the normal loop while the line remains observable. No protocol/API, receipt, accounting, migration, signer, QA-owned test or workflow was changed.

## Focused exact-source CI

- Final source SHA: `5d3dc5547606841209ade10c888dab67e1ffcaa7`
- Run: [#44069258396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44069258396)
- Job: `133990936760`
- Result: **SUCCESS**

Both board-shaped source-extracted harnesses passed:
- Debounce floor: 8/8
- Poll-window guard: 12/12
- Blocking-poll relay inhibit: 1/1
- Poll response default-deny: 11/11
- Strict root JSON: 13/13
- Coin disposition default-deny: 4/4
- Register configuration denial: 7/7
- Quarantine: 23/23
- Pending attempt marker: 28/28
- Mount/output protection: 7/7
- Boot recovery: 16/16
- Pending clear: 17/17
- Pending write/readback: 22/22
- Coin POST gate: 10/10

These are C++ host tests and fake-LittleFS simulations only.

## Full validation and blockers

- Full run: [#44069254356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44069254356)
- Validation job: `133991048028`
- Result: **FAILED** at QA-owned `tests/controllers.sh`: `Missing poll signature check` in the ESP8266 sketch.

Master Architecture Contracts §6.3 keeps poll admission default-deny until PHX-CORE publishes the canonical producer/consumer contract and PHX-QA approves exact positive/negative vectors. The inherited positive-signature assertion is stale against that decision; firmware was not weakened to satisfy it. Other target jobs were still running at the last observation. A second Full run `#44069258582` had its validation job queued at that observation, so it is not claimed green or failed.

Flags: `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

## Ownership and next action

- PHX-QA: reconcile the inherited controller-parity assertion with Master §6.3, repair its canonical extractor, and independently rerun Full at the exact combined head.
- PHX-MASTER: review the 250 ms local guard against the electrical acceptance plan and update the role index/control-plane assignment to include #318.
- PHX-CORE: publish the canonical authenticated poll/receipt contract; no hardware admission change is authorized before it exists.
- PHX-HARDWARE: retain default-deny; do not claim physical pulse-loss closure until an approved noncustomer bench measures the actual acceptor/relay timing.

No flashing, reset, customer device, live coin, financial migration, signing, release tagging, merge or deployment occurred.
