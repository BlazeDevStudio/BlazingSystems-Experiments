# PHX-MASTER UTC10 — Hardware #349 exact-head, COE #26 provenance and RELEASE #291 CI

**Timestamp:** 2026-11-24T10:05:28Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** `coordination/phoenix/`, architecture/interface contracts, cross-repository migration provenance and integration matrices only. Strict NO CODEX.

## 1. Starting live state

| Ref | Exact SHA / state |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Issue-designated development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Comparison-only v0.6 audit branch | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch / PR #288 starting head | `08345f148162d83c2558e7823aa478be0cb7d3da` |
| PR #288 base | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 was OPEN / DRAFT / UNMERGED with 194 changed paths, all under `coordination/phoenix/`, before this update. The branch ref and PR head matched. Issue #172 is OPEN; cleanup #266 is OPEN / 0-of-7. `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, Master target null.

## 2. Current owner PRs and exact-head CI

| Role / candidate | Exact head | Exact-head result |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS, scoped. CORE ownership preserved. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) + API [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; synthetic only. |
| HARDWARE #347 | `960184670379f01e20f0e7e8bc23b3e5eedacd3f` | Quarantine [#45299741995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299741995), Relay [#45299742437](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299742437), build [#45299741993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299741993): all FAIL. |
| HARDWARE #348 | `eb7afcb2ba0d1e84054c052c8b129cb51a91d062` | Focused [#45352513178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513178) PASS; build [#45352513177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513177) FAIL at missing `mbedtls/sha256.h` under Arduino core 4.0.0. |
| HARDWARE #349 | source/test `75b4c9a7ef923cc9f58e228d12d673ea1a31541c`; docs/PR `861e80de8eec289ef04a84bd80484eec032a3b73` | Quarantine [#45369924816](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45369924816) PASS; Relay [#45369924755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45369924755) PASS; Full [#45369924781](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45369924781) FAIL at QA-owned `Missing poll signature check` (validation job 138361265140). All 13 firmware targets and Android pass; dependent stages skip. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered runs; NOT VERIFIED. |
| RELEASE #291 | `6345b71318e1ed20557c7faa88c2bdafac2c61bf` | Windows [#45370196597](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45370196597) FAIL at `negative-selftest.ps1:326`, `missing tag accepted=False`; build [#45370196549](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45370196549) PASS; ESP32 compatibility [#45370196649](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45370196649) PASS; publisher skipped. |

The current #349 full validation log identifies the inherited QA-owned `Missing poll signature check` in the ESP8266 sketch. Hardware's consumer remains deny-only until CORE publishes an approved versioned authenticated producer envelope and QA independently reconciles the assertion; Master does not guess a signature or relax admission.

The current #291 Windows log confirms package parity and release-policy guards pass before the negative self-test fails at line 326. PISONET owns the test path; RELEASE owns publisher semantics. Master does not modify either source area. No publisher/signing action ran.

## 3. Exact COE #26 source/destination tree audit

All three recursive trees were non-truncated:
- Experiments #349 final docs head `861e80de8eec289ef04a84bd80484eec032a3b73`: **2,504 entries**.
- COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`: **286 entries**.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`: **3 entries**.

| Mapped scope | Source #349 | Destination #26 | Result |
|---|---:|---:|---|
| ESP32 + ESP8266 board subtree entries | 58 | 4 | 54 fewer destination entries |
| Board-local Python labs/helpers | 44 | 0 | 44 source files absent |
| QA test files | 47 | 19 | 1 exact; 3 divergent; 43 source-only; 15 destination-only |
| ESP8266 sketch | `2f87a9de84ac53dbb0d2718b5c79a4662b63de8f` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different blobs |
| ESP32 sketch | `a9a1c2fecb001d71f8f22b43952edbd160aacaf8` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different blobs |

Same-relative-path test comparison:
- Exact blob+mode match: `portal.sh`.
- Divergent same-path files: `config.sh`, `integration.sh`, `security.sh`.
- 43 source tests have no same-relative-path destination counterpart.
- 15 destination tests have no same-relative-path source counterpart.

Filename similarity is not test identity. The three divergent files are not counted as exact imports; destination-only tests are not silently discarded or overwritten. This bounded tree audit does not rerun the historical 61-row intake reconciliation.

### License / notice identities

| Artifact | Source SHA | Destination SHA | Result |
|---|---|---|---|
| Product LICENSE | `1ee55b94183417be977ca287cd7391f9a6f7e721` | same | Exact match |
| QRCode LICENSE | `150770c0fc2994865ccdbef6662735cc083e780d` | same | Exact match |
| TailAdmin LICENSE | `cb92d4176b21b0594e5a6caf94d79340505e3d33` | same | Exact match |
| TailAdmin NOTICE | `f0425bbbe34c1227311098173b1eae0c3e2a807b` | same | Exact match |
| Root NOTICE | `f6d92cd21465312be5993631fe26977219be0fb9` | absent | Gap |
| Tabler LICENSE | `22ee8122400915cbff18e5f69368fa9eea6145eb` | absent | Gap |
| BlazeRentalLauncher LICENSE | `c5b1efa7aac764ae6d8da63476a2d5cec02a6a5d` | absent | Gap |

COE #26 exact-head Actions still return five queued workflows (case collision 43096752609, PISONET synthetic 43096752632, Shared Hardware 43096752800, Rental 43096752563, PisoWiFi overlay 43096752557), zero jobs and zero commit statuses. **FROZEN:** no staging, copy, move, overwrite, rebase, cherry-pick, retarget or promotion.

## 4. Branch/version authority and governance

Exact version-file reads:
- Experiments main `VERSION=0.5.3-dev.5`, blob `43c05666668b2a6d1eef2c5dca9032d8c6b77869`.
- Issue-designated development `VERSION=0.5.3-dev.1`, blob `62d8e87b40a05fb7a39b60d72369d10a4fccca21`.
- Comparison branch `blazepwifi-v0.6.0-audit-foundation` has `VERSION=0.5.3`, blob `be14282b7fffb9ba95d51c6546ed9816dc8f3ff8`, while its handover policy says active from v0.6.0 onward.

The designated development branch remains v0.5.3-development. The v0.6 audit-foundation branch is not silently promoted as the development source of truth. CORE must resolve the version/handover authority before any release or integration decision.

Experiments main and development, plus COE main, report `protected=false`; both repositories' ruleset lists are empty. Master branch protection could not be queried through the connector path for the slash-containing branch and remains UNKNOWN. Root Experiments AGENTS.md blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f` was read, along with linked Cloud Artifact Policy blob `5e503925750c4e511314e4b7624579d82f60aae2` and Storage Handover blob `a15f14cb3baf46424b820e1a921462794422f06b` from `BlazeDevStudio/BlazingSystems`. COE main has no root AGENTS.md (404).

The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain NOT ACCESSIBLE through the available connector surface. Library search did not provide the canonical v11 file; older snapshots were not substituted. No private registry contents or IDs were published.

## 5. Test execution and limits

**Executed:** connected GitHub exact refs/PRs/issues; owner PR metadata and exact-head workflow runs; failed-job logs for #349 and #291; complete non-truncated recursive source/destination trees; exact blob+mode test comparisons; license/notice blob comparisons; JavaScript static assertions over counts and identity classifications; source/version file reads.

**NOT RUN:** Master Python unittest suite and `verify_coordination.py`. A shallow sparse Git clone failed because the runner could not resolve `github.com`. Master PR #288 had zero workflow runs and zero combined statuses at the starting head. No Master Python or CI pass is claimed.

## 6. Ownership and next actions

1. PHX-CORE publishes the approved authenticated register/poll response envelope and canonical golden vectors; PHX-QA independently resolves the inherited poll-signature assertion; PHX-HARDWARE keeps the current consumer deny-only and reruns Full at the approved exact source/docs SHA.
2. PHX-PISONET owns the #291 negative-selftest correction; PHX-RELEASE owns publisher semantics and reruns exact-head Windows/build/compatibility after the correction. Do not copy or edit PISONET files from Master.
3. COE integration owner supplies a per-file source/test/license map, explains destination-only tests, and obtains exact destination-head CI before any staging proposal.
4. Registry custodian restores authorized private v11/newer-correction access; repository administrators establish and verify effective branch protection.
5. An authorized human runner with a local authenticated checkout executes the Master Python suite and `verify_coordination.py` at the final PR #288 SHA.

No subsystem source, COE destination, ownership manifest, secret, signer, financial state, hardware, or release artifact changed. No merge, release, flash, physical test, payment operation, customer cutover or financial migration occurred. **PRODUCTION NO-GO.**