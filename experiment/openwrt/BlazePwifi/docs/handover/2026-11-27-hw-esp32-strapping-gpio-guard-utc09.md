# PHX-HARDWARE — ESP32 strapping GPIO role guard

## Purpose and exact source

Task: Hardware-owned extension of DRAFT PR #357. This is a board-specific configuration safety guard, not a positive coin-admission change.

- Repository: `BlazeDevStudio/BlazingSystems-Experiments`
- Branch: `phoenix/hw-runtime-pin-config-guard-20261127-utc04`
- Source/test SHA: `32f63aa335714d63fba8bae406a102a8d5d191e9`
- PR: [#357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357), OPEN / DRAFT / UNMERGED
- Base: #355 at `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`

## Change

The ESP32 Vendo runtime GPIO validator now rejects GPIO0, GPIO2, GPIO5, GPIO12 and GPIO15 for coin and relay roles. It rejects GPIO0, GPIO5, GPIO12 and GPIO15 for the LED role. GPIO2 remains allowed only as the LED role to preserve the existing default tuple `(27,26,2)`.

Espressif documents GPIO0/2/5/12/15 as strapping pins. GPIO2 is retained as a narrow LED-role compatibility exception; its external circuit and exact board revision have not been electrically inspected. It can affect serial-download boot if the reset level is wrong. Do not treat this as hardware acceptance.

## Exact evidence

- Focused PR [#45972810167](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45972810167), job `140417125204`: PASS.
- Focused push [#45972801632](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45972801632), job `140417096963`: PASS.
- ESP32 Mbed TLS matrix [#45972810179](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45972810179): 3/3 PASS. Clean A/B builds match for Arduino core 3.3.13 and 4.0.0.
- Full pre-sync [#45972810260](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45972810260): 14/14 target/platform builds PASS; overall validation failed only at the mandatory handover freshness gate. Rerun after this handover sync.
- Native [#45972810157](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45972810157), job `140417125670`: FAIL at QA-owned PAY-0745 literal active-clear assertion. No unsafe pending-clear workaround added.

## Limits / blockers

Source-extracted tests are SIMULATED / CI VERIFIED only. Physical strap voltages, external pulls, relay contacts, coin pulses, brownout, LittleFS power loss, 150 controlled power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

CORE owns authenticated poll/receipt/disposition. QA owns independent assertion semantics. MASTER owns stack/integration/release sequencing. Active P0 #177 remains unresolved; keep coin/relay admission denied.

Private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not accessible through this runtime. No older registry snapshot was substituted.

## Resume instruction

Resume PHX-HARDWARE on this exact branch. Re-read live #172, #177, #266, #34, #31/#32, #43, Master PR #288, and current #239/#254/#283 heads. First rerun Full on the final docs HEAD, then coordinate remaining QA/CORE contract blockers. Do not use Codex, do not flash/reset devices, and do not enable coin/relay admission.

