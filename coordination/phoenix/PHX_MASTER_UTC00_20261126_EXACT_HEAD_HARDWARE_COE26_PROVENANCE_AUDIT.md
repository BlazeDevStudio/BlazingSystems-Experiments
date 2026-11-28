# PHX-MASTER UTC00 — exact-head Hardware / COE #26 provenance audit

**Observed:** 2026-11-26T00:33:13Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX.  
**Scope:** `coordination/phoenix/` only; no subsystem or destination source ownership taken.

## 1. Live refs and control plane

| Ref | Exact current SHA / state |
|---|---|
| Experiments `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Active v0.6 `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master `phoenix/master-coordination` at start | `a27a397b90c066cd443c177345e195dbfbadf782` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

- Issue #172 remains the single control-plane inbox; the latest separate owner checkpoint is PHX-RELEASE UTC00. No PHX-MASTER UTC00 checkpoint for 2026-11-26 existed at audit start.
- Cleanup issue #266 remains OPEN / 0-of-7.
- Master PR #288 remains OPEN / DRAFT / UNMERGED at the starting Master SHA. Main→Master compare: 587 ahead / 1 behind, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; 225 changed paths, all under `coordination/phoenix/`.
- `OWNERSHIP_ROUTES.json` is blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`, Master target null. CORE remains with its separate owner. No ownership route changed.

## 2. Exact Hardware role and ancestry recheck

### HARDWARE #349

- PR HEAD `1a2ecf5fa8c8c20a0095ac898c1bff254280ad27`; source/test SHA `9dc0ae39832e5fe7db79694b670a841f0c90ffe0`.
- Source/test commit changes only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_token_normalizer.py`: the C++ line-splice scanner now recognizes backslash-CRLF as well as backslash-LF inside `//` comments. It does not change either firmware sketch.
- Quarantine [#45724609180](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45724609180) and Relay [#45724609178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45724609178) PASS.
- Full [#45724609215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45724609215) FAILS in Controller protocol parity at `Missing poll signature check` in the ESP8266 sketch. ESP32/ESP8266 build jobs in that run passed; the failure is the validation gate, not a board compile failure.

### Stacked Hardware ancestry

| Child | Parent snapshot | Exact comparison against current parent |
|---|---|---|
| #352 `0e984e267b3a8fb10c314800d1a7f120806354b7` | Captured #349 base `2a5c997add4f49fcd74f753101d3a9daac0040bf` | Current #349 `1a2ecf5` vs #352: 43 ahead / 3 behind; merge base `2a5c997`. #352 focused checks PASS; Full [#45683122413](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45683122413) FAILS at Controller protocol parity. |
| #353 `dc9cf634248ecc23f51f1477bd1769d63d3fe5ea` | Captured #352 base `6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec` | Current #352 `0e984e26` vs #353: 17 ahead / 11 behind; merge base `6d743ae`. No exact-head PR-triggered runs. |
| #340 `547148eeb4384df7971d17d762e3f12bc5dcab3c` | Captured #283 base `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d` | Current #283 `4dd0b01b` vs #340: 43 ahead / 4 behind; merge base `88581eef`. Full [#45708073607](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45708073607) PASS, but ancestry remains stale. |

HARDWARE owns all stack rebase/retarget and handover changes. Master did not rewrite any Hardware branch.

### HARDWARE #348 and COE #49 Mbed TLS boundary

- #348 head `ed172016`: focused helper [#45716221522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45716221522) PASS; Full [#45716221609](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45716221609) FAIL because ESP32 Arduino core 4.0.0 cannot find inherited `mbedtls/sha256.h` at `BlazePwifiVendo32.ino:6`.
- COE #49 shared ESP32 compile [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) fails at the same header; Stage 5.1 and case guard pass. No provider/toolchain decision was made by Master.

## 3. Exact #349 source → COE #26 destination provenance

Recursive Git trees were fetched at the exact source/test and destination commits; both responses were complete and non-truncated.

| Measure | Experiments source #349 | COE #26 candidate |
|---|---:|---:|
| Recursive tree entries | 2,552 | 286 |
| ESP32 board blobs | 16 | 1 |
| ESP8266 board blobs | 60 | 1 |
| Total board blobs | 76 | 2 |
| Board-local Python helpers | 64 | 0 |
| Project `tests/` files | 47 | 19 in `Pisowifi/tests/` |

Exact board blob comparison: both destination sketches have the same relative path as their source counterpart but different blob SHA; 74 source board blobs have no destination counterpart; no extra destination board blob exists under `Hardware/esp32` or `Hardware/esp8266`.

Test identity mapping from source `experiment/openwrt/BlazePwifi/tests/` to destination `Pisowifi/tests/`: four same-relative-path files; `portal.sh` is byte/mode identical; `config.sh`, `integration.sh` and `security.sh` diverge; 43 source-only and 15 destination-only. The separate `Hardware/tests/` subtree contains one script. Do not equate destination-wide tests owned by Rental/Pisonet/Shared with Hardware test coverage.

License/provenance: source product `experiment/openwrt/BlazePwifi/LICENSE` (blob `1ee55b94183417be977ca287cd7391f9a6f7e721`) and source root `NOTICE.md` (blob `f6d92cd21465312be5993631fe26977219be0fb9`) have no root counterparts in the COE #26 tree. The destination contains only PisoWiFi `SOURCE_INTAKE.json` and `MIGRATION_MAP.md`; no Hardware-specific intake or migration map exists. The PisoWiFi manifest is not Hardware provenance.

**Decision:** COE #26 remains FROZEN. No staging, copy, move, overwrite, cherry-pick, retarget or destination write was performed or proposed. The PR body's licensing/privacy resolution claim is not supported by the exact current tree.

## 4. Active v0.6 and COE #26 response-auth P0

Exact active v0.6 blobs re-read:

- ESP32 `29f1125d52ff474a0d028ad41f7af201be1f0f9d`: register at line 290 and poll at line 314 call `applyRemoteConfig()`; the poll result also sets `insertMode` and `activeTarget`.
- ESP8266 `12c4bb82b6fddafe813674a0b5f692c1d3634073`: register at line 324 and poll at line 354 call `applyRemoteConfig()`; poll fields are consumed.
- CGI `db58041c0575ad0a1101d99cb85403e03c8dcb22`: register/poll response body at line 137 contains `ok`, `insert`, `target_nonce`, `expires` and nested `controller`, but no `response_sig`. Other member API signatures do not authenticate this response.

COE #26 candidate board blobs remain `3cc7ec54...` (ESP32) and `c8be98f7...` (ESP8266). Both initialize `sigOk=true` and only enter response verification when the controller key is nonempty; with an empty key the default remains true. Setup paths do not require a nonempty controller key. This is a source-level keyless verification bypass, not a live exploit demonstration.

**P0:** CORE owns the versioned response contract, canonical serialization, key provisioning and golden vectors; HARDWARE owns fail-closed firmware consumption; QA owns independent positive/negative tests. Do not synthesize a signature or weaken the inherited Full gate.

## 5. COE RELEASE #35 exact-head recheck

- Current PR HEAD `2f87287f4b1176fffd96e79d2209f2164af86c98`; corrected source/test `781a7ad5b4df64fb37d8be2f8bef75d9b269b774`; test-first RED `5a99b556`; first source attempt `50e10bbb` failed two existing symlink-order tests and was not accepted as green.
- The corrected source hardens recursive artifact manifest scanning against group/world-writable nested directories and regular payload files; it preserves symlink/non-regular rejection precedence and refuses unsafe inputs instead of chmodding them.
- Current PR-head shared [#45728600559](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45728600559): 240 tests PASS / 2 intentional skips, then all 10 appliance profiles fail closed because approved site-scoped RFC 4193 ULA `/48` authority is missing; ESP32/ESP8266 compiles skipped.
- Current PR-head sandbox [#45728600582](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45728600582): 42/42 host tests PASS, then Bubblewrap is unavailable / exit 125; namespace and mandatory sandbox packaging were not executed.
- Current PR-head case-collision guard [#45728600639](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45728600639) PASS.

These are hosted CI/host tests, not successful ImageBuilder sandbox execution, physical appliance acceptance or release approval.

## 6. Remaining roles and blockers

- CORE #252 build PASS is scoped and not financial acceptance. COE CORE #45 focused receipt-vector tests pass but do not approve the separate poll/register response contract.
- RENTAL #328 focused APK/API/auth checks pass; shared build fails at CORE handover freshness and inherited Mbed TLS header. PISONET #255 and QA #290 are synthetic Windows only; native COM was not invoked. QA #292 has no PR-triggered runs.
- RELEASE #291 Windows and Full fail CORE-owned `CURRENT_STATE.md` freshness; ESP32 compatibility passes; signing/publication skipped.
- Cleanup #266 remains OPEN / 0-of-7. `OWNERSHIP_ROUTES.json` remains 11 routes / `DRAFT_REVIEW_ONLY` / Master target null.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. Library search returned older v3–v7 snapshots only; no Google Drive connector is exposed. The AGENTS-linked Cloud Artifact Policy and Recovery Handover could not be read at the expected repository path.
- Master Python unittest suite and Master GitHub Actions were NOT RUN; no Master workflow run exists. This run performed read-only GitHub source/tree/CI inspection plus coordinator-side assertions only.

## 7. Next exact actions

1. HARDWARE updates its canonical handovers and reconciles #352 against current #349, #353 against #352, and #340 against #283; do not let Master rewrite those branches.
2. CORE publishes the approved authenticated register/poll response envelope and mandatory controller-key provisioning contract; CORE remains separately owned.
3. HARDWARE implements fail-closed consumption against that approved contract; QA independently tests missing, malformed, forged, stale, replayed, mismatched and keyless responses on both boards.
4. RELEASE/INFRA/CORE obtain approved site-scoped ULA `/48` authority, a trusted unprivileged Bubblewrap runner and canonical CORE handover freshness for #291.
5. COE integration owner supplies Hardware-specific exact blob/mode/license/test provenance and destination CI before any migration proposal.
6. Registry custodian restores authorized access to private Drive v11 and newer corrections; repository owner provides the AGENTS-linked policy/handover documents at a readable path.

## 8. Final disposition

Master changed coordination documentation only. No subsystem source, COE destination, interface schema, signing identity, secret, payment system or physical device was modified or operated. PR #288 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

Mandatory release gates remain independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release approval.
