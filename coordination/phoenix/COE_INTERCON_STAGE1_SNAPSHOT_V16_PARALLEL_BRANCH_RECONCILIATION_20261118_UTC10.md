# COE INTERCON Stage-1 snapshot and parallel V1.6 branch reconciliation

**Date:** 2026-11-18 UTC10  
**Role:** PHX-MASTER  
**Scope:** coordination/phoenix only; no subsystem source edits

## Executive correction

The previous UTC10 Master checkpoint said that the COE V1.5-derived Stage-1 code had no GitHub source snapshot. That statement was too broad and is corrected here:

- COE PR #36 **does contain a GitHub staging snapshot** at head `b4d7434764aab72673de1f496ed9e442f031ddff`.
- Its staging sketch, helper header and sketch-types header are present as exact Git blobs, and the branch has successful static-contract and ESP8266 compile CI.
- What remains unverified is the staging snapshot's **lineage to the original V1.5 local attachment**. The original attachment was not found in the accessible Library search, and no matching source blob/hash has been established. The staged snapshot is not an exact import of the legacy Labs file.
- The earlier sentence in PR #36's description saying the V1.5 local firmware was not confirmed in GitHub is stale relative to its later Stage-1 checkpoint. The COE PR owner should reconcile the wording; PHX-MASTER does not edit the COE PR description.

## Exact source and destination refs

| Ref | Exact identity |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| COE Stage-1 PR #36 | `b4d7434764aab72673de1f496ed9e442f031ddff` |
| COE parallel V1.6 branch | `1e9b0269e3ed2138813fcd0c838b0034a08dfd90` |
| Experiments Master PR #288 before this correction | `c440cc066a2ffa046ce50c5bf7e4d5673d41c6d3` |

PR #36 is a draft child of #26, not content already present in #26. The separate V1.6 branch has no open PR associated with its exact head in the current open-PR query.

## PR #36: Stage-1 V1.5-derived snapshot

Exact paths and Git blobs at #36 head:

| Path | Blob |
|---|---|
| `Hardware/esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/BlazePisonetIntercon.ino` | `af622d14a9d514fbbd7df3f7b02d18bb413c93c7` |
| `Hardware/esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/InterconDiscovery.h` | `c29c728267a546c4dd700074eee8385a0e0a27f6` |
| `Hardware/esp8266/BlazePisonetUniversal/staging/BlazePisonetIntercon/SketchTypes.h` | `816450a532d10fb18a87c2aa150cd5f82f436d49` |
| `Hardware/tests/test_intercon_stage1_contract.py` | `a700b4dbf2bdaf9091d898492ae40421b45e9132` |
| `.github/workflows/intercon-stage1-ci.yml` | `d1d0cc3eb8f403f747b4498bda4c768087009f80` |

The workflow's static test explicitly describes itself as static source-contract checking, not runtime or hardware validation. It checks AP+STA presence, role defaults, bounded discovery, coin-gate denial for Master/Slave, password non-echo and preservation of pin defaults. Its compile job compiles the staging sketch for NodeMCU v2; it does not compile the legacy imported sketch.

Exact CI for #36:

