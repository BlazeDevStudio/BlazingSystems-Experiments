# PHX-HARDWARE handover: duplicate quarantine evidence hard stop

- Role: PHX-HARDWARE
- Scope: ESP32 and ESP8266 coin quarantine journal only
- Base: PR #311 exact head `e6a25a56e9edb1c39e99ec0f5b1e8854ba350e32`
- Branch: `phoenix/hardware-quarantine-duplicate-evidence-20261115`
- Status at handoff: **SIMULATED** pending exact-head workflow evidence; **NOT HARDWARE ACCEPTED**

## Proven defect

The reboot inspector treated every complete record with the same persisted event identity as one successful prior commit. If a log already contained two complete records for one pending event, inspection returned success and `quarantinePending()` could clear the pending journal despite duplicated accounting evidence.

## Change

Both board sketches now reject a second matching complete record while streaming `/quarantine.log`. The inspector returns failure, latches `journalRecoveryRequired`, preserves the pending event and log bytes, blocks same-boot retry, and re-establishes the hard stop after simulated reboot.

The exact-source host lab adds scenario 16 for two complete matching records. It expects no clear attempt, unchanged log bytes, retained pending pulses, recovery latch, blocked retry, and the same failure after volatile state reset. Coverage is 17 scenarios per board / 34 total.

## Boundary and review

No controller API, finance, relay authorization, migration, deployment, signing, release, flashing, reset, or production state was changed. This draft remains stacked on PR #311 and must not merge independently. QA should independently rerun the exact-source lab and confirm the duplicate-record case on the exact PR head.

Real LittleFS power interruption, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected anti-rollback witness, migration, and independent release acceptance remain untested or blocked.
