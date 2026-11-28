# PHX-MASTER — Pinned COE source-intake audit

**Checkpoint:** 2026-11-16 UTC21  
**Status:** DRAFT REVIEW ONLY · **PRODUCTION NO-GO**  
**Scope:** Read-only Git tree/provenance comparison for COE draft PR #26. No subsystem source was modified.

## 1. Exact repository identities

| Item | Exact ref |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Active Phoenix development branch | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Older development-named branch | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Manifest-pinned source | `Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00` |
| COE default branch | `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration draft | `PR #26@b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Master draft before this audit's docs | `PR #288@598131be8eeae65c136e77781fce008b3aeab610` |

The manifest source commit is an ancestor of the active Phoenix development head: the active development branch is 22 commits ahead and zero commits behind that source pin. The source pin is therefore historical, not the current development HEAD.

## 2. Rootfs manifest: independently re-derived from exact Git trees

Recursive Git trees were fetched at the manifest's exact source commit and COE PR #26 head. The 61 manifest entries were compared against actual source and destination tree paths, blob SHAs, and Git modes.

| Check | Result |
|---|---:|
| Source rootfs files at pinned source | 61 |
| Destination rootfs files at PR #26 | 62 |
| Manifest runtime entries | 61 |
| Entries present at both exact refs | 61 |
| Recorded source blob IDs matching actual source tree | 61/61 |
| Recorded destination blob IDs matching actual destination tree | 61/61 |
| Git modes matching manifest and both trees | 61/61 |
| Actual byte-identical source/destination blobs | 46 |
| Actual derived/different blobs | 15 |

**Confirmed manifest defect:** `SOURCE_INTAKE.json` summarizes 47 byte-identical / 14 derived, but both its 61 records and the exact Git trees prove 46 byte-identical / 15 derived. The manifest's source and destination blob IDs are individually accurate; the aggregate classification totals are not.

The 15 derived rootfs paths are:

- `etc/init.d/blazepwifi`
- `etc/init.d/blazepwifi-remote-admin`
- `etc/uci-defaults/99-blazepwifi`
- `usr/lib/blazepwifi/auth.sh`
- `usr/lib/blazepwifi/capabilities.sh`
- `usr/lib/blazepwifi/common.sh`
- `usr/lib/blazepwifi/config.sh`
- `usr/lib/blazepwifi/member.sh`
- `usr/lib/blazepwifi/rental.sh`
- `usr/sbin/blazepwifi-core`
- `usr/sbin/blazepwifi-remote-admin-run`
- `usr/sbin/blazepwifi-remote-guard`
- `www/blazepwifi/cgi-bin/admin`
- `www/blazepwifi/cgi-bin/api`
- `www/blazepwifi/cgi-bin/vendo`

The destination has one additional rootfs file not represented by the 61-entry manifest: `usr/sbin/blaze-appliance-diag` (destination blob `6690c739e931929d7beb3c256dd50b4531be3ba3`). Treat it as a separate destination-derived artifact requiring owner provenance and test identity, not as a recovered source file.

## 3. Source drift since the manifest pin

The active development branch still has 61 rootfs files, but `usr/lib/blazepwifi/common.sh` changed after the manifest source commit:

- Manifest-pinned source blob: `4ccb10777b08f541d092f7c2c2d2aad4d2f6562e`
- Current development blob: `50fa2d02d40af7fd8b06e83974345f1016a317f9`
- COE PR #26 destination blob: `ae00667da26c68c9e44a54a941887191029afc11`

The destination candidate was compared to the pinned source snapshot, not the current development source. CORE must review this newer source revision and the destination-derived version before any integration decision. MASTER did not edit either file.

## 4. Test-tree identity and import completeness

| Test tree | Files | Tree SHA |
|---|---:|---|
| Pinned source `BlazePwifi/tests` | 149 | `7e3b16f2a981c1c8ecab3b1da0d34a82b4e44f17` |
| Current development `BlazePwifi/tests` | 150 | `077ce6782f0a0586b6d7529c9ead4d7fd5cc1bf9` |
| COE `Pisowifi/tests` | 19 | `47f49a223a8e9f9d9d34f6f3eb60eaf8de258ca4` |

At the pinned source/destination snapshots, only two test files are byte-identical with matching paths and modes: `portal.sh` and `security.sh`. Two same-path files are changed (`config.sh`, `integration.sh`); 147 source test paths have no same-path destination counterpart; 15 destination test paths are destination-only.

