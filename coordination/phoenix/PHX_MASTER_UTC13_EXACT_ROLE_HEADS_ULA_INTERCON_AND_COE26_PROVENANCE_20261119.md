# PHX-MASTER UTC13 — exact role heads, ULA authority, INTERCON routing and COE #26 provenance

**Date:** 2026-11-19T13:42:22Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** `coordination/phoenix/`, architecture/interface contracts, role/CI reconciliation, cross-repository provenance and integration matrix only. No subsystem source ownership taken.

## 1. Exact repository refs and coordination state

| Reference | Exact live ref |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments current development reference | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy development branch still present | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master branch | `phoenix/master-coordination@d52d346e51d135615833f4f843204b36e0f78a99` (starting head) |
| COE default branch | `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration #26 | `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12` |

Experiments and COE default branches are both `main`. PR #288 is OPEN/DRAFT at the starting Master head with 103 changed paths, all under `coordination/phoenix/`; no Master PR-triggered workflow run returned. Cleanup #266 remains OPEN. The current role routing manifest is blob `e4db324315a1b3543fec17a148fbf960170fcb29`, valid JSON, `DRAFT_REVIEW_ONLY`, destination candidate #26, PHX-MASTER destination null.

## 2. Exact role PR and CI reconciliation

| Role | Current draft / exact head | Exact-head evidence |
|---|---|---|
| PHX-CORE | Experiments #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS, scoped only. The separate CORE continuation owns implementation; no competing CORE task was started. |
| PHX-RENTAL | Experiments #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235), [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) PASS, scoped only. |
| PHX-PISONET | Experiments #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS, scoped only. COE #28 `b21b04617d38a177260258de2d56b24382822117` [43632393888](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43632393888) PASS; #30 `4897348d94a0cf7884ecd53244bfcd59e7bf2fbc` [43653415598](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598) PASS. |
| PHX-HARDWARE | Experiments #327 `bba3ba4ec42904247fdbdabb5719d03a1f6545cc`, base #326 `58c558fb6a237935214621adc3dee65a10fe1a51` | Quarantine [44535332759](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44535332759) PASS; relay [44535332462](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44535332462) PASS; Full [44535332457](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44535332457) FAIL at QA-owned `Missing poll signature check`. Thirteen firmware/platform targets and Android pass; downstream simulation/update/signing/publishing skip. Focused test/workflow commit `ef541fc5a37296f9c39a7b5351e87c54db098f6e`. |
| PHX-QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS, scoped only. #292 has no current-head run. QA owns replacing the obsolete positive poll fixture with source-exact negative/default-deny assertions. |
| PHX-RELEASE | Experiments #291 `10b2de74f108cb6ae70d34a83b3599cf5038b687`, base #242 `734b89d9e7792247e8376335c3f3685500ab3f89`; source/test head `69619210865259918ed74e081427ba960539af7a` | ESP32 compatibility [44532306237](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44532306237) PASS on cores 3.3.13 and 4.0.0 using source commit `984ea8ff65a9` and sketch blob `528187f68aaad7d76a690bbf1cbe338165ad3839`, identical to current #327 ESP32 sketch bytes. BlazePwifi [44532306202](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44532306202) PASS, including validate/platform and simulation jobs; signer/publisher skipped. Windows [44532306579](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44532306579) FAIL at PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is uninitialized; publisher skipped. #291 diff contains three CORE handover files and two PISONET test files; owner review is required. |

PR #327's description still names an older API head (`47eceaf...`) while the live API head is `bba3ba4...`; PR #291's description similarly names an older head (`63f9952...`) while its live API head is `10b2de74...`. The owners should refresh their PR descriptions/handover pointers. Master records API heads and does not edit subsystem files.

## 3. COE release and receipt candidates

- COE #26 is OPEN/DRAFT at `b382d233...`, 205 changed files, five workflows queued with zero jobs.
- COE #31 is `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 is `5047af8b5a8296e06294bbda6bf42a6baea2294d`. #35 shared/firmware [44465377784](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465377784) and case [44465377781](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465377781) PASS. Mandatory sandbox [44465377807](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465377807) FAILS CLOSED because Bubblewrap is absent (exit 125) after 14/14 host-preflight tests; no unsandboxed fallback.
- COE #44 is OPEN/DRAFT at `582fd5d5e83e36b36546ac28534740298ba94af4`, `mergeable=false`, diverged from #35 by 15 ahead / 25 behind. Shared/case checks pass; sandbox [44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) fails closed because Bubblewrap is absent.
- COE #45 is `9d76a134c1f6512aa40c20ec4d247306a71a8cce`; case [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) and synthetic Pisowifi receipt-v1 shell suite [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) pass. These are synthetic contract vectors, not durable ledger authority or v2 financial migration evidence.

