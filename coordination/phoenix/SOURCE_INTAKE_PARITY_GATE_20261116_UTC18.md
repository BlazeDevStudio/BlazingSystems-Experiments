# PHX-MASTER — Source intake provenance gate (UTC18, 2026-11-16)

**Status:** DRAFT / PRODUCTION NO-GO. **Scope:** coordination only; no source migration or financial changes.

## Immutable observations

- Experiments default main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master draft #288 previous head: `7079d5b7f817b3d6630b843feb68ac86452b5ac2`; COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE integration draft #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- The staged `Pisowifi/SOURCE_INTAKE.json` at COE #26 identifies **historical origin commit `6d4c9b487af4d768c4d7627654d119417fcc6e00`**, not the current Experiments default main. Its summary records **61 recovered rootfs files, 47 byte-identical and 14 locally derived**, with zero unrecovered rootfs files and two unchanged original tests. These are **manifest assertions read from a GitHub file**, not independently reproduced comparisons or tests.
- Therefore “61/61 recovered” must not be paraphrased as “61/61 byte-identical”; the 14 derived files require individual source blob, destination blob, semantic diff, licensing, dependency, tests, and reviewer disposition. A different current-main `cgi-bin/vendo` blob is already recorded in `DESTINATION_VENDO_BLOB_DIVERGENCE_20261116_UTC17.md`; comparisons against different source revisions must not be conflated.
- COE #26 exact-head Actions query returned five **queued** workflows (case collision, Windows SoftTimer, Hardware/Shared, Rental, Pisowifi), none completed. Master #288 exact-head Actions query returned no runs. This is metadata inspection, not CI execution.

## Reproducible human review procedure

1. Pin both repositories and the source-intake manifest to their exact SHAs above; check whether the manifest's origin commit is reachable and the destination's Git blob IDs still match its declared entries.
2. Enumerate all 61 runtime entries in `Pisowifi/SOURCE_INTAKE.json`; calculate counts from the actual entries rather than trusting summary fields; compare original/destination blobs and file modes using `git cat-file -p <blob>` and `git ls-tree` at pinned commits. Record any stale manifest entries.
3. For every derived file, review the actual diff, dependencies, tests, licensing, and rollback/migration behavior. Ask PHX-CORE for accounting semantics and PHX-QA for independent regression evidence; do not edit their branches.
4. Compare exact test file identities, runnable commands, and completed CI logs. A queued run or test count in a PR description is not a pass.
5. Retain the staging branch as draft and the historical source unchanged. Do not merge, flash, deploy, provision signing, or process real money.

## Blockers / disposition

**BLOCKED:** Independent exact-blob audit and test execution absent; five destination CI workflows queued; independent protected signing/anti-rollback, crash-atomic accounting, reversible migration, native hardware acceptance, 150 real power cuts and 30-device/24h soak lack accepted evidence. Private registry v11 was not retrieved in this activation; earlier retrieval claims are historical, not a fresh validation. The private registry must never be copied into public coordination docs.

**Next owner action:** PHX-QA reproduce 61-entry provenance table at pinned SHAs and review the 14 derived files; COE integration owner diagnose queued Actions; PHX-CORE validate financial semantics. MASTER only reconciles evidence and routing.
