# Remote-configuration source/staging parity audit — 2026-11-17 UTC04

**Role:** PHX-MASTER  
**Task:** #172 / #266 / #288 / COE #26 / HARDWARE #315  
**Disposition:** BLOCKED — PRODUCTION NO-GO  
**Scope:** read-only comparison of the current HARDWARE-owned source PR and the existing COE integration candidate. No firmware, COE integration, QA, CORE, or RELEASE source was changed.

## Exact repository refs

| Ref | Exact SHA |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development, blazepwifi-v0.5.3-development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master branch / PR #288 | fc9ba1391908f8d49d8f9e9c578e43b49e21417f |
| HARDWARE PR #315 | 75dc5f0b888f16e2c85e4321f62df4685639ad33 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 remains open and draft. The routing manifest remains DRAFT_REVIEW_ONLY; PHX-MASTER is coordination-only and has no runtime migration target.

## 1. Owner source correction is present on HARDWARE #315

At exact source head 75dc5f0b888f16e2c85e4321f62df4685639ad33:

| Source firmware | Blob SHA | Lines | applyRemoteConfig occurrences |
|---|---|---:|---:|
| ESP8266 | f59e624ae2da04bddc70ddc2809bf6d8ff486aac | 1001 | 1 (dormant definition only) |
| ESP32 | 38a2d239eed6af876d421f9f908bbb62b3ae27e1 | 931 | 1 (dormant definition only) |

Both current connectSta() implementations verify the provisioned-key register tuple when a key and response signature are present. The result is only used to report an unauthenticated register response; the response is not passed to applyRemoteConfig(). Both sketches retain the function definition for now, but the exact source contains no applyRemoteConfig(r) call sites.

The owner-owned register-config lab is present at:
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/register_config_failclosed_lab.py
- Blob SHA ea413137ab18e153ac4ee1625c28f16ce35101ab

The focused exact-head CI run [44013351048](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44013351048), job [133805326507](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44013351048/job/133805326507), completed SUCCESS. Its log reports register-config denial 7/7 for each board, poll/config 11/11 per board, strict root JSON 13/13 per board, debounce 8/8, poll-window 8/8, quarantine 34/34, mount/output 14/14, boot recovery 32/32, pending-clear 22/22, write/readback 44/44, and coin POST gate 18/18. These are source-extracted host/fake-filesystem simulations, not physical hardware acceptance.

The full exact-head run [44013351035](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44013351035) completed FAILURE in validation job [133805413831](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44013351035/job/133805413831). Its raw log confirms the QA-owned poll-intake extractor omitted acceptPollResponse(), producing undeclared-function errors for ESP8266 and ESP32. Both board compilation jobs and the returned target image jobs succeeded; production signing/import/publish and candidate simulation jobs were skipped. No overall full-build success is claimed.

## 2. COE PR #26 still contains the older unsafe remote-config path

At exact destination candidate b382d233ff06c8791b1028bed3c617cc7b670d12:

| Destination firmware | Blob SHA | Lines | applyRemoteConfig occurrences | sigOk=true defaults |
|---|---|---:|---:|---:|
| ESP8266 | c8be98f72596681e36a3ad1f8939bf8046c96887 | 489 | 3 (definition + 2 call sites) | 2 |
| ESP32 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | 410 | 3 (definition + 2 call sites) | 2 |

The destination calls applyRemoteConfig(r) from both register and poll response paths. In each path sigOk starts true and signature verification is conditional on a nonempty key. Therefore a positive ok:true response with an empty key can reach the configuration mutator. A provisioned-key register signature still authenticates only the register tuple, not the returned configuration object. This is a source-level trust-boundary defect in the staged candidate, not a claim that a live attack or physical actuation occurred.

The destination test file Hardware/tests/test_firmware_hardening.sh (blob f921c56cecc19cab1989507b9b4ade1f45dac54e) checks that response_sig, register and poll signature strings exist, but does not assert empty-key denial or that applyRemoteConfig has no response call sites. The current HARDWARE #315 register-config lab is not part of COE #26's candidate evidence.

The destination Hardware/README.md (blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb) describes the construction as HMAC/SHA256. The inspected firmware uses a keyed SHA-256 concatenation via hexDigest; this is not established as standard HMAC. The README also does not describe a separate configuration-authentication domain.

