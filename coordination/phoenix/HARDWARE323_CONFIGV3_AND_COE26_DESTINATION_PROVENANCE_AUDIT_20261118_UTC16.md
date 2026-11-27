# PHX-MASTER UTC16 — ConfigV3 two-board boot-gate and COE #26 staging provenance audit

**As of:** 2026-11-18T16:41:00Z  
**Role:** PHX-MASTER — coordination, architecture contracts, cross-repository provenance and integration gates only  
**Disposition:** REVIEW EVIDENCE UPDATED / MIGRATION BLOCKED / PRODUCTION NO-GO

## 1. Live coordination snapshot

- Experiments default branch: **main**, SHA **f4e8a891aed8af86d5fd315d28750a0ac3a7372b**.
- Current development branch: **blazepwifi-v0.6.0-audit-foundation**, SHA **2fbd2475e9f54878c316fa7cea2f228386b0e859**. The older aad3aade snapshot in prior notes is not the current development-branch head.
- Master branch before this update: **phoenix/master-coordination**, SHA **18cd5064f0b0682bb50b8c53b145cb0fd356ea0d**.
- PR #288: OPEN / DRAFT, base main f4e8a891..., head 18cd5064..., 82 changed paths before this update; all are under coordination/phoenix/.
- COE main: **a6513ab4412b4c014eee2863e45cbe32d06cb243**.
- COE integration PR #26: OPEN / DRAFT at **b382d233ff06c8791b1028bed3c617cc7b670d12**, 205 changed paths, five workflows QUEUED and zero jobs.
- Cleanup-first issue #266 remains OPEN. No broad cleanup, source migration or owner-scope change was performed.
- OWNERSHIP_ROUTES.json remains blob **e4db324315a1b3543fec17a148fbf960170fcb29**, DRAFT_REVIEW_ONLY, PHX-MASTER destination null.

## 2. Hardware #323 — current exact-head evidence

Current PR #323 head is **988904e8bcd058b62a9fac4aa6319a9b7c5b2470**, child of #322 at **50d93e0de3d682550b6f02fb43484e76ad9c7e08**. The latest source/test tree is **359bd8f685a2a464f4a77b84501fcf4055944d5c**; later commits 7eceb441, 766a861f and 988904e8 are documentation-only.

| Component | Exact blob |
|---|---|
| ESP8266 firmware | 312884c534637a3179180b432b9e345b36dc6af9 |
| ESP8266 boot-polarity lab | db0ac51115638d567d73e0dbfdff1129ef5efd3d |
| ESP32 firmware | 7ebf0d3489c87abb52ca980f862cd6314a20af6e |
| ESP32 boot-polarity lab | 17f45e30402c1481983d3710336f7252f484ac6b |
| ESP8266 dual-store/poll-fault lab | 25f5e8bd1a344d69acc0505324156f66a1abffa4 |
| Source controller test entrypoint | f7896647713d6bf8034ff48ed19b6383e4dedea0 |
| Legacy positive poll-signature fixture | 41211b2c110ab409f6d9d1812ef12fda73b13211 |

The earlier UTC15 boot-lab discrepancy is now resolved in the Hardware-owned candidate. Focused logs record ESP8266_COMMIT_FAILURE_TRACE=PASS, UNKNOWN_EEPROM_SCHEMA_PRESERVED=PASS, ESP8266_BOOT_POLARITY_CONFIG_V3=PASS, MISSING_CORRUPT_COMMIT_READBACK_FAIL_CLOSED=PASS, UNKNOWN_POLARITY_OUTPUTS_REMAIN_INPUT=PASS and ACTIVE_HIGH_AND_ACTIVE_LOW_OFF_PRELOAD=PASS. The ESP32 boot lab also passes local marker/readback, unknown/legacy-polarity INPUT, active-high/active-low OFF preload and remote-polarity-denial checks.

| Run | Result | Meaning |
|---|---|---|
| [44347847077](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347847077) | SUCCESS | Quarantine/readback focused lab |
| [44347847191](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347847191) | SUCCESS | ESP8266 and ESP32 source-extracted boot/output-polarity labs |
| [44347846832](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347846832) | FAILURE | Full validation stops at QA-owned Missing poll signature check; 13/13 firmware target jobs and Android completed successfully, downstream release/simulation/signing/publishing gates did not pass |

The focused labs report SIMULATED_ONLY=1, physical relay/polarity acceptance 0, and physical power-cut acceptance 0. These are source-extracted host regressions, not board-level acceptance.

Both current firmware paths retain deny-only poll-response admission and coin-POST disposition. The Full failure is not permission to add a fake signature or enable positive poll/coin admission. QA must replace the positive response_sig / |poll| string-presence expectation with negative default-deny behavior tests; CORE owns the canonical producer/consumer contract and golden vectors.

## 3. COE #26 destination staging — exact provenance comparison

No move or copy is proposed. The existing manifest is review-only and #26 remains a draft destination candidate.

| Component | Current source candidate #323 | COE #26 destination |
|---|---|---|
| ESP32 sketch | 7ebf0d3489c87abb52ca980f862cd6314a20af6e | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 |
| ESP8266 sketch | 312884c534637a3179180b432b9e345b36dc6af9 | c8be98f72596681e36a3ad1f8939bf8046c96887 |

The source candidate's ESP32/ESP8266 boot-polarity labs and ESP8266 dual-store lab are absent from the destination tree. COE #26 instead has generic Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e. It still asserts response_sig and |poll| in both firmware sketches. Its .github/workflows/hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 runs that generic test and shared/tools validation; it does not invoke the new two-board boot-polarity labs or dual-store fault lab. This is not test-identity equivalence.

