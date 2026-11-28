# PHX-MASTER UTC08 — exact-head release handover, poll-deny and COE staging audit

**Updated:** 2026-11-19T08:31:28Z  
**Role:** PHX-MASTER — coordination/phoenix only  
**Disposition:** DRAFT REVIEW ONLY · COE migration BLOCKED · PRODUCTION NO-GO

## 1. Exact repository and PR identities

| Item | Live ref |
|---|---|
| Experiments default branch | main @ f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Current development branch | blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Legacy development branch still present | blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| PHX-MASTER branch | phoenix/master-coordination @ 75319bb34a44cfa442f46d462664154b2926bb34 |
| Master PR #288 | OPEN / DRAFT, head 75319bb34a44cfa442f46d462664154b2926bb34, base main @ f4e8a891aed8af86d5fd315d28750a0ac3a7372b, 98 changed files |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | OPEN / DRAFT, head b382d233ff06c8791b1028bed3c617cc7b670d12, base main @ a6513ab4412b4c014eee2863e45cbe32d06cb243, 205 changed files |

The Experiments default branch is main. The v0.6.0 audit-foundation branch is the development ref named by the current control-plane body; the older v0.5.3 development branch remains present but is not substituted for it. COE main has only three tree entries in the current tree response; the 286-entry destination tree inspected here is PR #26 staging, not main.

The routing manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, destination PR #26, PHX-MASTER target null. It was not edited.

## 2. PHX-HARDWARE #327 — current deny-only source vs legacy positive fixture

Current PR #327 is OPEN / DRAFT at c62af73ec5b45cd87f4c8f3295ede18f307fb359, based on #326 at 58c558fb6a237935214621adc3dee65a10fe1a51.

Exact-head Actions:
- Quarantine/readback #44486759401: SUCCESS.
- Relay/output #44486759408: SUCCESS.
- Full PR build #44486759380: FAILURE at validation job 135432034884, step Controller protocol parity. Log: “Missing poll signature check” in the ESP8266 source. All 13 firmware/platform target jobs and Android completed successfully; downstream simulations, update bundle, candidate, signing and publishing jobs were skipped.
- Push Full #44486749742: FAILURE.

The current source-extracted poll-response lab is blob 69dbddee4133588940f4c5b53817401db531a8a4. It compiles the production parser/acceptance/output functions and explicitly denies unauthenticated and positive-looking poll responses; its log contract reports 11/11 fail-closed cases per board, strict root JSON cases and default-deny coin disposition. It is simulated host evidence, not hardware acceptance.

The inherited source fixture tests/v05_firmware_hardening_test.sh is blob 41211b2c110ab409f6d9d1812ef12fda73b13211. It still requires positive source strings response_sig, |register| and |poll|. That expectation conflicts with the current firmware's deliberate default-deny behavior. The destination Hardware/tests/test_firmware_hardening.sh has the same positive-presence assumptions. Do not add fake tokens or enable unauthenticated poll admission to satisfy the fixture. PHX-QA owns replacing the stale positive assertion with source-exact negative/default-deny tests; PHX-HARDWARE retains firmware ownership.

## 3. Exact Hardware migration staging comparison — no move proposed

At source #327 head c62af73, the ESP32 sketch blob is 754a5738d30500fe12a573b89956fedeb0e279c3 (62,883 bytes) and the ESP8266 sketch blob is 1b32cb90be11da79ba7ea1155f128aee9e495dd2 (67,304 bytes).

At destination PR #26 head b382d233, the corresponding Hardware blobs are:
- ESP32: 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 (18,505 bytes).
- ESP8266: c8be98f72596681e36a3ad1f8939bf8046c96887 (18,394 bytes).

Neither pair is byte-identical. The current source tree contains 22 board-local Python lab files across the ESP32 and ESP8266 directories (8 ESP32, 14 ESP8266); the destination Hardware subtree contains one generic shell hardening test. The test identities and expected behavior are not equivalent: source poll-response tests deny all current positive-looking responses, while destination/source legacy shell checks require positive signature/poll markers.

License readback:
- Source BlazePwifi/LICENSE and destination Pisowifi/LICENSE are identical blob 1ee55b94183417be977ca287cd7391f9a6f7e721 (1,071 bytes).
- Source BlazePwifi/NOTICE.md is absent at the inspected source ref.
- Destination Hardware/LICENSE and Hardware/NOTICE.md are absent at PR #26 head.
- The Pisowifi license does not establish license/NOTICE scope for the separate Hardware subtree.

COE #26 exact-head workflows remain five QUEUED runs with zero jobs: #43096752609, #43096752632, #43096752800, #43096752563 and #43096752557. No destination build/test has executed from these runs. No copy, move, overwrite, staging edit or migration proposal was made.

## 4. PHX-RELEASE #291 — stale checkpoint head and live handover failure

