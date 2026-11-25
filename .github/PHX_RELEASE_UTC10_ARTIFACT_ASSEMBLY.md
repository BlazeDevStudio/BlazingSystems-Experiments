# PHX-RELEASE — v0.5.3 artifact assembly collision guard

**Date:** 2026-11-25 UTC10  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291) — OPEN / DRAFT / UNMERGED  
**Starting branch head:** `2076b434451bfaa82fb4f301d6f7eaca67c48d82`  
**Scope:** RELEASE-owned staging workflow and its regression/path-coverage tests only.

## Defect and test-first evidence

The v0.5.3 stage flattened firmware artifacts into `release-out/`. It first tried the source basename; on collision it prefixed only the immediate parent-directory name. If a third artifact shared both basename and immediate parent name, the prefixed destination already existed and `cp` silently overwrote the previously staged artifact. The original `find` traversal order was also unspecified, so the artifact receiving the unprefixed name could vary between runs.

- Test-first commit [`29fc04fc`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/29fc04fc719073faceb886fdd36e502a4ff2aa09) introduced the regression fixture, but its first CI attempt failed in fixture extraction; this was a test-harness error, not accepted RED evidence.
- Fixture correction [`deab037d`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/deab037d79188ad9da44dd768464ba2dc42e99f0) corrected the extracted shell loop but still had a literal command-separator escape; that run was also a harness error, not accepted RED evidence.
- Corrected regression commit [`1d3610d4`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1d3610d4eaa0ff163384fac48e351b47c144973d) reproduced the actual defect in compatibility push run [#45598879347](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45598879347), provenance job `139152649463`: the test expected fail-closed behavior, but the old loop returned exit 0 with no diagnostic after overwriting the colliding destination. This is the accepted expected RED. The two ESP32 core jobs were still running at the last read and are not part of the RED assertion.

## Bounded correction

- Sort NUL-delimited source paths with `sort -z` before assigning output names, making name selection deterministic.
- After optional parent-prefix disambiguation, reject an existing path or symlink with a clear `RELEASE-BLOCKED` diagnostic before copying.
- Preserve already-staged bytes; never overwrite on a second-level collision.
- Exercise the real extracted shell loop with three synthetic artifacts created in reverse lexical order. The fixture verifies deterministic names and that the third colliding copy fails without overwriting the second artifact.
- Add the v0.5.3 release-stage workflow, its regression test and this narrow handover to the compatibility workflow's push/PR path filters. Include the regression test in the PR path filter.

No real release stage, tag, signing operation, release upload or customer package was run. The fixture uses synthetic bytes only.

## Ownership and safety

Only these RELEASE-owned paths are changed by this increment:
- `.github/scripts/test_release_workflow_concurrency.py`
- `.github/workflows/blazepwifi-v053-release.yml`
- `.github/workflows/phx-release-esp32-core-compatibility.yml`
- `.github/PHX_RELEASE_UTC10_ARTIFACT_ASSEMBLY.md`

The existing `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` and `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md` are CORE-owned paths. Intervening documentation commits `f313fe0d` and `2076b434` touched those paths; RELEASE did not modify or overwrite them. MASTER should reconcile that branch-level ownership overlap.

## Verification status at source-fix commit

Exact-source compatibility, Full CI-0701 and Windows successor results are pending. Do not infer a full integrated build from the expected RED. Update this file only with terminal run/job evidence.

**PRODUCTION NO-GO.** No merge, signing, publication, hardware flash, payment migration or customer deployment. Protected signer and independent freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unestablished or NOT TESTED.
