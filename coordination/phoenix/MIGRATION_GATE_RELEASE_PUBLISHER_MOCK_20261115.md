# PHX-MASTER — release-publisher mock CI integration hold (2026-11-15 UTC15)

Status: **DRAFT REVIEW ONLY / PRODUCTION NO-GO**. This is a coordination finding, not a modification of PHX-RELEASE source or an authorization to publish.

## Exact reviewed refs
- Experiments default `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- PHX-MASTER draft PR #288 parent head `90556982d02c2d81908d1f0810fdc0b116871c2f` before this document.
- PHX-RELEASE stacked draft PR #291 `f737c5dd9bb8a231bb4865a201975371a360f249`.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; draft integration PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.

## New exact-head CI finding
GitHub Actions [release run #43728468457](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43728468457), queried by the #291 head SHA, is **completed/failure**. Job `handover` succeeded; `build-windows` failed at `RELEASE-PUBLISHER-MOCK execute complete publication command path without credentials`. All downstream native build, packaging and parity steps in that job were skipped. The separate `publish-release` job was skipped. Do **not** cite the older successful #291 run as current exact-head validation or infer that publication was attempted.

The PR changes include `.github/workflows/blazepisonet-softtimer-release.yml` and `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/PublisherMockCli.ps1`, `negative-selftest.ps1` plus handover files. The failure step is confirmed from GitHub Actions job metadata; **the failure's root cause is not established** without inspecting that job's log. No source execution was performed in this Master audit.

## Human debugging and reversible handoff
1. **PHX-RELEASE owner:** inspect job `132855522860` log, isolate the failing mock command and exit code, and reproduce with the same PowerShell source at #291 exact head; keep the privileged publisher disabled and the frozen version gate intact.
2. Make a narrowly scoped RELEASE-owned correction and regression only on its existing draft stack; preserve the failing run as historical evidence.
3. **Independent PHX-QA:** verify denied duplicate release, ambiguous HTTP response, missing-tag vs auth/transport failure, invalid signing evidence and skipped publisher on PRs. Re-run full native build/installer/parity pipeline at the corrected exact SHA. The previous green run is not interchangeable with this head.
4. **PHX-MASTER:** before any cross-repo release workflow migration, compare source and destination **exact Git blob SHAs, file modes, licenses, imports/dependencies, test identity and corresponding exact-SHA CI**. COE #26 still reports queued workflows at its head; no green integration conclusion. Do not recursively copy release workflow files or overwrite staged behavior.
5. Keep release, signing, finance and hardware gates closed until independent protected signing/anti-rollback witness, crash-atomic accounting, reversible migration, native acceptance, 150 physical power cuts and 30-device 24-hour soak are verified and owner-authorized.

## Private registry limitation
The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not resolved by the connected Drive keyword searches during this audit. Do not treat the search failure as proof of absence; resolve via the private mirror's canonical folder/registry path before migration, without copying identifiers or contents into public GitHub.

Rollback: revert only this Master documentation commit. No runtime code, release workflow, hardware or payment state is changed by this document.
