# PISONET stacked destination candidates and installer state-guard audit — 2026-11-17 UTC10

**Role:** PHX-MASTER · **Scope:** coordination/phoenix provenance only · **Disposition:** review-only; no file move, merge, release or production approval.

## Exact refs re-read

| Ref | Exact head / base |
|---|---|
| Experiments default main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` (comparison only) |
| PHX-MASTER branch / PR #288 | `8bffe20f4a0ff5b722766c42d7dd3f03e97bee78` |
| PISONET owner PR #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| COE PISONET PR #28 | `b21b04617d38a177260258de2d56b24382822117` |
| COE PISONET PR #30 | `4897348d94a0cf7884ecd53244bfcd59e7bf2fbc` |

The private Drive registry and newer corrections were not available through the connected tool surface. The Library exposed only older registry snapshots; none was substituted for the canonical private record.

## Commit graph: #30 is not a child of integration #26

GitHub compare of COE #28 base/head to #30 returns **27 commits ahead, 0 behind**, with merge base exactly #28 head `b21b046...`. #30 is a real continuation of #28.

GitHub compare of COE #26 to #30 returns **diverged**, merge base COE main `a6513ab...`, with #30 **56 commits ahead / 85 behind** relative to #26. Therefore #30 is not a child of #26 and must not be described as already integrated into the umbrella candidate. A future integration requires an owner-approved graph/merge plan and conflict review.

## Exact path/blob inventory

Trees were fetched recursively at each exact commit and compared after stripping only the source/destination project prefixes. Counts below are tracked blob entries; all compared entries use mode `100644`, with no file-mode mismatch observed.

| Comparison | Source files | Candidate files | Same-path identical blobs | Same-path differing blobs | Source-only | Candidate-only |
|---|---:|---:|---:|---:|---:|---:|
| #255 → COE #26 | 68 | 47 | 27 | 11 | 30 | 9 |
| #255 → COE #28 | 68 | 48 | 28 | 10 | 30 | 10 |
| #255 → COE #30 | 68 | 48 | 26 | 12 | 30 | 10 |
| COE #28 → COE #30 | 48 | 48 | 38 | 10 | 0 | 0 |

The 30 source-only paths include source-owned documentation and distinct regression identities such as `NativeCoinDispatchLab`, `NativeSerialReconnectGuard`, `V2NativeEnvelopeContract`, `V2PendingSequenceLab`, `V2PublicAckProbe`, `SerialFaultModel` and `BuildLocalExitCode`. Candidate-only paths include `InstallerLayoutGuard`, `MemberTimeCommitGuard`, `StateRecoveryGuard`, `TimerCreditCommitGuard`, `MIGRATION_PROVENANCE.md` and `docs/STATE_RECOVERY_TROUBLESHOOTING.md`. These are different test identities, not proof that the source suite was imported equivalently.

The #28→#30 10 changed same-path blobs include `AppConfig.cs`, `AppController.cs`, `MainForm.cs`, `SerialHardware.cs`, `Storage.cs`, `NativeSerialPinFaultLab` sources and recovery/migration documents. Review these as deliberate owner changes; do not collapse them into a recursive copy.

## Important source-versus-destination safety distinction

The older PISONET owner source #255 still has a conditional active-low external-board read-error hazard in exact blobs:

- `SerialHardware.cs` `af15d41c22ab8ed6a507e38fed3ccdfc40f4054f`: `GetSignal()` returns boolean false on status-read exception.
- `AppController.cs` `f315f18826c9cb6f20bfe03dfaff8fe16ccb2b7d`: active-low mode inverts that false value and can call `SetAuthoritativeSeconds(1)`.

This is a source-confirmed conditional logic hazard, **not** evidence of a physical incident. PHX-QA already called out this exact risk in the #255 discussion.

Do **not** forward-port those two older files over the safer COE candidate versions:

- COE #26 `SerialHardware.cs` `1c6fcdc08a51187d84d4360276cb11c7843e7fe1` and `AppController.cs` `ee85dd498bf0e4f6432def8805658dcea562f942` use `TryGetSignal(..., out level)` and deny an unknown/error sample before polarity inversion.
- COE #30 `SerialHardware.cs` `ed1f2517b98ae142ff43c652e39da627ee550f0c` retains that tri-state guard and calls `OpenedSerialHandleIdentity.TryVerify(candidate, selected)` after opening the selected SerialPort; `AppController.cs` `d905a1f610ee0c47f3fb958943c4714eaad18291` denies before inversion.

COE #30 Windows synthetic CI includes same-opened-handle and read-error cases, including `NATIVE_INTERFACE_FAKE_SAME_HANDLE_POSITIVE_PASS` and `READ_ERROR_SAFETY_GREEN: 4/4`. This is source-linked synthetic evidence only, not physical USB/serial acceptance.

## New P0 installer guard finding in COE #30

Exact COE #30 installer blob: `installer/BlazePisonet-SoftTimer.nsi` `6a6b7af2d92362b0f082aa59e501ec3cdb74a7db`. Its line 44 uses:

```nsis
IfFileExists "$COMMONAPPDATA\\BlazeSystems\\BlazePisonetSoftTimer\\*.*" 0 +3
```

Exact #30 installer-lab log from run [43653415598](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598) records NSIS 3.13 **warning 6000**: unknown variable/constant `COMMONAPPDATA\\BlazeSystems\\BlazePisonetSoftTimer\\*.*` detected, **ignoring** (line 44). The workflow still concludes SUCCESS.

The current `Storage.RootDirectory` uses `Environment.SpecialFolder.CommonApplicationData`. The candidate's `InstallerLayoutGuard` blob `037a2a6939f0650fb5d503b5ed3209962977293b` only checks that the literal `$COMMONAPPDATA` text exists; it does not validate NSIS variable resolution, fail on warning 6000, or execute a sentinel-existing-state test against the runtime's actual CommonApplicationData path. Thus the LAB install refusal for existing paid state is **not proven**. Treat the installer as blocked until PHX-PISONET corrects the path resolution, makes relevant NSIS warnings fatal, and adds an exact existing-state guard test. Do not assume the green installer-lab job proves this guard.

## License / notice scope

- Experiments main has repository `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9`; no Pisonet-subtree LICENSE/NOTICE was found in the inspected source tree.
- COE main has no root LICENSE/NOTICE in the inspected tree; no `Pisonet/SoftTimer/LICENSE` or `NOTICE` was found in #26/#28/#30 trees.
- `Pisowifi/LICENSE` is a different subtree and is not evidence of Pisonet license coverage.

This is a provenance gap requiring owner/custodian decision, not a legal conclusion. No license text was copied.

## Exact CI reconciliation

| Candidate | Exact-head evidence | Result / limitation |
|---|---|---|
| Experiments #255 | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) | Handover + Windows build SUCCESS; does not erase the source read-error hazard |
| COE #26 | Five runs: 43096752609, 43096752632, 43096752800, 43096752563, 43096752557 | All still QUEUED at read; no combined-tree CI conclusion |
| COE #28 | [43632393888](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43632393888) | Windows-lab + installer-lab SUCCESS; synthetic/source-linked |
| COE #30 | [43653415598](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598) | Windows-lab + installer-lab SUCCESS, but NSIS warning 6000 above remains unhandled |
| COE #32 QA | [43653540607](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653540607) | Scoped synthetic CI SUCCESS; not physical acceptance |
| QA #290 on Experiments | head `5c29d15994cee1279058f1eca12f2a3180704292` | No workflow runs returned; native exception/callback cases remain NOT EXECUTED |
| COE #31 RELEASE | [44064212523](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44064212523), [44064212547](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44064212547) | Scoped CI SUCCESS at current #31 head; separate release role |

For completeness, current HARDWARE #317 is child of #315: focused [44065129637](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44065129637) SUCCESS (56/56 source-extracted marker cases); Full [44065129519](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44065129519) FAILURE at QA-owned validation job 133976753982 because the inherited poll-signature fixture still expects the unapproved positive signature. Keep default-deny; QA owns that test.

## Disposition and owner actions

1. Keep COE #26, #28, #30 and #32 draft; no copy, overwrite, relocation, cherry-pick, merge or promotion is authorized by this audit.
2. PHX-PISONET reviews/fixes the COE #30 NSIS state-path guard and warning handling; preserve the safer `TryGetSignal`/opened-handle checks.
3. PHX-QA runs #290's native COM test suite at its exact head on an authorized Windows runner and independently reviews COE #32; no run is currently evidenced for #290.
4. COE integration owner documents the exact graph/merge base and per-file import/test/license plan before proposing any #28/#30 material for #26.
5. PHX-QA repairs the #317 legacy positive poll-signature fixture and reruns Full without weakening firmware default-deny.
6. Registry custodian restores authorized access to the canonical private Drive registry and newer corrections; do not substitute old Library snapshots.

**PRODUCTION NO-GO** remains: independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are not independently verified. No physical test, real payment, signing, secret provisioning, flash, merge or release occurred.
