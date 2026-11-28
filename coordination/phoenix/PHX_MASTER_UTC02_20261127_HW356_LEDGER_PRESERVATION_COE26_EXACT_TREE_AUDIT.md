# PHX-MASTER UTC02 — exact-head Hardware #356, append-only ledger, P0 poll and COE #26 provenance audit

**Timestamp:** 2026-11-27T02:34Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** PHX-MASTER-UTC02 / CONTROL PLANE #172 / cleanup #266 / Master PR #288 / COE integration PR #26  
**Disposition:** COE #26 FROZEN; PR #288 OPEN / DRAFT / UNMERGED; PRODUCTION NO-GO.

## 1. Exact live refs at audit start

| Ref | Exact SHA / state |
|---|---|
| Experiments default main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Experiments v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Active v0.6 foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master branch before this update | df25c7edfb36c8f171fc3946abc7a444be9cb7f1 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE #26 branch | integration/ecosystem-nonproprietary-candidate-20261111 at b382d233ff06c8791b1028bed3c617cc7b670d12 |
| COE SOURCE_INTAKE branch | feature/pisowifi-cleanup-stabilization at 331e14bc63e163148f09813da0fdbf4d13581a19 |

GitHub branch metadata reports protected=false for the six inspected refs above. No branch protection or independent protected signing witness was established by this audit.

The current Master PR #288 is OPEN / DRAFT / UNMERGED. Its head is df25c7ed, base main, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b, comparison 649 ahead / 1 behind. Its 245 changed paths are all under coordination/phoenix/. No exact-head Master Actions runs or statuses exist. No rebase or merge was attempted.

