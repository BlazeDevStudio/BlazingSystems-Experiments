# PHX-MASTER UTC13 — live role CI and COE Stage 5.1 exact provenance audit

**Updated:** 2026-11-22T13:36:09.293Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** coordination/phoenix/, architecture/interface contracts, role CI reconciliation, cross-repository migration provenance  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.  
**Disposition:** REVIEW ONLY · COE #26 FROZEN · PRODUCTION NO-GO

## 1. Exact live refs

| Ref | Exact head | State |
|---|---|---|
| Experiments default main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b | Default branch |
| Experiments legacy development | aad3aade72c1156eecba1fed30907c6d0283b2c5 | Separate v0.5.3 development branch |
| Experiments v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 | Separate comparison/audit branch |
| PHX-MASTER branch | a65d96161319740d4a54f62b5637bf7d65fb8a7f | Current branch head before this audit commit |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | Destination default branch |
| Experiments PR #288 | a65d96161319740d4a54f62b5637bf7d65fb8a7f | OPEN / DRAFT / UNMERGED; base main; 168 changed paths, all under coordination/phoenix/ |
| COE PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | OPEN / DRAFT / UNMERGED / FROZEN; base main@a6513ab4 |

The exact branch head and PR #288 head agree at the start of this run. The ownership manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, schema phoenix/ownership-routes/v1, 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER destination null. No route promotion is proposed.

## 2. Current owner PR heads and exact-head CI

| Role | PR / exact head | Current CI evidence | Disposition |
|---|---|---|---|
| CORE | #252 c82705f2de865c89ab733b10efa84f26f56a5cc4 | General build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS | Dedicated response-auth workflow not returned; CORE implementation remains separately owned and untouched |
| RENTAL | #328 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) SUCCESS; full build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAILURE | Handover freshness gate fails; ESP32 compile also fails because staged sketch includes missing mbedtls/sha256.h |
| PISONET | #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS | Scoped Windows CI only; native COM / physical adapter acceptance not established |
| HARDWARE | #327 0655b6129adc3e293a341b6d379cdc7c06d46c70 | Quarantine [#45025078636](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45025078636) and Relay [#45025078630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45025078630) SUCCESS; Full [#45025078677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45025078677) FAILURE | Validate job still reports “Missing poll signature check”; target/platform build jobs pass. Preserve default-deny; do not add a legacy poll signature |
| HARDWARE | #339 b3e1558845ae2cd508e42d0d4722fdcd28293e32 | Quarantine [#44986635350](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635350) SUCCESS; Full [#44986635417](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635417) FAILURE | Same inherited poll-signature assertion |
| HARDWARE | #341 a655d0b5c144535a3ad8e48009fc4498318ff5e3, child of #339 | Quarantine [#45014156653](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45014156653) SUCCESS; Full [#45014156658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45014156658) FAILURE | Separate owner-scoped lexical-fixture port; same inherited poll-signature assertion |
| HARDWARE | #340 20c5889fc4ceeb95ab0b05c7c11952704caff36b, separate #283 child | Six workflows, including Full [#44983396262](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396262), SUCCESS | Candidate CI only; deny-only and no physical acceptance |
| QA | #290 5c29d15994cee1279058f1eca12f2a3180704292 | Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS | Scoped pass |
| QA | #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs | Based on stale Master parent b1ca02e2087f3b1a7169ceab9c34e52646e700df; QA owns any refresh |
| RELEASE | #291 42797e2f3d65c30a1070caf49c93aebec149d897 | Compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) SUCCESS; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) FAILURE | Both failing at mandatory handover freshness; publisher skipped |

CORE, RENTAL, PISONET, HARDWARE, QA and RELEASE implementation ownership was not changed. No competing worker was started.

## 3. COE release and integration candidates

| Candidate | Exact head | Exact-head CI | Disposition |
|---|---|---|---|
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows remain QUEUED; zero jobs | FROZEN; no destination edit or migration |
| COE RELEASE #35 | d2a32356bcce8efdcf4512d3534add3fefb1b7ac | Case guard [#45027228214](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45027228214) SUCCESS; shared validation [#45027228200](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45027228200) FAILURE after 181 unit tests, then 10/10 profiles fail closed without approved site-scoped RFC 4193 ULA /48; sandbox [#45027228210](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45027228210) FAILURE, exit 125, Bubblewrap absent | No privileged install or unsandboxed fallback |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Golden vectors [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) SUCCESS | Contract vectors only; runtime remains deny |
| COE INTERCON #49 Stage 5.1 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919, base #48 at 8286548e395366f2332830025fed00ceebdfb24a | Stage-specific [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) SUCCESS (static contract, signed-wire, router bridge fault tests, ESP8266 compile, source package); shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) has shared-contract and ESP8266 jobs SUCCESS but ESP32 compile FAILURE | Separate stacked draft chain #46 → #47 → #48 → #49; not part of #26 and not a hardware/production acceptance |

