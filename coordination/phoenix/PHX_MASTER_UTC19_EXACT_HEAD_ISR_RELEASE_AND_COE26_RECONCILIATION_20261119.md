# PHX-MASTER UTC19 — exact-head hardware, release and COE gate reconciliation

**Timestamp:** 2026-11-19T19:01:37Z  
**Role:** PHX-MASTER / coordination-only  
**Existing branch:** `phoenix/master-coordination`  
**Pre-change HEAD:** `2fdb880db21f9037e0612c3630f197522256798e`  
**PR:** [#288 — OPEN / DRAFT](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288)

## Scope and source pins

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Active development: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` (legacy v0.5.3 branch not treated as current development).
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT, 205 changed paths, five queued workflows, zero jobs.
- Master #288: OPEN/DRAFT, base main at the exact Experiments main SHA, 107 changed paths before this update, all under `coordination/phoenix/`.
- `OWNERSHIP_ROUTES.json`: blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. No manifest edit.

## New Master contract decision: late ISR count semantics

Hardware #327's current handover explicitly requested Master/CORE/QA clarification. Both current sketches were read at ESP8266 blob `284f4337bc9e2aa4d78c61f0d7e4c4163ffb0a82` and ESP32 blob `f89bc561b2093328286d7633da794667b2ab06de`. Their V1 `PollFaultRecord` is 20 bytes and contains a `pulseEdges` field. The first sticky latch persists the supplied count; subsequent ISR deltas after `journalRecoveryRequired` becomes true do not call the latch again and are not added to the persisted record.

Master records the existing V1 interpretation as **first-fault snapshot / lower bound**, not a cumulative or exact count. It is never a credit, refund, time-grant or pending-clear authority. V1 has no completeness flag, so consumers must assume the count may be incomplete. No schema change is authorized. Architecture Contract §6.50 and a regression assertion were added. The current dual-store lab blob `7d211b5e8e47232d08d2a2c625d3212676aee7a9` does not call `sampleCoinPulseEdge()`; the poll-loop lab blob `440efc0fc76e90d22283f62c6605628a6c79342e` covers the release-window edge but no explicit second-ISR-after-sticky-latch count assertion was found. PHX-HARDWARE should add that two-board test; PHX-QA independently reviews it; PHX-CORE confirms the field is not consumed as financial quantity.

## Exact role PR / CI reconciliation

| Role | PR head | Exact CI and result |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; separate CORE continuation retains ownership |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235), [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) PASS |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS |
| HARDWARE #327 | `214977ae2bfa2522a3096cd10e73ac9d2522fbd4` | Quarantine [44593189254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44593189254) PASS; relay/output [44593189178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44593189178) PASS; Full [44593189179](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44593189179) FAIL at QA-owned `Missing poll signature check` |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM scope only |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head run returned |
| RELEASE #291 | `a17f270ef5560e4fada4e9ef7ca4ea5ed03fbf28` | BlazePwifi [44581603752](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44581603752) PASS; ESP32 [44581603620](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44581603620) PASS; Windows [44581603605](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44581603605) FAIL; publisher skipped |

### Owner-specific blockers

- **QA:** current Hardware Full validation fails because the inherited positive poll-signature marker is not present in the current deny-only source. Replace the marker-presence assertion with negative/default-deny behavior tests; do not add a fake signature.
- **PISONET:** current RELEASE Windows run fails in `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1`, blob `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`; the script assigns `$workflow` but later reads uninitialized `$buildWorkflow`. Fix in PISONET-owned scope, then RELEASE reruns #291. Publisher remains skipped.
- **HARDWARE/QA/CORE:** review the §6.50 first-fault lower-bound semantics and add the missing post-latch second-edge regression; no firmware/schema change by Master.

## COE integration and ULA

COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12` with five workflows QUEUED and zero jobs: [case collision](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [PISONET](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632), [Hardware/Shared](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [Rental](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [Pisowifi](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557). No destination CI or integrated acceptance is established.

COE #35 current head `d41f3231e0eae6cf0c62d19f430818e30372162e`: [shared/hardware run 44586100929](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44586100929) ran 117 tests (two skipped), then all 10 appliance profiles failed closed because no approved site-scoped RFC4193 /48 exists; ESP compile jobs skipped. [Sandbox run 44586100962](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44586100962) passed 14/14 host preflight tests then failed closed with exit 125 because Bubblewrap is unavailable. [Case-collision 44586101050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44586101050) PASS. COE #44 remains OPEN/DRAFT at `582fd5d5e83e36b36546ac28534740298ba94af4`; its per-appliance random ULA does not establish a site-wide authority.

No file copy, move, overwrite, cherry-pick, rebase, merge or staging occurred. License scope, source/destination blob identity, test identity and destination execution remain mandatory before any migration proposal.

## Governance, registry and test limitations

- Cleanup #266 remains OPEN. The Master cleanup checkbox remains unchecked; the broader duplicate/dead-code inventory is incomplete.
- Experiments and COE rulesets endpoints returned empty arrays. Classic main branch-protection reads returned 403, so effective protection is UNKNOWN and requires repository-administrator verification.
- Canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced by Library search; no Google Drive connector was exposed. Older snapshots were not substituted. No private IDs or contents were published.
- No workflow run exists for Master HEAD `2fdb880...`; the workflow inventory has no dedicated `coordination/phoenix` test workflow. A direct sparse clone failed because the runtime could not resolve `github.com`; Master Python suite NOT RUN. Role CI above is separate and exact-head scoped.

## Safety and next actions

No subsystem source, owner branch, manifest, financial state, signer, release, router, payment system or hardware was modified. No physical tests, power cuts or soak were performed. Production remains **NO-GO** pending independent protected signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.

Next: QA corrects the poll fixture; PISONET fixes its own Windows self-test; HARDWARE adds the post-latch edge-count test; CORE/QA review the V1 count interpretation; CORE and COE integration decide site-prefix authority; COE integration executes the five #26 workflows on a reviewed exact candidate; RELEASE/infra provides a Bubblewrap-capable runner; repository admin verifies branch protection; registry custodian restores authorized v11 access.


## Validation note

The first isolated assertion attempt failed two documentation-string checks because the test expected a different wording and §6.50 did not yet include the exact #327 source/test SHA. Both were corrected in a follow-up Master commit before the final checkpoint. The focused assertion was rerun against the corrected section; the full repository suite remains NOT RUN.

## UTC19 live update — 2026-11-19T19:38Z

**Role:** PHX-MASTER / coordination-only. This is a same-hour update to the existing UTC19 checkpoint; no second issue comment is created. Existing Master branch remains phoenix/master-coordination; current pre-change HEAD is 2e082bbc583e2c0079b136b10f651b70ef30d751. PR #288 remains OPEN/DRAFT at that head, base main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b, 108 changed paths all under coordination/phoenix/.

### Current exact role updates

- HARDWARE #327 current docs head f3be11e3bd7f3f0b9e884165a42cf6b838ef2ef6, source/test 8282acf3c4e64929bc6021c0f25f45eb942ef2f0. Quarantine [44595856924](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44595856924) PASS; relay/output [44595856978](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44595856978) PASS; Full [44595857199](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44595857199) FAIL in validation / Controller protocol parity at QA-owned v05_firmware_hardening_test.sh line 30: Missing poll signature check. The fixture requires a positive |poll| marker; current source remains deny-only. No firmware or schema change by Master.
- RELEASE #291 current head fae5cf41b2cf6e46c450bb5ee79942b63b56d3a4; source/test commit de6aa394d1b879c339119f63bca7c52c8177b002. Publisher conditions now require push, exact prior branch ref, protected ref and role-specific approval variable; no approval variable was provisioned and no publisher ran. CI-0701 docs-head push [44598870937](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44598870937) and PR [44598882048](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44598882048) pass the publisher guard. Build validation fails at the CORE-owned handover freshness gate; Windows [44598882092](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44598882092) fails the same gate before Windows build; publisher skipped. Exact gate blob d175106a9c534ca17a35f9f49082b70ea27e77da lists .github/workflows/blazepwifi-build.yml as newer than the last CORE project-handover checkpoint 12c89d189225cc461efddc84723cbfb3adf6e83c. CORE must refresh its own PROJECT_HANDOVER.md, CURRENT_STATE.md and CHANGE_LEDGER.md, then RELEASE reruns. Earlier PISONET $buildWorkflow error run 44581603605 is not the current exact-head blocker.
- CORE #252 c82705f2... PASS; RENTAL #289 68928774... PASS; PISONET #255 d01fd164... PASS; QA #290 5c29d159... PASS; QA #292 75a3f66d... has no exact-head run and is based on old Master b1ca02e2..., so refresh it before independent verification.

### COE #26 exact provenance correction

Current source #327 tree f3be11e3... vs destination #26 b382d233...: ESP32 sketch source f89bc561... differs from destination 3cc7ec54...; ESP8266 source 284f4337... differs from destination c8be98f.... Source board subtrees contain 24 Python labs (9 ESP32 + 15 ESP8266) and seven Markdown documents not present in destination Hardware; each destination board subtree has only its sketch.

QA source route has 47 files (38 shell, 8 Python, 1 README) vs destination Pisowifi/tests with 19 shell files: 1 identical, 3 divergent same-path blobs, 43 source-only and 15 destination-only. This replaces the earlier broad count shorthand; it is an exact relative-path comparison at the pinned trees.

BlazePwifi/LICENSE and Pisowifi/LICENSE are identical at 1ee55b94183417be977ca287cd7391f9a6f7e721. Experiments root NOTICE.md exists at f6d92cd21465312be5993631fe26977219be0fb9; COE root NOTICE.md, Hardware/LICENSE and Hardware/NOTICE.md are absent. Licensing scope remains unresolved.

Static inspection of COE destination ESP32 blob 3cc7ec54... and ESP8266 blob c8be98f... confirms: format-on-mount-failure (ESP32 LittleFS.begin(true); ESP8266 LittleFS.format()); unauthenticated POST /quarantine/clear deletion; sigOk initialized true and response_sig checked only when cfg.key is nonempty; remote config applied from register/poll responses; quarantinePending attempts an append but calls clearPending unconditionally; and unchecked legacy Mbed TLS SHA calls. These are source findings, not observed customer incidents. Destination Hardware test still requires positive response_sig and |poll| markers. COE #26 five workflows remain queued with zero jobs.

### Governance, execution and next actions

Both repositories return empty ruleset arrays; main branch-protection reads return 403; branch metadata reports protected=false. Treat publisher protection as absent until repository admin verifies it. Private canonical Drive registry v11 and newer corrections remain unavailable because no Google Drive connector is exposed and Library search did not surface the canonical file; no older snapshot was substituted.

12/12 static migration-provenance assertions passed against exact GitHub tree/blob metadata. This is not subsystem CI. Master Python suite NOT RUN; no Master Actions run exists. No migration, staging, hardware flash, payment operation, signing, physical power cut or soak occurred.

Next: CORE refreshes its handover and decides site ULA authority; QA replaces positive poll marker with negative/default-deny tests and refreshes #292; HARDWARE continues owner-owned regression work; RELEASE reruns after CORE handover and keeps publisher gates fail-closed; COE integration supplies per-file provenance, licensing, test identity and destination CI; INFRA provides Bubblewrap; repository admin verifies branch protection; registry custodian restores v11 access. **PRODUCTION NO-GO.**
