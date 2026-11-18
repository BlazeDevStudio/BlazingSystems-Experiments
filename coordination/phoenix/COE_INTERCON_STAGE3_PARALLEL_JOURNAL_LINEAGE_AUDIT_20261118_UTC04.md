# COE Pisonet INTERCON — parallel Stage-3 journal lineage audit
**Audit timestamp:** 2026-11-18T04:39:47Z  
**Role:** PHX-MASTER — coordination, architecture contracts and migration provenance only  
**Status:** BLOCKED / DRAFT ONLY / PRODUCTION NO-GO  
**Master source:** `BlazeDevStudio/BlazingSystems-Experiments` `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**COE destination:** `BlazeDevStudio/CoinOperatedEcosystem` `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration draft #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`  
**Master branch before this audit:** `1c6c874c489474eb6b5aa1b10793e10eff547f63`

## Executive decision

**Do not select, merge, transplant or promote any COE INTERCON Stage-3 journal candidate yet.** Three open draft PRs (#39, #40, #42) independently replace the same staging sketch, workflow and durable-journal contract with incompatible record encodings/adapters. Stage-4 PR #41 is built specifically on #39 and is not a portable child of #40 or #42. The existing ownership manifest has no route for the Labs-origin Universal project or this new COE INTERCON tree. The imported public source also has no explicit license grant in the inspected source tree.

This is a provenance/coordination hold, not a claim that the host tests failed. The exact PR-triggered CI runs for all three Stage-3 alternatives and the Stage-4 child completed successfully, but they are host fault-injection tests and a source-only NodeMCU compile—not physical flash, power-cut or paid-credit acceptance.

## 1. Source custody, import completeness and license

The COE PR #36 source is the existing public [Blaze Pisonet Universal](https://github.com/BlazeDevStudio/BlazingSystems-Labs/tree/main/embedded/blaze-pisonet-universal), not the Phoenix Windows SoftTimer and not the router-linked BlazePwifi Vendo firmware.

- Labs source: [original .ino](https://github.com/BlazeDevStudio/BlazingSystems-Labs/blob/main/embedded/blaze-pisonet-universal/BLAZE_PISONET_UNIVERSAL_PUBLIC.ino), blob `3fb15ecb9272b65500260bc7c92f05590163fa6d`.
- COE #36 legacy import: [destination .ino](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/migration/blaze-pisonet-universal-intercon-audit-20261118/Hardware/esp8266/BlazePisonetUniversal/legacy/BLAZE_PISONET_UNIVERSAL_PUBLIC/BLAZE_PISONET_UNIVERSAL_PUBLIC.ino), same blob `3fb15ecb9272b65500260bc7c92f05590163fa6d`. **Byte-identical source-file identity verified.**
- The Labs source folder contains three files: the .ino, its README and browser-only `preview.html`. COE #36 imports the .ino unchanged, writes an adapted destination README, and omits the browser-only preview. This is a selective firmware-source intake, not a complete folder mirror; the omitted preview is not an ESP8266 build dependency.
- Labs root has `NOTICE.md` but no root `LICENSE`; the notice describes public/private separation and does not grant a software license. The .ino has no SPDX/license header. COE main has no root LICENSE/NOTICE and #36 adds no license file. **Redistribution/license status therefore remains UNKNOWN**, not implicitly MIT/public-domain. Obtain an owner/custodian license determination before any further copy into #26/main.
- The destination README correctly keeps the legacy plaintext UDP CREDIT and relay-toggle hazards visible. Do not flash this legacy source or treat its unauthenticated credit path as a financial interface.

## 2. Exact PR ancestry and competing branches

All listed PRs remain OPEN / DRAFT / UNMERGED at the inspected heads.

```text
COE #26 @ b382d233 (integration candidate; not main)
  └─ #36 @ b4d74347  legacy-source intake + V1.5-derived staging
       ├─ #37 @ 1e9b0269  separate V1.6 AP+STA/discovery branch
       └─ #38 @ 8dc5cc65  V1.7 authenticated peer transport
            ├─ #39 @ 33e87fbd  Stage-3 journal A (64-byte record)
            │    └─ #41 @ 021e2474  Stage-4 shadow-credit lab child
            ├─ #40 @ 85f38c6e  Stage-3 journal B (76-byte record)
            └─ #42 @ a35672fb  Stage-3 journal C (92-byte record)
```

- #36 is based on #26 at `b382d233...`.
- #37's recorded base snapshot is `f58e6951...`; comparing current #36 head `b4d74347...` to #37 head `1e9b0269...` returns **diverged, 7 ahead / 11 behind**, merge base `d12126fb...`. #37's CI is green, but its branch is not a clean current child of #36.
- #38 is based on current #36 head `b4d74347...`.
- #39, #40 and #42 all use #38 head `8dc5cc65...` as their base. Compare #39 → #40 is **diverged, 9 ahead / 12 behind**; #39 → #42 is **12 / 12 diverged**; #40 → #42 is **12 ahead / 9 behind**. They are alternatives, not a sequential Stage-3 stack.
- #41 is 7 commits ahead / 0 behind #39 and directly depends on #39's journal implementation. If another Stage-3 candidate is selected, #41 needs explicit owner reconciliation/rebase; do not assume it composes.

## 3. Journal formats and test identities

| Candidate | Exact sketch blob | Journal/adapter identity | Host test identity | Record format |
|---|---|---|---|---|
| #39 `33e87fbd...` | `e4c4991d...` | `InterconDurableJournal.h` blob `8fabe4a0...`; `InterconJournalFS.h` blob `63311355...` | `intercon_durable_journal_test.cpp` blob `54c8ab76...` | 64-byte record; CRC32; generation + one pending Master event |
| #40 `85f38c6e...` | `f37bb3c2...` | `InterconDurableJournal.h` blob `012fa7bd...`; `InterconLittleFSJournal.h` blob `d3f3a90a...` | same test path, different blob `a746f9a1...` | 76-byte record; CRC32; local/peer chip binding and event/balance snapshot |
| #42 `a35672fb...` | `a782bb91...` | `InterconJournalCodec.h` blob `a4d3a265...`; `InterconFlashJournal.h` blob `cb130663...` | `intercon_journal_fault_test.cpp` blob `3abde663...` | 92-byte image; CRC32 plus a 128-bit HMAC-derived key fingerprint |
| #41 `021e2474...` | inherited #39 sketch + Stage-4 changes | `InterconLabCredit.h` and signed shadow-credit dispatch | `intercon_lab_transfer_test.cpp` blob `19b2cc51...` | Depends on #39's 64-byte journal; shadow-credit test path only |

The same source path `BlazePisonetIntercon.ino`, workflow path `.github/workflows/intercon-stage1-ci.yml`, and—between #39/#40—the same journal header/test paths carry different blobs. Selecting one without owner/QA reconciliation would silently choose a different on-flash schema and adapter.

## 4. Exact CI and what it proves

The signed-wire job logs were opened, not inferred from green badges:

- [#39 Stage-3 run 44234479271](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44234479271), job 134567170504: HMAC wire test, credit-ledger test and 64-byte journal test executed; log reports dual-slot/CRC, atomic event+balance, lost ACK, reboot, torn-write and uncertain-result PASS. NodeMCU compile and static contract/case-collision jobs also succeeded.
- [#40 Stage-3 run 44235077999](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44235077999), job 134569137586: HMAC wire, credit ledger and 76-byte journal test executed; log reports 76 torn-write positions, ACK loss, reboot and idempotency PASS. NodeMCU compile and static/case jobs succeeded.
- [#42 Stage-3 run 44235625165](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44235625165), job 134570938316: HMAC wire, credit ledger and 92-byte image fault test executed; log reports two-slot generation, pre/post-rename crash model, ACK loss, dedupe, wrong issuer and degraded fail-closed recovery PASS. NodeMCU compile and static/case jobs succeeded.
- [#41 Stage-4 run 44235451605](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44235451605), job 134570368384: Stage-3 tests plus signed Master → durable Slave → signed ACK shadow-transfer test executed; log reports lost ACK, reboot, replay, corrupt/torn storage and fail-closed PASS.
- #36 Stage-1 [44226768392](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226768392), #37 V1.6 [44226761277](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226761277), and #38 Stage-2 [44229469988](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44229469988) completed success for their stated source/host/compile scopes.

These are **host simulation and source compilation**. They do not prove ESP8266 LittleFS crash atomicity on real flash, brownout behavior, relay/coin isolation on a physical board, real two-device radio behavior, 150 physical power cuts, or a 30-device/24-hour soak. CRC32 is an integrity checksum, not an authentication primitive; key/peer binding and the signed transport remain separate contracts.

## 5. Integration and cross-role status

- COE #26 remains OPEN/DRAFT at `b382d233...`; its five integration workflows (case, Pisonet, Hardware/Shared, Rental, PisoWiFi) are still QUEUED with zero jobs returned. #36–#42 are not merged into #26 or main.
- COE #35 current head `a7eacc99...`: shared/board [44237486266](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44237486266) and case [44237486270](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44237486270) succeeded; mandatory sandbox [44237486257](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44237486257) failed closed at the hosted unprivileged UID-map probe. Release remains blocked.
- Experiments role snapshot: CORE #252 `c82705f2...` scoped CI success; RENTAL #289 `68928774...` scoped CI success; Windows PISONET #255 `d01fd164...` scoped CI success; QA #290 `5c29d159...` success, #292 has no runs; RELEASE #291 `a74b8b94...` scoped success.
- Hardware remains unresolved: #317 Full validation fails at the QA-owned legacy positive poll-signature fixture; #320 Full run is cancelled; #322 focused output/quarantine labs pass but Full validation fails; #318 has no current-head run. No Hardware stack selection or reboot-safe marker-open recovery proof is inferred here.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. It has no route for Labs `embedded/blaze-pisonet-universal` or the COE INTERCON staging subtree. Existing PHX-PISONET scope is Windows SoftTimer; existing PHX-HARDWARE source scope is BlazePwifi ESP32/ESP8266. Do not infer a new owner from the destination folder name.

## 6. Master decision and exact owner actions

1. Keep #39, #40 and #42 as separate OPEN/DRAFT alternatives. Do not merge, cherry-pick, transplant or promote one by recency.
2. The COE INTERCON maintainer must nominate one canonical Stage-3 schema/adapter and explain the compatibility or retirement plan for the other two.
3. PHX-QA must independently review the selected exact source/test SHA and its negative/recovery vectors. Keep #41 explicitly dependent on #39 unless its owner reconciles it against the selected Stage-3 implementation.
4. The responsible Hardware owner must run real-board LittleFS fault/power-cut, relay, coin-input and two-node tests. Host simulations are not physical acceptance.
5. The Labs/COE source custodian must confirm redistribution rights for the imported public source; public visibility and the engineering NOTICE do not establish a license grant.
6. COE integration owner must preserve #26 and its current staging history; no source moves until per-file provenance, licensing, imports, tests and exact-head CI are reconciled.
7. Restore authorized access to the canonical private Drive v11 registry and newer corrections. The exposed Library search did not contain that exact canonical file; older snapshots and a later checkpoint were not substituted or published.

**No subsystem source branch was changed. No migration, merge, release, signing, flashing, physical test, secret provisioning or real-payment operation occurred. PRODUCTION NO-GO remains mandatory.**
