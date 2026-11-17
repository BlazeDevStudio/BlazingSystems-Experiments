# PHX-HARDWARE handover — poll inhibit pulse-drain guard

- Role: PHX-HARDWARE
- Task: Project Phoenix #177 / control plane #172
- Repository: `BlazeDevStudio/BlazingSystems-Experiments`
- PR: [#318](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/318), DRAFT, stacked on DRAFT #317
- Branch: `phoenix/hardware-poll-inhibit-settle-20261117`
- Base branch: `phoenix/hardware-clear-pending-marker-match-20261117`
- Base SHA: `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`
- Source-fix SHA: `5072e8fd352eab63bf479b13704cdfcb9caf9991`
- Documentation checkpoint SHA: `8b3a9407c7daae7bbb38fb609d482cbaf7eb92ed`
- Status: DRAFT / FOCUSED CI VERIFIED / FULL VALIDATION FAILED / PHYSICAL ACCEPTANCE NOT TESTED / PRODUCTION NO-GO

## One proven source-level gap

Both ESP sketches used the configured debounce interval as the post-relay-inhibit quiet window before a synchronous poll. The Master Architecture Contract §2.1 permits coin pulses up to 100 ms, while the configured debounce can be 20 ms (default 40 ms). The previous quiet check could therefore return before a delayed/in-flight acceptor output pulse appeared.

This is a bounded risk model. It does not prove any particular coin acceptor emits a delayed pulse after relay de-energization; the physical delay must be measured on an isolated noncustomer bench.

## Test-first RED

- Test-only commit: [`3948b9c405c57fea6e90e610774ce956ef3a5033`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3948b9c405c57fea6e90e610774ce956ef3a5033).
- Focused run: [#44067323124](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44067323124), job `133984253325`.
- Expected RED: the new 120 ms quiet-window assertion failed at scenario return 17 against the old 20 ms guard.

The test adds two fault-injection cases: an 80 ms pulse beginning 80 ms after relay inhibit under both 20 ms and 40 ms debounce settings. It also updates the quiet/no-pulse case to require the full 120 ms interval.

## Firmware correction

- ESP8266: [`4e6225b8e8bf520715a0e5cb1e176c8e472520b6`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4e6225b8e8bf520715a0e5cb1e176c8e472520b6)
- ESP32: [`5072e8fd352eab63bf479b13704cdfcb9caf9991`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5072e8fd352eab63bf479b13704cdfcb9caf9991)

`coinLineQuietAfterInhibit()` now waits for `max(runDebounceMs, 100 ms + 20 ms)`. A pulse observed during the interval cancels polling, releases the inhibit, and returns to the ordinary loop so the existing pulse/journal path can observe it. No API, receipt, accounting, migration, signer, QA source or workflow changed.

## Exact-head focused CI

- Run: [#44067564257](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44067564257)
- Job: `133985101193`
- Exact source SHA: `5072e8fd352eab63bf479b13704cdfcb9caf9991`
- Result: **SUCCESS**

Both board-shaped source-extracted harnesses passed:
- Debounce floor: 8/8
- Poll-window guard: 11/11
- Blocking-poll relay inhibit: 1/1
- Poll response default-deny: 11/11
- Strict root JSON: 13/13
- Coin POST ACK root status: 4/4
- Coin disposition default-deny: 4/4
- Register configuration denial: 7/7
- Quarantine: 23/23
- Pending attempt marker: 28/28
- Mount/output protection: 7/7
- Boot recovery: 16/16
- Pending clear: 17/17
- Pending write/readback: 22/22
- Coin POST gate: 10/10

These are host tests and fake-filesystem simulations only.

## Full validation and blockers

- Full run: [#44067564436](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44067564436)
- Validation job: `133985242101`
- Result: **FAILED** at QA-owned `tests/controllers.sh`: `Missing poll signature check` in the ESP8266 sketch.

Master §6.3 currently requires default-deny poll admission until PHX-CORE publishes the canonical producer/consumer contract and PHX-QA approves both sides' vectors. The firmware remains default-deny; it was not weakened to satisfy the stale assertion. Target build jobs were still running at the last observation, so no Full workflow success is claimed.

Flags: `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

## Ownership and next action

- PHX-QA: reconcile the stale controller-parity assertion with Master §6.3 and independently rerun Full at the current PR head.
- PHX-MASTER: review the 120 ms local guard against the electrical acceptance plan and confirm whether a larger measured drain interval is required.
- PHX-CORE: publish the canonical authenticated poll/receipt contract; no firmware admission change is authorized before it exists.
- PHX-HARDWARE: keep coin/poll admission default-deny; do not claim physical pulse-loss closure until an approved noncustomer bench measures the actual acceptor/relay timing.

No flashing, reset, customer device, live coin, financial migration, signing, release tagging, merge or deployment occurred.
