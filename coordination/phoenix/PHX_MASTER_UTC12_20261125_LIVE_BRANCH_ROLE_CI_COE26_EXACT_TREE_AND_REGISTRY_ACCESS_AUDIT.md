# PHX-MASTER UTC12 — live branch, owner CI, and COE #26 exact-tree admission audit

**Checkpoint:** 2026-11-25T12:36:47Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Boundary:** Strict NO CODEX; coordination-only changes.

## Exact refs and PR state
- Experiments main `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`; development `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master before this update `5ff54bf3140f0b4b3065e22b20183c1564c57edb`; COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- PR #288 OPEN / DRAFT / UNMERGED, head `5ff54bf3140f0b4b3065e22b20183c1564c57edb`, recorded base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- COE #26 OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Current main vs Master comparison: **554 ahead / 1 behind**, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. The one main-only commit adds unrelated root file `promp CallerID`. No merge, rebase, retarget, cherry-pick or force update; repository owner must decide synchronization.

## Control plane and ownership
- Issue #172 OPEN; its body still begins with an older UTC07 snapshot, while current owner progress is in comments.
- Cleanup #266 OPEN / **0-of-7**; Master ownership/dependency/duplicate-module inventory remains incomplete.
- `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER source `coordination/phoenix/`, target null.
- CORE remains with its separate production continuation. No subsystem source or COE destination was modified.

## Exact-head owner CI
| Owner / PR | Exact head | Current CI |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build #42698139210 PASS (scoped). |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK/API PASS; build #44782114390 FAIL. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows #42462978704 PASS (synthetic only). |
| HARDWARE #340 | `38f3e9419f37109443c806a2362577d9efc50e4d` | Six focused/build workflows PASS. |
| HARDWARE #347 | `960184670379f01e20f0e7e8bc23b3e5eedacd3f` | Quarantine/Relay/build FAIL. |
| HARDWARE #348 | `eb7afcb2ba0d1e84054c052c8b129cb51a91d062` | Focused header PASS; build FAIL. |
| HARDWARE #349 | `2a5c997add4f49fcd74f753101d3a9daac0040bf` | Quarantine #45603969253 PASS; Relay #45603968961 PASS; Full #45603969181 FAIL at `Missing poll signature check` in ESP8266. 14 target/platform + Android jobs pass; downstream stages skip. |
| QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows PASS; #292 no PR-triggered runs. |
| RELEASE #291 | `ab719afe38ea9af97b0d46ab34a67c675d690d87` | Build #45614130499 and Windows #45614130429 FAIL at CORE-owned CURRENT_STATE freshness; compatibility #45614130744 PASS 3/3. |
| COE RELEASE #35 | `f611c96091a1014ad36bf64251c180bcbc2d1f65` | Shared #45541598251 FAIL (10/10 site-ULA denials); sandbox #45541598267 FAIL (Bubblewrap missing); case #45541598250 PASS. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay/shell and case PASS (scoped). |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1/case PASS; shared ESP32 compile #44646341922 FAIL (missing `mbedtls/sha256.h`). |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs; FROZEN. |

CORE owns canonical CURRENT_STATE/PROJECT_HANDOVER and authenticated poll/register producer. RELEASE owns its workflow and reruns after CORE refresh. HARDWARE owns firmware; QA owns independent poll-signature assertion review. No shared owner file changed.

## COE #26 exact Hardware tree and provenance
| Measure | Current Hardware source subtree | COE #26 destination subtree |
|---|---:|---:|
| Complete repository tree entries | 2,552 | 286 |
| Scoped `BlazePwifi/{esp32,esp8266}` / `Hardware/{esp32,esp8266}` entries | 78 | 4 |
| Board-local Python helpers/labs | 64 | 0 |

ESP32 source blob `c07aba7d518ef7eb5d536aafdd77ef6193e676cb` differs from destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`. ESP8266 source blob `56b7ff524f6b55a1305196b27494c87fb9ffa6ab` differs from destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.

Two current source labs are absent from the destination:
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_token_normalizer.py` (source blob `fd77601b264c1d3f9d9dd853a6934853da602c7b`).
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_token_normalizer_contract_lab.py` (source blob `e0e59645930c964279d969e810561a1ccb23d56b`).

SOURCE_INTAKE declares 47 byte-identical / 14 derived. Its 61 runtime rows recount to **46 identical / 15 derived**. Root `NOTICE.md`, `ui/vendor/tabler/LICENSE`, and `BlazeRentalLauncher/LICENSE` are present in source but absent from the destination. The manifest is selective-review only and does not authorize recursive copying.

**Admission:** COE #26 remains FROZEN. No staging, copy, move, overwrite, cherry-pick, rebase or destination write occurred.

## Tests and blockers
- 20 read-only ref/tree/manifest assertions passed; these are audit checks, not product tests.
- Master Python unittest suite and `verify_coordination.py` NOT RUN. `git ls-remote` failed because this runtime cannot resolve `github.com`; no authenticated local checkout is available. No Master Actions run is claimed.
- Exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found by exact-name Library search. No Google Drive connector is exposed; older snapshots were not substituted and no private data was published.
- AGENTS.md-linked Cloud Artifact Policy and Storage Handover could not be retrieved through the current GitHub connector surface; repository-owner access or corrected links required.

## Next actions
1. Repository owner decides whether/when to synchronize #288 with the one-commit-newer main; no automatic rebase/merge.
2. CORE publishes canonical post-workflow-change CURRENT_STATE/PROJECT_HANDOVER; RELEASE reruns #291.
3. CORE publishes authenticated poll/register producer contract; QA independently resolves the #349 poll-signature assertion without weakening deny-default.
4. COE integration owner prepares Hardware-specific per-file source/destination/test/license mapping and reconciles 46/15 vs 47/14 before staging review.
5. Registry custodian restores authorized private v11/newer-correction access.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, flash, physical test, real-payment operation, customer cutover or financial migration occurred.