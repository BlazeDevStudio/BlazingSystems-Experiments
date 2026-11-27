# PHX-MASTER — exact-head role/CI and registry evidence matrix (2026-11-16 UTC04)

**Status: DRAFT / PRODUCTION NO-GO.** Source-grounded coordination only; no integration authorization. This checkpoint supplements (not replaces) the existing destination zero-job triage. GitHub metadata was re-read during UTC04; do not treat these observations as immutable.

## Reproducible reference points

| Scope | Branch / PR | Exact observed HEAD | Evidence and limitations |
|---|---|---|---|
| Experiments default | main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | Historical source, not automatic migration choice |
| Experiments development | blazepwifi-v0.5.3-development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` | Distinct historical branch |
| PHX-MASTER | draft #288 / phoenix/master-coordination | `c45886f8a19dfa91b57fba6f1860e3f28e19dc26` (pre-document) | No matching PR-triggered workflow runs returned; local 18-test suite not executed |
| PHX-HARDWARE | draft #314 | `556adc20ef0cfd355089aff3b979c0169af79bdd` | Software workflows [43782088748](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088748), [43782088731](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088731) completed success; no physical acceptance |
| PHX-RELEASE | draft #291 | `2c4edff231d9b2819415086825530d80b8801307` | [43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) success; no protected signing witness |
| PHX-RENTAL | draft #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | Source branch observed; no current exact-head acceptance established here |
| PHX-PISONET | draft #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Source branch observed; no native hardware acceptance established here |
| PHX-QA | draft #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | Independent review and source-linked evidence still required |
| COE default | main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | Structure-only destination |
| COE integration | draft #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five most recent exact-head workflows remain queued: [43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632), [43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557) |

## Independent source-of-truth access gate

The private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was **not retrieved on this activation**: searches by exact basename and `name contains 'BLAZE_PROJECT_REGISTRY'` returned no matching registry item. Do not claim registry validation or invent corrections. Previous run claims are not substitutes for this activation's read. Human next action: verify the authenticated Drive connection's access to the private mirror and supply a resolvable registry file reference through the approved private channel; then compare newer corrections privately. Never paste registry identifiers/content into public issue comments.

## Migration gate and ownership

`OWNERSHIP_ROUTES.json` at the pre-document master HEAD is still `DRAFT_REVIEW_ONLY`. Its broad `Rental/` target remains explicitly non-copyable and requires per-file mapping; PHX-MASTER has no runtime destination. No source blob/license/test-identity/CI equivalence approval is inferred. Before any move, the responsible subsystem owner and independent QA must enumerate exact source and destination Git blob SHA, mode, license, dependency closure, negative-test identity, rollback plan and completed destination CI at the candidate SHA. The COE integration owner must diagnose queued workflows; PHX-MASTER must run `python3 -m unittest discover -s coordination/phoenix -p 'test_verify_coordination.py' -v` and `python3 coordination/phoenix/verify_coordination.py` in a full checkout. These commands are **not claimed executed** here.

Protected signing and independent anti-rollback witness, crash-atomic financial accounting, reversible migration, native acceptance, 150 physical power cuts, 30-device 24-hour soak, independent QA and owner authorization are unverified. No merge, release, flashing, financial migration or production admission.
