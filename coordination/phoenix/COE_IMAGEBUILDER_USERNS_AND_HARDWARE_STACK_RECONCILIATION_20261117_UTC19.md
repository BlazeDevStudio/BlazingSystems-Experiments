# PHX-MASTER UTC19 — COE sandbox substrate, ULA and Hardware stack revalidation

**Audit time:** 2026-11-17T19:34:39Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Branch:** phoenix/master-coordination  
**Pre-audit HEAD:** 598481bfc2eb91efd1f6cb1ced96752de615973c  
**Scope:** coordination/phoenix/ only; no subsystem or destination source changes.

## Executive disposition

**P0 BLOCKED / PRODUCTION NO-GO.** The current COE #31 release branch contains the approved unprivileged single-ID bubblewrap runner and bounded process timeouts, but the hosted runner denies user-namespace creation. A separate ULA defect remains. HARDWARE #317 focused source-extracted labs pass, while Full validation still fails at a QA-owned positive poll-signature fixture. HARDWARE #318 remains a divergent, untested child. COE #26 remains an unaccepted destination staging branch.

## 1. Exact repository and PR references

| Reference | Exact SHA / state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development | blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| PHX-MASTER PR #288 pre-audit HEAD | 598481bfc2eb91efd1f6cb1ced96752de615973c; open/draft; base main |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12; open/draft |
| COE RELEASE PR #31 | 390f2acc45969689caa00a4647d365b0122877ca; open/draft; base #26 |
| Experiments HARDWARE PR #317 | 7b42713376853337d622979df3a07d36ebc7b045; open/draft |
| Experiments HARDWARE child PR #318 | be371b03a36306a7691b411bf1b29da60b916646; open/draft; mergeable=false |

PR #288 had 61 changed paths before this audit; all 61 were under coordination/phoenix/. The ownership manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. No destination move is authorized.

## 2. COE #31 — source fixes present, sandbox substrate still blocked

Current source identities: packager 0763b1ea18ceff2fb9ccae212d5bb86a78119baf; sandbox runner 7bf7ec5b2512704aca52bedd8ccc7067786533af; packaging tests 18b13939b6d1e64477737c51f7b97acc1dc45169; workflow 2a865da751e00175bfd18687323899730659799b. The generated operator wrapper now routes through the runner. The runner has bounded build timeouts and process-group termination; the earlier missing-timeout finding is superseded at source level.

The UTC19 release owner reproduced a path-dependent overlay mode bug: a staging destination beneath a parent named usr/sbin caused ordinary generated UCI/profile files to receive mode 0755 instead of 0644. Test-first RED: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158122050. Source correction commit 15ca3499aefd9836acc592256309834d0e0747b1; final handover/PR HEAD 390f2acc45969689caa00a4647d365b0122877ca. Final shared/hardware run https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158649108 completed validation, ESP8266 and ESP32 jobs successfully; case-collision https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158649064 passed.

Mandatory sandbox run https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44158649032 failed at bubblewrap user-namespace setup: `bwrap: setting up uid map: Permission denied`. The suite ran 54 tests and reported 20 failures because the owner probe could not be created; sandbox-dependent symlink and real timeout integration paths were not reached. Do not reinterpret these as 20 independent product regressions or a sandbox pass. The infrastructure owner must provide an authorized disposable, ephemeral, no-secret runner with unprivileged user namespaces enabled. Do not add sudo, newuidmap/newgidmap, broad subordinate-ID grants or an unsandboxed Make fallback.

The runner still uses --share-net and read-only binds the host root. The host network is shared and host files remain readable: this is write confinement only, not network isolation or confidentiality. Do not expose secrets/customer data to untrusted build inputs.

## 3. ULA contract remains P0

