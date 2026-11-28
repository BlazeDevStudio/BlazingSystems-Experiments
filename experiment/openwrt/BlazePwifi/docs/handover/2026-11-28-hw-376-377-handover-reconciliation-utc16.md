# PHX-HARDWARE — canonical #376/#377 reconciliation handover

Updated: 2026-11-28T16:19:00Z

This exact file content is intentionally identical on the #376 and #377 branches so the reconciliation handover itself does not create a fourth divergent shared path. The three historical shared handovers remain append-only and are independently byte-prefix verified on both branches.

## Independent branch sequence

- **#376 storage preflight:** branch `phoenix/hw-storage-superblock-rw-guard-20261128-utc14`; source/test head `22ff6eb054b9578daf74a30d5c04d51fd754917e`; docs parent head before this identical-file sync `627bf4f53199a337e3821bf634e53b6289d2c671`; child of #356 `0ea32d31ed5c902b2187d98c181aab14bc9fdeae`. Scope: read-only STORCHK-0674 mountinfo/superblock preflight.
- **#377 poll candidate:** branch `phoenix/hw-poll-deny-wrapper-child-20261128-utc15`; source/test head `95e54790ab986dab3c1b3723ea9603a3d125c0d6`; docs parent head before this identical-file sync `f52524d20a589c7c300f0a97a13bfdb5ac3e8a6c`; child of #374 `cfb19ed5df920bf5fa7e33e08dc73a25f8b14db9`, preserving #375 `94b1231c631eb32da0f019604ce00a4a0851a471` as the second parent. Scope: deny-only poll/EEPROM fail-closed candidate.
- Do not merge, cherry-pick or rebase these branches together. Master retains sequencing and integration authority. Neither branch is active v0.6 or main.

## Exact-head CI before this identical-file synchronization

### #376 — CI VERIFIED / SIMULATED ONLY

- Focused docs head [#46163693189](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46163693189), job `141036420946`: PASS. `CHANGE_LEDGER_DELETED_LINES=0`; `CHANGE_LEDGER_APPEND_ONLY_PASS`; STORCHK mountinfo, physical-parent and superblock mutation matrices PASS. Explicit `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `CUSTOMER_INSTALL_AUTHORIZED=0`.
- Mbed [#46163693190](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46163693190): 3/3 PASS (source contract, core 3.3.13, core 4.0.0).
- Full [#46163693229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46163693229): SUCCESS; validation PASS, 14/14 target/platform builds PASS, 9/9 v0.4 simulations PASS, update bundle PASS. Production import/sign/release skipped.

### #377 — CI VERIFIED only for passing sub-gates; integration NO-GO

- Poll [#46163774315](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46163774315): PASS.
- Mbed [#46163774257](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46163774257): 3/3 PASS.
- Native [#46163774177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46163774177): FAIL at QA-owned PAY-0745 assertion `if(any) return false;`.
- Full [#46163774224](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46163774224): FAIL at mandatory controller parity validation after 14/14 target/platform builds PASS. Update bundle, simulations, candidate, signing and publication skipped.

## Exact controller schema divergence

The Full failure is explained by a real branch difference:

- #377 ESP8266 sketch blob `426ada921d6d20a56e3fdad9f3efd4bdf5047464` and ESP32 blob `449c76a6f2fbab548bd355c07a39bbfc850e0cb0`: neither contains `config_revision`.
- #376 ESP8266 sketch blob `12c4bb82b6fddafe813674a0b5f692c1d3634073` and ESP32 blob `6edefc9283a3a4554c15ec9c9e4a9e038e98504d`: both contain `config_revision`.

CORE must publish the canonical controller config-revision/register/poll/receipt/disposition contract; QA owns semantic validation. Hardware must not synthesize a field, signature, or positive admission path without that contract.

## Append-only verification

All three shared handover files retained their exact previous byte prefixes.

- #376: PROJECT_HANDOVER 457473→462053 chars; CURRENT_STATE 453098→457678; CHANGE_LEDGER 1097199→1101779.
- #377: PROJECT_HANDOVER 627966→631947 chars; CURRENT_STATE 597344→601325; CHANGE_LEDGER 1208242→1212223.

## Unresolved gates and next exact actions

- Active v0.6 branch `2fbd2475e9f54878c316fa7cea2f228386b0e859` still performs synchronous poll before the first coin sample on both boards; P0 #177 remains OPEN.
- PHX-QA: replace PAY-0745 and controller-parity literal assertions with independent semantic source-linked vectors.
- PHX-CORE: publish authenticated controller config-revision/register/poll/receipt/disposition contract and golden vectors.
- PHX-MASTER: refresh role/integration pins after this identical-file sync; preserve separate PR ancestry.
- PHX-HARDWARE: resume P0 #177 intake-inhibit/capture only after CORE/QA approval; keep coin/relay denied.

Physical relay/pulse/power acceptance, 150 power cuts, 30-device/24-hour soak, protected signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff remain NOT TESTED / NOT ACCEPTED. Production remains NO-GO.
