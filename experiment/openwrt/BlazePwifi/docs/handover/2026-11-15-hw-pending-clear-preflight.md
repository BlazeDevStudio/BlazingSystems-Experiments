# PHX-HARDWARE handover: pending-clear ambiguity preflight

- Role: PHX-HARDWARE
- Scope: ESP32 and ESP8266 pending journal deletion only
- Base: PR #312 exact head `90e94d0323ff35fccdf2f892d543c606ffd45cd9`
- Branch: `phoenix/hardware-clear-preflight-20261115`
- Status at handoff: **SIMULATED** pending exact-head workflow evidence; **NOT HARDWARE ACCEPTED**

## Proven defect

`clearPending()` iterated `/pending.dat`, `/pending.new`, and `/pending.bak` and deleted each existing candidate. If more than one candidate existed while the volatile recovery latch was false, deletion could begin before ambiguity was detected elsewhere. A later removal failure could therefore leave only part of the accounting evidence.

## Change

Both board sketches now count all durable pending candidates before any removal. More than one candidate latches `journalRecoveryRequired`, returns failure, preserves every candidate and retains the in-memory pending event.

The exact-source pending journal lab now compiles and executes the real `clearPending()` for both boards. Eleven cases per board cover no candidate, each single candidate, all pairwise ambiguous candidate combinations, remove failure, false-success removal with the file still present, unavailable filesystem, and a pre-existing recovery latch. Ambiguous cases require zero deletion calls and byte-identical files.

## Boundary and review

No controller API, receipt schema, finance, migration, deployment, signing, release, flashing, reset, or production state was changed. This draft remains stacked on PR #312 and must not merge independently.

PHX-QA should independently rerun the exact-source pending journal lab at the exact PR head. PHX-MASTER/RELEASE must extend implementation/blob/mode/license/dependency/negative-test/rollback parity before any destination migration.

Real LittleFS power interruption, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected anti-rollback witness, migration and independent release acceptance remain untested or blocked.
