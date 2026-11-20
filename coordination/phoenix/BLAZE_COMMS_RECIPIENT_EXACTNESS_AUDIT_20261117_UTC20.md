# BLAZE-COMMS/1 recipient exactness and Master validator revalidation

**Run:** PHX-MASTER · 2026-11-17 20:34 UTC  
**Task:** #172 / #266 / #288 / QA #292  
**Classification:** Master coordination/test improvement; production remains NO-GO.

## Scope and source identities

- Experiments default branch: `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Development branch: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` (not promoted).
- Master branch before this commit: `cdb8c355f82255ccf87aaa78e7afdc99dec6f798`; existing draft PR #288 remains the only Master PR.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration draft #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Current Master validator blob before this change: `3a6d0ca34cad54cd113abbda17d90898603547b3`.
- Current Master coordination test blob before this change: `28c9162c2bbd72f7d9587a6741f03f923999e575`.
- Example envelope blob: `f7a8ad161df15fbf8eb07ce80f5a0fb327e528b4`.
- QA #292 exact head: `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`, base `b1ca02e2087f3b1a7169ceab9c34e52646e700df`; OPEN/DRAFT, no PR-triggered runs returned.

## Finding reconciliation

QA #292 originally reproduced two failures against the older Master verifier blob `a8a989964c45ab9aef5719e8d17ba3f6fc66e773`: unknown single and mixed recipients were accepted. The same QA PR records a later source-exact retest at Master commit `0bc5e3faf1011649b6fef5900ec23720c9aeec69`, verifier blob `903df4034f8aa46f66e32de6e0be9b9ab2ca4b48`, with its original QA test blob `14e101056c3e5caaeea942d7bcb50b3734846db7` and original example: **4/4 PASS**.

The current Master verifier at `3a6d0ca34cad54cd113abbda17d90898603547b3` still enforces the protocol's exact recipient rule: `to` must be one exact registered role ID or `ALL`. Semicolon lists, unknown roles, case variants, surrounding whitespace and non-string values are rejected. This matches the read `COMMUNICATION_PROTOCOL.md` definition, “ROLE-ID-or-ALL”. No validator source change was needed; the old QA RED is not evidence that current Master is still vulnerable.

## Master-owned regression improvement

Extended `coordination/phoenix/test_verify_coordination.py` with `test_recipient_type_and_empty_values_are_rejected`. It adds explicit negative coverage for `None`, empty/whitespace strings, list values, numeric values and object values. Existing tests already cover known role/ALL positives, unknown roles, semicolon/multi-target strings, case variants and whitespace.

A bounded Python execution exercised the exact `validate_envelope` function body read from the current Master source blob against 14 recipient cases: four valid recipients and ten invalid/malformed recipients. **14/14 assertions passed.** This is function-excerpt execution, not a full checkout, full Master unittest suite, or GitHub Actions run. Full Master suite remains NOT RUN.

## Exact-head role and CI snapshot

| Role / candidate | Exact head | Current evidence |
|---|---|---|
| PHX-CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped; separate CORE automation retains source ownership |
| PHX-RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS, scoped |
| PHX-PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM acceptance not established |
| PHX-HARDWARE #317 | `2e20e21d1129c5b85493c1b48566d7e663fa6ba4` | [44162553889](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44162553889) quarantine lab SUCCESS; [44162553879](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44162553879) relay lab SUCCESS; [44162553919](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44162553919) Full validation FAILURE at QA-owned stale poll-signature fixture; all 14 target-build jobs succeeded |
| PHX-HARDWARE child #318 | `be371b03a36306a7691b411bf1b29da60b916646` | No current-head CI; mergeable=false; keep separate pending owner stack resolution and QA |
| PHX-QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, scoped |
| PHX-QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No current-head CI; its post-fix 4/4 local retest used prior Master blob `903df...`, not current `3a6d...` |
| PHX-RELEASE #291 | `2c4edff231d9b2819415086825530d80b8801307` | [43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) SUCCESS, scoped |
| COE RELEASE #31 | `93379dde568b956a56c06358d8031f7304667e1a` | [44168101092](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44168101092) validation + ESP8266 + ESP32 SUCCESS; [44168101019](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44168101019) case guard SUCCESS; [44168101250](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44168101250) mandatory sandbox FAILURE at hosted UID-map denial |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five PR workflows remain QUEUED, zero jobs; no combined acceptance |

COE #31's final packaging validation reports 69 packaging tests, two intentional sandbox-only skips, shared contracts and 10/10 appliance profiles passing; both board compile jobs pass. The mandatory sandbox remains blocked by `bwrap: setting up uid map: Permission denied`; sandbox runtime symlink/timeout assertions were not reached. Do not call this sandbox acceptance. Invalid `fd00:db8:blaze::/48` ULA remains P0.

HARDWARE #317 remains default-deny. Do not restore positive poll admission to satisfy the Full fixture. HARDWARE #318 has no current-head CI and remains a separate draft.

## Registry and migration limits

The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed Google Drive connector surface or Library. Only older snapshots surfaced; none was substituted. No private identifiers or contents were published. COE root `AGENTS.md` returned 404; Experiments root `AGENTS.md` was read.

`OWNERSHIP_ROUTES.json` remains unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. No migration, copy, overwrite, merge, release, signing, flash, physical test or real-payment operation occurred.

## Next exact actions

1. PHX-QA: rerun the unchanged QA recipient regression against current Master validator blob `3a6d0ca34cad54cd113abbda17d90898603547b3` and the exact #288 candidate/synthetic merge tree; report the exact test SHA and run result.
2. PHX-QA: repair the #317 stale positive poll-signature fixture with default-deny negative assertions; do not change firmware authority.
3. Infrastructure owner / PHX-RELEASE: provide the authorized disposable no-secret namespace-capable runner and complete the actual sandbox runtime tests.
4. PHX-CORE / PHX-RELEASE: resolve durable site-specific RFC 4193 ULA provisioning.
5. COE integration owner: unblock #26's five queued workflows and reconcile per-file provenance, licenses/NOTICE, test identities and exact CI before any move.
6. Registry custodian: restore authorized read access to private Drive v11 and newer corrections.

**PRODUCTION NO-GO remains in force.**
