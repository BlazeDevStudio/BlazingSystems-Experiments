# PHX-MASTER UTC06 — live owner CI, Hardware import parity and branch-governance audit

**Observed:** 2026-11-25T06:34:41Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repository provenance and integration matrices only.  
**Execution:** Strict NO CODEX. No subsystem source branch, COE destination or production system was modified.

## 1. Exact repository and control-plane state

| Reference | Exact SHA / state |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master branch / PR #288 parent | `dd63d11f34c168e8eaf2e5a533c589853203ae11` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT / UNMERGED |
| Master PR #288 | OPEN / DRAFT / UNMERGED, base `main`, 210 changed paths |
| Routing manifest | `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, Master target null |

Issue #172 remains OPEN. Cleanup issue #266 remains OPEN with zero of seven checkboxes complete, including the Master ownership/dependency/overlap inventory. A fresh PR #288 changed-filename read confirms all 210 paths remain under `coordination/phoenix/`; no path is outside Master scope.

The current root `AGENTS.md` blob is `d8777e3b58efc41caa5aa3c969c932aee9103d5f`. The linked cloud policy and handover were re-read at `BlazeDevStudio/BlazingSystems@main`: policy blob `5e503925750c4e511314e4b7624579d82f60aae2`, handover blob `a15f14cb3baf46424b820e1a921462794422f06b`. They require private-registry verification before Drive artifact work, exact readback for VERIFIED transfers, and BLOCKED/NOT_RECOVERED when access is missing.

## 2. Current role-owned PRs and exact-head CI

| Owner / PR | Current exact head | Current evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build #42698139210 PASS (older scoped evidence). CORE retains producer, durable finance and canonical handover ownership. No CORE source was touched. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK #44782114384 PASS; API #44782114393 PASS; shared build #44782114390 FAIL. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Synthetic Windows #42462978704 PASS; this is not native Windows acceptance. |
| HARDWARE #340 | `38f3e9419f37109443c806a2362577d9efc50e4d` | Six build/focused workflows #45530901795, #45530901830, #45530901893, #45530901919, #45530901824, #45530901908 PASS. |
| HARDWARE #347 | `960184670379f01e20f0e7e8bc23b3e5eedacd3f` | Quarantine #45299741995, Relay #45299742437 and build #45299741993 FAIL. |
| HARDWARE #348 | `eb7afcb2ba0d1e84054c052c8b129cb51a91d062` | Focused header #45352513178 PASS; build #45352513177 FAIL at missing `mbedtls/sha256.h`. |
| HARDWARE #349 | PR/docs `bbd3f343c952ddaab1bec210cfa342981bca742e`; source/test `61689ab4764018f3b913303b4bf508f1d04a88af` | Quarantine #45556869789 PASS; Relay #45556869915 PASS; Full #45556869883 FAIL at `Missing poll signature check` (validation job 139010921482). Fourteen target/platform + Android jobs PASS; twelve dependent stages SKIPPED. The source/test commit changes the mutation-count report in the structure guard; no production firmware sketch changed in that commit. HARDWARE's current control-plane checkpoint is #7154164374. Its PR body still pins the older `56de0761` / `f591cb85` / `dc6ef11c` tuple and must be refreshed by HARDWARE, not Master. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows #43633486963 PASS. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered runs; no pass claimed. |
| RELEASE #291 | PR/docs `8f444097d398b429bf4109bfdf3d8dc5f9746cdd`; source/test `ea8e66b9a7a2833656af984630909575fe4a1759` | Full #45560126132 FAIL at CORE-owned CURRENT_STATE freshness (job 139021759365; last checkpoint `d85eb6a2766781b6cac1807cef461993d8216b84)); Windows #45560126057 FAIL at the same handover gate (job 139021569907); ESP32 compatibility #45560126037 PASS 3/3. RELEASE's current control-plane checkpoint is #7154577602. The PR body still carries an older UTC17 summary; RELEASE owns its refresh and reruns after CORE publishes current state. |
| COE RELEASE #35 | `f611c96091a1014ad36bf64251c180bcbc2d1f65` | Shared #45541598251 FAIL; sandbox #45541598267 FAIL after 40/40 host preflight because Bubblewrap is unavailable (exit 125); case guard #45541598250 PASS. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay #44295049727 and case guard #44295049903 PASS. |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1 #44646341873 and case guard #44646341992 PASS; shared Hardware #44646341922 FAIL. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED with zero jobs. No destination CI pass exists. Keep FROZEN. |

Master PR #288 has no Actions runs at its current head. Owner CI is evidence for those exact owner SHAs only; it is not Master product testing, independent QA approval or physical acceptance.

## 3. COE #26 Hardware import — exact current-source comparison

The ownership manifest routes Hardware ESP32/ESP8266 only as `selective-review`; it does not authorize recursive copying. The current source/test ref is HARDWARE #349 source/test `61689ab4764018f3b913303b4bf508f1d04a88af`; the candidate remains COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.

