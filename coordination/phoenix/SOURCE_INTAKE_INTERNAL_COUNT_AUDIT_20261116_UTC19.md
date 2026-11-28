# PHX-MASTER — source-intake internal count audit (2026-11-16 UTC19)

**Status: BLOCKED / PRODUCTION NO-GO.** Coordination-only audit; no runtime code, financial migration, or release approval.

## Pinned evidence

- Experiments default `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master draft PR #288, prior head `2e00308b18aeccd639912895becfa315b925cd9e`.
- COE default `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; draft integration PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Examined `Pisowifi/SOURCE_INTAKE.json` at COE #26 pinned head; blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`.
- Its historical source is explicitly `6d4c9b487af4d768c4d7627654d119417fcc6e00`, **not** Experiments default main.
- The restricted Drive v11 registry was successfully parsed locally as JSON. Its contents and identifiers must remain private.

## Reproduced internal consistency failure

A direct JSON parse and count of all `runtime[]` records (61 total) gives:

| Classification | `summary` asserts | Actual `runtime[]` count |
|---|---:|---:|
| `byte_identical` | 47 | **46** |
| locally derived (`derived_cleanup_review_required_real_router_test`) | 14 | **15** |
| recovered total | 61 | 61 |

Each of the 61 entries' `status` matches the equality/inequality of its *recorded* source and destination Git blob IDs (zero internal identity-status mismatches). This only checks manifest-internal assertions, **not** that either blob is actually present at the claimed source/target commits. The summary counts are stale or incorrect relative to the entries. Therefore do not promote the earlier 47/14 summary to independently verified provenance.

Reproduce in a complete COE checkout pinned to `b382d233ff06c8791b1028bed3c617cc7b670d12`:

```sh
python3 - <<'PY'
import collections, json
m=json.load(open('Pisowifi/SOURCE_INTAKE.json', encoding='utf-8'))
counts=collections.Counter(x['status'] for x in m['runtime'])
print('runtime',len(m['runtime']), 'statuses',dict(counts))
assert len(m['runtime'])==m['summary']['recovered_rootfs_file_count']
assert counts['byte_identical']==m['summary']['recovered_byte_identical_count']
assert len(m['runtime'])-counts['byte_identical']==m['summary']['locally_derived_files']
PY
```

**Expected current result:** the second assertion fails (46 != 47). This command is a reproducibility instruction; it was **not** executed in an exact-head checkout. The independent count was executed on connector-fetched JSON, not against a cloned Git working tree.

## Ownership and next actions

1. **COE integration owner / PHX-CORE:** reconcile manifest summary against all 61 entries and actual Git blobs at the *historical* source SHA and COE #26 SHA. Make a narrow manifest correction on the integration owner branch; no recursive copy.
2. **PHX-QA:** independently verify all 61 source/destination paths, modes, blobs, licenses, imports, test identities, 15 currently marked derived entries, and rollback evidence; execute exact-head negative regressions.
3. **PHX-MASTER:** track the discrepancy only; do not edit destination owner branch or assume this metadata correction establishes behavioral equivalence.
4. **COE integration owner:** investigate five queued Actions workflows at `b382d233...`; queued is not passing CI.

Production remains **NO-GO** until protected signing and independent anti-rollback witness, crash-atomic durable financial state, reversible migration, QA, native acceptance, 150 real power cuts and 30-device/24h soak are independently evidenced and owner authorized. No Codex, merge, release, flash, payment, physical test or live migration.
