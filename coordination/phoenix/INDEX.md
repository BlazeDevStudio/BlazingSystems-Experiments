# Project Phoenix — Coordination Index

**Updated:** 2026-11-20T04:39:26Z  
**Role:** PHX-MASTER — coordination / architecture / integration provenance only  
**Safety:** DRAFT REVIEW ONLY · PRODUCTION NO-GO

## Start here — authoritative live sources

1. [Control plane issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) — canonical role inbox, assignments and BLAZE-COMMS/1 checkpoints.
2. [Cleanup-first issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) — seven-role cleanup checklist. The Master inventory remains incomplete; do not treat the checklist as proof of cleanup.
3. [Phoenix Master draft PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) — Master-owned coordination branch only.
4. `OWNERSHIP_ROUTES.json` — machine-readable draft routing; current blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, Master destination `null`.

## Canonical live documents

| File | Purpose |
|---|---|
| `ARCHITECTURE_CONTRACTS.md` | Cross-subsystem invariants and candidate interface gates; current Remote CS review gate is §6.55. |
| `ROLE_ASSIGNMENTS.md` | Current owner/PR heads, scope boundaries and next owner actions. |
| `INTEGRATION_MATRIX.md` | Exact source/destination heads and CI dispositions. |
| `AUDIT_SUMMARY.md` | Current blockers and release-readiness disposition. |
| `REPOSITORY_ROUTING.md` | Human-readable routing and manual-review restrictions. |
| `OWNERSHIP_ROUTES.json` | Machine-readable routes; do not modify without exact per-file provenance and owner review. |

## Verification tools

- `verify_coordination.py` / `test_verify_coordination.py`
- `verify_migration_map.py` / `test_verify_migration_map.py`
- `verify_source_intake_manifest.py` / `test_verify_source_intake_manifest.py`
- `test_architecture_contracts.py` and `test_snapshot_identity.py`

Run the repository's actual test suite from an authenticated checkout at the exact branch SHA. A static document/manifest check or a scoped subsystem CI run is not a full Master-suite result.

## Append-only audit reports

Timestamped `PHX_MASTER_*.md`, subsystem audits, and migration-gate reports are immutable historical evidence. They are **not** the current source of truth when their exact SHA differs from the live branch/PR API. Start with the four canonical live documents above, then open the newest report only for the issue under investigation. Do not mass-delete or rename older reports; first inventory inbound links and consumers.

## UTC04 cleanup-first inventory

- Coordination tree at the audited Master head: 116 files (105 `.md`, 3 `.json`, 8 `.py`).
- Exact duplicate blob SHA count: **0**.
- Architecture-contract numbered heading collisions: §6.9, §6.10, §6.11, §6.12, §6.25, §6.32. No renumbering performed because references have not been fully inventoried.
- No source files, test files, route manifest, or historical report were deleted or moved.

## Live refs at the UTC04 audit

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`
- v0.5.3 development: `aad3aade72c1156eecba1fed30907c6d0283b2c5`
- v0.6 audit-foundation: `2fbd2475e9f54878c316fa7cea2f228386b0e859`
- Master branch at UTC04:39 audit start: `5d96b2df6351788613dfc49d4a246637f7b23f64`
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, 205 paths, five queued workflows / zero jobs.

## Standing gates

No route promotion, source migration, merge, release, signing, secret provisioning, hardware flash, customer payment, or physical test is authorized by this index. Production remains NO-GO pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates.

## Latest exact-head reconciliation — 2026-11-20 UTC04:39

- [Hardware stack and terminal CI audit](PHX_MASTER_UTC04_20261120_HARDWARE_STACK_AND_RELEASE_TERMINAL_CI_RECONCILIATION.md).
- Active Hardware child #327: docs head b6304208d65548a9cfe371504badf03ae3e15dcf, source/test 2f89326d5b555ffdb2bfaba0a404483d665aa614, base #326 58c558fb6a237935214621adc3dee65a10fe1a51.
- Release #291: BlazePwifi full CI #44673292595 PASS with production signing/publishing skipped; ESP32 reproducibility #44673292516 FAIL on both cores; Windows #44673293276 FAIL.
- COE #26 remains frozen at b382d233ff06c8791b1028bed3c617cc7b670d12 with five queued workflows / zero jobs.
- No source migration, ownership transfer, route promotion, merge, release or hardware acceptance.