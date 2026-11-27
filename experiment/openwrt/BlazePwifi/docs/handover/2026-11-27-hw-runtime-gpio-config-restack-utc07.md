# PHX-HARDWARE — PR #357 restack onto current #355

**Date:** 2026-11-27 UTC07  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-runtime-pin-config-guard-20261127-utc04`  
**PR:** [#357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357), OPEN / DRAFT / UNMERGED  
**Parent PR #355 HEAD at restack:** `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`  
**Pre-restack #357 HEAD:** `79470fb6cfa1daf274c33d2100ad19eabd5b39fd`

## Restack mechanics and preservation

PHX-MASTER UTC06 explicitly assigned Hardware to restack #357 onto the live #355 head and rerun exact-head CI. This update uses a two-parent merge commit (old #357 HEAD first, current #355 HEAD second) and a non-force fast-forward ref update. It does not rewrite either parent history or modify #355.

The tree is based on the current #355 tree, then overlays only #357's Hardware-owned firmware, host-lab, workflow and handover paths. PROJECT_HANDOVER.md and CURRENT_STATE.md retain the full current #355 contents with this restack note prepended. CHANGE_LEDGER.md preserves the current #355 ledger as an exact byte prefix and appends the #357-only suffix plus a restack entry. No existing ledger byte was deleted or rewritten.

## Scope carried forward

- ESP8266/ESP32 strict decimal GPIO parsing and board-specific pin range checks.
- Reject flash-reserved GPIOs and duplicate coin/relay/LED assignments.
- Validate persisted tuples before runtime pin configuration; invalid tuples use documented defaults, with ESP32 station/poll kept disabled until corrected.
- Reject invalid save-form pin assignments before Wi-Fi verification or EEPROM/Preferences persistence.
- Host-only failure injection for duplicate roles, flash pins, nonnumeric/overflow input, ESP32 input-only outputs and removed early return.
- Workflow includes and executes runtime_pin_config_lab.py.

## Exact evidence and limitations

Pre-restack exact-source #45955340512 at `79470fb6cfa1daf274c33d2100ad19eabd5b39fd` passed. Pre-restack Full #45955340513 failed the QA-owned controller parity validation (config_revision); target/platform builds and Android passed. Those are historical pre-restack results only. Exact-head post-restack Full, Native, focused GPIO/Poll and Mbed TLS runs must be read after the new commit; no new-head CI result is claimed by this handover.

This is source-extracted host testing, not physical GPIO or relay acceptance. Board strap pins, electrical voltage, relay contacts, coin pulse timing, brownout recovery, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. Coin admission and pending disposition remain fail-closed. No CORE API, finance, migration, signer, witness, or COE path was changed.

## Ownership / next action

- PHX-QA: reconcile deny-only controller parity and pending-disposition assertions using semantic state-transition tests.
- PHX-CORE: publish authenticated register/poll and receipt/disposition contract.
- PHX-MASTER: refresh the role/integration matrix after exact-head evidence.
- PHX-HARDWARE: record post-restack exact-head CI and keep PR draft/unmerged.

**Classification:** GPIO failure injection SIMULATED; hosted checks CI VERIFIED only when exact-head runs complete; physical acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