## 3. Migration provenance and license review

- The COE candidate's Pisowifi/SOURCE_INTAKE.json (blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f) explicitly describes a PisoWiFi-only rootfs recovery. It does not inventory the Hardware firmware files.
- The candidate docs/audits/HARDWARE_FIRMWARE_AUDIT.md (blob 86c06e7574761465b80482430296eb712d985367) says the ESP32/ESP8266 firmware has not been copied into COE, while the same PR #26 tree contains both Hardware sketches. The audit also pins older source blobs. This provenance note is stale relative to the inspected candidate tree and must be reconciled by its owner.
- Source project license experiment/openwrt/BlazePwifi/LICENSE and COE Pisowifi/LICENSE have the same MIT blob SHA 1ee55b94183417be977ca287cd7391f9a6f7e721. However, no LICENSE or NOTICE file exists under the candidate Hardware/ subtree, and a COE root LICENSE path was not found. The scope of the Pisowifi license copy for Hardware is not established here. This is a provenance/legal-review gap, not a conclusion of infringement.
- No source move, destination overwrite, or license change is authorized by this audit.

## 4. CI and role evidence at the observed heads

| Role / PR | Exact head | Observed evidence |
|---|---|---|
| MASTER #288 | fc9ba1391908f8d49d8f9e9c578e43b49e21417f | No PR-triggered workflow runs returned |
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Run 42698139210 success; scoped, not integrated |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Runs 43653329235 and 43653329229 success; scoped |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Run 42462978704 success; scoped |
| HARDWARE #315 | 75dc5f0b888f16e2c85e4321f62df4685639ad33 | Focused run 44013351048 success; full run 44013351035 failed in validation |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered workflow runs returned |
| QA #267 | ff5367990c2d27b8ebbb822ee208251af0c890e2 | Run 41452247439 success; older scoped lab |
| RELEASE #291 | 2c4edff231d9b2819415086825530d80b8801307 | Run 43744993487 success; scoped |
| RELEASE #242 | 734b89d9e7792247e8376335c3f3685500ab3f89 | Run 40882814472 success; no release authorization |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five candidate-head workflows remain queued |

These results do not establish combined integration, independent QA, hardware acceptance, or production readiness.

## 5. Required owner sequence

1. PHX-HARDWARE keeps the source-side no-remote-config behavior on #315 and supplies a clear handover describing the dormant function and register tuple semantics. Do not weaken keyless poll denial.
2. PHX-QA repairs the canonical extractor omission, independently reproduces the register-config denial lab on both boards at the exact #315 head, and adds an equivalent negative check to the proposed COE candidate before migration.
3. PHX-CORE reviews whether register tuple authentication is needed for any remaining operation and defines a separate configuration envelope only if remote configuration is reintroduced. Any future envelope needs canonical serialization, domain separation, controller identity, nonce/freshness, revision, all behavior-changing fields, bounds, and atomic persistence.
4. The COE integration owner reconciles the stale firmware audit, exact source/destination blob provenance, Hardware license/notice scope, and candidate test coverage before any per-file transplant. Do not copy the older candidate over the corrected owner source.
5. PHX-RELEASE keeps signing/publication gates closed.

## 6. Human reproduction

From an authorized checkout of the exact commits, compare the two sketches without modifying them:

    git show 75dc5f0b888f16e2c85e4321f62df4685639ad33:experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino
    git show b382d233ff06c8791b1028bed3c617cc7b670d12:Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino
    rg -n 'applyRemoteConfig|sigOk' experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino

Repeat for ESP32. Keep the source and destination refs pinned; do not infer equivalence from filenames or README claims.

## 7. Limitations and safety

This activation performed GitHub source/tree inspection and read existing CI job logs. No Master Python suite was executed; no COE destination test was run. Private registry access was unavailable through the exposed connected tools, no older Library snapshot was substituted, and no private registry contents were published. No Codex, merge, release, firmware flashing, physical test, secret provisioning, payment operation, or migration occurred.

**Disposition: BLOCKED / PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration, independent QA, native acceptance, 150 real power cuts, and a 30-device 24-hour soak remain unverified.
