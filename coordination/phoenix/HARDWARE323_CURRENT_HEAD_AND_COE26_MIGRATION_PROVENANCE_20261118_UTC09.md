# HARDWARE #323 current-head and COE #26 migration-provenance audit — 2026-11-18 UTC09

**Role:** PHX-MASTER  
**Task:** #172 — cross-repository source/test/license/CI reconciliation  
**Disposition:** BLOCKED / DRAFT REVIEW ONLY / PRODUCTION NO-GO  
**Scope:** Master coordination, architecture contracts and migration provenance. No subsystem source was changed.

## Executive finding

The current Hardware #323 child candidate contains a newer, source-extracted dual-store poll-fault lab and a hardened lexical extractor. COE integration PR #26 does not contain that lab or invoke its workflow. The two firmware sketches at the mapped destination are not byte-identical to the current source. The destination's generic QA fixture still asserts positive response_sig and |poll| strings, while the current source intentionally denies poll admission. This is an incomplete and behaviorally divergent staging candidate, not a migration.

**Decision: no copy, move, overwrite, rename, rebase, cherry-pick, merge or route change.** Keep #323 and #26 separate drafts. The ownership manifest remains unchanged and PHX-MASTER's destination remains null.

## Exact refs

| Repository / candidate | Exact ref | Meaning |
|---|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b | Current default branch |
| Experiments development | aad3aade72c1156eecba1fed30907c6d0283b2c5 | blazepwifi-v0.5.3-development; not promoted |
| PHX-MASTER before this audit | 0f53e469b430f5fb8707623acf1dfd5f22331ce0 | Parent of this coordination-only commit |
| HARDWARE #323 branch head | 1761bf38d01c44f3bfd87acc6c7f03d97d7e1d17 | Current docs/handover head |
| HARDWARE #323 source/test SHA | d37d5da9bdd8e3be08f6344f4a2520c29c2d0abb | Exact code/test head; docs-only successor follows it |
| HARDWARE parent #322 | 50d93e0de3d682550b6f02fb43484e76ad9c7e08 | Parent candidate |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | Destination default branch |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Current destination draft |
| Ownership manifest | e4db324315a1b3543fec17a148fbf960170fcb29 | Unchanged, DRAFT_REVIEW_ONLY, PHX-MASTER target null |

The #323 source/test branch is phoenix/hardware-poll-fault-dual-store-20261118; its current branch head is the docs/handover successor 1761bf38. Do not confuse the source/test SHA d37d5da9 with the current branch head.

## Per-file staging evidence

The source #323 PR changes eight paths:

1. .github/workflows/phx-hardware-quarantine-byte-readback.yml
2. experiment/openwrt/BlazePwifi/docs/handover/2026-11-18-hw-poll-fault-dual-store.md
3. experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino
4. experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/journal_mount_failclosed_lab.py
5. experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino
6. experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/coin_pulse_capture_lab.py
7. experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab.py
8. experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py

| Source item at #323 source/test SHA | Source blob | COE #26 mapped target | Destination evidence |
|---|---|---|---|
| ESP32 sketch | bd74b11c1496b0943404ff387ee72bb45d4743e5 | Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino | Blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422; different |
| ESP8266 sketch | 8e79b9eb8856e67d966f4c6385f89fccdc8be7fc | Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino | Blob c8be98f72596681e36a3ad1f8939bf8046c96887; different |
| Dual-store lab | 25f5e8bd1a344d69acc0505324156f66a1abffa4 | Hardware/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab.py | Not present at #26 (exact path read returned 404) |
| Hardware workflow | 2358e4ab940b9879e961046180f01fc3d5356709 | COE .github/workflows/hardware-ci.yml | Blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793; different workflow |
| Source root MIT license | 1ee55b94183417be977ca287cd7391f9a6f7e721 | COE Pisowifi/LICENSE | Same blob; this proves the sibling Pisowifi license only |
| Source root NOTICE.md | f6d92cd21465312be5993631fe26977219be0fb9 | COE root / Hardware NOTICE | No matching root or Hardware NOTICE in the #26 tree |

The other source lab/handover paths are also absent from the #26 Hardware tree: journal_mount_failclosed_lab.py, coin_pulse_capture_lab.py, poll_loop_blocking_inhibit_lab.py, and the source handover has no explicit route. The source workflow is a hardware-owned exact-source lab workflow; the COE workflow is a separate reimplementation and does not invoke the missing source dual-store lab. The target has only the two older sketch blobs plus a generic shell fixture and README for this Hardware path.

### Test identity and protocol mismatch

COE #26 Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e asserts response_sig, |register| and |poll| by grep and runs a Python SHA-256 concatenation example. It does not run the source #323 dual-store lab or test the current deny-only poll contract.

COE #26 Hardware/README.md blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb labels key | action | id | nonce | ... | key as HMAC/SHA256. That concatenated SHA-256 expression is not standard HMAC. The current Experiments source intentionally keeps acceptPollResponse() and coin disposition hard-deny; the inherited positive grep assertion fails at the exact current #323 Full workflow. Do not add synthetic strings or enable positive admission to satisfy it.

### License / NOTICE gate

The source MIT license blob equals COE Pisowifi/LICENSE, but the COE tree has no root or Hardware-specific LICENSE/NOTICE. A sibling Pisowifi license match does not establish Hardware subtree applicability. The source root NOTICE is not present in the destination tree. Obtain explicit repository/license-custodian review before proposing any Hardware staging. No license conclusion is inferred.

