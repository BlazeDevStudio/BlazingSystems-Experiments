# PHX-MASTER — Hardware/QA/COE staging and release CI reconciliation

**Checkpoint:** 2026-11-17T23:38:30Z
**Role/task:** PHX-MASTER · #172 / #266 / #288 / #283 / #317 / #318 / #291 / COE #26 / #31
**Disposition:** coordination-only; P0 owner review required; **PRODUCTION NO-GO**.

## Authority and exact repository state

- Re-read the uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`, latest Library copies `README_FIRST(20261114-191926).md` and `COMMUNICATION_PROTOCOL(20261114-191925).md`, live Experiments `AGENTS.md`, control-plane #172, cleanup-first #266, PR #288, the role/ownership routing manifest, relevant role PRs/CI, COE main and #26/#31.
- Experiments root `AGENTS.md` requires restricted Drive registry/manifest/ledger readback before artifact work and says missing access must be reported as BLOCKED. COE root `AGENTS.md` returned 404; COE main README contains only its heading.
- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. Development `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`; it remains separate.
- Master branch `phoenix/master-coordination` before this commit: `a6f8406472f0227d86613c75f5d44c46476c95ec`. Existing PR #288 is OPEN/DRAFT against main; 64 pre-audit changed paths, all under `coordination/phoenix/`; no PR-triggered workflow runs were returned for that head.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`. COE integration #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT. COE RELEASE #31: `7bdba18b86f706d7fb96831094338600e28cc9c5`, OPEN/DRAFT.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, 11 routes; PHX-MASTER remains coordination-only with `target: null`. No route change is justified.
- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed Drive connector or Library. Library search surfaced a 2026-11-09 checkpoint that references v11, not the canonical registry or a newer correction. No older registry was substituted and no private contents/IDs were published.

## Live role/CI reconciliation

| Owner / candidate | Exact head | Exact evidence and disposition |
|---|---|---|
| PHX-CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Scoped CI `42698139210` SUCCESS; separate hourly CORE automation retains implementation ownership. No CORE branch changed. |
| PHX-RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | Runs `43653329235` and `43653329229` SUCCESS, scoped only. |
| PHX-PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Run `42462978704` SUCCESS, scoped; native COM acceptance remains UNKNOWN. |
| PHX-HARDWARE #283 | `83646f309a84f3f0de9c1af6dac2c7ee08b61c85` | Exact-head run [44182715006](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44182715006): validation, ESP32/ESP8266, 14 target/platform jobs, Android, simulations and candidate gate SUCCESS; production import/sign/publish skipped. Two new source-extracted labs are not invoked by the workflow. |
| PHX-HARDWARE #317 | `a166f91d6c790aa81ff98794038d76b39bc6562d` | Focused relay [44193392313](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44193392313) and quarantine [44193392314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44193392314) SUCCESS. Full [44193392383](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44193392383) fails in QA-owned `tests/controllers.sh` at `Missing poll signature check`; all 14 target builds passed. Preserve firmware default-deny; do not restore positive poll admission. |
| PHX-HARDWARE #318 | `696e28ed4cd53b9189b78095b38aee973d774683` | No current-head CI returned; PR reports `mergeable=false`. Exact compare with #317 is DIVERGED: #318 is 51 commits ahead and #317 is 68 ahead; merge base `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`. |
| PHX-QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 run `43633486963` SUCCESS, scoped. #292 has no current-head CI returned; independent current-Master regression verification remains requested. |
| PHX-RELEASE #291 | Current PR head `a74b8b940fba3aa8651f1a9ee8bbf23cf112726e`; source/test head `4d36160ccffb7bee34aa713bc896be33e355646d` | Exact source/test run [44199068618](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199068618) SUCCESS. Final docs-only head run [44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756) is IN_PROGRESS. Signing and write-privileged publisher are skipped in PR validation; this is not a signed release. |
| PHX-RELEASE #242 | `734b89d9e7792247e8376335c3f3685500ab3f89` | Existing scoped release candidate; no production authorization inferred. |
| COE RELEASE #31 | `7bdba18b86f706d7fb96831094338600e28cc9c5` | Shared/hardware [44179122507](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44179122507) and case guard [44179122882](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44179122882) SUCCESS. Mandatory sandbox [44179122674](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44179122674) fails at hosted unprivileged UID-map setup; sandbox regressions are not executed. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five PR-triggered workflows remain QUEUED with zero jobs: `43096752609`, `43096752632`, `43096752800`, `43096752563`, `43096752557`. No combined acceptance. |

## Exact Hardware source and destination blob comparison

All four trees were read recursively at their exact PR heads. Firmware blobs and executable modes were compared, not inferred from PR descriptions.

| Artifact | #283 | #317 | #318 | COE #26 destination |
|---|---|---|---|---|
| ESP32 sketch | `91e2add2635d18228065a96a6dd1e3db3409c43a` | `067c79405a6eb81a6c0b292b858191d3a131ed4f` | `7a24b1b643aa90c0056b5f7634d3c67e3ecb5a34` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` |
| ESP8266 sketch | `dd91ae49abeb675015c8fae38e096156170a2e96` | `2f6dce596368d74f51aa6ab6a66b6dde875511c1` | `ebd1572cf82cd1c6ef2c5afbb7b4075533697440` | `c8be98f72596681e36a3ad1f8939bf8046c96887` |
| `tests/controllers.sh` | `0f73e9024b98cfe5c6cc131f70a58cf50375d0fe` | `f7896647713d6bf8034ff48ed19b6383e4dedea0` | `f7896647713d6bf8034ff48ed19b6383e4dedea0` | `Pisowifi/tests/controllers.sh` ABSENT |

All three source ESP32 and ESP8266 blobs differ from one another and from the COE destination. #283's `controllers.sh` is mode `100755`; #317/#318 share a different `100755` blob. COE #26 instead has `Hardware/tests/test_firmware_hardening.sh` blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`, mode `100755`; it is not the routed source test and still asserts `response_sig`, `|poll|`, and `/quarantine/clear`. This is not import-equivalent coverage for the current default-deny source.

