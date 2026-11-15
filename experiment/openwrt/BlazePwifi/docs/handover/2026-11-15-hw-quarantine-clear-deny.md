# PHX-HARDWARE handover — quarantine deletion denial

**Date:** 2026-11-15 Asia/Manila  
**Role:** PHX-HARDWARE  
**Task:** preserve unpaid-coin quarantine evidence  
**Branch:** `phoenix/hardware-quarantine-clear-deny-20261115`  
**Stack base:** DRAFT #295 at `7b6e28c9cdc71b5c4b56c54e522ba79a3653f994`  
**Classification:** DRAFT / LAB ONLY / PRODUCTION NO-GO

## Proven defect

Both ESP setup servers registered `POST /quarantine/clear` and deleted
`/quarantine.log` without request authentication, durable receipt proof, or
operator reconciliation. The same web server remains reachable on the station
interface after the temporary setup AP closes, so a LAN request could erase
the only copied record after a rejected coin event was moved out of the active
pending journal.

## Bounded correction

- The existing read-only `GET /quarantine` route remains for evidence export.
- `POST /quarantine/clear` now returns HTTP 403 and contains no filesystem
  deletion call.
- The response explains that evidence must be preserved and reconciled offline.
- No CORE receipt schema, journal format, signing contract, router endpoint, or
  financial authority changed.

## Verification

`tests/v060_esp_quarantine_clear_deny.py` extracts the exact clear-handler body
from each sketch, compiles it with a fake web response sink, injects a hostile
POST, and requires HTTP 403 plus the preservation message. It also rejects any
remaining `LittleFS.remove("/quarantine.log")` occurrence while requiring the
read/export route to remain.

At handover creation, exact-head Actions are **NOT RUN / PENDING**. Test source
is not proof of passage.

## Explicit limits

- Host denial is software evidence only. Flash durability, power cuts, physical
  coin pulses, relay behavior, and operator reconciliation are **NOT TESTED**.
- A future authenticated deletion/reconciliation workflow requires
  MASTER/CORE ownership of the durable signed receipt contract and independent
  QA review; this firmware branch does not invent one.
- No merge, flash, device reset, customer money, deployment, tag, or release.
