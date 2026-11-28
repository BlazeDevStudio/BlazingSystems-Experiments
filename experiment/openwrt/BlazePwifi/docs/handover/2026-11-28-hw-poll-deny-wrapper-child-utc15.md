# PHX-HARDWARE UTC15 — canonical #374/#375 deny-only poll integration

**Issue:** [P0 #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#377](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/377) — OPEN / DRAFT / UNMERGED  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-poll-deny-wrapper-child-20261128-utc15`  
**Integration commit:** `4d99c023aa65ed84c6e80d705acc3da044d13075`  
**First parent:** #374 `cfb19ed5df920bf5fa7e33e08dc73a25f8b14db9`  
**Second parent:** #375 `94b1231c631eb32da0f019604ce00a4a0851a471`

## Master-directed sequencing

PHX-MASTER PR #288 UTC14 chose #366 → #373 → #374 → a new child of #374 carrying the five #375 commits. This branch is that child. The original #375 branch remains untouched; its five-commit history is preserved as the second parent. The nine shared paths were manually reconciled, with the #374 ESP8266 configuration-store readiness condition retained.

Historical source handovers from #375 are preserved in:
- `2026-11-28-hw-poll-deny-wrapper-utc13.md`
- `2026-11-28-hw-poll-gpio-off-mutation-utc14.md`

## Integrated changes

- ESP8266 and ESP32 use one `pollDenyOnly()` function for the synchronous 3.5-second poll boundary.
- The helper denies remote control and physically applies outputs before the wait, discards the untrusted response, denies again, and updates `lastPoll`.
- No poll response is consumed; no remote config is applied; no pending evidence is cleared; coin/relay admission remains denied.
- The source contract requires a single helper call in the bounded loop, a single poll POST in the helper, unconditional pre/post deny, and completion timestamp after the post-deny.
- The GPIO host harness retains the failure injection that removes `applyOutputs();` from the real extracted deny function; the expected rejection marker is `PREPOLL_GPIO_OFF_WRITE_MUTATION_REJECTED`.
- The #374 ESP8266 `configStoreReady` poll guard is preserved and is recognized by the updated contract.

## Validation

The prior #375 exact-head evidence is historical only:
- Poll push [#46153921703](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153921703), job `141006279696`: PASS.
- Mbed push [#46153921753](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153921753): 3/3 PASS.
- Native [#46153921746](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153921746): FAIL at QA-owned PAY-0745 corrupt-state assertion.
- Full [#46153917616](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153917616): FAIL at QA-owned `tests/controllers.sh:21` controller parity after 14/14 target builds PASS.

Those results do not transfer to this child. Exact-child Poll/Mbed/Native/Full results are pending independent GitHub Actions readback. Local repository tests were NOT RUN.

## Ownership and blockers

- PHX-CORE owns authenticated register/poll/receipt/disposition.
- PHX-QA owns PAY-0745 and controller parity assertions.
- PHX-MASTER owns role/integration pins and release sequencing.
- PHX-HARDWARE changed only its sketches, poll lab/contract/harness, Hardware workflows and handover records.

## Acceptance

SIMULATED / CI pending on this child. Physical relay terminal polarity, actual acceptor inhibit/reject, pulse retention, EEPROM/NVS brown-out, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. Protected signer/witness, v1→v2 migration, durable accounting/replay and independent QA/release signoff remain **NOT ACCEPTED**.

**HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.** No flashing, device reset, live money, migration, signing, release, merge or deployment occurred.

**Next exact action:** inspect exact-child Poll/Mbed/Native/Full workflow runs and update this handover with terminal run/job evidence; request QA/CORE fixes only through their owned issues.
