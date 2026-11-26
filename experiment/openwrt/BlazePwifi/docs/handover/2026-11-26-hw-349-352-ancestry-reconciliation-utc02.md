# PHX-HARDWARE UTC02 — #349/#352/#353 ancestry reconciliation

Observed: 2026-11-26T02:38Z
Role: PHX-HARDWARE
Repository: BlazeDevStudio/BlazingSystems-Experiments
PRs: #349, #352, #353 (OPEN / DRAFT / UNMERGED)

## Exact refs

- #349: `1a2ecf5fa8c8c20a0095ac898c1bff254280ad27`.
- #352 prior: `0e984e267b3a8fb10c314800d1a7f120806354b7`.
- #352 reconciled merge: `a1720e1724a15b5254d9dd1ee57e6212259a4896` (parents: prior #352, then #349).
- #353 prior: `4e2185b150ba6d1a614fe86d875a9d2bfc7db9a4`.
- #353 merge second parent: reconciled #352 `a1720e1724a15b5254d9dd1ee57e6212259a4896`.

## Changes carried into #353

- CRLF-aware C++ token normalizer and its 15-case regression contract from #349.
- #349 UTC23 narrow handover and this UTC02 stack handover.
- Additive #349 UTC23 and UTC02 entries in `PROJECT_HANDOVER.md`, preserving the #353 UTC01 history.
- The prior #353 UTC01 ancestry handover is retained and annotated as superseded by the new parent snapshot.
- All #353 ISR-specific source, fixtures, structure guards and workflows are preserved from the first-parent tree.

## Safety and verification

- The #352 merge uses first parent `0e984e267b3a8fb10c314800d1a7f120806354b7` and second parent `1a2ecf5fa8c8c20a0095ac898c1bff254280ad27`.
- The #353 merge uses first parent `4e2185b150ba6d1a614fe86d875a9d2bfc7db9a4` and second parent `a1720e1724a15b5254d9dd1ee57e6212259a4896`.
- Both branch ref updates are expected-SHA guarded and non-forced.
- No production `.ino` behavior, CGI producer, CORE contract, finance, signer/witness, migration, COE destination, physical device or release artifact changed.
- Focused and Full exact-head CI must be re-read; no result is inferred from prior SHAs.
- Physical coin/relay/electrical acceptance, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. Protected signer/witness, v1→v2 migration and durable accounting/replay remain NOT ACCEPTED.

Status: SIMULATED / CI VERIFIED inherited evidence only; HARDWARE ACCEPTED: NO; PRODUCTION READY: NO-GO.