Live PR #291 is OPEN / DRAFT at d498afbf2aa0e60fc1b1d0471328f5e6eb8e597c, base 734b89d9e7792247e8376335c3f3685500ab3f89.

The UTC08 RELEASE checkpoint comment #7003579497 names b8f4e3619a8c84b4e81d8bb24ba3da02825fa9e6 as the current head. GitHub compare proves that b8f4 is an ancestor of the live PR head: d498 is 12 commits ahead / 0 behind b8f4. The intervening 12 commits touch seven paths, including the provenance scripts, BlazePwifi workflow, and canonical product handover/current-state/change-ledger documents. The comment's head identity is therefore stale; it is not evidence for the current PR head.

Exact current-head Actions:
- Windows release #44487146268: FAILURE at handover job 135433327396. The log reports source/workflow changes newer than experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md, last checkpoint dd62b3b468690fcfa3add9268d4ddd6842f3cc8a, and identifies .github/workflows/blazepwifi-build.yml. Windows build and publisher jobs were skipped.
- BlazePwifi build #44487146258: overall FAILURE at validation job 135433430795, mandatory handover freshness gate. Board compile jobs, including ESP32 and ESP8266, completed successfully; downstream validation/release gates were skipped.
- ESP32 compatibility #44487146336: SUCCESS.
- Push ESP32 compatibility #44487138529: SUCCESS.

Do not bypass the handover gate. PHX-RELEASE must refresh the authoritative product handover, current state and change ledger on its own branch with the exact workflow/source SHAs, toolchain pins, artifact hashes, CI run/job IDs and unsigned/unreleased state, then rerun exact-head CI and post a corrected checkpoint naming d498af.

## 5. COE Release and other role exact-head evidence

COE Release #35 is OPEN / DRAFT at 5047af8b5a8296e06294bbda6bf42a6baea2294d, based on #31 at 59ed44d0b911e176f1a95b9cf5585ef811ffd31b:
- Shared/firmware #44465377784: SUCCESS.
- Case-collision #44465377781: SUCCESS.
- Mandatory sandbox #44465377807: FAILURE closed after 14/14 host-preflight tests because bubblewrap is not installed; no fallback was used.

Current scoped role references:
- CORE #252 c82705f2de865c89ab733b10efa84f26f56a5cc4: scoped run #42698139210 SUCCESS; separate CORE continuation retains source ownership.
- RENTAL #289 68928774d0d7cf65adb26bc6b54199a3159d066c: #43653329235 and #43653329229 SUCCESS.
- PISONET #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09: #42462978704 SUCCESS, scoped; native COM acceptance not established.
- QA #290 5c29d15994cee1279058f1eca12f2a3180704292: #43633486963 SUCCESS, scoped.
- QA #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96: no current-head workflow run returned.
- COE CORE #45 9d76a134c1f6512aa40c20ec4d247306a71a8cce: #44295049727 and #44295049903 SUCCESS for synthetic receipt-v1 scope only; not Master-v2 adoption or financial authority.

## 6. Governance, access and execution limits

- Cleanup issue #266 remains OPEN; its seven-track cleanup checklist is not evidence of completion or worker notification.
- Branch objects for Experiments main, v0.6.0 development, Master and COE main report protected=false; both repository rulesets endpoints return empty arrays. Repository administration must independently verify effective required-check/protection settings.
- Experiments AGENTS.md, README_FIRST, the Master prompt and BLAZE-COMMS/1 were read. COE root AGENTS.md returns 404. The AGENTS-linked cloud policy/storage handover could not be fetched through the available GitHub connector.
- The canonical private Drive registry v11 and newer corrections were not found in the Library search. No Google Drive connector is exposed in this runtime. Older registry snapshots were not substituted and no private contents or identifiers were published.
- Master branch source/PR inspection completed. Exact-head Master Actions returned no runs. A direct shallow Git clone failed because this runtime could not resolve github.com; the full Master Python suite was NOT RUN. No Master test pass is claimed.

## 7. Owner actions

1. PHX-QA: replace the stale positive poll-signature fixture with source-exact negative/default-deny tests and retain the fail-closed lab in Full validation at #327's exact source/test SHA.
2. PHX-HARDWARE: retain deny-only firmware behavior and refresh its own exact-head handover after any source change.
3. PHX-RELEASE: refresh #291 product handovers at the live branch head d498af, correct the stale checkpoint identity, and rerun exact-head gates without bypassing freshness.
4. PHX-RELEASE / infrastructure owner: provide an authorized bubblewrap-capable runner for COE #35; no unsandboxed fallback.
5. COE integration owner: complete per-file blob/mode/license/test identity and import mapping, pin destination toolchains, and obtain executable #26 exact-head workflows before any staging proposal.
6. Repository administrator: verify branch protection and required checks.
7. Registry custodian: restore authorized read-only access to private registry v11 and newer corrections.

**PRODUCTION NO-GO:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, flash, secret provisioning, real payment operation or financial migration occurred.