The exact COE #31 packager blob still emits `fd00:db8:blaze::/48`; `blaze` is not a hexadecimal hextet. The EW1200G Pro profile blob 6e797cf9c9922209efe4c0da49c49fa1da16c11a has no networking.ula_prefix property, and the exact packaging tests have no ULA/IPv6 assertions. Preserve Architecture Contracts §6.9: installation/site-scoped RFC 4193 ULA /48, durable across reboot/upgrade/restore and shared by devices on the same LAN. No prefix is guessed or hardcoded as a global replacement.

Master executed Python stdlib ipaddress checks: 4/4 passed (invalid `fd00:db8:blaze::/48` rejected; valid ULA /48 accepted; /64 rejected for the /48 contract; non-ULA 2001:db8::/48 rejected). These are parser checks only, not UCI/netifd, ImageBuilder or router tests.

## 4. HARDWARE #317/#318 exact-head status

HARDWARE #317 source/test SHA 5f4aab0cf52854f550dae63c2f555558feed4130; final PR/handover HEAD 7b42713376853337d622979df3a07d36ebc7b045. Focused poll-drain run https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44159494324 passed 11/11 per ESP8266/ESP32 board with short-debounce and unsafe-deadline mutations rejected. Relay-output run https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44159494397 passed 48/48 per board with polarity and poll-inhibit mutations rejected. Full run https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44159479287 failed in the validation job at `Missing poll signature check`; all 14 target build jobs completed successfully, while production import/signing/update-bundle jobs were skipped.

The current firmware remains default-deny: no positive sigOk default and no active applyRemoteConfig call on either source sketch. The failing inherited QA assertion must be replaced with source-linked negative checks proving unauthenticated/unsigned poll cannot enable admission or mutate remote configuration. Do not restore positive poll admission to make Full green. PHX-QA owns the fixture correction.

HARDWARE #318 current PR metadata is head be371b03a36306a7691b411bf1b29da60b916646, base/merge-base 3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3. Compared with current #317 head 7b42713376853337d622979df3a07d36ebc7b045, GitHub reports DIVERGED: 49 commits ahead / 45 behind, mergeable=false; no current-head CI runs returned. Its PR description still carries stale head/base pins (7cd93a70 / 8bde0c26); live PR metadata is authoritative. Keep #317 and #318 separate until HARDWARE proposes stack direction and QA verifies the selected exact source/test SHA. No rebase, cherry-pick, force-push or merge.

## 5. COE #26 Hardware staging provenance — no move

| Item | Experiments source | COE #26 destination |
|---|---|---|
| ESP32 sketch | 6399b471460effe7817ec849b2f6a9ca271fbc57 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 |
| ESP8266 sketch | b0aba5fb9d18a6c3a51f04eed3a52c1e85074d7b | c8be98f72596681e36a3ad1f8939bf8046c96887 |
| Source controllers.sh | f7896647713d6bf8034ff48ed19b6383e4dedea0 | Pisowifi/tests/controllers.sh absent (404) |
| Destination Hardware test | — | f921c56cecc19cab1989507b9b4ade1f45dac54e |
| Destination Hardware README | — | 99af3e5b46cd8b6f35c6479b204683f60c55ebcb |

The destination sketches still default sigOk=true, actively call applyRemoteConfig, and expose quarantine clearing; Hardware/tests/test_firmware_hardening.sh expects a positive `|poll|` signature and `/quarantine/clear`, while Hardware/README.md still documents the clear route. Current #317 source is fail-closed and preserves quarantine evidence. The destination test is not an equivalent import of the current source test suite.

The source MIT license blob 1ee55b94183417be977ca287cd7391f9a6f7e721 is identical to COE Pisowifi/LICENSE, but no Hardware/LICENSE, Hardware/NOTICE.md, COE root LICENSE or root NOTICE.md was found. Sibling Pisowifi licensing does not establish Hardware license/NOTICE applicability. Resolve owner/legal provenance before any move.

COE #26 remains open/draft at b382d233ff06c8791b1028bed3c617cc7b670d12. Five PR-triggered workflows remain queued with zero jobs returned: 43096752609, 43096752632, 43096752800, 43096752563, 43096752557. No combined integration acceptance exists.

