# PHX-MASTER — development-branch ancestry and integration evidence gate (2026-11-15 UTC20)

Status: **DRAFT / PRODUCTION NO-GO**. Coordination-only audit; no code migration or approval.

## Exact live refs inspected
- Experiments default `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments named development branch `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- GitHub compare `main...development` returned **behind**, ahead 0, behind 293; the development commit is the merge base. This is a Git ancestry result, **not** proof of runtime equivalence or evidence that the development branch should be deleted or merged.
- Master coordination draft #288 `phoenix/master-coordination@89def7fd88e1503accb6ab8d7f5b8e5dafc025b3` before this audit.
- COE `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` (structure-only); integration draft #26 `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`.
- COE #26 exact-head PR workflow query returned five **queued** runs (43096752609, 43096752632, 43096752800, 43096752563, 43096752557); queued is neither PASS nor FAIL.
- RELEASE #291 `2c4edff231d9b2819415086825530d80b8801307`; HARDWARE #310 `da18da4c2afc3f42037ee3ac4cfa48bdba4f4f01` (role-owned, no edits).
- The restricted Drive v11 registry was fetched and parsed locally; no private data is reproduced here.

## New actionable source-selection gate
**Do not select the development branch as the canonical source merely because of its name.** It is an ancestor of main by 293 commits. Before routing any runtime file to COE, record: (1) role owner and intended target; (2) source branch and full commit SHA; (3) source path, Git blob SHA and mode; (4) existing COE #26 target path, Git blob SHA and mode; (5) dependencies and license; (6) test file identity and CI run bound to the same candidate SHA; (7) independently reviewed semantic differences and rollback.

Use `coordination/phoenix/OWNERSHIP_ROUTES.json` as review-only; the broad Rental destination remains non-copyable. Do not assume a newer branch automatically supersedes a staged fail-closed implementation. The historical development ref must remain available for provenance.

## Owner-routed next action
PHX-CORE / PHX-RENTAL / PHX-PISONET / PHX-HARDWARE: identify any *specific* source file that still depends on the old development branch and report its exact blob versus current owner PR and COE #26. PHX-QA: independently check behavioral differences, licenses, dependencies, negative regressions and reversible migration evidence. PHX-MASTER: maintain routing matrix only; execute 18-test coordination suite on exact head when a source-linked checkout is available. PHX-RELEASE: maintain protected publisher/signing separation.

No independent protected signer/anti-rollback witness, crash-atomic financial state, reversible migration acceptance, native hardware acceptance, 150 real power cuts or 30-device/24-hour soak is established by this audit. No merge, signing, release, flashing, live payment, or production migration authorized.
