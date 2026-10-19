# Project Phoenix — maintainer entrypoint

> Development baseline only. Verified on 2026-10-20 against `blazepwifi-v0.6.0-audit-foundation`. This is a map of **existing tools**, not a new build or payment authority. Check live Git HEAD, PRs and CI before relying on dates or historical claims.

## Clean checkout and fast nonproduction verification

On an isolated Linux developer machine with Git, POSIX shell, GNU coreutils, awk, flock and Python 3:

```sh
git clone --branch blazepwifi-v0.6.0-audit-foundation https://github.com/BlazingSystems/BlazingSystems-Experiments.git
cd BlazingSystems-Experiments
git rev-parse --is-shallow-repository  # must print false for the handover gate
P=experiment/openwrt/BlazePwifi
sh "$P/tests/handover_gate.sh"
sh "$P/tests/static.sh"
sh "$P/tests/v060_rental_paid_lock_race.sh"
sh "$P/tests/v060_rental_revoke_safety.sh"
sh "$P/tests/v060_paid_v2_cutover_interlock.sh"
```

These are **selected fast source/synthetic regression checks**, not the entire CI test matrix, an installer acceptance test or any proof of physical durability. Tests create disposable fixtures; never point them at a customer's state. The authoritative full software validation steps are in `.github/workflows/blazepwifi-build.yml` (job `validate`).

## Reproducible build entrypoints already in source

- **OpenWrt** — `sh experiment/openwrt/BlazePwifi/build/build-openwrt-image.sh ruijie` (also `x86_64`, `orangepi_zero3`, `orangepi_one`, `orangepi_pc`, with other profiles defined in that script). It pins OpenWrt **25.12.5** by default, checks the downloaded official ImageBuilder SHA256, and writes to `experiment/openwrt/BlazePwifi/dist/<target>/`. Requires an approved Linux build host, curl, zstd and ImageBuilder prerequisites. **Generated images are not customer-authorized.**
- **ESP8266/ESP32, Android, firmware matrix and update packaging** — the actual versioned commands and runners are encoded in `.github/workflows/blazepwifi-build.yml`; inspect each job's toolchain versions and artifact label. Do not assume a GitHub CI APK uses the owner's permanent Android signing certificate.
- **Windows SoftTimer** — on Windows with a matching .NET 8 SDK, run `pwsh -NoProfile -File experiment/windows/BlazePisonet-SoftTimer/build-local.ps1`. The project also has `.github/workflows/blazepisonet-softtimer-release.yml` for Windows installer and separate tests. Neither compilation nor unsigned packaging proves customer-safe payment operation.
- **Native v2 authority** — `sh experiment/openwrt/BlazePwifi/tests/v060_native_v2_authority.sh` is a host synthetic test. `.github/workflows/blazepwifi-v060-sdk-lab.yml` cross-compiles lab-only native binaries. They do not activate v2 payment or provision an independent witness.
- **Local update overlay** — `sh experiment/openwrt/BlazePwifi/tools/build-update-bundle.sh` builds a versioned overlay; preserve the v0.6 upgrade interlock. It is not production release approval.

For an **intentional full GitHub CI run**, an authorized maintainer can dispatch the existing `blazepwifi-build.yml` workflow on the development branch via GitHub Actions. Review the exact trigger SHA, each job's final conclusion (including skipped/cancelled jobs), and artifact digest. Do not blindly rerun unchanged deterministic failures.

## Single navigation chain

- Architecture: [ARCHITECTURE](../ARCHITECTURE.md), [payment/migration invariants](../LEDGER_TRANSACTION_V060.md), [wire protocol](../PROTOCOL.md).
- Latest actual work: [current state](../handover/CURRENT_STATE.md), [change ledger](../handover/CHANGE_LEDGER.md), [mandatory policy](../handover/HANDOVER_POLICY.md) and [root project handover](../../PROJECT_HANDOVER.md). These are existing records; **do not introduce a parallel changelog**.
- Deploy/recover: [installation](../INSTALL.md), [migration and rollback decision](../RELEASE_0.6.0_MIGRATION.md), [physical acceptance](../V060_PHYSICAL_DURABILITY_ACCEPTANCE.md), [signer custody](../V2_TARGET_SIGNER_CUSTODY_ADMISSION.md).
- Source ownership: the OpenWrt runtime lives at `openwrt/rootfs`, ESP at `esp8266` and `esp32`, Android at `android/BlazeRentalLauncher`, and Windows under `experiment/windows/BlazePisonet-SoftTimer`. Standalone rental profiles have separate release history; do not merge identities by name.

## Financial/production admission — fail closed

Check current [P0 #31](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/31) (member durability), [#32](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/32) (rental atomicity), [#43](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/43) (independent monotonic witness) and [#34](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/34) (hardware, signing, migration). Two source safety changes [PR #112](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/112) and [#113](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/113) are merged **into development only**, not an activated v2 journal or production release.

- The repository development `VERSION` remains **0.5.3**. Published `v0.6.0-alpha.4` is a **LAB ONLY prerelease**, not installable commercial evidence.
- Native v2 and off-device SQLite candidate are not proof of an independently protected monotonic hardware witness, protected server signer, provisioned controller identity, or irreversible-cutover rollback protection.
- Only owner-approved isolated, disposable hardware can supply the required actual power-loss trials and real 30-device/24-hour soak. Never repurpose customer installations as test rigs.
- A release must use correct source versions, verifiable signing continuity, accepted migration, actual device evidence, SHA256SUMS and matching packages. Absent any required evidence, keep customer deployment and paid v2 ACK **disabled**.

## Human maintainer's repeatable next step

1. `git fetch --all`; compare `git rev-parse HEAD` with PR #30 and the last **completed** CI SHA. Read the source and the first current-status block, not just historical handover prose.
2. Choose one unmerged P0 source change, inspect its real diff and tests; write one reproduction that fails on base, then verify the smallest fix on the candidate.
3. Integrate only after exact-head verification, no active branch overwrite and clean ancestry; update existing three canonical handovers once per meaningful checkpoint.
4. Resume native v2 source-owned protected witness/signing and reversible migration work on [PR #89](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/89) **only after reconciling its nonmergeable branch against development**; never fall back to v1 for v2 receipt ACKs.
5. For external blockers, retain a precise operator-run instruction and evidence requirement. **Do not mark release completed, re-sign Android with substitute keys, flash customer storage or alter real balances to satisfy a deadline.**

This entrypoint intentionally adds no dependencies or duplicate build commands, no new financial authority, and no release status overrides.
