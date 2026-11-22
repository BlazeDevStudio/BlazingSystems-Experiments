# PHX-MASTER UTC14 — Hardware Mbed TLS lab, poll-fixture and COE migration provenance

**Updated:** 2026-11-22T14:45:38Z  
**Role:** PHX-MASTER — coordination, architecture contracts, integration provenance only  
**Task:** PHX-MASTER-UTC14-EXACT-HEAD-COE26-REVIEW  
**Status:** DRAFT REVIEW ONLY · PRODUCTION NO-GO

## 1. Exact refs and ownership

- Experiments default branch: `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Legacy development: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Active v0.6 audit/development: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- PHX-MASTER branch: `phoenix/master-coordination@b7c6bb66d5603447d06fb8559c61457ee587c372`; parent `a65d96161319740d4a54f62b5637bf7d65fb8a7f`.
- Experiments PR #288: OPEN / DRAFT / UNMERGED, base `main@f4e8a891...`, 169 changed paths; all 169 are under `coordination/phoenix/`.
- COE default branch: `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: OPEN / DRAFT / UNMERGED, branch `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`, 205 changed files.
- Routing manifest: `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, 11 routes, PHX-MASTER target `null`.

The live PR metadata head is authoritative over stale prose in the existing PR #288 description, which still contains an older `737af73...` / 164-path summary. This audit refreshes that stale description separately after the commit.

## 2. New HARDWARE #342 exact-head finding

PR [#342](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/342) is OPEN / DRAFT / UNMERGED at `4cd878d2a55751d25f7bd91628d0c91d8111889e`, based on HARDWARE #327 at `fadac4ed3bc837cf729753264b9427fa3fd312b9`. It changes only:
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/mbedtls_compat_guard_lab.py` — blob `df294a5baca71a75355a2f9621d1e337a639700f`.
- One Hardware handover — blob `e45c3cd7f36989b59017e900cf9da78df0bf7548`.

The lab now reuses the Hardware-owned ESP8266-path helper `firmware_lab_source.py` at blob `d54fe57fa5ddca3aac5bd27fb8ec313740b9bd9e` for lexical masking and function extraction. It removes a second naive brace counter and tests braces inside ordinary/raw strings and comments. The source/test implementation commit is `c56140813a5bc04e80e8a779c97fea2973ff01eb`; the PR head `4cd878d...` is the later handover/docs head. No production ESP sketch, crypto implementation, GPIO behavior, admission, finance, QA fixture or release workflow was changed.

