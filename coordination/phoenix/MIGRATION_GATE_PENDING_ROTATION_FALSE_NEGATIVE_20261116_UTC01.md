# PHX-MASTER — pending-rotation false-negative migration hold (2026-11-16 UTC01)

**Status:** DRAFT / PRODUCTION NO-GO. Coordination and provenance only. No runtime code migration, acceptance or release.

## Exact-ref audit

- Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master PR #288 prior head `7bf3bfe4aeb3e7164bd9d0263a530e87ee52bb35`; routing manifest and AGENTS.md re-read. PHX-MASTER owns only `coordination/phoenix/`; no competing CORE/HARDWARE edits.
- HARDWARE stacked draft [#314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/314) `phoenix/hardware-rotation-evidence-preservation-20261116@556adc20ef0cfd355089aff3b979c0169af79bdd`, based on #313 `6b8583b7b0b39314bce39666d1cdd0b8f84afe48`. Exact-head [workflow 43782088731](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088731) and [43782088748](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088748) completed success; these are **software CI only**, not physical validation.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243` is structure-only; existing integration draft [#26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) head `b382d233ff06c8791b1028bed3c617cc7b670d12`. Its five existing PR workflow checks remain queued, not passed.

## Git tree source/destination comparison at exact SHAs

| Board/file | HARDWARE #314 source Git blob | COE #26 destination Git blob | Mode | Status |
|---|---|---|---|---|
| ESP32 `BlazePwifiVendo32.ino` | `be674b08d65b68d5218f2bf60f58d4842960b691` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | both `100644` | DIFFERENT |
| ESP8266 `BlazePwifiVendo.ino` | `e369d661d9c6d6a39c789b4b346b5adb888d0ff5` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | both `100644` | DIFFERENT |

Source paths: `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`, `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`. Destination paths: `Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`, `Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`.

The mismatches prove only nonidentity. **License, imports, dependency closure, functional equivalence and corresponding negative-test identities are NOT VERIFIED**. Do not copy firmware or assert regression coverage at the destination based on this audit.

## New safety issue to verify

The #314 PR diff changes `savePending()` to retain the read-back-verified `/pending.new` after failed/ambiguous rename and latch `journalRecoveryRequired`. Its simulated LittleFS harness adds rename false-negative cases (bytes moved but API returns false) and reports 22 cases per board. This is source/PR inspection, not a local execution by PHX-MASTER.

PHX-HARDWARE and independent PHX-QA must inspect both rename boundaries: `pending.dat -> pending.bak` and `pending.new -> pending.dat`; clean failure versus false negative; reboot reconciliation with old/new candidates; deletion failure; monotonic pulse evidence; default-deny relay behavior; and crash windows. Record exact executed commands, board target, test identity and CI SHA. No claims about real LittleFS power-loss atomicity without device evidence.

## Migration/acceptance instructions

1. HARDWARE owner: supply per-file semantic diff, SPDX/license provenance, include/library closure, test-to-source identity, and reversible migration patch after #313/#314 stack review.
2. QA owner: independently rerun exact-SHA negative tests, including failed rename and false-negative rename, and compare staged destination behavior rather than just names.
3. COE integration owner: investigate five queued exact-SHA workflows and record completed CI before considering any migration; do not replace staged files blindly.
4. MASTER: run `coordination/phoenix/verify_coordination.py` plus companion tests at exact master head in a suitable checkout. This audit only inspected Git trees, PR diffs and CI metadata; no local regression suite executed.

Private Drive v11 project registry was validated as JSON in restricted workspace; do not publish its contents or identifiers. Remain PRODUCTION NO-GO until independent protected signing/anti-rollback witness, crash-atomic financial accounting, reversible migration, independent QA, native hardware acceptance, 150 real power cuts, 30 devices for 24 hours and owner-authorized release. No merge, flashing, release or real financial action.
