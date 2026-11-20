# COE integration #26: exact-head CI escalation and reproducible review (2026-11-16 UTC02)

**Role:** PHX-MASTER, coordination-only. **Decision:** DRAFT / PRODUCTION NO-GO. This is a reversible, documentation-only escalation; it does not authorize reruns with write credentials, merges, hardware operations or financial migration.

## Ref-pinned source of truth (read from live GitHub this activation)
- Experiments default `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; historical development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master draft #288 branch `phoenix/master-coordination@dbbe822d6e3f3ff15f6b88bf0b4525b8a898a690` before this document.
- COE structure-only `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration draft #26 `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`.
- `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`; its 11 routes are **review candidates**, not migration authorization. Broad `Rental/` target remains manual-file-mapping-required and copy-prohibited.
- Private Drive v11 registry was parsed locally as JSON; no private identifiers or contents are published here.

## Observable CI condition, not a test result
GitHub's commit-specific workflow-run query for COE PR #26 head returned **five queued runs**, no completed exact-head outcome:
| Workflow run | Observed state | Link |
|---|---|---|
| 43096752609 | queued | https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609 |
| 43096752632 | queued | https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632 |
| 43096752800 | queued | https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800 |
| 43096752563 | queued | https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563 |
| 43096752557 | queued | https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557 |

These run IDs are historical, not evidence of tests passing or failing. No Master exact-head pull-request workflow runs were returned for the pre-document Master SHA. HARDWARE #314 at `556adc20ef0cfd355089aff3b979c0169af79bdd` has two completed **software** successes (43782088748, 43782088731), which do not validate COE's staged firmware or physical acceptance.

## Human-debuggable recovery sequence — COE integration owner, not PHX-MASTER
1. Open each linked run and inspect event, queue reason, runner eligibility, concurrency, permissions and cancellation status. Record run/job URL and precise terminal status; do not infer a cause from `queued`.
2. Confirm the integration PR head SHA has not advanced; if it has, rebase the evidence matrix on the **new** SHA. Never reuse green checks from another commit as exact-head evidence.
3. If the original runs cannot complete, request an authorized nonprivileged validation rerun or new PR-scoped validation on the **same candidate tree**. Avoid workflow changes or privileged release triggers solely to force green.
4. Require completed checks for case-collision, Pisonet Windows, Hardware/Shared, Rental and Pisowifi, with failing job logs and exact source commit preserved. Compare PR head and GitHub checkout/merge SHA semantics.
5. Before migration approval, PHX subsystem owners must supply per-file source/destination Git blob IDs, modes, licenses, dependencies, import completeness, test identities and reversible rollback mapping. PHX-QA independently reproduces negative regressions and signs off only on observed evidence.
6. PHX-MASTER runs `python3 -m unittest discover -s coordination/phoenix -p 'test_verify_coordination.py' -v` and `python3 coordination/phoenix/verify_coordination.py` on a checkout of **this draft head**, preserving stdout, exit status and SHA. These commands are instructions, **not executed tests** in this checkpoint.

## Gates and rollback
No copy, cherry-pick, force-push, merge, release or production mutation was performed. Revert this single documentation commit if superseded; preserve its historical evidence. Protected signing and independent anti-rollback witness, crash-atomic durable financial state, reversible migration, native QA acceptance, 150 real power cuts and 30-device 24-hour soak remain independently unverified. **PRODUCTION NO-GO.**