Exact-head evidence:
- Current PR-head Quarantine run [#45034441999](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034441999): SUCCESS.
- Current PR-head Full build [#45034442014](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034442014): terminal CANCELLED after validation job failure. The failed step is inherited `Controller protocol parity`, exact log: `Missing poll signature check`. Remaining target jobs were cancelled/skipped; this is not a full build pass.
- Earlier exact source/test commit focused run [#45031682091](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45031682091): SUCCESS. Its source-extracted Mbed TLS 3/4 stub tests are simulated host tests, not real Arduino/ESP32 package compilation or physical acceptance.
- Earlier Full run [#45031682054](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45031682054): validation failure at the same inherited poll-signature assertion.

**Master disposition:** preserve firmware default-deny. CORE owns the canonical controller-response producer; QA owns the stale parity fixture; HARDWARE owns its consumer and lab. Do not add a fake positive poll signature or bypass the assertion merely to turn CI green.

## 3. COE #26 exact destination staging audit

Complete recursive Git trees were fetched at exact refs (`truncated=false`):
- HARDWARE candidate source tree at #342 head: 2,478 entries / 1,899 blobs.
- COE #26 destination tree: 286 entries / 207 blobs.

| Item | Source candidate | COE #26 destination | Disposition |
|---|---|---|---|
| ESP32 sketch | `7ffb7b534c7163678726902946a17b04992950a0` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Divergent |
| ESP8266 sketch | `c2aa71963eaa0288721f0bb13cff771aaaabc42f` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Divergent |
| Firmware hardening test | `41211b2c110ab409f6d9d1812ef12fda73b13211` | `f921c56cecc19cab1989507b9b4ade1f45dac54e` | Divergent |
| Board-local Python helpers | 32 | 0 | Imports/inventory incomplete |
| ESP32 Mbed TLS lab/helper | `df294a5...` / `d54fe57...` | Not present | No import |
| PisoWiFi LICENSE | `1ee55b94183417be977ca287cd7391f9a6f7e721` | `1ee55b94183417be977ca287cd7391f9a6f7e721` | Byte-identical |
| Source root NOTICE | `f6d92cd21465312be5993631fe26977219be0fb9` | Root `NOTICE.md` absent | Required review/copy decision |
| Hardware LICENSE / NOTICE | Not present as route-local destination metadata in COE tree | Absent | Required owner/license review |

The source test (181 lines) and destination test (103 lines) are not byte-identical. Both still assert `response_sig`, `|register|` and `|poll|` at lines 28–30. The source test's positive poll assertion is stale against the current deny-only firmware baseline; the destination copy does not independently prove compatibility. A passing lexical or host-lab test cannot repair that contract mismatch.

**Migration decision: NO MIGRATION.** No staging, copy, move, overwrite, rebase, cherry-pick, route promotion or COE destination write occurred. Keep #26 FROZEN.

## 4. Separate COE Stage 5.1 boundary

COE #49 remains a distinct router-side Python companion candidate at `aeb8ff11b2f5db9a5f86280ab62ab988245f3919`, not a port of #342's Mbed TLS lab or CORE's nested `config_auth` contract. Its adapter documentation uses the legacy v1 SHA256 joined-field request digest (explicitly not HMAC), while the ESP command channel uses a separate HMAC. Its FakeRouter/FakeEsp + SQLite tests are simulated host tests; its optional `--enable-paid-lab` path was not invoked.

- Stage-specific run [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873): PASS.
- Case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992): PASS.
- Shared hardware/contracts run [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922): FAIL, including ESP32 Mbed TLS compatibility.

Do not treat #49 as an approved replacement for #26 or as positive financial admission.

## 5. Live owner CI reconciliation

| Owner / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) build PASS; dedicated response-auth workflow not returned |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) APK identity PASS; [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) API21/23 PASS; [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) build FAIL |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) Windows CI PASS; native COM acceptance NOT TESTED |
| HARDWARE #327 | `fadac4ed3bc837cf729753264b9427fa3fd312b9` | [#45029852010](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029852010) relay lab PASS; [#45029851960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851960) quarantine PASS; [#45029851959](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851959) Full FAIL |
| HARDWARE #341 | `a655d0b5c144535a3ad8e48009fc4498318ff5e3` | [#45014156653](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45014156653) focused PASS; [#45014156658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45014156658) Full FAIL |
| HARDWARE #342 | `4cd878d2a55751d25f7bd91628d0c91d8111889e` | [#45034441999](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034441999) Quarantine PASS; [#45034442014](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034442014) Full CANCELLED after poll parity FAIL |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) Windows CI PASS |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered runs; stale base `b1ca02e...` |
| RELEASE #291 | `42797e2f3d65c30a1070caf49c93aebec149d897` | [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) ESP32 compatibility PASS; [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) build FAIL; [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) Windows FAIL |
| COE RELEASE #35 | `b01c8d44a21e54ef432bd6a00d35955ff3a4210c` | [#45033301449](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45033301449) case guard PASS; [#45033301454](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45033301454) shared profiles FAIL (10/10 lack approved site ULA /48); [#45033301432](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45033301432) sandbox FAIL (Bubblewrap missing, exit 125) |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) overlay/shell PASS; [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) case guard PASS; contract vectors only, runtime deny |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs |

## 6. Access, branch protection and execution limits

- GitHub branch API reports `protected=false` for Experiments `main`, v0.6 audit-foundation, v0.5.3 development and COE `main`. The Master branch's effective protection could not be verified through the branch endpoint; do not assume it is protected.
- Private Drive canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not accessible. Library search found only older v3–v7 snapshots and a 2026-11-09 checkpoint that references v11 by filename; no older copy was substituted. No Google Drive connector is exposed.
- Local authenticated Git checkout is blocked: `git ls-remote` failed with `Could not resolve host: github.com`. Full Master unittest discovery and `verify_coordination.py` were NOT RUN.
- Exact GitHub tree/blob inspection and remote CI evidence above are not local test execution. No new Master test suite was executed.
- Cleanup issue #266 remains OPEN, 0/7 tracks complete; Master cleanup inventory remains incomplete.

## 7. Owner actions and release gate

1. QA: replace the inherited positive `|poll|` fixture with source-linked negative/default-deny tests; do not weaken firmware.
2. CORE: publish the canonical versioned controller-response producer contract and ensure its dedicated response-auth workflow runs at exact head. CORE source remains untouched by Master.
3. HARDWARE: keep #342 scoped to its shared lexical lab helper; do not claim physical or target-build acceptance from the focused source-extracted test.
4. COE owner: keep #26 frozen; any future candidate needs exact per-file source/target blob, license/NOTICE, import, test identity and exact-head CI review.
5. RELEASE/site authority: provide approved site ULA /48 and trusted Bubblewrap runner; resolve stale release handover.
6. Registry custodian: restore authorized private Drive v11 and newer-correction access.
7. Human runner: restore authenticated GitHub network access and run the full Master suite at the latest commit.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

No subsystem source, COE destination, private registry, secret, signer, payment system or hardware device was modified or used. No merge, release, flash, financial migration, physical test or production approval occurred.
