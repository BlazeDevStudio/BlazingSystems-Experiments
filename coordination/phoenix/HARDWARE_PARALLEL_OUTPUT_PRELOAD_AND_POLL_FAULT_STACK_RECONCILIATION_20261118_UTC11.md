# PHX-MASTER — Hardware parallel stack reconciliation

**Date:** 2026-11-18 UTC11  
**Role:** PHX-MASTER  
**Scope:** `coordination/phoenix/` only. No Hardware, QA, CORE, Release, or COE implementation source was changed.

## Current exact repository references

| Reference | Exact ref |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| PHX-MASTER `phoenix/master-coordination` | `2dae0d4f1ffe608713dbc603d8ea3efc3ef757af` before this audit |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Existing PR #288 | OPEN / DRAFT, base Experiments main, 77 changed paths before this audit |

The live Master branch and PR #288 both resolved to `2dae0d4f...`. The current control-plane issue body still named `5e11daf8...` as the Master head; that active index entry was stale and is refreshed in the same activation. The branch-local `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER target `null`.

## Hardware branch topology

| PR | Current head | Current base | Live disposition |
|---|---|---|---|
| #317 | `fce915c1167fc43c6936f3594ae9efce376b711f` | #315 at `84fe6b790139d147f330f13a40b3ae3e89a7042d` | Focused labs pass; Full build fails at legacy poll-signature assertion |
| #318 | `5af39837f5ce42b45e8e707c86fa015a415cc75d` | `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3` | No workflow runs returned for this exact head; base is not current #317 head |
| #321 | `4c54d6299388617e9ff3d41d5501358ea545c54a` | #317 exact head `fce915c...` | Separate output-preload child; focused runs pass, Full fails |
| #322 | `50d93e0de3d682550b6f02fb43484e76ad9c7e08` | #320 at `b2b41a3d6ce7887b9624137c966f58462895d3fa` | Alternate output-preload child; focused runs pass, Full fails |
| #323 | `1761bf38d01c44f3bfd87acc6c7f03d97d7e1d17` | #322 exact head `50d93e0...` | Dual-store poll-fault child; focused runs pass, Full fails |
| #324 | `8e7f02201cb9295f15672dc21f8a75fc4e5cd0ba` | #322 exact head `50d93e0...` | Output-inhibit test child; focused runs pass, Full fails |

### Exact changed-path overlap

- #321 and #322 share **four** changed paths: the relay/output workflow, ESP32 sketch, ESP8266 sketch, and `output_enable_sequence_lab.py`. They are not a single linear stack: #321 is based on #317; #322 is based on #320. Both alter the same output-enable invariant on different ancestry. Keep both draft until PHX-HARDWARE chooses one base/candidate and records any required test port.
- #323 and #324 share **three** changed paths: both board sketches and `poll_loop_blocking_inhibit_lab.py`. They are sibling children of #322.
- #323 already deasserts outputs with `applyOutputs()` before its NVS/EEPROM and LittleFS persistence attempts. Its current poll-loop lab does not contain the direct marker-open observer or direct latch test added by #324.
- #324 adds `observeFaultMarkerOpen()`, starts with relay/LED asserted, calls the extracted production latch, and asserts both outputs are OFF at the exact `/pollpulse.fault` open boundary. It also injects a `defer-fault-output-inhibit` mutation. This is a test-coverage delta even though the source-ordering correction is already present in #323.
- Do not merge both siblings or cherry-pick/rebase either branch automatically. PHX-HARDWARE must select the canonical stack and, if #323 is selected, decide whether to port #324's direct marker-open regression into it.

### Exact CI evidence

| Candidate | Focused evidence | Full build |
|---|---|---|
| #317 | [44209812693](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812693), [44209812920](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812920) SUCCESS | [44209812745](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812745) FAILURE |
| #321 | [44294008493](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44294008493), [44294008398](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44294008398) SUCCESS | [44294008523](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44294008523) FAILURE |
| #322 | [44232877611](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877611), [44232877649](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877649) SUCCESS | [44232877624](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877624) FAILURE |
| #323 | [44278980263](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980263), [44278980129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980129) SUCCESS | [44278980291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980291) FAILURE |
| #324 | [44290338178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44290338178), [44290338468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44290338468) SUCCESS | [44290338340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44290338340) FAILURE |

The #321 and #324 validation logs explicitly fail at the QA-owned legacy `Missing poll signature check`; the deny-only firmware behavior must not be weakened to satisfy that positive string assertion. #324's board/firmware jobs passed, but Full validation is still failed and downstream gates are not accepted. #318 has no exact-head workflow run.

## Other current role and destination evidence

- CORE #252 head `c82705f2de865c89ab733b10efa84f26f56a5cc4`: [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped. Separate active CORE continuation retains implementation ownership.
- RENTAL #289 head `68928774d0d7cf65adb26bc6b54199a3159d066c`: [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS.
- PISONET #255 head `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09`: [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM acceptance remains unverified.
- QA #290 head `5c29d15994cee1279058f1eca12f2a3180704292`: [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, scoped. QA #292 head `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`: no exact-head workflow runs returned.
- RELEASE #291 head `18f61977ba374b90d4002887bce29cb7921bee78`: [44296238509](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44296238509) SUCCESS; handover and Windows build passed, signing steps and publish-release were skipped. This is not a signed or published release.
- COE Release #35 current head `ad69c4e945045ebe1c29c2645e40927249c29b4f`: case guard [44294942334](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294942334) SUCCESS; shared validation [44294942295](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294942295) FAILURE because the test requires the missing-bubblewrap branch to use `exit 125`, while the current workflow uses `exit 1` (89 tests, one failure, two intentional skips); sandbox [44294942227](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44294942227) FAILURE. Release owns the correction.
- COE CORE #45 head `9d76a134c1f6512aa40c20ec4d247306a71a8cce`: [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) and [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) SUCCESS, scoped; this remains a separate COE candidate, not part of integration #26.
- COE integration #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; its five workflows are QUEUED with zero jobs. No combined integration acceptance exists.

## Ownership, routing and required human actions

1. PHX-HARDWARE: choose the canonical output-preload/poll-fault stack among #321/#322 and #323/#324; explicitly reconcile #318's old base. Do not let PHX-MASTER select or modify Hardware source.
2. PHX-QA: replace the stale positive poll-signature fixture with negative deny-behavior assertions for missing/malformed/forged responses. Keep the current consumer fail-closed.
3. PHX-RELEASE: reconcile the #35 `exit 125` contract/test mismatch and obtain an authorized disposable namespace-capable runner with pre-provisioned bubblewrap; no privileged install or unsandboxed fallback.
4. COE integration owner: keep #26 blocked until each source blob, license/NOTICE, test identity and exact-head workflow is reconciled.
5. Registry custodian: restore owner-authorized access to private Drive v11 and newer corrections. No older Library copy is substituted.

No source files were copied, moved, overwritten or deleted. No ownership route was added. No rebase, merge, release, signing, secret provisioning, flash, physical test or real-payment operation occurred.

**Production:** PRODUCTION NO-GO. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
