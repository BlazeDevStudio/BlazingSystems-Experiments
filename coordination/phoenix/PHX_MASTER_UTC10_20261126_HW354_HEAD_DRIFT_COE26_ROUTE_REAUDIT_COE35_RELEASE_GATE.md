# PHX-MASTER UTC10 — owner-head drift, COE route provenance and release gates

**Scope:** PHX-MASTER coordination only. COE #26 remains FROZEN. PRODUCTION NO-GO. No subsystem source branch or COE destination path was changed.

## 1. Exact refs and Master scope

- Experiments main: 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5.
- Experiments development: blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master branch and PR #288 starting HEAD: 57b7dc10c95579edf56be6470166e3cb9293a29c.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- PR #288: OPEN / DRAFT / UNMERGED; 607 ahead / 1 behind main; merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b; 232 changed paths, all under coordination/phoenix/.
- OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29; 11 routes; DRAFT_REVIEW_ONLY; historical source_ref f4e8a891; destination candidate #26 at b382d233ff06c8791b1028bed3c617cc7b670d12; PHX-MASTER target null.

## 2. Live owner PR heads and CI

| Role / PR | Exact head | Exact-head CI / disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; no authenticated poll or financial acceptance. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | Focused API/auth/APK PASS; shared [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL at handover freshness and missing ESP32 mbedtls/sha256.h. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM NOT TESTED. |
| HARDWARE #340 | f70f6af78c64ef86ba0f631faeb02b6cb6eb2725 | Six exact-head workflows PASS; Full [#45747758154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747758154) 26 successful jobs / 4 production skips. |
| HARDWARE #353 | cb1787ac8f89562f20b6ecdee0c7969fbd12bd01 | Quarantine [#45756942179](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942179) and Relay [#45756942276](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942276) PASS; Full [#45756942184](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942184) FAIL at inherited poll-signature parity. |
| HARDWARE #354 | 046bced7c8765d5e27daeb2885f0654f9ec62149 | PR body stale at e7f63da29b8b27ff2143aebc128e63f9789b0ad2; actual head 10 commits ahead. Focused [#45802963675](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963675) PASS; native [#45802963561](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963561) FAIL at QA-owned clearPending(true/false) assertion; Mbed matrix [#45802963530](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963530) PENDING; Full [#45802963678](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45802963678) IN_PROGRESS, with validation job 139850939852 failing handover freshness while target jobs remain in progress. Latest commit changes only the output-enable polarity lab's expected OFF-write count from two to three; production sketches unchanged. HARDWARE must refresh PR/handover; QA owns the obsolete assertion. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Synthetic Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM NOT TESTED. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head PR runs or statuses. |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No exact-head PR runs or statuses. |
| COE RELEASE #35 | f66ac305dd5602e5a2b45acf12a9ca61c6d88213 | Case guard [#45800298224](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45800298224) PASS; shared [#45800298285](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45800298285): 247 tests, 245 passed / 2 skipped, then 10/10 appliance profiles fail closed for missing approved site-scoped RFC 4193 ULA /48. Sandbox [#45800298258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45800298258): 42/42 host preflight PASS, then Bubblewrap unavailable / exit 125. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; synthetic only. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL at ESP32 Mbed TLS compatibility. |
| COE RELEASE #44 | 582fd5d5e83e36b36546ac28534740298ba94af4 | Separate ULA candidate remains divergent from current #35 and does not clear current site-prefix or sandbox gates. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED with zero jobs; FROZEN / DRAFT_REVIEW_ONLY. |

The previous Full run at the older #354 pin e7f63da had failed a QA-owned config_revision parity assertion. At current 046bced7, Full validation fails earlier at handover freshness, so the old Controller-parity result is not re-established at the current head.

## 3. Exact owner-tree route comparison to COE #26

All owner-source recursive trees and the COE #26 tree returned truncated=false.

| Source PR | Tree SHA | Entries |
|---|---|---:|
| CORE #252 | 47244f4a86cf38911d33cd04e9927cefb46a393e | 2,394 |
| RENTAL #328 | c25b705412e6f31a2cce457a5430d6e5cb80c050 | 2,412 |
| PISONET #255 | de2534cf0416854ef9a9d09d7079c8c98fce7301 | 2,411 |
| HARDWARE #340 | 21b59155f8e88fecff58b5862d2830796c187251 | 2,372 |
| HARDWARE #353 | 7cea8fde4b705dbbf37aa600503a20ad819e1c6c | 2,572 |
| HARDWARE #354 | f9ff27480aad325c1e7984dc770603e54b1d574a | 2,404 |
| QA #290 | 5b144b573c4c26ccc6ba142f19a7ad2bc196b254 | 2,411 |
| RELEASE #291 | 60ceadb25830ed473473bf108724c09e412e7f73 | 2,426 |
| COE #26 | 8a7d4cf81d7227118b876c1138dd2da12345fefa | 286 entries / 207 blobs |

| Route | Source | Destination | Common | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| CORE rootfs | 20 | 20 | 20 | 13 | 7 | 0 | 0 |
| CORE vendo CGI | 1 | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 994 | 8 | 0 | 0 | 0 | 994 | 8 |
| RENTAL Server | 12 | 4 | 1 | 0 | 1 | 11 | 3 |
| PISONET SoftTimer | 68 | 47 | 38 | 27 | 11 | 30 | 9 |
| HARDWARE #340 ESP32 / ESP8266 | 9 / 6 | 1 / 1 | 1 / 1 | 0 / 0 | 1 / 1 | 8 / 5 | 0 / 0 |
| HARDWARE #353 ESP32 / ESP8266 | 16 / 67 | 1 / 1 | 1 / 1 | 0 / 0 | 1 / 1 | 15 / 66 | 0 / 0 |
| HARDWARE #354 ESP32 / ESP8266 | 4 / 8 | 1 / 1 | 1 / 1 | 0 / 0 | 1 / 1 | 3 / 7 | 0 / 0 |
| QA tests | 145 | 19 | 4 | 2 | 2 | 141 | 15 |
| RELEASE workflow reimplementation | 1 | 1 | 1 | 0 | 1 | 0 | 0 |

Standalone Rental remains manual-file-mapping-required; recursive copy is prohibited. All common Hardware sketch paths are divergent.

License/NOTICE: Product MIT, QRCode and TailAdmin LICENSE/NOTICE counterparts match exactly. Source root NOTICE, Tabler LICENSE and BlazeRentalLauncher LICENSE are missing from the destination; COE root LICENSE is absent. Exact blob identities are recorded in this audit.

The QA route remains incomplete: 145 source test blobs versus 19 destination, four common paths (two exact, two divergent), 141 source-only and 15 destination-only. Historical intake counts are not interchangeable with the current owner-head inventory.

**Decision: COE #26 remains FROZEN.** No staging, copy, move, overwrite, cherry-pick, rebase, retarget, workflow dispatch or destination write.

## 4. Governance and execution limits

- Cleanup-first #266 remains OPEN / 0 of 7; bounded Hardware comments do not complete any global role gate.
- Experiments main, development and COE main report protected=false; both rulesets endpoints return empty arrays. Master branch ref is verified, but its slash-containing branch protection flag was not readable; effective required-check enforcement remains NOT ESTABLISHED.
- Experiments AGENTS.md was read. COE AGENTS.md returned 404; COE README contains only the repository heading.
- No Google Drive connector is exposed; accessible Library search did not return the canonical private v11 registry or a verified newer correction. No older snapshot substituted; no private contents or IDs published.
- Available automation inventory surfaced PHX-MASTER, PHX-HARDWARE and PHX-RELEASE continuations, but not the exact title “Blaze Production Continuation”. CORE was not touched or started by Master.
- Master HEAD workflow-run query returned no runs. Master Python unittest suite and verify_coordination.py were NOT RUN because no authenticated local checkout or Master runner was available. Owner CI is exact-SHA evidence, not a Master test execution.

## 5. Required next owner actions

1. PHX-QA: replace active clearPending(true/false) assertion with deny-only / no-active-callsite / pending-evidence-preservation checks. Revalidate current-head Controller parity separately; do not restore unsigned response consumption.
2. PHX-HARDWARE: refresh #354 PR description and canonical handover to 046bced7, then rerun Full at that exact head. Keep production sketches deny-only until CORE's contract is approved.
3. PHX-CORE: publish authenticated register/poll response and event receipt/disposition contract with exact serialization, controller binding, mandatory key provisioning, freshness and replay semantics.
4. PHX-RELEASE / INFRA: obtain approved site-scoped ULA /48 authority and a supported Bubblewrap runner; do not invent a prefix or bypass the sandbox.
5. COE integration owner / QA: keep #26 frozen until per-file source identity, import completeness, test equivalence, licenses/NOTICE and destination CI are reconciled.
6. Registry custodian: restore authorized private Drive v11 and newer-correction access.
7. Repository administrator: establish and independently verify branch protection and required-check enforcement.

**Final disposition:** OPEN DRAFT only; PRODUCTION NO-GO. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates remain mandatory.

No merge, release, signing, secret provisioning, firmware flashing, physical test, real-payment operation or financial migration occurred.
