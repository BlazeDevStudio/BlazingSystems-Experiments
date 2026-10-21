# Optional REA lab investigation — BlazePwifi / BlazeRental / BlazePisonet

Status: **investigation-only**. REA is a third-party local analysis utility, NOT a required component, build dependency, antirollback witness, trusted P-256 signer, or a substitute for real equipment testing. Do not install it on customer routers or ship it inside BlazePwifi images. No automated use of Codex.

## Provenance and acceptable scope

Upstream: [morluto/rea](https://github.com/morluto/rea), public MIT-licensed `rea-agents`. Examined repository `main` on 2026-10-20: README blob `d75cac321bf3327fe868ab601aec322cd9141135`; upstream `package.json` reported `6.7.0`. For reproducible investigations, record the actual installed version, target SHA-256 and engine versions; never assume `latest` is fixed or verify a package by its name. Review upstream [security](https://github.com/morluto/rea/blob/main/SECURITY.md) and [responsible use](https://github.com/morluto/rea/blob/main/DISCLAIMER.md).

Use only BlazingSystems-owned binaries and builds, or targets whose owner has authorized analysis. Work on COPIES in a disposable offline or network-restricted workstation without access to live portal/customer payments, credentials, signing keys, retained receipts, production backups, or private customer data. Native parsing engines are not sandboxes. Do not execute untrusted artifacts on a real paid network. Do not place proprietary dumps or personal data in public CI logs/issues.

## Repeatable operator procedure

1. Record target filename, literal build commit, build workflow run ID and artifact digest from GitHub Actions. Verify local bytes using `sha256sum` / Windows `Get-FileHash -Algorithm SHA256`. Do not analyze an unknown replacement as if it were the recorded CI product.
2. On a separately administered analysis machine, install a reviewed, pinned REA version (requires Node 22.19+, 24.11+ or 26+). Run `rea --help` and `rea capabilities --json` to verify the installed version/provider functionality. Prefer explicit target paths and `--json` for retained evidence. Do not run agent auto-setup against a production admin workstation.
3. For a LAB-generated native **x86_64 ELF** copied from the installed preview, use Ghidra (operator-provided install) to collect static functions, symbols, calls and references: `rea analyze /absolute/path/blazepwifi-paid-authority --provider ghidra --json`. Alternatively `rea inspect-binary-layout /absolute/path/blazepwifi-paid-authority --json` requires operator-supplied Linux-x64 pwntools per REA upstream docs. Never run the ELF with private production controller keys.
4. For a **BlazeRental Android APK** built from the current source, use `rea inspect-android-package /absolute/path/BlazeRental.apk --json` and focused `rea search-android-classes /absolute/path/BlazeRental.apk MainActivity`. This needs a full JDK 17+ and the pinned headless JADX provider documented upstream. Review requested permissions, manifest, exported components, network routes, provisioning and timer entrypoints, then reconcile with source and behavioral tests. Static analysis does not verify APK signing, device runtime, kiosk escape prevention or paid-time persistence.
5. For a **BlazePisonet SoftTimer managed DLL** built from the current source, use `rea inspect-managed-artifact /absolute/path/SoftTimer.dll --json`, `rea inspect-managed-members /absolute/path/SoftTimer.dll --json`, and `rea inspect-managed-native-boundaries /absolute/path/SoftTimer.dll --json`. Static .NET metadata/CIL analysis does not execute the assembly; confirm exact filename and build identity first. Some native-published executables may need native tools instead.
6. Document each finding with exact tool/provider version, target SHA-256, reproducible command, scope, source path/function or byte offset, what was OBSERVED, what is merely INFERRED, limitations and explicit unknowns. Create a narrow failing regression against the current project and fix it only after source review; rerun exact-commit CI and relevant hardware tests.

## Where this helps

- Confirm lab x86 installed package includes expected functions and native crypto dependencies; detect missing/extra linked components, unsafe privileges, suspicious imports, or unexpected APIs.
- Compare BlazeRental app manifests, classes and package surfaces across releases to prioritize enrollment and kiosk security verification.
- Compare SoftTimer managed assemblies with source contracts for billing/identity and native P/Invoke boundaries.
- Investigate lawfully obtained, authorized competitor interoperability artifacts for behavior evidence, **without copying protected code/assets, breaking DRM, bypassing authentication or executing on customer networks**.

## Evidence and release boundary

Primary lab installed x86 source work: PR #110 forward-ported via the current integration branch; preview mode is opt-in `BLAZE_V2_PAID_PREVIEW=lab-only` under CI, x86_64-only with same-commit native APK provenance and rootfs verifier. That environment switch is a LAB guard, not cryptographic protection if a person controls the host. Ordinary production firmware excludes this native package and the built-in runtime rejects paid COMMIT/REPLAY ACK without independently protected witness and P-256 signer.

REA reports are supplemental: even a clean reverse-engineering report **does not** establish trustworthy monetary durability, independent antirollback, response-key custody, rollback recovery, activated v1-to-v2 migration or physical acceptance. Do not assert v0.6.0 production release while P0 #31/#32/#43/#34 remain open.

References: [REA CLI and Evidence](https://github.com/morluto/rea/blob/main/docs/cli.md), [native binary diagnostics](https://github.com/morluto/rea/blob/main/docs/binary-diagnostics.md), [Android analysis](https://github.com/morluto/rea/blob/main/docs/android-analysis.md), [managed .NET analysis](https://github.com/morluto/rea/blob/main/docs/managed-code-analysis.md).