## 4. Exact COE #26 / Stage 5.1 provenance

Both recursive trees were complete (not truncated): current Hardware source PR #327 tree 2,476 entries; COE #26 destination tree 286 entries.

- Source has 32 board-local Python lab/helper files under the ESP32/ESP8266 firmware directories; COE Hardware has 0 such Python files.
- Source ESP32 sketch blob 7ffb7b534c7163678726902946a17b04992950a0 differs from COE #26/#49 ESP32 blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- Source ESP8266 sketch blob c2aa71963eaa0288721f0bb13cff771aaaabc42f differs from COE #26 ESP8266 blob c8be98f72596681e36a3ad1f8939bf8046c96887.
- Source ESP32 uses an explicit Mbed TLS major-version guard: Mbed TLS 4 uses PSA Crypto; Mbed TLS 3 uses the checked legacy SHA API. COE #26/#49 still includes mbedtls/sha256.h directly. The exact COE #49 shared-workflow ESP32 compile log reports “fatal error: mbedtls/sha256.h: No such file or directory”.
- Source hardening test blob 41211b2c110ab409f6d9d1812ef12fda73b13211 differs from COE #26/#49 Hardware test blob f921c56cecc19cab1989507b9b4ade1f45dac54e. The destination test still expects the old poll-signature strings; it is not the same test identity as the current source test.
- The source BlazePwifi LICENSE and COE Pisowifi/LICENSE are byte-identical at blob 1ee55b94183417be977ca287cd7391f9a6f7e721. Source repository NOTICE.md exists; the COE #26 tree has no root NOTICE.md. COE Hardware/LICENSE and Hardware/NOTICE are absent.
- COE #49 changes seven Stage 5.1 files and does not modify Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino or Hardware/tests/test_firmware_hardening.sh. Its Stage 5.1 tests use FakeRouter/FakeEsp and SQLite; the test file explicitly says these are not real OpenWrt/ESP hardware tests.
- The Stage 5.1 adapter documents the existing router v1 request digest as SHA256(secret|action|id|nonce|pulses|target|secret), explicitly not HMAC. The ESP command channel uses a separate HMAC protocol. These are distinct authentication boundaries and must not be described as one shared HMAC contract.

**Migration decision: NO MIGRATION.** No copy, move, overwrite, cherry-pick, rebase, retarget, staging, route promotion or destination edit occurred. PR #49 is a separate COE candidate stack and does not make #26 current or complete.

## 5. Master execution and access limits

- Master commit a65d96161319740d4a54f62b5637bf7d65fb8a7f has zero PR-triggered workflow runs and zero combined status checks. This is NOT RUN, not PASS.
- Local clone attempt failed with exit 128: “Could not resolve host: github.com”. Therefore the full coordination unittest discovery and verify_coordination.py were NOT RUN.
- The exact canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in Library search. Only older v3–v7 snapshots and 2026-11-09 checkpoint files surfaced; they were not substituted. No Google Drive connector is exposed in this runtime. No private registry contents or identifiers were published.
- AGENTS.md, README_FIRST and COMMUNICATION_PROTOCOL were read. The linked cloud artifact policy and storage handover could not be fetched through the connected GitHub content surface; do not claim those two documents were verified.
- Cleanup issue #266 remains OPEN. Its seven-role checklist is not complete; the broad Master duplicate/dead-code inventory remains incomplete. No mass deletion or refactor was attempted.

## 6. Owner actions

1. PHX-QA: replace the inherited positive legacy poll-signature assertion with source-linked negative/default-deny assertions; do not add a legacy signature to firmware.
2. PHX-CORE: publish the versioned nested config_auth producer contract and ensure its dedicated exact-head auth test actually runs.
3. PHX-HARDWARE: preserve deny-only behavior until CORE and QA approve a compatible contract.
4. COE integration owner: keep #26 frozen; review per-file source/test/license provenance and reimplement only under the owner-controlled destination branch.
5. PHX-RELEASE / infrastructure: obtain approved site ULA /48 authority and a trusted Bubblewrap-capable runner; no privileged installation or fallback.
6. Registry custodian: restore authorized access to the canonical private v11 registry and newer corrections.
7. Human runner: restore authenticated GitHub checkout/network and run the complete Master coordination suite at the exact final SHA.

## 7. Production gate

**PRODUCTION NO-GO.** Independent protected signing and anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device 24-hour soak and explicit owner-authorized release gates remain unverified. No merge, release, signing, secret provisioning, hardware flash, real-payment operation, financial migration or physical test was performed.
