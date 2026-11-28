# Hardware staging parity refresh and duplicate candidate audit — 2026-11-17 UTC08

**Role:** PHX-MASTER · **Task:** #172 / #266 · **Disposition:** BLOCKED for migration; PRODUCTION NO-GO.

## Scope and exact refs

This is a read-only source/destination audit plus Master-owned coordination documentation. No firmware, test-owner, CORE, or COE runtime file was changed.

| Ref | Exact HEAD |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Experiments v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master PR #288 before this audit | 349c5e24c3083dc78ffe9fe96e495d66285b7f2d |
| Current HARDWARE source PR #315 | cc0743009f44baeda0ea12d84eb6199a8a6916c7 |
| Separate HARDWARE PR #316 | 888e6941e3a7a81641682c23d937f97d8117d2ea |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |
| COE Hardware & Shared PR #27 | 009f70cc2c2775039a5fb072c9d4fdedee76cfc7 |

The Master branch is based on Experiments main. The source and destination PR heads above are separate, unmerged candidates; no path is assumed compatible from a matching filename.

## Current owner-source versus destination blobs

Exact recursive Git trees were read at #315, #26 and #27; none was truncated.

| Firmware | #315 source blob | #26 / #27 destination blob | Mode |
|---|---|---|---|
| ESP32 BlazePwifiVendo32.ino | 7ad3edddf8a643a14c40d4d21f8b69d454dc256d | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | 100644 / 100644 |
| ESP8266 BlazePwifiVendo.ino | d73fea6866ea4836245de6b786d7e1a9c0cd2bbf | c8be98f72596681e36a3ad1f8939bf8046c96887 | 100644 / 100644 |

The current #315 source files are 42,490 bytes / 1,086 lines (ESP32) and 42,746 bytes / 1,153 lines (ESP8266). The destination files are 18,505 bytes / 410 lines and 18,394 bytes / 489 lines respectively. Neither pair is byte-identical. PR #26 and PR #27 contain the same two destination firmware blob IDs, so #27 is not a newer hardware-source import.

## Behavior and security parity

Both #315 source sketches currently show:
- Exactly one applyRemoteConfig occurrence (the dormant definition only), with no response-driven register/poll call site.
- Zero sigOk=true defaults.
- pendingPostAttempted, markPendingPostAttempt, coinPostDispositionVerified and acceptPollResponse helpers.
- The /quarantine/clear POST handler returns HTTP 403 and does not delete /quarantine.log.

Both #26/#27 destination sketches currently show:
- Three applyRemoteConfig occurrences and two sigOk=true defaults per board.
- No pendingPostAttempted, markPendingPostAttempt, coinPostDispositionVerified or acceptPollResponse helper.
- The /quarantine/clear POST handler removes /quarantine.log and returns HTTP 200.

These are source observations at the exact refs above, not claims about an attack or deployed device. The destination retains the older remote-configuration and destructive-clear behavior while omitting current one-shot POST/reconciliation protections.

## Test identity and import completeness

The #315 source tree includes board-local source-extracted labs:
- ESP32: coin_post_gate_lab.py, journal_mount_failclosed_lab.py, pending_attempt_marker_lab.py, pending_journal_recovery_lab.py, pending_write_readback_lab.py, quarantine_readback_lab.py.
- ESP8266: poll_response_failclosed_lab.py, poll_response_keyless_authority_red.py, register_config_failclosed_lab.py.

The COE Hardware test tree contains only Hardware/tests/test_firmware_hardening.sh (103 lines, mode 100755). It is a shell/static hardening check; the source labs above are not imported under the same identities. The source labs use host/fake-filesystem extraction and explicitly do not prove physical flash durability or real coin acceptance.

## License and notice provenance

The source project license is experiment/openwrt/BlazePwifi/LICENSE, blob 1ee55b94183417be977ca287cd7391f9a6f7e721 (MIT text). COE Pisowifi/LICENSE has that same blob. No Hardware-local LICENSE or NOTICE and no destination root LICENSE were present in the exact #26/#27 trees. This does not establish a legal violation; the destination license scope for Hardware remains unresolved and needs the source owner/custodian's explicit mapping.

## Exact-head CI

| Candidate | Run(s) | Result |
|---|---|---|
| Experiments #315 focused quarantine/source lab | [44041818004](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44041818004) | SUCCESS; job 133897942170 |
| Experiments #315 full validation/build | [44041818133](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44041818133) | FAILURE; validation job 133898063910 |
| Experiments #316 focused | [43972511337](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511337) | SUCCESS |
| Experiments #316 full | [43972511250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511250) | FAILURE |
| COE #26 candidate | 43096752609, 43096752632, 43096752800, 43096752563, 43096752557 | All QUEUED at observation |
| COE #27 Hardware & Shared | [43079646264](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646264), [43079646393](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646393) | SUCCESS on the stale #27 candidate; does not validate #315 parity |

The #315 full-validation log shows the QA-owned poll extractor omits pendingPostAttempted, acceptPollResponse(), markPendingPostAttempt(), coinPostDispositionVerified() and pollJsonTopLevelTrue(). Both ESP board compile jobs and returned appliance target-build jobs passed, but the overall workflow failed and release/sign/publish/candidate-gate jobs were skipped.

Other current role evidence: CORE #252 c82705f2… run 42698139210 SUCCESS; RENTAL #289 68928774… runs 43653329235 and 43653329229 SUCCESS; PISONET #255 d01fd164… run 42462978704 SUCCESS; QA #292 75a3f66d… has no PR-triggered runs returned; RELEASE #291 2c4edff2… run 43744993487 SUCCESS. COE child PRs #29, #30, #28, #32 and #31 have scoped successes at their own exact heads; none clears the combined #26 candidate.

## Migration decision and owner actions

- Keep COE #26 and #27 draft. Do not copy, overwrite, relocate, merge or promote the current destination firmware.
- PHX-QA: update the canonical extractor for the five missing current #315 dependencies and independently rerun full validation at exact #315 HEAD cc0743009f44baeda0ea12d84eb6199a8a6916c7.
- PHX-HARDWARE: retain source ownership and reconcile its separate #315/#316 stacks; Master does not combine or edit them.
- COE integration owner: choose one destination staging route, import and pin the current owner-approved firmware and matching tests, and record per-file source/destination blobs, modes, dependencies and license scope before review.
- Registry custodian: restore authorized access to the exact private Drive registry and newer corrections. No older Library snapshot is substituted.

## Verification limits

Fourteen source-readback assertions passed against the exact fetched firmware/license/test blobs. These are bounded static assertions, not a unit suite, GitHub CI, physical hardware test or migration acceptance. Master Python suite was not executed in this run. The private v11 Drive registry was not available through the exposed connector surface; no private registry contents or identifiers are included here.

No Codex, merge, release, signing, secret provisioning, firmware flash, physical test, real payment, financial migration or production operation occurred. **PRODUCTION NO-GO remains mandatory.**
