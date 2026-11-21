# PHX-MASTER — pending-clear, Hardware stack and COE test-parity audit

**Checkpoint:** 2026-11-18 UTC00  
**Scope:** PHX-MASTER coordination, architecture evidence classification, cross-repository provenance and integration matrix only.  
**Disposition:** DRAFT / BLOCKED / PRODUCTION NO-GO.

## Exact refs read

| Ref | Exact HEAD |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development (blazepwifi-v0.5.3-development) | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| PHX-MASTER branch / PR #288 | f657a177e17b61e54dc507984c551cfc65a9f10a |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |
| COE RELEASE #31 | 7b6487a72c2f527457afca0dde61740bf5d65035 |
| HARDWARE #283 | e8c6619ba97aa7ba1152e4c78b786842f7fa9180 |
| HARDWARE #317 current PR head | fce915c1167fc43c6936f3594ae9efce376b711f |
| HARDWARE #317 source/test head | ddc7ed1f15865b629f78b87536dec8fb6f513353 |
| HARDWARE #318 | 696e28ed4cd53b9189b78095b38aee973d774683 |

The existing #288 branch is OPEN/DRAFT. No branch update, merge or release was present before this audit. The current PHX-MASTER branch head was used as the sole parent for this coordination update.

## 1. Architecture review — pending-clear preconditions

Master Architecture Contracts §2.3.1 requires a one-shot attempt marker bound to the exact pending event, fail-closed behavior for missing/ambiguous evidence, and removal of the pending journal before the attempt marker, with the marker removed last only after an authoritative receipt or separately durable quarantine disposition. §6.6 requires an event-bound authenticated receipt; HTTP status, root ok flags, response text, timeout or transport success are not financial authority.

At HARDWARE #317 source/test head ddc7ed1f (ESP32 blob 067c79405a6eb81a6c0b292b858191d3a131ed4f; ESP8266 blob 2f6dce596368d74f51aa6ab6a66b6dde875511c1), the current clearPending implementation:

1. Requires a matching durable /pending.attempt marker bound to the current RAM pulse count, nonce and target.
2. Requires exactly one of /pending.dat, /pending.new or /pending.bak.
3. Reads and validates that candidate and compares the complete pending record to the attempt marker.
4. Removes and verifies the pending candidate first.
5. Removes and verifies /pending.attempt last.
6. Latches journalRecoveryRequired and preserves remaining evidence on any failure.

This matches the Master deletion-precondition contract. It does **not** create disposition authority. The exact source's coinPostDispositionVerified function returns false for every response; the normal loop therefore keeps the recovery hold and denies automatic replay. The helper is not an approved route to clear a coin event.

### Exact source-extracted CI evidence

The current #317 quarantine workflow at ddc7ed1f ran exact ESP32 and ESP8266 source-extracted C++ helpers with fake LittleFS in [run 44209657736](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209657736), job 134484475383:

- pending-journal boot recovery: 16/16 per board;
- pending-clear preconditions: 17/17 per board;
- coin POST gate: 10/10 per board;
- poll-window drain: 11/11 per board;
- pulse capture after abort: 8/8 per board;
- quarantine readback: 36/36 per board;
- mutation checks rejected; SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_VERIFIED=0, FINANCIAL_PRODUCTION_AUTHORIZED=0.

The focused relay/poll-intake workflow [44209657629](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209657629) also succeeded. These are software simulations against extracted production helpers, not physical flash or power-cut evidence.

The current PR head fce915c has fresh exact-head focused runs [44209812693](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812693) and [44209812920](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812920), both SUCCESS. Its Full build [44209812745](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812745) is FAILURE: validation job 134485113755 fails at the QA-owned “Missing poll signature check” assertion; all 14 target jobs succeeded, while v0.4 simulations and production/sign/publish jobs were skipped. Do not label this Full GREEN.

## 2. QA test identity — static string presence is not protocol verification

HARDWARE #317's inherited QA test blob 41211b2c110ab409f6d9d1812ef12fda73b13211 requires the literal strings response_sig and |poll|. It fails against the current #317 source because that source deliberately keeps poll admission denied and does not contain the old candidate token. The failure is a stale QA fixture, not a reason to restore positive poll admission.

HARDWARE #283 current head e8c6619 has different firmware blobs (ESP32 d86d94568c0de9a5be6648e8d83c219a9cc58c62; ESP8266 710572a1aae661cfa7ba3936f2170f921200150e). Its test blobs are controllers.sh 0f73e9024b98cfe5c6cc131f70a58cf50375d0fe and v05_firmware_hardening_test.sh dc20a6ce1a1828c9cba9631fc67193840de5c224. The v05 test still greps for response_sig and |poll|. In the #283 sketch, the |poll| and response_sig strings occur in comments describing a rejected candidate; connectSta posts register then calls denyRemoteControl(), and the loop posts poll then calls denyRemoteControl(). Thus the static grep passes without proving any signature acceptance. This is not positive admission, but it is not a meaningful authorization test either.

#283's exact-head Full build [44203456152](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44203456152) succeeded with validation, 15/15 target jobs and software simulations; quarantine append/readback [44203456142](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44203456142) succeeded. However #283 modifies QA-owned tests/controllers.sh and tests/v05_firmware_hardening_test.sh. PHX-QA must review and own the replacement tests before any integration. The current green does not supersede #317's default-deny source or independently prove poll/receipt authorization.

**QA action:** replace static response_sig / |poll| presence checks with source-linked negative tests of acceptPollResponse and coinPostDispositionVerified, asserting intake remains disabled, target is cleared, outputs stay off and pending/attempt evidence is retained. Preserve positive acceptance vectors as blocked until CORE publishes the canonical producer/consumer and event-bound receipt contracts.

## 3. Hardware stack remains unresolved