## Exact CI evidence

### Experiments Hardware #323

- Source/test SHA d37d5da9: quarantine / dual-store run [44278751521](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278751521) SUCCESS; relay/output run [44278751557](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278751557) SUCCESS.
- Current branch/docs head 1761bf38: quarantine [44278980129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980129) SUCCESS; relay/output [44278980263](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980263) SUCCESS.
- Current-head Full build [44278980291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980291) FAILURE. Validation job 134714480245 fails in Controller protocol parity with exact log Missing poll signature check from tests/controllers.sh. All 13 returned firmware-target jobs and Android completed SUCCESS; downstream simulations, update bundle, candidate gate, signing and publishing were skipped.
- These are CI host labs / target builds, not physical relay, coin acceptor, flash durability, 150 power-cut or 30-device soak acceptance.

### COE destination

- Integration #26 remains OPEN/DRAFT at b382d233; five workflows are QUEUED (run IDs 43096752609, 43096752632, 43096752800, 43096752563, 43096752557) and zero jobs are returned. No combined integration acceptance.
- COE Release #35 is a separate RELEASE-owned child: branch head f751c542bfc82602554c6d0900504080aedc99fe, source/test SHA 233a9adde1f51e73ff5b228d59e058900430d73c. Shared/board [44275990852](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44275990852) and case-collision [44275990853](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44275990853) PASS. Mandatory sandbox [44275990821](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44275990821) FAILS CLOSED: 9/9 host preflight tests and unprivileged identity pass, but bubblewrap UID-map setup returns Permission denied; mandatory sandbox packaging regressions are skipped. No unsandboxed fallback.

## Release/ownership correction

The PHX-RELEASE UTC09 checkpoint was independently rechecked for experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md:

| Ref | Blob | Bytes / lines |
|---|---|---|
| #242 base 6d4c9b487af4d768c4d7627654d119417fcc6e00 | c035869680732ddcce3a960d456858387bf69fb2 | 0 bytes / 0 lines |
| #242 head 734b89d9e7792247e8376335c3f3685500ab3f89 | dc0c433cba481b546d92866ce198b913004ab56f | 0 bytes / 0 lines |
| #291 current head bf96680ab1d0040da8b70641c7dd3b1ca21ccea4 | 25ea8904b85a5ede76f971d127081b9ca4f021c6 | 45,738 bytes / 198 lines |

Therefore the earlier assistant summary's claimed 3,360-to-188-line deletion is unsupported by these exact refs and must not be repeated as a verified deletion or used to trigger a restoration. No release-owned file was changed by Master.

## Current role evidence (exact branch refs)

| Role | Current owner branch / PR | Current CI observation |
|---|---|---|
| PHX-CORE | #252 c82705f2de865c89ab733b10efa84f26f56a5cc4 | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped; separate CORE automation retains implementation ownership |
| PHX-RENTAL | #289 68928774d0d7cf65adb26bc6b54199a3159d066c | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS, scoped |
| PHX-PISONET | #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM acceptance unverified |
| PHX-HARDWARE | #323 branch 1761bf38..., source/test d37d5da9...; #317 fce915c1...; #318 696e28ed... | #323 focused PASS / Full FAILURE; #317 focused PASS / Full FAILURE; #318 no current-head runs and mergeable=false |
| PHX-QA | #290 5c29d15994cee1279058f1eca12f2a3180704292; #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, scoped; #292 no current-head runs |
| PHX-RELEASE | #291 bf96680ab1d0040da8b70641c7dd3b1ca21ccea4; COE #35 f751c542... | #291 [44270351439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44270351439) SUCCESS, publisher skipped; #35 sandbox host-blocked |
| COE integration owner | #26 b382d233ff06c8791b1028bed3c617cc7b670d12 | Five queued workflows / zero jobs; no combined acceptance |

## Required next actions

1. PHX-HARDWARE: keep #323 draft-only; refresh the handover/PR description to exact current branch head 1761bf38 and source/test SHA d37d5da9; preserve deny-only behavior.
2. PHX-QA: replace the positive poll-signature grep with source-linked negative deny tests at exact current #323 source/test SHA. Do not weaken firmware.
3. PHX-CORE: publish the versioned response schema, cryptographic construction, key/version lifecycle, freshness/nonce/target binding and shared golden vectors before any positive poll path.
4. COE integration owner + license custodian: create a per-file source/destination map for all eight #323 paths, test invocation identities, root/Hardware license/NOTICE applicability and exact-head CI. No route or copy permission until independently reviewed.
5. PHX-RELEASE / infrastructure owner: provide an authorized disposable no-secret runner with unprivileged user namespaces; keep mandatory sandbox fail-closed.
6. Registry custodian: restore authorized access to the canonical private Drive v11 registry and newer corrections. The exposed Library returned only an older November 9 checkpoint; it is not a substitute.

## Limits and release gate

The canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections remain unavailable through the exposed Library/connector surface. No older snapshot was substituted; no private registry content or identifiers were published. The AGENTS-linked cloud artifact policy/storage handover also could not be retrieved through the current GitHub connector. Master Python suite / full Master CI were not run at the pre-change head; no Master PR-triggered run was returned.

**PRODUCTION NO-GO:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