- [Stage-1 static-contract + ESP8266 compile #44226768392](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226768392) — SUCCESS; both jobs completed successfully.
- [Case-collision #44226768389](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226768389) — SUCCESS.
- [Hardware & Shared #44226768488](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226768488) — SUCCESS.

These results verify the exact Stage-1 branch's bounded checks and compile only. They do not prove source-attachment lineage, authenticated pairing, durable paid-event transfer, relay electrical safety, physical coin acceptance or power-loss behavior.

## Legacy Labs import: exact one-file scope

Labs main `5d8e4f1d95b6bfc551996634df9c6f7b86af56b4` and the COE #36 legacy destination contain the same `.ino` Git blob:

`3fb15ecb9272b65500260bc7c92f05590163fa6d`

This confirms one exact archival file import. It does not confirm a complete directory migration:

- Labs `README.md` blob `7281abd6...` is absent from the COE legacy destination.
- Labs `preview.html` blob `106411cc...` is absent.
- Labs root NOTICE blob `403478d10bdaf1582fa0ab4287865d3314dc0885` is not present in the inspected COE root/Hardware tree.
- The destination parent README is a different document/blob.
- No explicit LICENSE grant was found in the inspected source/destination roots and source directory. The public-safe NOTICE is not itself a license grant.

**Disposition:** exact one-file preservation verified; complete import and redistribution rights remain unverified. Obtain license-custodian disposition before any distribution or migration.

## Parallel V1.6 branch: separate implementation and test identity

The separate branch `feature/blaze-pisonet-intercon-v1-6-apsta-discovery-20261118` is at `1e9b0269e3ed2138813fcd0c838b0034a08dfd90`. It uses a different source path and different test/workflow identity:

| Path | Blob |
|---|---|
| `Hardware/esp8266/BlazePisonetUniversal/BLAZE_PISONET_INTERCON_V1_6/BLAZE_PISONET_INTERCON_V1_6.ino` | `13c27bb6fe3d7792095cad5c92e88dfbb1292989` |
| `Hardware/esp8266/BlazePisonetUniversal/BLAZE_PISONET_INTERCON_V1_6/InterconPeerParser.h` | `9632b7eee168bfab2bb22b0bba9510859a4b5c82` |
| `Hardware/tests/intercon_v16_peer_parser.cpp` | `0f7806b34d49657f66842b573cef0d3de34b093a` |
| `.github/workflows/blaze-pisonet-intercon-v16.yml` | `4b1137c35830ca7804b2539870fd4ef932566dc2` |

The V1.6 host parser fixture reports 15 parser cases and tests strict HELLO packet parsing; its workflow also compiles the V1.6 sketch. Exact branch CI:

- [V1.6 parser + ESP8266 compile #44226761277](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226761277) — SUCCESS; both jobs completed successfully.
- [Case-collision #44226761300](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226761300) — SUCCESS.
- [Hardware & Shared #44226761298](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44226761298) — SUCCESS.

The V1.6 branch is not the #36 Stage-1 staging directory, has different source/test blobs, and has no open PR found for this exact branch. Its passing branch workflow is not integration acceptance and does not select it as canonical.

## Ownership and migration decision

Current `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`. It contains no route for COE `Hardware/esp8266/BlazePisonetUniversal/`; PHX-MASTER's destination remains null.

**Correction to the previous UTC10 ownership wording:** directory placement makes this an ESP8266 firmware-domain review, but it does not by itself create a formal PHX-HARDWARE assignment. The COE integration owner must nominate an accountable implementation owner. PHX-HARDWARE is the appropriate technical-domain reviewer to request; PHX-PISONET remains a timer/credit-interface stakeholder, not the firmware owner by product name. No source ownership was changed.

Do not copy, move, cherry-pick, rebase, merge or promote #36, the V1.6 branch, or Stage-3/Stage-4 candidates. The three Stage-3 journal layouts and two Stage-4 behaviors remain separate candidates; no canonical candidate is selected.

## Current role and integration CI snapshot

| Role / candidate | Exact head | Exact evidence |
|---|---|---|
| PHX-CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped; separate CORE continuation retains ownership |
| PHX-RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235), [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS, scoped |
| PHX-PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM acceptance unknown |
| PHX-HARDWARE #323 | `1761bf38d01c44f3bfd87acc6c7f03d97d7e1d17` | Focused [44278980129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980129) and [44278980263](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980263) PASS; Full [44278980291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980291) FAILS at QA-owned legacy poll-signature assertion |
| PHX-QA #292 / #290 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` / `5c29d15994cee1279058f1eca12f2a3180704292` | #292 no current-head run; #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, scoped |
| PHX-RELEASE #291 | `bf96680ab1d0040da8b70641c7dd3b1ca21ccea4` | [44270351439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44270351439) SUCCESS, scoped |
| COE RELEASE #35 | `0e6787160b98ceb650fe1ece03366c3116117cbe` | Shared [44284450562](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44284450562) and case [44284450631](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44284450631) PASS; mandatory sandbox [44284450618](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44284450618) FAILS closed |
| COE Stage-4 #41 | `021e2474c5bc8df37ab016a586db516fb4f2445f` | [44235451605](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44235451605) SUCCESS, host/simulation + ESP8266 compile |
| COE Stage-4 #43 | `8f5eec790dc2a3e25c219a6f51651113cd1c90cd` | [44246962253](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44246962253) SUCCESS, host/simulation + ESP8266 compile; known volatile pulse alarm and up-to-60-second recovery gap remain |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs; no combined acceptance |

The COE #35 sandbox fails at hosted unprivileged bubblewrap UID-map setup after its host preflight; do not bypass with an unsandboxed fallback. Hardware #323 remains deny-only; QA owns the obsolete positive poll-signature fixture correction.

## Access and test limits

- The private Drive v11 registry and newer corrections were not found in the accessible Files Library. The current tool surface exposes no Google Drive connector. Older v3–v7 snapshots and the November 9 checkpoint were not substituted.
- The AGENTS-linked Cloud Artifact Policy and Cloud Storage Handover could not be retrieved through the available GitHub file surface.
- A local Git clone attempt failed because the execution container could not resolve `github.com`. The full Master Python suite was therefore **NOT RUN**.
- GitHub source/tree inspection and exact-head Actions metadata were completed. Do not label these as a local Master test run.
- No physical hardware, coin, relay, power-cut or 30-device soak test was run.

## Required next actions

1. COE integration owner: correct #36's stale V1.5 provenance wording and nominate an accountable owner for the Universal/INTERCON subtree.
2. PHX-HARDWARE: review #36 and V1.6 source/test differences and recommend one candidate only after owner assignment; no merge request yet.
3. PHX-PISONET: review only the timer/credit interface boundary.
4. License custodian: resolve Labs NOTICE and explicit redistribution rights.
5. PHX-QA: retain deny-only firmware behavior and independently review exact Stage-1/V1.6 test scope.
6. Registry custodian: restore authorized access to private v11 registry, artifact manifest and sync ledger.
7. Infrastructure: provide a supported namespace-capable sandbox runner; no policy bypass.

**Disposition: review-only, migration blocked, production NO-GO.** No subsystem source, routing manifest, payment state, secret, hardware or release artifact was changed.