| Artifact | Current Experiments source | COE #26 destination | Result |
|---|---|---|---|
| ESP32 sketch | `adfd2f110d88243d03f2195658fb456b154dcb84` (74,740 bytes) | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` (18,505 bytes) | Different blob and behavior |
| ESP8266 sketch | `8a0b458b6c7fb99c0913df16c5b4ca94dbcdc50e` (77,072 bytes) | `c8be98f72596681e36a3ad1f8939bf8046c96887` (18,394 bytes) | Different blob and behavior |
| Firmware hardening test | `41211b2c110ab409f6d9d1812ef12fda73b13211` (6,782 bytes) | `f921c56cecc19cab1989507b9b4ade1f45dac54e` (4,118 bytes) | Different test identity; coverage parity not established |

Exact destination source inspection at #26 head found:

1. ESP32 uses `LittleFS.begin(true)` (format-on-mount-failure); current source uses `LittleFS.begin(false)` and retains a journal-recovery deny latch.
2. ESP8266 explicitly calls `LittleFS.format()` after mount failure; current source does not auto-format.
3. Destination `quarantinePending()` clears pending state after the append attempt without proving durable append success. Current source requires the durable attempt marker and successful append before `clearPending()`.
4. Both destination `/quarantine/clear` handlers remove `/quarantine.log` and return success without an authenticated recovery contract. Current source preserves unpaid-coin evidence.
5. Destination register/poll paths initialize `sigOk=true` and only verify inside the non-empty-key branch, so an empty key bypasses response-signature verification. Destination also calls `applyRemoteConfig()` from register/poll responses; current source has only the function definition and no call sites.

The current candidate PR description claims response-signature verification and quarantine endpoints; the exact destination code does not satisfy the required fail-closed behavior.

### SOURCE_INTAKE, tests and licenses

- `Pisowifi/SOURCE_INTAKE.json` schema 8, blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`, pins historical Experiments source `6d4c9b487af4d768c4d7627654d119417fcc6e00` and historical destination pre-manifest head `cf59b41e5273bcc42acf59a7971481670e4b2611`. It is a PisoWiFi runtime manifest, not a Hardware intake.
- Its 61 runtime rows declare 47 byte-identical / 14 derived; exact Git-blob recount is 46 identical / 15 derived.
- Four primary test rows: two exact (portal/security) and two derived (config/integration). Fifteen additional derived tests are listed; several remain NOT_RUN or PENDING_CI_RUN. `hardware_tested=false`; `full_ci_tested=false`.
- Source project LICENSE and `Pisowifi/LICENSE` match exactly at blob `1ee55b94183417be977ca287cd7391f9a6f7e721`. Source root `NOTICE.md` has no destination counterpart; the source Tabler license also has no Hardware destination counterpart. COE root `LICENSE` and root `NOTICE.md` are absent.
- No Hardware-specific SOURCE_INTAKE or MIGRATION_MAP exists. Five #26 workflows remain QUEUED with zero jobs.

**Admission:** FROZEN. Require a Hardware-specific per-file source/destination map at current exact SHAs, explicit test identity and toolchain mapping, license/NOTICE disposition, owner review and terminal exact-head destination CI before even proposing reversible staging. No copy, move, overwrite, cherry-pick, rebase or merge occurred.

## 4. Branch governance, registry and execution limits

- Experiments main, development and COE main branch metadata each report `protected=false`. Repository rulesets reads returned empty arrays. Effective classic protection was not independently established. No protection setting was changed.
- The private canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were NOT RECOVERED. No Google Drive connector surfaced in the available connected tools. Library search surfaced a separate November 9 checkpoint and older v5-v7 registry snapshots only; none was substituted. No private registry data or IDs were published.
- An ordinary `git ls-remote` attempt failed because this runtime could not resolve `github.com`. No authenticated local checkout was available. Master Python tests and `verify_coordination.py` were NOT RUN. Exact-head owner Actions were inspected separately; no Master Actions run exists.

## 5. Owner actions / next exact steps

1. HARDWARE refreshes its own #349 PR description to source/test `61689ab` and docs/PR `bbd3f343`, preserving the Full failure.
2. CORE publishes the authenticated register/poll response contract and refreshes canonical `CURRENT_STATE.md`; Master does not edit CORE files.
3. QA independently reconciles the `Missing poll signature check` assertion and approved positive/negative vectors against the same pinned source SHA.
4. RELEASE refreshes #291's PR body and reruns Full/Windows only after CORE publishes the current handover.
5. COE integration owner keeps #26 frozen and creates Hardware-specific per-file provenance, test identity, license and CI mapping before any staging proposal.
6. Registry custodian restores authorized access to private v11 and newer corrections; do not substitute older snapshots.
7. Repository administrator reviews required branch protection/ruleset enforcement.
8. Master continues the #266 ownership/dependency/overlap inventory; the Master checkbox remains unchecked.

## 6. Final safety disposition

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

No subsystem source branch, COE destination, shared CORE handover, signer, secret, financial state, release artifact, device, payment system or customer data was modified or operated. No merge, release, flash, physical test, provisioning or financial migration occurred.
