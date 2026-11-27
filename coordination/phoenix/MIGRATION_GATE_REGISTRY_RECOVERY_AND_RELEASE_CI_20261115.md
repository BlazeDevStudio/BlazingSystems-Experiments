# PHX-MASTER — Registry recovery and release-CI migration hold (2026-11-15 UTC17)

**Status: DRAFT / PRODUCTION NO-GO.** This is coordination evidence, not permission to copy, merge, sign, flash, charge, or release. PHX-MASTER owns this file only.

## Verified references

- Experiments default `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; Master draft PR #288 `phoenix/master-coordination@2d0babf7261af3a0f7ed422dd4e59375546fe41c` before this note.
- COE default `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` is structure-only; integration draft PR #26 `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12` remains unmerged. Five PR-triggered workflow runs returned **queued**, not passing.
- RELEASE draft PR #291 `phoenix/release-publisher-isolation-20261115@c53c4677ad55575e95ade6cd47c62bd1bdcb1355` has [exact-head workflow #43740125754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43740125754) **completed/failure**. Do not treat the earlier handover freshness diagnosis as the cause of this newer failure without reading this run's logs.
- HARDWARE draft PR #308 `phoenix/hardware-pending-exact-size-20261115@12d374d3332fbf8774ea5efdf7cdf5e95611b0a5` has [focused #43737090905](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43737090905) and [build #43737090898](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43737090898) completed/success. Software CI is not physical acceptance.
- Master prior exact-head workflow query returned no PR-triggered runs; the 18 authored Master tests were **not executed** in this pass.

## Private recovery registry: access restored

The canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was located **by listing the private Project-Registry folder**, after filename/keyword search failed. Its downloaded copy was successfully parsed as JSON (45,338 bytes). The filename search failure was therefore a **discovery/indexing limitation, not proof that the registry was absent**. No private Drive ID, file content, project entries, or recovery metadata is included here. This access verification does **not** establish artifact recovery, source parity, license clearance, or the absence of newer corrections.

## Migration/release guard

1. **RELEASE owner:** inspect the new #43740125754 failing job and step logs; distinguish handover, publisher mock, packaging, and downstream skips. Fix only on the RELEASE-owned draft branch, refresh handover and obtain successful exact-head rerun.
2. **QA independently:** verify the RELEASE result and HARDWARE #308 trailing-byte pending-journal negative/reboot behavior at exact source and proposed destination SHAs; retain fail-closed coin/relay state.
3. **Migration reviewers:** before moving any file, record source/destination Git blob SHA, mode, license, imports/dependencies, test identities and exact-head CI. Keep the known broad `Rental/` target-prefix collision in `OWNERSHIP_ROUTES.json` blocked for recursive copy. Never overwrite a safer staged implementation with an older source solely by path/name.
4. **Master:** execute `python3 coordination/phoenix/verify_coordination.py` and `python3 -m unittest discover -s coordination/phoenix -p 'test_verify_coordination.py' -v` against the same checked-out Master commit; current pass is source/API inspection, not execution.

## Standing gates

Protected signing and independent anti-rollback witness; crash-atomic durable financial accounting and reversible v1→v2 migration; independent QA; native target acceptance; 150 real power cuts; 30-device 24-hour soak; explicit owner authorization. **All remain unproven for production here.** No automatic migration or release. Revert this single documentation commit to roll back this coordination-only change.
