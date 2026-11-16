# PHX-HARDWARE handover: pending rotation evidence preservation

- Role: PHX-HARDWARE
- Scope: ESP32 and ESP8266 pending journal rotation only
- Base: PR #313 exact head `6b8583b7b0b39314bce39666d1cdd0b8f84afe48`
- Branch: `phoenix/hardware-rotation-evidence-preservation-20261116`
- Status at handoff: **SIMULATED** pending exact-head workflow evidence; **NOT HARDWARE ACCEPTED**

## Proven defect

After writing and exactly reading back a valid updated `/pending.new`, `savePending()` deleted that verified new record when either journal rename failed. A clean or false-negative `pending.dat → pending.bak` result could therefore leave only the older event. A failed `pending.new → pending.dat` result removed the updated candidate and restored the old backup. A power cut after either return could discard the newest pulse evidence.

## Change

Both board sketches now preserve every durable candidate and latch `journalRecoveryRequired` after either failed or ambiguous rename. No rollback path deletes the verified updated record.

The exact-source write/readback lab adds false-negative rename behavior, where storage moves bytes but reports failure. Twenty-two cases per board cover clean failures and false negatives at both rotation boundaries. Tests require the updated three-pulse record and prior one-pulse record to remain available for reconciliation.

## Boundary and review

No controller API, receipt schema, finance, migration, deployment, signing, release, flashing, reset, or production state was changed. This draft remains stacked on PR #313 and must not merge independently.

PHX-QA should independently rerun the exact-source rotation lab at the exact PR head and inspect all four rename boundaries. PHX-MASTER/RELEASE must extend implementation/blob/mode/license/dependency/negative-test/rollback parity before any destination migration.

Real LittleFS rename behavior under power interruption, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected anti-rollback witness, migration and independent release acceptance remain untested or blocked.
