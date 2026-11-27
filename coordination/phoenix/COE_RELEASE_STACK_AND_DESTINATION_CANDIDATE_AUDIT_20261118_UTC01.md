# COE release stack and destination candidate audit

**As of:** 2026-11-18T01:33:01Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, provenance and integration matrices only.  
**Disposition:** OPEN / DRAFT / BLOCKED / PRODUCTION NO-GO.

## 1. Exact repository and candidate refs

| Repository / ref | Exact SHA | State |
|---|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | default branch |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` | separate; not promoted |
| Experiments PHX-MASTER #288 | `583a2053cc29825b63ead1b614192331d78fd730` | OPEN / DRAFT |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | default branch |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT |
| COE Hardware/Shared #27 | `009f70cc2c2775039a5fb072c9d4fdedee76cfc7` | OPEN / DRAFT |
| COE Release #31 | `20e75fc0e6fb7e7ada560a9ec41cb9695d198fa8` | OPEN / DRAFT |
| COE Release child #35 | `61e2d8ef77e5cd3740ab9e630e5bfcc1994b7d09` | OPEN / DRAFT; nonmergeable |

PR #288 base remains Experiments main at `f4e8a891...`; its remote branch HEAD and PR head both read `583a2053...`. COE #26 base remains COE main at `a6513ab4...`.

## 2. COE #31 — exact mandatory sandbox outcome

Current COE #31 head `20e75fc0...` has three exact-head workflow results:

| Run | Workflow | Result |
|---|---|---|
| [44213707995](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213707995) | Mandatory ImageBuilder sandbox | FAILURE / fail-closed |
| [44213709669](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213709669) | Shared contracts, firmware and packaging | SUCCESS, scoped |
| [44213707845](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44213707845) | Case-collision guard | SUCCESS, scoped |

Sandbox job `134498145987` installed bubblewrap 0.9.0, passed all seven host-preflight unit tests, passed the non-root UID/GID checks, and then failed at the real namespace capability probe:

```text
RELEASE-BLOCKED: required unprivileged bubblewrap user namespace is unavailable
bwrap: setting up uid map: Permission denied
exit code 125
```

The required packaging regressions were **SKIPPED** after the fail-fast preflight. This is a hosted-runner user-namespace capability failure, not a packaging-regression pass and not a product test failure. The fail-closed behavior is correct: no privileged mapping or unsandboxed fallback was attempted. The two ESP compile jobs and shared validation passed, but they do not replace the mandatory sandbox gate.

## 3. COE #35 — stale stacked Release candidate and missing mandatory sandbox run

PR #35 branch `phoenix/release-build-script-publication-safety-20261117` is based on the historical COE #31 head `7bdba18b86f706d7fb96831094338600e28cc9c5`, not current #31 `20e75fc0...`.

Exact compare current #31 → #35:
- status: **DIVERGED**
- #35: 2 commits ahead / 7 commits behind
- mergeable: false
- changed paths overlap the Release parent in `tools/package_appliance_firmware.py` and `tools/test_package_appliance_firmware.py`.

Exact #35-head runs returned:
- [44180549932](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44180549932) case-collision guard: SUCCESS.
- [44180549950](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44180549950) shared contracts / firmware / packaging plus ESP32 and ESP8266 compile jobs: SUCCESS.

**No mandatory ImageBuilder sandbox run was returned for #35.** The current `release-imagebuilder-sandbox.yml` pull-request trigger is restricted to base branch `integration/ecosystem-nonproprietary-candidate-20261111`; its push trigger is restricted to branch `phoenix/release-imagebuilder-failclosed-20261115`. #35 targets the Release branch and pushes to its own child branch, so neither automatic trigger covers it. `workflow_dispatch` exists, but no manual exact-head run was found.

Owner action: PHX-RELEASE must reconcile #35 onto the current #31 head (or explicitly supersede it), and ensure the mandatory sandbox workflow is run on the exact resulting head through an authorized trigger/dispatch. Do not infer that the two scoped green runs establish sandbox acceptance. PHX-MASTER did not rebase or modify Release source.

## 4. COE #27 versus #26 — separate destination candidate, not integrated

COE #27 is based on COE main, not #26. Compare #26 → #27 reports **DIVERGED**, 3 commits ahead / 83 behind, merge base `45639579ecadc23f240763593d3776d67c4ca428`. The PR metadata reports mergeable true, but the compare result is not a fast-forward integration and does not prove admission into #26.

Exact firmware blob identities:

| File | COE #26 | COE #27 | Experiments #283 | Experiments #317 |
|---|---|---|---|---|
| ESP32 | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | same | `d86d94568c0de9a5be6648e8d83c219a9cc58c62` | `067c79405a6eb81a6c0b292b858191d3a131ed4f` |
| ESP8266 | `c8be98f72596681e36a3ad1f8939bf8046c96887` | same | `710572a1aae661cfa7ba3936f2170f921200150e` | `2f6dce596368d74f51aa6ab6a66b6dde875511c1` |

#27 therefore repeats the same two firmware blobs already staged in #26; it does not supply the current Experiments #283 or #317 firmware. Its available exact-head runs [43079646393](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646393) and [43079646264](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646264) are scoped CI only. COE #26 still has five queued workflows (43096752609, 43096752632, 43096752800, 43096752563, 43096752557) and zero jobs returned. No combined integration acceptance exists.

Keep #27 and #26 separate. Do not copy, move, cherry-pick or merge based on matching two file blobs alone; all other file/test/license/import identities and exact destination CI remain required.

## 5. Current Experiments Hardware and role evidence

| Owner PR | Exact head | Exact-head CI / status |
|---|---|---|
| HARDWARE #283 | `e8c6619ba97aa7ba1152e4c78b786842f7fa9180` | 44203456152 and 44203456142 SUCCESS; scoped software/target evidence |
| HARDWARE #314 | `556adc20ef0cfd355089aff3b979c0169af79bdd` | 43782088731 and 43782088748 SUCCESS; scoped |
| HARDWARE #315 | `84fe6b790139d147f330f13a40b3ae3e89a7042d` | 44054778537 SUCCESS; 44054778555 FAILURE |
| HARDWARE #316 | `888e6941e3a7a81641682c23d937f97d8117d2ea` | 43972511337 SUCCESS; 43972511250 FAILURE |
| HARDWARE #317 | `fce915c1167fc43c6936f3594ae9efce376b711f` | 44209812693 and 44209812920 focused SUCCESS; Full 44209812745 FAILURE at QA-owned `Missing poll signature check`; all 14 target builds passed; compatibility simulations skipped |
| HARDWARE #318 | `696e28ed4cd53b9189b78095b38aee973d774683` | no current-head CI returned; mergeable=false |
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | 42698139210 SUCCESS, scoped; separate CORE automation owns source implementation |
| RENTAL #240 / #287 / #289 | `a7d113fb...` / `a4fffd01...` / `68928774...` | 40910311141/40910311159; 43754089203; 43653329235/43653329229 SUCCESS, scoped |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | 42462978704 SUCCESS, scoped; native COM acceptance UNKNOWN |
| QA #267 / #290 / #292 | `ff536799...` / `5c29d159...` / `75a3f66d...` | #267 41452247439 SUCCESS; #290 43633486963 SUCCESS; #292 no current-head runs returned |
| RELEASE #291 | `a74b8b940fba3aa8651f1a9ee8bbf23cf112726e` | 44199987756 SUCCESS, scoped; signing/publishing not authorized |
| COE #28 / #29 / #30 / #32 | `b21b0461...` / `d0830332...` / `4897348d...` / `29b6fe08...` | 43632393888; 43653906676/43653906675; 43653415598; 43653540607 SUCCESS, scoped |

The #317 poll-signature fixture remains QA-owned. Preserve firmware default-deny; do not add positive unauthenticated poll admission to satisfy the legacy assertion. #283/#317/#318 remain separate candidates pending HARDWARE stack direction and QA exact-SHA review.

## 6. Ownership, registry and validation boundaries

- `coordination/phoenix/OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, pinned to Experiments main and COE #26; PHX-MASTER destination remains null.
- Experiments root `AGENTS.md` was read at blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`. Its canonical cloud artifact policy and storage handover were read from `BlazeDevStudio/BlazingSystems` main (policy blob `5e503925750c4e511314e4b7624579d82f60aae2`; handover blob `a15f14cb3baf46424b820e1a921462794422f06b`). Both require the private canonical registry/sync ledger before artifact operations.
- COE root `AGENTS.md` returned 404; no alternate file was assumed.
- The connected GitHub surface has no Google Drive connector action. Library search surfaced only older registry snapshots and a 2026-11-09 checkpoint, not canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` or newer corrections. No older registry was substituted; no private IDs or contents were copied to GitHub. Drive registry verification and any artifact operation remain BLOCKED.
- Master #288 has no PR-triggered workflow run returned. The full Master Python suite was not executed. This report is source/tree and exact GitHub Actions metadata/log inspection, not a Master test-suite pass or hardware acceptance.

## 7. Exact next owner actions

1. **PHX-RELEASE:** reconcile #35 with current #31 head and run the mandatory sandbox workflow on the exact resulting head; keep packaging regressions skipped until the approved namespace boundary is available.
2. **Infrastructure owner:** provide an authorized disposable, ephemeral, no-secret runner supporting unprivileged user namespaces. No privileged mapping or unsandboxed fallback.
3. **PHX-RELEASE + PHX-CORE:** define and implement durable site-scoped RFC 4193 ULA provisioning; current packager still emits invalid placeholder `fd00:db8:blaze::/48`. Do not guess a replacement prefix.
4. **PHX-HARDWARE + PHX-QA:** declare the authoritative #283/#317/#318 sequence; replace the stale positive poll-signature fixture with source-linked default-deny regressions and verify the exact selected source/test SHA.
5. **COE integration owner + HARDWARE + QA:** reconcile #27/#26 and current Experiments source/test/license/import identities before any destination change.
6. **Registry custodian:** restore authorized read-only access to canonical Drive v11 and newer corrections.

**No subsystem source branch was modified. No destination file was moved/copied/overwritten/deleted. No migration, merge, release, signing, secret provisioning, hardware flash, physical test or real-payment operation occurred. PRODUCTION NO-GO.**
