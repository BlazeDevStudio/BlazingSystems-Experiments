# PHX-MASTER — HARDWARE #323 dual-store poll-fault and COE #26 parity audit

**Audit window:** 2026-11-18 UTC05  
**Disposition:** candidate-only; no source migration, merge, or production authorization.

## Scope and authority

This is a PHX-MASTER coordination/architecture audit. Subsystem source remains owned by PHX-HARDWARE, PHX-QA, PHX-CORE and PHX-RELEASE. No firmware, test, workflow, or COE destination source file was changed. The existing routing manifest remains review-only and unchanged.

Instructions re-read for this activation: the uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`, latest `README_FIRST(10).md`, `COMMUNICATION_PROTOCOL(10).md`, Experiments root `AGENTS.md`, live issue #172, cleanup issue #266, current #288/#26, current role PRs and exact-head CI. The COE root `AGENTS.md` path returned 404.

## Exact live refs at audit start

| Ref | Exact state |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| PHX-MASTER `phoenix/master-coordination` before this audit | `e95cda0ae3f08c4f1dbdfcdfa79808cc887cd7b3` |
| Existing Experiments PR #288 | OPEN / DRAFT, base `main@f4e8a891...`, head `e95cda0a...` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT, base `main@a6513ab4...`, head `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| `OWNERSHIP_ROUTES.json` | blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null` |

The live branch API and PR metadata agreed before the documentation commit. PR #288 had 70 changed paths, all under `coordination/phoenix/`.

## HARDWARE candidate lineage

| PR | Exact head | Exact parent/base | Current disposition |
|---|---|---|---|
| #317 | `fce915c1167fc43c6936f3594ae9efce376b711f` | parent #315 | Current base for #320; focused quarantine/relay checks pass, Full build validation fails |
| #318 | `696e28ed4cd53b9189b78095b38aee973d774683` | `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3` | DIVERGED / nonmergeable; no current-head CI |
| #320 | `b2b41a3d6ce7887b9624137c966f58462895d3fa` | exact #317 head | Focused relay/quarantine pass; Full build cancelled |
| #322 | `50d93e0de3d682550b6f02fb43484e76ad9c7e08` | exact #320 head | Focused output-order/quarantine pass; Full validation fails |
| #323 | `f98bc39c29eeb82b292aa83fa680d05d2e36efd5` | exact #322 head | OPEN / DRAFT / mergeable; candidate dual-store fallback |

#323 source/test change commit is `6738171209a748c3c210ac13ebe69450eb6405f5`; current PR/docs head is `f98bc39c...`. All three current PR-triggered runs below report head SHA `f98bc39c...`.

## Source review: what #323 changes

### ESP32

- Adds a fixed 20-byte versioned `PollFaultRecord` in Preferences NVS namespace `phx_fault`, key `poll_fault`.
- Checks write length and exact readback.
- Treats an existing, malformed, or unreadable record as a deny hold; no automatic clear path.
- NVS is a separate flash partition from LittleFS, but on the same physical flash chip.

### ESP8266

- Reserves a 20-byte record at EEPROM-emulation offset 512; expands the emulation buffer to 544 bytes.
- Static assertions keep the existing `Config` before offset 512 and the record within the buffer.
- Commits, ends/reopens the EEPROM emulation and verifies the flash-backed record.
- Any non-erased bytes in the reserved record are a deny hold; malformed/partial bytes are not auto-cleared.

### Output ordering and residual failure

Both `latchPollPulseFault()` implementations now set the RAM deny state, disable insertion, clear the active target, and call `applyOutputs()` **before** attempting NVS/EEPROM or LittleFS writes. This removes the source-level window where a potentially blocking flash write could precede the logical output inhibit.

If either persistent store records the hold, boot remains denied. If both stores fail, the source explicitly reports that only the current boot remains fail-closed and reboot durability is **not established**. The two stores are same-chip regions, not an independent physical witness. The FNV-1a checksum is corruption detection only, not authentication, signing, or anti-rollback.

## Exact-head GitHub Actions evidence

| Run | Exact head | Result | What it proves |
|---|---|---|---|
| [44242190343 — Quarantine Byte Readback LAB](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190343) | `f98bc39c...` | SUCCESS | Log reports `POLL_FAULT_DUAL_STORE_LAB=PASS` for ESP32 and ESP8266; both-store failure is explicitly `EXPECTED_CURRENT_BOOT_ONLY`. Source-extracted mount/journal/pending-clear labs also ran. |
| [44242190332 — Relay Output Polarity LAB](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190332) | `f98bc39c...` | SUCCESS | 48/48 logical polarity scenarios per board; output-enable ordering checks pass. Logs explicitly say physical relay polarity is not verified. |
| [44242190324 — BlazePwifi build](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190324) | `f98bc39c...` | FAILURE | Validation job fails at the inherited QA-owned `Missing poll signature check` assertion. All 14 target/platform build jobs completed SUCCESS; downstream simulations, signed import, update bundle, candidate gate, signing and publishing jobs were SKIPPED. |

The PR's earlier test-first RED is recorded as [44241798015](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44241798015). The Full workflow failure is a validation-fixture blocker, not evidence that the target compilation jobs failed. It is also not permission to restore a positive poll path.

## COE #26 exact-source staging comparison

At COE #26 head `b382d233...`:

| Item | Experiments #323 source | COE #26 destination | Result |
|---|---|---|---|
| ESP32 sketch | blob `b0dfe6cf4dcea1c7fbad00d5b2c2cda08f26f8ba` | blob `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different |
| ESP8266 sketch | blob `8e79b9eb8856e67d966f4c6385f89fccdc8be7fc` | blob `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different |
| New dual-store lab | blob `fbfe2c72a21a9555cf1c586a1aac226ea0b93b75` | Not present in destination tree | Missing |
| Focused source workflow | blob `2358e4ab940b9879e961046180f01fc3d5356709` | COE hardware workflow blob `fe79adbdb3745a22c5ef6d1f0c87c868b7785793` | Different; COE workflow does not invoke the dual-store lab |

COE #26's `Hardware/tests/test_firmware_hardening.sh` is a separate static hardening check; it is not an import of the new source-extracted dual-store regression. COE #26's five PR workflows remain QUEUED with zero jobs returned. No combined destination CI acceptance exists.

### License/NOTICE scope

Experiments source `experiment/openwrt/BlazePwifi/LICENSE` and COE `Pisowifi/LICENSE` are the same MIT blob `1ee55b94183417be977ca287cd7391f9a6f7e721`. The COE #26 tree has that license under sibling `Pisowifi/`, but no root `LICENSE`, root `NOTICE`, or `Hardware/LICENSE`/ `Hardware/NOTICE` entry. This does not establish how the sibling license applies to the Hardware subtree. Keep license/NOTICE applicability as an explicit owner/custodian decision before any copy.

## Master disposition

1. **Accept as a draft-only fail-closed fallback candidate:** output inhibit before potentially blocking persistence and sticky no-auto-clear records are directionally correct.
2. **Do not accept it as an independent witness or production durability proof:** NVS and EEPROM emulation are on the same chip; both-store failure remains current-boot-only; no real flash/brownout/power-cut evidence exists.
3. Keep PR #323 OPEN / DRAFT / UNMERGED. No migration to COE #26, no source overwrite, and no change to `OWNERSHIP_ROUTES.json`.
4. Preserve default-deny poll/coin admission. The stale Full-build fixture belongs to QA; do not weaken firmware to satisfy a string-presence assertion.

## Required next actions

| Owner | Exact next action |
|---|---|
| PHX-HARDWARE | Document board/partition/EEPROM reservation assumptions and keep the same-chip fallback explicitly non-witness; provide physical flash/relay/power-cut plan |
| PHX-QA | Independently test exact #323 head for reboot after primary-store failure, secondary-store failure, partial/corrupt marker, and both-store failure; repair the stale positive poll-signature fixture without restoring admission |
| PHX-CORE | Review fault-hold event identity, receipt/disposition and replay/reconciliation implications |
| PHX-RELEASE | Review the focused workflow extension; keep signing/publishing skipped |
| COE integration owner | Reconcile exact blobs, test identity, workflow invocation and license/NOTICE scope before any destination staging |
| Registry custodian | Restore authorized private Drive v11 registry and newer corrections |

## Bounded verification and limits

- 12/12 Master static source/tree assertions passed: output-before-persistence ordering on both sketches, lab reboot/failure semantics, source workflow invocation, destination test absence, source/destination sketch blob divergence, and license blob identity. These are static assertions, **not** firmware unit tests.
- Exact-head GitHub Actions logs were inspected for #323 runs 44242190343, 44242190332 and 44242190324.
- Master Python suite: NOT RUN in this activation. Master PR-triggered CI at pre-change head `e95cda0...`: no runs returned.
- Physical GPIO/relay, actual NVS/EEPROM/LittleFS flash behavior, brownout, real coin pulses, power cuts, 150-cut acceptance and 30-device/24-hour soak: NOT TESTED.
- Private canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found through the exposed Library search; no Google Drive connector was available in this execution surface. Older v3–v7 snapshots were not substituted. No private registry content or identifiers were published.

**PRODUCTION NO-GO remains in force.**
