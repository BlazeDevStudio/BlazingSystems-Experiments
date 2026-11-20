# PHX-MASTER — destination `vendo` blob divergence (2026-11-16 UTC17)

Status: **DRAFT / PRODUCTION NO-GO**. Scope: cross-repository provenance only; no source code changes or migration approval.

## Exact snapshots (live GitHub API inspection)
- Historical source: `BlazeDevStudio/BlazingSystems-Experiments` main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Coordination: draft PR #288 `phoenix/master-coordination@e40f49cd4e037a0107208452c4b497936aa907a2` before this audit.
- Destination: `BlazeDevStudio/CoinOperatedEcosystem` main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; existing draft PR #26 `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`.

## Concrete per-file comparison (Git tree blob identities)
| File | Git blob SHA |
| --- | --- |
| Source `experiment/openwrt/BlazePwifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo` | `2e3a1430d08cc6606429a042df3b5848f53c7267` |
| Destination `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo` | `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e` |
| Source `experiment/openwrt/BlazePwifi/LICENSE` | `1ee55b94183417be977ca287cd7391f9a6f7e721` |
| Destination `Pisowifi/LICENSE` | `1ee55b94183417be977ca287cd7391f9a6f7e721` |

**Finding:** `vendo` blobs are **different**, so this is not a byte-identical copy at these snapshots. This does **not** establish that either implementation is newer, safer, or functionally equivalent. The top-level Pisowifi license blob is identical, but that alone does not establish complete dependency/license compliance. Source and target Git trees were returned untruncated (2340 and 286 entries respectively).

## Required human follow-up (PHX-CORE and independent PHX-QA)
1. Fetch both exact blobs by SHA; review a bounded diff for receipt verification, durable ledger mutation, replay/idempotency, controller authentication, error handling and default-deny semantics. Preserve both originals.
2. Inspect `Pisowifi/SOURCE_INTAKE.json` and `Pisowifi/MIGRATION_MAP.md` against the *exact* destination commit, and compare each imported source blob, dependency, license and corresponding test identity.
3. Execute native/focused negative regressions and destination CI against the same reviewed SHA; attach run URLs, environment and observed outcomes. Five destination workflow records were queued when checked, with no conclusion.
4. Require independent PHX-QA approval and owner authorization before any migration. The broader `Rental/` destination remains non-copyable until per-file routing resolves its two prefix overlaps.

## Evidence limitations
GitHub API tree/blob **metadata** inspection was performed; neither full blob diff nor tests/CI were executed in this audit. The private v11 Drive registry was retrieved and parsed locally, but its contents and identifiers must remain private and are not copied into this public document. Signing/anti-rollback witness, crash-atomic accounting, reversible migration, native acceptance, 150 real power cuts and 30-device 24h soak remain independently unverified. No merges, flashes, payments, releases or physical tests.
