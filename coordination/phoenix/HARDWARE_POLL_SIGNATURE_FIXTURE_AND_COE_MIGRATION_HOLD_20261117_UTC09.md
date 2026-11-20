# PHX-MASTER — legacy poll-signature fixture conflict and COE migration hold

**Checkpoint:** 2026-11-17 UTC09  
**Role:** PHX-MASTER  
**Status:** BLOCKED / PRODUCTION NO-GO  
**Scope:** `coordination/phoenix/` only; no subsystem source edits

## Live refs read for this activation

| Ref | Exact head |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments active development `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Experiments older `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| HARDWARE PR #315 | `84fe6b790139d147f330f13a40b3ae3e89a7042d` |
| HARDWARE separate PR #316 | `888e6941e3a7a81641682c23d937f97d8117d2ea` |
| PHX-MASTER PR #288 before this commit | `47f2f6e9107f58902396d5731cfcd77b80598eb5` |

There is no branch literally named `development`; the v0.6 audit-foundation ref is the active development line referenced by cleanup/control-plane handovers. The older v0.5.3 development ref is retained as a separate historical branch.

The live `OWNERSHIP_ROUTES.json` blob is `e4db324315a1b3543fec17a148fbf960170fcb29`; it remains `DRAFT_REVIEW_ONLY`, pinned to source main `f4e8a891...` and COE PR #26 `b382d233...`. It was not changed.

## New exact-head finding: the Full failure is a stale positive-poll test oracle

At HARDWARE PR #315 head `84fe6b790139d147f330f13a40b3ae3e89a7042d`, both ESP sketches deliberately implement:

- `acceptPollResponse()`: clear `insertMode` and `activeTarget`, then return DENY unconditionally.
- `coinPostDispositionVerified()`: return DENY unconditionally until the CORE-owned event-bound authenticated receipt contract and QA golden vectors exist.
- `applyRemoteConfig()`: dormant definition only; response handlers do not invoke it.

This is the intended fail-closed state under Architecture Contracts §§6.3–6.6. It is not permission to reintroduce the derived `response_sig` poll formula.

The current Full run [44054778555](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054778555) failed in validation job [133941354361](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054778555/job/133941354361). Its log reaches `tests/controllers.sh`, which invokes the inherited legacy `tests/v05_firmware_hardening_test.sh`. That test's exact blob is `41211b2c110ab409f6d9d1812ef12fda73b13211` (mode `100755`); the wrapper blob is `f7896647713d6bf8034ff48ed19b6383e4dedea0` (mode `100755`). The test still requires `grep -q '|poll|'` and simulates the old positive `response_sig` construction. The failing log reports **“Missing poll signature check in ESP8266.”**

Neither test file is in PR #315's changed-file list. They are inherited from its base stack; PHX-MASTER did not modify them. The separate `v060_esp_poll_intake_guard.py` extractor omission reported by PHX-HARDWARE remains a secondary QA issue and was not reached by this run.

**Interpretation:** the Full workflow is genuinely FAILED, but the immediate failing assertion conflicts with the current default-deny contract. Do not restore positive poll admission to make this legacy test green. PHX-QA must replace the stale positive-signature assertion with source-linked negative cases that prove the current denial behavior on both boards, and retain positive acceptance cases as blocked until CORE publishes the canonical contract.

## Exact source/destination firmware provenance

Both recursive Git tree responses were complete and non-truncated.

| Board | HARDWARE #315 source blob | COE #26 destination blob | Mode |
|---|---|---|---|
| ESP32 | `c3833a0236a77d387c11a72fcf9776a1eff26f2a` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | `100644` / `100644` |
| ESP8266 | `77c403adab3730e4b12da4f42c5e90b34562f9b6` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | `100644` / `100644` |

The blobs differ on both boards. Current #315 includes the durable `/pending.attempt` gate, default-deny poll and coin disposition helpers, dormant remote configuration, and quarantine evidence preservation. COE #26 still stages the older response-driven configuration paths (three `applyRemoteConfig` occurrences and two `sigOk=true` defaults per sketch), lacks the current attempt/disposition helpers, and retains the HTTP-200 quarantine-clear/delete path. No file was copied or overwritten.