PR #283 contains two additional source-extracted host labs: `littlefs_mount_failclosed_lab.py` blob `8b63f8ec93111167f23ce5c89c9421228fc1e82a` and `quarantine_clear_deny_lab.py` blob `e09b3b76d07eb011890833bcf0e236903c0832e9`. Both are absent from #317, #318 and COE #26. Source workflow `.github/workflows/blazepwifi-build.yml` blob `2cd6ce83b01c65fd78df091e502b68bf4fd277dc` does not invoke either lab. Therefore #283's green workflow does not prove these two lab cases. PHX-HARDWARE's PR #283 checkpoint explicitly requests PHX-QA to wire and run both at the exact current head.

Pairwise current-head comparisons:
- #283 vs #317: DIVERGED; #317 is 277 commits ahead of #283 and #283 is 13 commits ahead of #317; merge base `a87567291e80006f3f30cea81fc20e8b299b95e8`.
- #283 vs #318: DIVERGED; #318 is 260 commits ahead of #283 and #283 is 13 commits ahead of #318; same merge base `a87567291e80006f3f30cea81fc20e8b299b95e8`.
- #317 vs #318: DIVERGED; #318 is 51 commits ahead and #317 is 68 commits ahead; merge base `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`.

Keep #283/#317/#318 as separate drafts. The no-autoformat LittleFS invariant is already present in the #317/#318 source; #283 aligns a separate branch and is not a new project-wide fix. No automatic stack composition, rebase, cherry-pick, force-push or merge is safe.

## COE #26 source-intake, license, workflow and test-identity gaps

- `Pisowifi/SOURCE_INTAKE.json` is blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`, schema 8, and pins historical Experiments source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00`, not current #283/#317/#318. It records 61 original rootfs files, 47 byte-identical and 14 locally derived; four original tests and 15 derived tests. It explicitly sets `release_authorized=false`, `hardware_tested=false`, `full_ci_tested=false`, and `source_admission_complete=false`.
- `Pisowifi/MIGRATION_MAP.md` is blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` and describes the same older source snapshot. These documents do not establish current Hardware candidate import completeness.
- Source product MIT license `experiment/openwrt/BlazePwifi/LICENSE` blob `1ee55b94183417be977ca287cd7391f9a6f7e721` equals COE `Pisowifi/LICENSE` at the same blob. However COE #26 has no `Hardware/LICENSE`, `Hardware/NOTICE.md`, root `LICENSE` or root `NOTICE.md`; source Experiments root `NOTICE.md` exists at blob `f6d92cd21465312be5993631fe26977219be0fb9`. The sibling Pisowifi license does not by itself establish Hardware subtree license/notice placement. Legal applicability and attribution mapping remain unresolved.
- Source `.github/workflows/blazepwifi-build.yml` and destination `.github/workflows/pisowifi-ci.yml` differ (`2cd6ce83...` vs `cf18705f...`). The routing manifest correctly marks the workflow as `reimplementation-review`; it is not a byte-copy candidate.
- COE #26 remains a staging candidate, not a completed migration. Refresh its source intake and migration map only after HARDWARE selects an exact source/test stack and QA verifies test identities. Do not overwrite the staged Hardware code or copy current candidate files into #26 during this hold.

## Master checks and limitations

- Bounded exact-tree, blob, mode, manifest, intake, workflow-coverage and CI-state assertions: **26/26 PASS**. These checks validate Git metadata and observed run states; they are not firmware runtime tests.
- Existing GitHub Actions evidence above was read at exact current heads. No new CI workflow was triggered by Master.
- Master PR #288 had no PR-triggered workflow runs at its pre-audit head. The full Master Python suite was NOT RUN.
- No native hardware, coin acceptor, router, filesystem, relay, physical power-cut or 30-device soak test was performed.
- The private v11 registry read remains BLOCKED; no registry-dependent archive/migration action was attempted.

## Owner actions

1. **PHX-HARDWARE:** publish one explicit authoritative sequence among #283/#317/#318, with exact base/head and source/test identities; refresh the selected handover. Keep all drafts separate until the decision is independently reviewable.
2. **PHX-QA:** review #283's QA-owned `tests/controllers.sh` changes; wire and execute both #283 source-extracted labs at exact head; correct #317's stale positive `Missing poll signature check` fixture to test the intended default-deny behavior, not to re-enable positive poll admission.
3. **PHX-RELEASE:** finish and classify docs-head run #44199987756 for #291; retain signing/publisher skips in PR CI. Keep COE #31 sandbox blocked until an authorized disposable no-secret runner supports unprivileged user namespaces.
4. **COE integration owner:** after Hardware/QA selection, refresh `SOURCE_INTAKE.json` and `MIGRATION_MAP.md` against the selected current exact source SHA, record Hardware test identities/modes, and resolve Hardware LICENSE/NOTICE placement before any import. Re-run all five queued #26 workflows.
5. **Infrastructure owner:** provide an ephemeral, disposable, no-secret namespace-capable runner for the #31 bubblewrap boundary tests; do not add sudo, broad subordinate-ID mappings or an unsandboxed fallback.
6. **Registry custodian:** restore authorized read access to the canonical private Drive v11 registry and newer corrections; until then Master keeps registry-dependent work BLOCKED.

No destination file was moved, copied, overwritten or deleted. No subsystem source branch was edited. No merge, release, signer provisioning, secret access, firmware flash, physical test, customer payment or financial migration occurred. **PRODUCTION NO-GO.**