# PHX-HARDWARE — ESP8266 boot-strap GPIO role guard

## ESP8266 boot-strap GPIO role rejection (2026-11-27)

**Task:** PR #357, Hardware-owned runtime GPIO validation hardening  
**Branch:** `phoenix/hw-runtime-pin-config-guard-20261127-utc04`  
**Source/test SHA:** `7ee0bc955cdf67763d032f81e488141e4a270a88`  
**Base:** PR #355 at `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`  
**PR:** [#357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357), OPEN / DRAFT / UNMERGED

### Defect and change

The ESP8266 `validRuntimePins()` policy rejected out-of-range, flash-reserved (GPIO6–11), and overlapping roles, but still allowed GPIO0, GPIO2 and GPIO15 for coin, relay or LED. Espressif documents these as reset-time boot-strapping pins; external circuits can alter normal flash boot or bootloader selection.

The Hardware-owned ESP8266 validator now rejects GPIO0/GPIO2/GPIO15 for all three configurable runtime roles. Existing defaults (coin GPIO4, LED GPIO14, relay GPIO5) remain valid. Invalid stored tuples continue to fall back to the existing default tuple; this change does not add positive coin/relay admission.

The source-extracted host lab now:
- Requires the strap-pin guard in the actual sketch.
- Tests GPIO0, GPIO2 and GPIO15 independently as coin, relay and LED roles.
- Removes the complete strap guard as a negative mutation and requires the harness to reject that unsafe candidate.

Reference: [Espressif ESP8266 boot-mode selection](https://docs.espressif.com/projects/esptool/en/latest/esp8266/advanced-topics/boot-mode-selection.html).

### Exact evidence at source/test SHA

- Focused PR [#45961383769](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961383769), job `140379762193`: **PASS**.
- Focused push [#45961376783](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961376783), job `140379740076`: **PASS**.
- Logs: `RUNTIME_GPIO_POLICY_PASS ESP8266`; `RUNTIME_GPIO_MUTATION_REJECTED ESP8266 boot-strap-guard-removed`; `RUNTIME_GPIO_FAILURE_INJECTION_PASS ESP8266`; both board policy harnesses passed; 14/14 injected regressions were rejected.
- Append-only ledger guard: `CHANGE_LEDGER_APPEND_ONLY_PASS base_bytes=1132798 appended_bytes=22069`.
- ESP32 Mbed TLS matrix [#45961383705](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961383705): **3/3 PASS** (source contract, Arduino core 3.3.13, Arduino core 4.0.0).
- Native synthetic journal [#45961383755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961383755), job `140379762596`: **FAIL** at QA-owned PAY-0745 assertion requiring active `clearPending(true/false)` callsites. Hardware did not add a pending-clear workaround.
- Pre-handover Full push [#45961376884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45961376884), validation job `140379814945`: **FAIL** at the mandatory handover-freshness gate because this source change had not yet been recorded. This is not terminal integrated validation; exact docs-head Full/Native runs are required after this sync.

### Scope and limitations

Only the ESP8266 sketch and Hardware-owned GPIO lab changed in the source commit. ESP32 strap policy/default GPIO2 was not altered; its board-specific electrical qualification remains separate. UART0 GPIO1/GPIO3 and GPIO16 role capability are not addressed by this change and must not be treated as physically accepted.

Host/source-extracted failure injection is **SIMULATED / CI VERIFIED** only. Physical strap levels, external pull-ups, GPIO voltage, relay contact behavior, coin pulses, brownout recovery, 150 power cuts and 30-device/24-hour soak remain **NOT TESTED**. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

No shared API, QA-owned test, financial code, migration, signer, witness, COE destination, production configuration or release path changed. No device was flashed or reset.

### Next exact action

Complete the post-handover exact-head Full and Native reads. PHX-QA/PHX-CORE still own the Controller protocol and pending-disposition contract blockers; PHX-MASTER owns the integration matrix. Hardware retains #357 DRAFT/unmerged.