### ULA site-authority decision remains open

COE #44's `generate_ula_firstboot_script()` samples a fresh random 40-bit Global ID per appliance installation and persists a local `network.globals.ula_prefix`. Its tests validate local first-boot provisioning and UCI behavior, not same-site multi-appliance distribution. Master Architecture Contract §6.9.1 already states that installation identity is the LAN/site boundary: appliances on one site must share one durable /48; different sites must be distinct; concurrent first boot and backup/restore must preserve one authority. #44 therefore remains an allocation primitive, not a site authority. CORE/COE integration must select the authority; RELEASE implements only after that decision; QA independently verifies.

## 4. COE #26 exact Hardware migration provenance

| Item | Experiments #327 source | COE #26 destination |
|---|---|---|
| ESP32 sketch | `528187f68aaad7d76a690bbf1cbe338165ad3839` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` — different |
| ESP8266 sketch | `aa021588b610f928f7af4f5fefb3f32114e6b5ae` | `c8be98f72596681e36a3ad1f8939bf8046c96887` — different |
| Board-local labs | 22 Python labs | Four Hardware files: README, two sketches, one shell test |
| Poll fail-closed lab | `69dbddee4133588940f4c5b53817401db531a8a4` | Not imported as an equivalent test |
| Generic hardening test | — | `f921c56cecc19cab1989507b9b4ade1f45dac54e` |

The destination test requires positive `response_sig`, `|register|` and `|poll|` strings. The current source poll lab compiles the production parser and asserts `acceptPollResponse()` and `coinPostDispositionVerified()` deny. These test identities are incompatible; do not add fake positive tokens or weaken firmware.

Source `BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` match at `1ee55b94183417be977ca287cd7391f9a6f7e721`. This is only the Pisowifi subtree license. Source `BlazePwifi/NOTICE.md`, destination `Hardware/LICENSE`, and destination `Hardware/NOTICE.md` return 404. Hardware license/NOTICE scope remains unresolved.

**Decision:** no copy, move, overwrite, cherry-pick, rebase, merge, staging, or route promotion. Require per-file path/mode/blob/license mapping, full source test import or reviewed equivalents, pinned toolchain on #26 itself, and runnable exact-head destination CI.

## 5. Pisonet Universal / INTERCON route boundary

COE #36 head `b4d7434764aab72673de1f496ed9e442f031ddff` is based on #26 and changes `Hardware/esp8266/BlazePisonetUniversal/` plus `Shared/contracts/pisonet-intercon/`; Stage-1 compile/shared/case runs [44226768392](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226768392), [44226768488](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226768488), [44226768389](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226768389) pass. COE #43 head `8f5eec790dc2a3e25c219a6f51651113cd1c90cd` is a separate Stage-4 candidate based on `a35672fb60228fb8f84801405d032293f0266023`; its hardware/shared, Stage-4 and case runs [44246962346](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44246962346), [44246962253](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44246962253), [44246962243](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44246962243) pass. These scoped results do not make them Phoenix SoftTimer candidates.

The unchanged ownership manifest routes only `experiment/windows/BlazePisonet-SoftTimer/` to `Pisonet/SoftTimer/`. It does not route Universal/INTERCON paths. Keep #36/#43 separate pending registry v11 and explicit product/owner scope; do not fold them into #26 or SoftTimer.

## 6. Governance, registry and execution limits

- Experiments and COE default branches are `main`. Repository rulesets endpoints return empty arrays. Classic branch-protection reads return HTTP 403 `Resource not accessible by integration`; effective protection is UNKNOWN, not proven `protected=false`. Repository administrator must verify effective required checks.
- Experiments AGENTS.md was re-read at blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`; linked Cloud Artifact Policy blob `5e503925750c4e511314e4b7624579d82f60aae2` and Cloud Storage Handover blob `a15f14cb3baf46424b820e1a921462794422f06b` were read from `BlazeDevStudio/BlazingSystems` main. COE root AGENTS.md returns 404.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were searched in the Library but not surfaced; no Google Drive connector is exposed in this runtime. No older registry was substituted and no private data was copied.
- Direct Git clone failed because the runtime cannot resolve `github.com`. Full Master Python suite NOT RUN; no Master Actions run returned. GitHub source/tree inspection and local manifest assertions are not a substitute for the full suite.

## 7. Local assertions and safety disposition

Local checks to be run after commit: parse unchanged ownership JSON; verify DRAFT_REVIEW_ONLY and Master target null; verify all changed PR paths remain under `coordination/phoenix/`; verify exact branch/PR head readback. These are coordination/static assertions, not the Master Python suite.

No subsystem source changes. No migration. No merge, signing, release, flash, secret provisioning, real-payment operation, physical power-cut test, or soak test.

**PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.