The manifest's `unchanged_original_test_count: 2` agrees with the two exact matches, but it is not a complete per-file test disposition map. The destination may intentionally curate or rewrite tests; the current evidence does not prove that the remaining source tests were reviewed, superseded, or safely excluded. PHX-QA and the COE owner must provide that mapping. No test suite was inferred to pass from file identity.

## 5. License and notice inventory

Exact matches confirmed in the destination:

- Project `LICENSE` → `Pisowifi/LICENSE` (blob `1ee55b94183417be977ca287cd7391f9a6f7e721`).
- Rootfs QR-code vendor `LICENSE` (blob `150770c0fc2994865ccdbef6662735cc083e780d`).
- Rootfs TailAdmin `LICENSE` and `NOTICE.md` (blobs `cb92d4176b21b0594e5a6caf94d79340505e3d33` and `f0425bbbe34c1227311098173b1eae0c3e2a807b`).

The pinned source also contains these license-bearing files without a corresponding candidate path in the inspected destination tree:

- `android/BlazeRentalLauncher/LICENSE` and `android/BlazeRentalLauncher/assets/license.html`.
- `tests/vendor/jsqr-1.4.0/LICENSE`.
- `ui/vendor/tabler/LICENSE`.

This is a **provenance/licensing review requirement**, not a finding of infringement: the COE Android/test/UI trees may be rewritten or use different assets. The relevant owners must identify whether any source or third-party material was reused and attach the appropriate license/notice or clean-room provenance before integration.

## 6. Master verifier hardening and execution evidence

The Master-owned read-only `verify_source_intake_manifest.py` now rejects unknown/missing status values, non-object JSON roots, control characters in paths, and inconsistent original/recovered/unrecovered totals. The regression file now has 11 synthetic tests.

- Code/test commit: `598131be8eeae65c136e77781fce008b3aeab610`.
- Local `py_compile`: exit 0.
- Local `unittest`: **11/11 passed** against the exact fetched code/test blobs from that commit.
- A synthetic 61-entry fixture with the observed 46/15 record split and 47/14 summary is rejected with exactly the two expected aggregate-count errors.
- This was a local synthetic execution, not a full repository checkout, GitHub Actions run, actual OpenWrt build, or independent QA signoff. The verifier deliberately does not fetch Git objects or claim live byte parity.

## 7. Current CI snapshot at inspected HEADs

| Role / candidate | Exact head | PR-triggered workflow observation |
|---|---|---|
| MASTER #288 | `598131be8eeae65c136e77781fce008b3aeab610` | No workflow runs returned |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows queued; none concluded |
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Run [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) success |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | Runs [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) success |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Run [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) success |
| HARDWARE #314 | `556adc20ef0cfd355089aff3b979c0169af79bdd` | Runs [43782088731](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088731) and [43782088748](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088748) success |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No workflow runs returned |
| RELEASE #291 | `2c4edff231d9b2819415086825530d80b8801307` | Run [43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) success |

All listed role PRs remain draft. These are scoped software checks on their respective heads, not an integrated COE acceptance run, protected signing proof, financial durability proof, or hardware acceptance.

## 8. Registry access and next human actions

The exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not accessible through the tools available in this activation: no Google Drive connector was exposed, and the Library search did not return the exact v11 file. No substitute registry version was treated as authoritative, and no private registry contents or identifiers were published.

1. **PHX-QA:** independently reproduce the exact tree comparisons and review the verifier at the final PR #288 head; produce a per-file test disposition for the 147 unmatched source paths and the two modified same-path tests.
2. **PHX-CORE:** review the 15 derived financial/runtime files, especially the newer `common.sh` source and derived destination, without treating blob differences as semantic approval.
3. **COE integration owner:** correct the 47/14 summary to the verified 46/15 counts; add provenance/tests for `blaze-appliance-diag`; document why test and license-bearing files are absent or replaced; diagnose the five queued #26 workflows.
4. **PHX-RENTAL / COE owner:** establish Android source-vs-reimplementation and third-party license provenance.
5. **Registry custodian:** restore authorized access to the exact private v11 registry and newer corrections; do not publish its contents.

Protected signing and independent anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, and the 30-device 24-hour soak remain unverified. **PRODUCTION NO-GO remains in force.**
