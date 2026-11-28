# PHX-MASTER — quarantine reboot-idempotency migration gate (2026-11-15 UTC22)

**Status: DRAFT / PRODUCTION NO-GO.** Coordination-only, no runtime source edits or migration approval.

## Exact evidence snapshot
- Experiments default `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`; Master branch prior HEAD `135ddbeb5cd87a7eb97006e716b4cd4d96467832`.
- COE default `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration draft PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- HARDWARE stacked draft PR #311 `e6a25a56e9edb1c39e99ec0f5b1e8854ba350e32` addresses reboot-idempotent quarantine evidence, torn log tails, and duplicate stable pulse/nonce/target identities. Source owner: PHX-HARDWARE, independent reviewer: PHX-QA. Do not modify its branch from Master.
- Exact-head HARDWARE workflow runs [43765446018](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43765446018) and [43765446015](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43765446015) completed success. PR checkpoint reports 32/32 focused reboot/idempotency scenarios, 16 per sketch. These are software/lab CI, not actual power-cut or hardware acceptance.
- COE PR #26 still has five queued workflow runs: 43096752609, 43096752632, 43096752800, 43096752563, 43096752557. None supplies completed destination acceptance.

## Exact Git blob comparison (GitHub contents read, not executable parity)
| Sketch | Source blob at HARDWARE #311 | COE #26 staged destination blob | Decision |
|---|---|---|---|
| `esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino` | `3ca3f85d86551796089a77505885a66ed366f434` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | DIFFERENT; hold |
| `esp8266/BlazePwifiVendo/BlazePwifiVendo.ino` | `3da06da5fc586b2beecc0f61247f064c8a43b876` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | DIFFERENT; hold |

These mismatches do **not** by themselves prove which protections the destination implements. Source files are under `experiment/openwrt/BlazePwifi/`; destination files are under `Hardware/`. No automatic copy is authorized.

## Required independent destination admission
1. PHX-HARDWARE provides a bounded source-to-destination implementation diff, exact Git tree file modes, dependencies, license provenance, and a reviewable selective migration plan. Retain historical sources and record rollback commit/ref.
2. PHX-QA independently tests torn/unterminated/corrupted quarantine tails, reboot after complete-but-unverified append, duplicate identity recognition, unchanged pending state on failure, and both ESP targets against **the destination candidate exact SHA**.
3. The COE integration owner obtains completed exact-SHA CI for all applicable destination workflows, including compile and test identity mapping; queued CI is not evidence.
4. PHX-MASTER rechecks cross-role API contracts and reversible migration matrix after owner and QA evidence. Master does not edit HARDWARE/QA/COE source or sign off financial admission.

## Human debugging and rollback
Read `coordination/phoenix/OWNERSHIP_ROUTES.json` first. Record source and destination Git blob IDs before comparing functions. Inspect journal validation, append/rename failure paths, stable record identity, and pending-clear order. If parity is unproven, keep PR #26 draft, preserve the existing destination SHA and source history, and report BLOCKED rather than replacing either tree.

Private Drive registry v11 was parsed locally; its private contents and identifiers are deliberately not reproduced. Master coordination Python tests were not executed in this run. Protected signing, independent anti-rollback witness, crash-atomic financial state, reversible migration, native acceptance, 150 real power cuts and 30-device 24-hour soak remain unverified production gates.