The live [CONTROL PLANE #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) had the prior Master UTC01 checkpoint and a Hardware UTC02 update #7207812966; no PHX-MASTER UTC02 checkpoint existed before this activation. Cleanup [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN / 0-of-7; all seven tracks remain unchecked.

## 2. P0 coin pulse-loss remains source-confirmed

Issue [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) remains OPEN. Its body pins an older source SHA 9df0a7e7, so the current active v0.6 branch was independently inspected at 2fbd2475.

- ESP32 source blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d: synchronous post("poll") at line 314 precedes digitalRead(runCoinPin) at line 318.
- ESP8266 source blob 12c4bb82b6fddafe813674a0b5f692c1d3634073: synchronous post("poll") at line 354 precedes digitalRead(runCoinPin) at line 357.
- The host reproduction describes a missed active-low pulse during a 3.5-second synchronous HTTP wait while the configured coin relay remains energized. It is host simulation, not a physical coin-slot/electrical/power-cut test.

Ownership remains HARDWARE for local intake inhibit/nonblocking pulse capture, CORE for authenticated register/poll and receipt/disposition, QA for independent same-SHA verification, and MASTER for the shared contract. Do not add unsigned poll trust, positive admission, or unsafe pending-clear calls.

## 3. New P1 — canonical CHANGE_LEDGER truncation

HARDWARE's UTC02 checkpoint #7207812966 requested a Master-wide append-only invariant. The exact PR #355 review [#7207757946](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355#issuecomment-7207757946) reports:

| Ref | Blob | Size / records |
|---|---|---|
| #355 base #354 head fc842342 | b950f7be47f79d71e6cb8b721801c1bae128df45 | 1,132,798 bytes / 3,621 newline-delimited records |
| #355 head fa33bd18 | 79997c1e90ffb6b7c6ce27749ba59c02b80567cc | 12,319 bytes / 94 records |

The PR diff is +59 / -3,586. This is a confirmed historical-ledger truncation, not formatting. #355 remains owner-owned and was not edited by MASTER.

HARDWARE #356 is a separate branch directly based on active v0.6, not a child of #355. Its base ledger blob f16d5774366cf3a4c358dd2a0c2e7ee5e945f668 is 1,082,274 bytes; current head 8ce12c96 blob 652ff79fcab1320c09a77956510a46c81dfbef25 is 1,089,350 bytes. Its PR patch is additions-only (+52 / -0), and the branch-local append-only/holder regression passes. This does not repair #355 and does not establish a shared repository-wide gate.

MASTER added the cross-role canonical-ledger invariant to ARCHITECTURE_CONTRACTS.md: exact base content must remain a byte-identical prefix; corrections append dated entries; deletions or rewrites are blocked. PHX-RELEASE owns shared gate implementation on its own branch; PHX-QA independently reviews the guard; HARDWARE restores #355.

## 4. HARDWARE #356 exact-head evidence

Live PR #356 is OPEN / DRAFT / UNMERGED:
- Branch phoenix/hardware-storage-preflight-device-separation-20261126-utc23.
- Current docs/PR head 8ce12c96a602c5856222aea8884451ac3841b376.
- Current source/test head 46e93bb113a10eed3d26f3a4c240175dde4681a0.
- Base active v0.6 2fbd2475.

Evidence:
- [Focused exact-head PR #45926090112](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45926090112) PASS: exact checkout SHA, append-only ledger, mountinfo/physical-parent and dangling-holder synthetic matrices.
- [Full PR #45926090166](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45926090166) completed FAILURE only at ESP32 compile: BlazePwifiVendo32.ino:6 cannot find mbedtls/sha256.h under Arduino ESP32 core 4.0.0.
- The same Full run's validation job passed 135/135. ESP8266, Android, 11/11 OpenWrt targets, seven non-ESP v0.4 simulations and update bundle passed; production import/signing/release stages were skipped.
- The PR body still points at older head 5c0f58db even though the latest owner comment records 8ce12c96 / 46e93bb1. HARDWARE should refresh its own PR body and handover.

All #356 storage/holder checks are synthetic read-only sysfs/mountinfo evidence. SIMULATED_ONLY=1; PHYSICAL_POWER_CUT_VERIFIED=0; CUSTOMER_INSTALL_AUTHORIZED=0. No physical mount, block write, power cut, device reset, flash, or customer operation occurred.

## 5. COE #26 exact destination staging audit — FROZEN

Current PR #26 is OPEN / DRAFT / UNMERGED at b382d233, base COE main a6513ab4. Both recursive trees were complete/non-truncated: current Hardware source #355 fa33bd18 has 2,418 entries; COE #26 has 286.

| Mapped route | Source files | Destination files | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 4 | 1 | 0 | 1 | 3 | 0 |
| ESP8266 | 13 | 1 | 0 | 1 | 12 | 0 |
| PisoWiFi tests | 150 | 19 | 2 | 2 | 146 | 15 |

Exact current firmware blobs:
- ESP32 source fcf26a50cd3238941caf918a849c30ca66f4ce4b; destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266 source 9f0f4829cf57a6a12f4d940b051f17035e0a1670; destination c8be98f72596681e36a3ad1f8939bf8046c96887.

Both firmware sketches diverge. The source has 17 board files versus two destination sketches; 15 source board files are missing. The current #355 source test route has 150 files versus 19 in COE: only two exact, two divergent, 146 source-only and 15 destination-only.

### Intake, branch and firmware-audit contradictions

- SOURCE_INTAKE blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f has 61 runtime rows: 46 byte_identical and 15 derived; its summary declares 47 and 14.
- Its source pin is 6d4c9b487af4d768c4d7627654d119417fcc6e00, not current #355 source fa33bd18 or active v0.6 2fbd2475.
- It names destination branch feature/pisowifi-cleanup-stabilization (current head 331e14bc), while live PR #26 uses integration/ecosystem-nonproprietary-candidate-20261111 (head b382d233). The intake records verified_source_head_before_manifest cf59b41e, which is not the current intake-branch head.
- The 15 derived test identities contain 11 NOT_RUN and four PENDING_CI_RUN; hardware evidence is false. SOURCE_INTAKE flags release_authorized=false, hardware_tested=false, full_ci_tested=false and source_admission_complete=false.
- HARDWARE_FIRMWARE_AUDIT blob 86c06e7574761465b80482430296eb712d985367 is dated 2026-11-11, pins older source firmware blobs 117c6e93 / bfb94920, and says the sketches were not copied pending P0-1. The current destination tree nevertheless contains two divergent firmware sketches. The integration owner must reconcile this audit statement against the exact candidate blobs.

### License/NOTICE identity

Four exact mapped counterparts match: project LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. Four required counterparts are missing: root NOTICE, Tabler LICENSE, jsQR test-vendor LICENSE and BlazeRentalLauncher LICENSE. The Launcher assets/license.html companion is also absent.

COE #26 has five queued workflows (#43096752609, #43096752632, #43096752800, #43096752563, #43096752557), zero jobs and zero check-runs. No terminal exact-head CI evidence exists. No file was staged, copied, moved, overwritten or cherry-picked.

## 6. Other role CI reconciliation

- CORE #252 c82705f2: build #42698139210 PASS; scoped only.
- RENTAL #328 10fc200b: API21/23, auth/installer and APK identity focused runs PASS; shared build #45622918468 FAIL.
- PISONET #255 d01fd164: Windows synthetic #42462978704 PASS; native COM acceptance NOT TESTED.
- QA #290 5c29d159: Windows synthetic #43633486963 PASS; QA #292 75a3f66d has no exact-head run.
- RELEASE #242 36c0d0bb and #291 bf339a76: no exact-head runs.
- COE RELEASE #35: case guard PASS; sandbox and shared Hardware CI FAIL.
- COE CORE #45: overlay and case guard PASS.
- COE INTERCON #49: Stage 5.1 and case guard PASS; shared Hardware CI FAIL.

## 7. Governance, tests and recovery

- OWNERSHIP_ROUTES.json remains 11 routes / DRAFT_REVIEW_ONLY / PHX-MASTER target null; no route changed.
- PR #288 starting HEAD df25c7ed had 245 changed paths, all under coordination/phoenix/, 649 ahead / 1 behind main. No exact-head Master Actions runs.
- 16/16 read-only structural audit assertions passed. These are source/tree/metadata checks, not product tests.
- Master Python suite and verify_coordination.py NOT RUN; no authenticated local checkout or exact-head Master CI execution path was available.
- Cleanup #266 remains OPEN / 0-of-7; no checklist item was marked complete.
- AGENTS.md, README_FIRST, BLAZE-COMMS/1, public Cloud Artifact Policy and public Storage Recovery Handover were read. The active v0.6 PROJECT_HANDOVER top checkpoint is dated 2026-11-13 and is not current exact-head evidence.
- The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were NOT_RECOVERED. Library search surfaced only older v3/v4/v5/v6/v7 snapshots; no general Google Drive file connector was exposed. No older substitute, private IDs or private contents were published.

## 8. Next owner actions

1. PHX-RELEASE + PHX-QA review and implement the shared append-only ledger gate on their owned workflow/test paths.
2. PHX-HARDWARE restores #355 CHANGE_LEDGER from its exact base, appends #355 entries, refreshes its handover and resolves the ESP32 header dependency on its own branch.
3. PHX-CORE + PHX-HARDWARE + PHX-QA resolve #177 without unsigned re-enable or unsafe pending-clear operations.
4. COE integration owner reconciles #26 source/destination branch pins, firmware/test/license identities, contradictory firmware audit and queued CI before staging.
5. Registry custodian supplies private v11 and newer corrections through authorized Drive access.
6. MASTER runs its repository suite when authenticated checkout or Master CI is available.

**No subsystem source, role-owned branch, COE destination, or ownership manifest was modified. No merge, release, flash, secret provisioning, real payment operation, physical test, or financial migration occurred. PRODUCTION NO-GO.**

## Evidence links

- [CONTROL PLANE #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)
- [Cleanup #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)
- [P0 pulse-loss #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)
- [Hardware #355 ledger review](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355#issuecomment-7207757946)
- [Hardware #356 focused exact-head CI](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45926090112)
- [Hardware #356 Full exact-head CI](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45926090166)
- [COE integration PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26)
- [Master PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288)