## 6. Role and CI reconciliation

| Role | Current exact PR head(s) | Exact evidence / status |
|---|---|---|
| PHX-CORE | #252 c82705f2de865c89ab733b10efa84f26f56a5cc4 | 42698139210 SUCCESS, scoped; separate CORE automation retains implementation |
| PHX-RENTAL | #289 68928774d0d7cf65adb26bc6b54199a3159d066c | 43653329235 and 43653329229 SUCCESS, scoped |
| PHX-PISONET | #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | 42462978704 SUCCESS, scoped; native COM acceptance unverified |
| PHX-HARDWARE | #314 556adc20ef0cfd355089aff3b979c0169af79bdd; #315 84fe6b790139d147f330f13a40b3ae3e89a7042d; #316 888e6941e3a7a81641682c23d937f97d8117d2ea; #317 7b42713376853337d622979df3a07d36ebc7b045; #318 be371b03a36306a7691b411bf1b29da60b916646 | #314 43782088731/43782088748 SUCCESS; #315 44054778537 SUCCESS / 44054778555 FAILURE; #316 43972511337 SUCCESS / 43972511250 FAILURE; #317 focused passes / Full validation fails; #318 no CI, diverged |
| PHX-QA | #290 5c29d15994cee1279058f1eca12f2a3180704292; #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 43633486963 SUCCESS, scoped; #292 no runs returned (UNKNOWN); QA owns stale poll fixture and independent #31 review |
| PHX-RELEASE | #291 2c4edff231d9b2819415086825530d80b8801307; COE #31 390f2acc45969689caa00a4647d365b0122877ca | #291 43744993487 SUCCESS, scoped; #31 shared/hardware 44158649108 and case 44158649064 SUCCESS; mandatory sandbox 44158649032 FAILURE at host userns setup |
| COE integration owner | #26 b382d233ff06c8791b1028bed3c617cc7b670d12; #28 b21b04617d38a177260258de2d56b24382822117; #29 d0830332dee8a1844a85606150681b41d91fe796; #30 4897348d94a0cf7884ecd53244bfcd59e7bf2fbc; #32 29b6fe08b10688182d981a66745f482758bd6630 | #26 five queued/no jobs; #28 43632393888 SUCCESS synthetic; #29 43653906676/43653906675 SUCCESS; #30 43653415598 SUCCESS synthetic with NSIS warning 6000; #32 43653540607 SUCCESS synthetic |

## 7. Validation performed by PHX-MASTER

- 23/23 bounded assertions passed against exact source blobs, destination blobs, manifest, compare result and CI job metadata.
- Python stdlib IPv6/ULA parser contract: 4/4 assertions passed.
- Full Master Python coordination suite: NOT RUN.
- Master PR-triggered CI: no runs returned for pre-audit #288 head.
- No hardware, physical, payment, signer, migration or release tests were executed.

## 8. Blockers and exact next actions

1. Infrastructure owner: authorize a disposable, ephemeral, no-secret runner with unprivileged user namespaces; then RELEASE reruns exact-head real bubblewrap/symlink/timeout regressions and QA independently reviews.
2. PHX-RELEASE + PHX-CORE: define and implement durable site-scoped RFC 4193 ULA provisioning, profile validation and negative tests; do not guess a prefix.
3. PHX-QA: replace the positive poll-signature fixture with source-linked default-deny tests and rerun Full on the exact #317 source/test SHA.
4. PHX-HARDWARE: propose #317/#318 stack direction; no Master rebase/cherry-pick/merge.
5. COE integration owner + PHX-HARDWARE + QA: reconcile exact firmware/test blobs, Hardware README, license/NOTICE and CI before any destination move.
6. Registry custodian: restore authorized private Drive access to canonical BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections. The current Library search did not surface that canonical file; no older snapshot was substituted.

**No source/destination file was copied, moved, overwritten or deleted. No subsystem branch was modified. PR #26/#31/#317/#318 remain draft. PRODUCTION NO-GO.**