Current exact compare results:

| Comparison | Git result | Decision |
|---|---|---|
| #283 e8c6619 vs #317 fce915 | DIVERGED; #283 15 ahead / 280 behind; merge base a87567291e80006f3f30cea81fc20e8b299b95e8 | Keep separate |
| #318 696e28 vs #317 fce915 | DIVERGED; #318 51 ahead / 71 behind; merge base 3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3 | Keep separate |
| #318 696e28 vs #283 e8c6619 | DIVERGED; #318 260 ahead / 15 behind; merge base a87567291e80006f3f30cea81fc20e8b299b95e8 | Keep separate |

#318 is nonmergeable and has no current-head CI. #283 and #317 have different ESP32/ESP8266 blobs. #317's current branch is stacked on #315; #283 is based on main. No rebase, cherry-pick, force-push or canonical stack selection is authorized by this audit.

Other current Hardware candidates: #314 556adc20 (full and focused CI success); #315 84fe6b79 (focused quarantine success, Full failure); #316 888e6941 (focused quarantine success, Full validation failure due the QA extractor not including acceptPollResponse). Keep role ownership intact.

## 4. COE #26 exact source/staging and license hold

COE #26 SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f and Pisowifi/MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 remain pinned to historical Experiments source 6d4c9b487af4d768c4d7627654d119417fcc6e00. The intake records 61 rootfs files, 47 byte-identical, 14 locally derived, zero unrecovered and two unchanged original tests. It does not establish import of current Hardware #283/#317/#318.

Exact firmware blob comparison:

| Artifact | #283 | #317 | #318 | COE #26 |
|---|---|---|---|---|
| ESP32 sketch | d86d9456... | 067c7940... | 7a24b1b6... | 3cc7ec54... |
| ESP8266 sketch | 710572a1... | 2f6dce59... | ebd1572c... | c8be98f7... |

All four columns are distinct source identities. Experiments source tests/controllers.sh is blob f7896647713d6bf8034ff48ed19b6383e4dedea0; COE #26 has no Pisowifi/tests/controllers.sh path. COE Hardware/tests/test_firmware_hardening.sh is a different test blob f921c56cecc19cab1989507b9b4ade1f45dac54e and still uses static response_sig / |poll| checks. It is not import-equivalent to the source controller suite.

License readback: Experiments BlazePwifi/LICENSE and COE Pisowifi/LICENSE are both blob 1ee55b94183417be977ca287cd7391f9a6f7e721. The #26 tree has no Hardware-specific LICENSE, root LICENSE/NOTICE, or Pisowifi/tests/controllers.sh. Resolve Hardware attribution/NOTICE applicability before any move.

OWNERSHIP_ROUTES.json remains unchanged at blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. No destination file was moved, copied, overwritten or deleted.

## 5. RELEASE / COE current-head blockers

COE RELEASE #31 current head 7b6487a72c2f527457afca0dde61740bf5d65035: shared validation [44206767345](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206767345) and case guard [44206767254](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206767254) succeeded. Mandatory sandbox [44206767227](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44206767227) failed closed at host preflight: bwrap could not set up the UID map (Permission denied), exit 125. Infrastructure must provide an authorized disposable no-secret namespace-capable runner; no privileged or unsandboxed fallback.

The exact current #31 packager blob b952f9acc16f3088a5ab29eb4d3fa143101c7c03 still emits invalid ULA fd00:db8:blaze::/48. The profile/test tree still lacks the required site-scoped RFC 4193 input and assertions. MASTER/CORE must approve the provisioning contract; RELEASE owns implementation.

COE #26 remains OPEN/DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12 with five PR-triggered workflows queued and zero jobs. No combined integration acceptance.

## 6. Current non-Hardware role evidence

- CORE #252 c82705f2: scoped build 42698139210 SUCCESS; separate hourly CORE automation retains source ownership.
- RENTAL #289 68928774: runs 43653329235 and 43653329229 SUCCESS.
- PISONET #255 d01fd164: run 42462978704 SUCCESS; native COM acceptance UNKNOWN.
- QA #290 5c29d159: run 43633486963 SUCCESS; #292 75a3f66d has no current-head run.
- RELEASE #291 docs head a74b8b94: source/test head 4d36160c run 44199068618 SUCCESS; docs-head run 44199987756 SUCCESS; publisher/signing skipped.
- COE #28 b21b0461, #29 d0830332, #30 4897348d and #32 29b6fe08 retain scoped successful runs 43632393888, 43653906675/676, 43653415598 and 43653540607 respectively.

These are scoped CI results, not integrated or production acceptance.

## 7. Registry and execution limits

The canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections did not appear in the accessible Library search; no Google Drive connector action was exposed for this run. Older snapshots/checkpoints were not substituted. No private registry content or identifiers were copied into GitHub.

The full Master Python suite was not executed. A direct Git clone attempt failed because this execution container could not resolve github.com. No Master PR-triggered CI run was returned for the current #288 head. Source/tree inspection and remote role CI are not represented as local Master test execution.

## Owner next actions

1. PHX-QA: review #283's QA-owned test changes; replace static poll-token checks with source-linked default-deny tests; rerun the selected #317/#283 exact source/test head.
2. PHX-HARDWARE: retain #283/#317/#318 as separate drafts until QA and owner stack direction are recorded; no automatic branch composition.
3. PHX-CORE: publish the canonical authenticated poll and event-bound receipt/disposition contracts; no positive coin admission until independent vectors and review.
4. PHX-RELEASE / infrastructure: fix the site-scoped ULA contract and provide an authorized no-secret user-namespace runner.
5. COE integration owner: refresh per-file source/test/license provenance only after owner stack selection and QA approval.
6. Registry custodian: restore read-only access to the canonical private Drive v11 registry and newer corrections.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