### Poll producer/consumer drift

- Source main producer cgi-bin/vendo: blob 2e3a1430d08cc6606429a042df3b5848f53c7267.
- Source development producer cgi-bin/vendo: blob db58041c0575ad0a1101d99cb85403e03c8dcb22.
- COE #26 destination producer cgi-bin/vendo: blob 0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e.

The source main/development producers emit response_sig for member snapshot/auth/mutation routes but do not define vendo_poll_sig or a signed poll response. The COE destination adds vendo_poll_sig and emits a poll response_sig. This is a real producer/consumer contract divergence. Do not silently accept the destination's positive poll contract or alter the current firmware's deny-only behavior; CORE, HARDWARE and QA must agree on an authenticated contract and exact-SHA negative/positive vectors before integration.

### License and import completeness

- Source project MIT license: experiment/openwrt/BlazePwifi/LICENSE blob 1ee55b94183417be977ca287cd7391f9a6f7e721.
- COE #26 Pisowifi/LICENSE is byte-identical at the same blob.
- No Hardware/LICENSE, Hardware/NOTICE, COE root LICENSE or COE root NOTICE.md exists at the inspected candidate ref. The Pisowifi-scoped license alone does not establish the intended license/NOTICE scope for the separate Hardware subtree.
- The 205-path #26 import does not contain the current #323 boot-polarity/dual-store labs. Exact source/destination blobs, license scope, complete import inventory, test identities and destination CI remain unresolved.

## 4. Other live role and CI reconciliation

| Owner / candidate | Current exact head | Exact CI observation |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped; CORE source ownership remains with the separate continuation |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS, scoped |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM acceptance unverified |
| HARDWARE #317 | fce915c1167fc43c6936f3594ae9efce376b711f | Focused [44209812693](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812693) / [44209812920](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812920) SUCCESS; Full [44209812745](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812745) FAILURE at legacy poll fixture |
| HARDWARE #318 | de428b7a3e15854804f09935a36a6afeb67d8cbe | No current PR-triggered run returned |
| HARDWARE #321 / #322 / #324 / #325 | 4c54d629... / 50d93e0... / 8e7f0220... / f66b45ec... | Focused runs passed at their own SHAs; each Full run failed at the inherited controller protocol fixture. They remain separate branches, not a composed stack. |
| QA #290 / #292 | 5c29d159... / 75a3f66d... | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS; #292 no current-head run returned |
| RELEASE #291 | ed3565395bd70c4de696e49a84f0bb454efebc8b | [44328674893](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44328674893) SUCCESS for handover/build; privileged publisher skipped |
| COE RELEASE #35 | b398906e23f95400ed39d08507e8a3ea1966dbff | Shared [44345859504](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345859504) and case [44345859677](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345859677) SUCCESS; mandatory sandbox [44345859641](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345859641) FAILURE at bubblewrap availability after 13/13 host preflight tests; packaging steps skipped |
| COE CORE candidate #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) shell suite and [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) case guard SUCCESS; separate CORE-owned candidate |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED, zero jobs; no integrated acceptance |

All scoped results are exact-SHA evidence only; none is combined release acceptance.

## 5. Governance, private registry and test limits

- Live branch objects report protected=false for Experiments main f4e8a891..., development 2fbd2475..., Master 18cd5064..., and COE main a6513ab4.... Both repositories' rulesets endpoints returned empty arrays. Dedicated branch-protection endpoints returned 403, so repository administrators must configure and independently read back protection/required checks.
- Library search surfaced older registry snapshots v3–v7 and production checkpoint records, but not the canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json or newer corrections. No Google Drive connector is exposed in this run. No older snapshot was substituted; no private registry content or IDs are published.
- Experiments root AGENTS.md was read at blob d8777e3b58efc41caa5aa3c969c932aee9103d5f; it requires the private registry/ledger before Drive writes. COE root AGENTS.md returned 404.
- Source/tree/blob and CI-log inspection completed. The full Master Python suite was NOT RUN; no Master exact-head CI run was returned. The 13/13 target builds and focused labs above are actual GitHub Actions executions, not local Master tests.
- The current Master automation executed this activation. CORE was read-only; no competing CORE source work was started.

## 6. Required next owner actions

1. **PHX-QA:** independently review both boot-polarity paths at source/test tree 359bd8f...; replace the positive poll-signature string fixture with negative deny-behavior tests on the exact source and COE destination candidates.
2. **PHX-CORE:** publish the canonical poll producer/consumer authentication envelope and golden vectors before any positive poll path is enabled.
3. **PHX-HARDWARE:** refresh #323 description/checkpoint to current head 988904e...; preserve both-board unknown-polarity INPUT gating and deny-only poll/coin behavior.
4. **COE integration owner:** reconcile #26 firmware blobs, missing labs, producer contract, license/NOTICE scope and import inventory; do not stage/move until exact-source and destination CI evidence is complete.
5. **PHX-RELEASE / infrastructure:** provide an authorized bubblewrap-capable sandbox runner; do not install privileged tools or bypass sandboxing.
6. **Repository administrator:** configure and independently verify branch protections and required status checks.
7. **Registry custodian:** provide authorized access to private Drive v11 and newer corrections.

## 7. Production gate

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, migration, release, signing, secret provisioning, flash, physical test or real-payment operation occurred.
