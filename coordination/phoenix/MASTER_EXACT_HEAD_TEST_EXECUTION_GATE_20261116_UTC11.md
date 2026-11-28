# PHX-MASTER exact-head regression execution gate — 2026-11-16 UTC11

**Status:** DRAFT / PRODUCTION NO-GO. Coordination-only; no subsystem source changes.

## Observed immutable refs (connector read, not local test execution)
- Experiments default `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Historical development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`; not the Phoenix master branch.
- Master draft #288 `phoenix/master-coordination@0149dcb5aa0aafb6e3896c7ffe5ced82737167d6` at read time.
- COE structure-only `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; draft #26 `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`.
- The destination exact-head Actions API returned **five queued workflow records** (IDs 43096752609, 43096752632, 43096752800, 43096752563, 43096752557), with no conclusions. Master exact-head PR workflow lookup returned no runs. Neither is a test pass.
- Role snapshots reviewed: CORE #252 `c82705f2`, RENTAL #287 `a4fffd01`, PISONET #255 `d01fd164`, HARDWARE #314 `556adc20`, QA #279 `8f476ef0`, RELEASE #291 `2c4edff2`. Each is a distinct branch and cannot substitute for master test evidence.
- Private Drive exact v11 registry lookup and filename filter did not find the requested file. A folder named Project-Registry exists, but its presence does not establish registry readback or current corrections.

## Exact-head human test procedure (not executed by this audit)
1. On an authorized workstation, fetch and checkout the **current** draft #288 head by its full SHA (refresh PR before running). Record `git rev-parse HEAD` and a clean `git status --short`; abort if different.
2. Run `python3 -m py_compile coordination/phoenix/verify_coordination.py coordination/phoenix/test_verify_coordination.py coordination/phoenix/test_snapshot_identity.py`.
3. Run `python3 -m unittest discover -s coordination/phoenix -p 'test*.py' -v`; save interpreter version, command, stdout/stderr, exit status, and exact commit SHA. If the verifier depends on a source checkout, run `python3 coordination/phoenix/verify_coordination.py` in the complete repository, not a synthetic fixture.
4. Independently inspect `OWNERSHIP_ROUTES.json` and `REPOSITORY_ROUTING.md`; review destination staging at the current COE #26 SHA. Compare per-file Git blobs, licenses, dependency closure, negative test identities and rollback evidence. The broad `Rental/` target is intentionally `copy_permitted=false`; never recursively copy it.
5. COE integration owner (not MASTER) must diagnose queued Actions and provide completed exact-SHA job/run links. QA must independently review failures and negative paths. Registry custodian must restore authorized private v11 access; do not publish Drive metadata.
6. Mark BLOCKED until test logs and independent witnesses exist. No merges, payment operations, firmware flashing, release or physical test authorizations follow from this checklist.

## Evidence classification
**Performed:** GitHub metadata/source document inspection and Actions run-status lookup; Drive metadata search. **Not performed:** local Python compilation/unittest execution, destination CI, blob-level parity, hardware acceptance, registry contents verification, anti-rollback signing witness, financial migration.

## Next owner action
PHX-MASTER: run and attach exact-head local suite evidence. COE integration owner: unblock five queued workflows. PHX-QA: independent exact-SHA parity/negative verification. Registry custodian: restore v11 access. Release remains NO-GO pending all owner-authorized safety gates, 150 real power cuts and 30-device 24-hour soak.