## Test identity and import completeness

- Current #315 changed files include board-local source labs for poll response, register/config denial, coin POST gating, attempt marker, pending-journal recovery/write-readback and quarantine readback.
- COE #26's `Hardware/tests/` tree contains only `Hardware/tests/test_firmware_hardening.sh`, blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`, mode `100755`.
- The source legacy v0.5 test blob `41211b2c...` and current source-extracted lab blob `4a627a44f5e7686a28b3fb4d4582290b1dedb02e` are not imported as matching test identities in COE #26.

The source tree has root `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` and BlazePwifi `LICENSE` blob `1ee55b94183417be977ca287cd7391f9a6f7e721`. COE #26 contains `Pisowifi/LICENSE` with that same license blob, but no root `NOTICE.md` and no Hardware-local LICENSE/NOTICE in the inspected tree. Hardware license/notice coverage therefore remains **OWNER REVIEW**, not presumed covered or legally resolved.

## Exact-head CI and role snapshot

- HARDWARE #315 focused [44054778537](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054778537): SUCCESS, quarantine-source job `133941208330`. This is a focused quarantine lab, not a poll-admission or physical test.
- HARDWARE #315 Full [44054778555](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054778555): FAILURE at validation job `133941354361`; returned ESP32/ESP8266 and other target builds passed, while production import/sign/publish jobs were skipped.
- HARDWARE #316 `888e6941...`: focused `43972511337` SUCCESS; Full `43972511250` FAILURE (separate draft; do not compose independently).
- HARDWARE #314 `556adc20...`: BlazePwifi build `43782088731` and focused quarantine lab `43782088748` SUCCESS.
- CORE #252 `c82705f2...`: scoped build `42698139210` SUCCESS; CORE source remains owned by its separate continuation.
- RENTAL #289 `68928774...`: `43653329235` and `43653329229` SUCCESS.
- PISONET #255 `d01fd164...`: Windows run `42462978704` SUCCESS.
- QA #292 `75a3f66d...`: no PR-triggered runs; QA #290 `5c29d159...` run `43633486963` SUCCESS; QA #267 `ff536799...` run `41452247439` SUCCESS; QA #279 `8f476ef0...` no runs returned.
- RELEASE #291 `2c4edff2...`: scoped Windows run `43744993487` SUCCESS.
- COE #26 `b382d233...`: five candidate workflows remain QUEUED (`43096752609`, `43096752632`, `43096752800`, `43096752563`, `43096752557`). COE #29, #30, #31, #32, #28 and #24 each have their listed scoped successes; none proves combined #26 acceptance.

PHX-MASTER's 15/15 checks this activation were bounded static assertions against GitHub-readback source/test/tree content. They are **not** Python unit tests, source-extracted hardware labs, or CI. The complete Master Python suite was not executed, and no exact-head PR #288 workflow run was returned.

## Next owner actions

1. **PHX-QA:** update the inherited v0.5 positive poll-signature check and the separate v0.6 extractor to test current default-deny behavior without restoring the unapproved formula; run Full at the exact current #315 head and report exact job/log evidence.
2. **PHX-CORE:** publish the canonical poll authorization/receipt producer-consumer contract, freshness and replay semantics, and positive/negative golden vectors. CORE implementation remains outside PHX-MASTER.
3. **PHX-HARDWARE:** preserve the fail-closed source candidate and provide a new exact-head focused poll lab after QA's test contract is repaired.
4. **COE integration owner:** keep #26 draft; reconcile both firmware blobs, all missing source test identities, license/NOTICE coverage and combined candidate CI before any per-file migration proposal.
5. **Registry custodian:** restore authorized access to the exact private Drive v11 registry and newer corrections. No older Library snapshot is substituted.

No merge, release, signing, secret provisioning, hardware flash, physical test, financial migration or live-payment operation occurred. **PRODUCTION NO-GO.**
