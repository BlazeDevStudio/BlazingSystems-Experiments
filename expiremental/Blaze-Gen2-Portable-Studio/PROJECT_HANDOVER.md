# PROJECT_HANDOVER — Blaze Gen2 Portable Studio

**Version:** 1.0.0 — Experimental  
**Repository:** https://github.com/BlazingSystems/BlazingSystems-Experiments  
**Project source:** `expiremental/Blaze-Gen2-Portable-Studio/` (intentional spelling)  
**Last verified (UTC):** 2026-10-09 21:50  
**Actual pre-release:** https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v1.0.0-experimental  
**Release source commit:** `1781416c4676bb1581ca6902aca5ea75d8275599`  
**Initial source commit:** `6ed34a103789da50bcdfb758305c4391a1614303`

## VERIFIED SUCCESS — Windows hosted build and publication

- **Workflow:** `.github/workflows/blaze-gen2-v100-release.yml` in the repository root, not under project source.
- **Runner:** `windows-2025`; .NET 10 LTS; Actions `checkout@v7`, `setup-dotnet@v6`, `upload-artifact@v7`.
- **Workflow run:** https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/37995567659
- **Job:** `114040597421`; **completed / success**.
- **Publication:** tag `v1.0.0-experimental`; GitHub pre-release `408374566`; not draft; release assets independently queried through GitHub API.
- **Binary build:** `Create.exe` and `BlazePortableLauncher.exe` both self-contained Windows PE x64 executables.
- **Automated synthetic tests:** **27/27 checks passed**, including MZ/PE validation, static inventory, preserving source, binary launcher execution, argument handling, child subprocess inheritance, writable data, resource copying, relocation, missing resource nonzero exit, unsafe destination rejection, cancellation cleanup and version-folder selection.
- **Distribution package:** `Blaze-Gen2-Portable-Studio-v1.0.0-win-x64.zip`; **93,803,418 bytes**.
- **SHA256:** `c77dc63c290f2adc6ed8d97eb53cdc51d49ebf09fd4893a3303e5b78e55a91a5`
- **Second asset:** `SHA256SUMS.txt`; GitHub release contains both named assets.
- **Workflow artifact ID:** `11646278902`, `Blaze-Gen2-v1.0.0-windows-verified`, not expired at verification.
- **Independent artifact inspection:** downloaded the GitHub Actions artifact, extracted embedded release ZIP, verified SHA256 matched the GitHub release asset digest; ZIP integrity passed; both bundled executables verified MZ + PE\0\0 and AMD64 machine 0x8664; archive has **17** ZIP entries.

## Build history and diagnosis

1. Run `37995390932`, commit `6ed34a1...`: **failed** compiling WPF Studio because `System.IO` import absent (File, Path and InvalidDataException unresolved). PortableLauncher successfully compiled; no release occurred.
2. Commit `1781416c...`: added missing `System.IO`, Windows-specific target framework to Shared, actual on-disk SHA256 verification for copied files, and handover update; run `37995567659` succeeded through publication and asset verification.

## Included ZIP entries (verified, exactly 17)

```
Blaze-Gen2-Portable-Studio/Runtime/
Blaze-Gen2-Portable-Studio/Templates/
Blaze-Gen2-Portable-Studio/Create.exe
Blaze-Gen2-Portable-Studio/BlazePortableLauncher.exe
Blaze-Gen2-Portable-Studio/VERSION
Blaze-Gen2-Portable-Studio/Configs/default.json
Blaze-Gen2-Portable-Studio/Configs/launcher-template.json
Blaze-Gen2-Portable-Studio/Configs/Profiles/generic.json
Blaze-Gen2-Portable-Studio/Configs/Profiles/synthetic-app.json
Blaze-Gen2-Portable-Studio/Docs/ARCHITECTURE.md
Blaze-Gen2-Portable-Studio/Docs/CHANGELOG.md
Blaze-Gen2-Portable-Studio/Docs/COMPATIBILITY.md
Blaze-Gen2-Portable-Studio/Docs/DISKLESS_GUIDE.md
Blaze-Gen2-Portable-Studio/Docs/LICENSE
Blaze-Gen2-Portable-Studio/Docs/README.md
Blaze-Gen2-Portable-Studio/Docs/TROUBLESHOOTING.md
Blaze-Gen2-Portable-Studio/Docs/USER_GUIDE.md
```

## Functional features present in release (source + integration-verified where specified)

- WPF native Windows Studio interface, dark themed navigation, manual executable/extracted directory selection, installed-app registry discovery, wizard, progress, cancellation, profile JSON import/export and basic manager screens. **GUI clickthrough has not been tested on an interactive desktop**.
- Static file inventory and native PE imported DLL names, heuristics and compatibility classification. No universal dependency guarantee.
- Copy-first staged file and directory copying, skip/reject reparse points, absolute destination validation, non-overlap checks, SHA256 readback integrity, rollback of staging; synthetic tests pass.
- Real prebuilt self-contained WinExe launcher copies into generated package; no client SDK required, relative paths, command-line arguments, environment, child environment inheritance, logs, per-client writable, local and temporary data modes.
- Fixed, configured, manifest and numeric directory executable selection; numeric directory discovery tested. **Incomplete version updates not fully detectable.**
- No third-party games or applications are redistributed.

## NOT implemented / NOT verified

- GUI usability testing (keyboard, DPI, accessibility, animations), clean stock Windows 10/11 desktop smoke testing and actual diskless machines.
- UNC paths under real SMB permissions, real shared read-only game storage under multiple clients, changed physical drive letter; relocation to another path was tested.
- Automatic profile matching, advanced profile paths, shortcut-based discovery, registry dependency collection or restoration, app-specific AppData interception, services and driver relocation, optional runtime observation, automatic update management, app-specific official updaters, full child process-tree lifetime and session locking.
- Real-world game compatibility including Roblox; anti-cheat, DRM, system drivers, activation and licensing bypasses unsupported.
- Published GitHub release ZIP is an initial experimental artifact; synthetic tests are not proof of compatibility with arbitrary real Windows apps.

## Next priorities

1. On real Windows 10 and 11 desktops extract actual release ZIP; launch Create.exe without SDK, inspect window usability and perform manual conversion.
2. Test ordinary unpacked legitimate app and a real network share/UNC path, plus simultaneous read-only multi-client usage.
3. Add profile-aware required-file validation during version discovery and safe application-specific data migration.
4. Add registry/shortcut/known-path dependency evidence without system writes, expand synthetic tests for broken PE, symlink cycles, access denied, network permissions and invalid manifest versions.
5. Improve native UI polish and progress cancellation; evaluate code-signing and antivirus false-positive handling.

## Exact resume procedure

Open the repo and this file. Preserve `expiremental` spelling and unrelated repository files. Inspect release tag `v1.0.0-experimental` and workflow run `37995567659`. Build and test any proposed fix in a **new version/tag**, not by overwriting these verified public assets silently. Read `BUILD.md`, `COMPATIBILITY.md`, `src/Shared`, `src/Studio`, `src/PortableLauncher`, `src/Analyzer`, `src/PackageBuilder`, and `tests/Integration`. Use a root-level Actions workflow with `windows-2025` and real PE/ZIP/synthetic checks. After each meaningful change append test evidence and update feature claims accordingly; never claim diskless/game support from synthetic tests alone. For a documentation-only handover edit the current workflow excludes this handover file from push triggers.

## v1.1.0 experimental debug fix — implementation milestone (2026-10-10)

**Reported incident:** PC1 launching a shared Roblox package displaced Roblox on PC2 and appeared to transfer an authenticated account. The v1.0 launcher executed a common shared EXE directory; its configurable data location alone cannot isolate Roblox Known Folder / registry / remote account sessions.

**Safety decision:** Roblox documents Error 264 for the same account joining an experience from multiple devices. Without a clean controlled real-client reproduction, do NOT falsely claim that modifying local game files fixes Roblox's service rules. Fail closed: Roblox portability is classified Unsupported and rejected both by the package builder and newly compiled launcher. Stop using v1.0 shared Roblox packages; prefer official per-PC installation and different Roblox accounts for simultaneous play. No account-token copying.

**Implemented in source (verification pending CI):**
- Client local copy option default ON for PerClientWritable builds, with a SHA256 file manifest, copy staging, per-user/per-PC paths, and application entry point resolved in the local cache.
- Reject shared UNC/network writable data roots, shared nonisolated launch paths, and FullyLocal data on network paths.
- Per-client session file lock and no process termination of any other client.
- DONATE native sidebar route + dashboard promotion + QR regenerated from the exact URL encoded in provided PayPal screenshot: https://www.paypal.com/qrcodes/p2pqrc/AEBWES36GX9K2. Optional, never collects payment credentials.
- Additional synthetic regression tests: independent client cache, source immutability, hash mismatch, staging cleanup, Roblox builder fail-closed.
- Workflow new root file .github/workflows/blaze-gen2-v110-release.yml (windows-2025), tagged v1.1.0-experimental; old v100 workflow changed to manual-only to avoid attempting existing tag on each push.

**At this milestone:** No v1.1.0 Windows build or release has yet been verified. Finalize only after Actions job success, synthetic integration checks and published ZIP/checksum assets.
**Known limitations:** Even with a local mirror, third-party Windows Known Folder / registry changes and server-side account auth are not intercepted. Actual dual PC Roblox test not performed (Roblox is deliberately blocked). Real SMB deployment and GUI clickthrough remain unverified. Cache consumes additional local writable space. Logically isolated local cache is not a virtual machine, sandbox or official platform support.

## v1.1.0 build/test/publish verification — 2026-10-10

**STATUS: ACTUAL EXPERIMENTAL PRERELEASE PUBLISHED AND BINARY-VERIFIED.**
- Source release commit: `d3a414869b64067d78625663713b176a38d8b804`.
- Windows GitHub Actions run: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/38045063516 ; job `114192821470`; **completed / success**.
- Runner `windows-2025`; .NET 10 LTS; native WPF `Create.exe` and independent self-contained WinExe `BlazePortableLauncher.exe`.
- Synthetic integration suite: **ALL 41 CHECKS PASSED**, including new local executable cache isolation for two simulated clients, per-client data, file-manifest SHA256, detection of corrupted shared package, staging cleanup, Roblox exclusion, unmodified original.
- Pre-release URL: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v1.1.0-experimental ; GitHub tag `v1.1.0-experimental`.
- ZIP: `Blaze-Gen2-Portable-Studio-v1.1.0-win-x64.zip`; **93,817,727 bytes**.
- Published ZIP SHA256: `f8b2d9400fb02a47eaefae24d631f0a9b59a3067d77bef06d9a3f86b2cbe58fd`; second release asset `SHA256SUMS.txt`.
- Artifact `11667087989` named `Blaze-Gen2-v1.1.0-windows-verified`, independently downloaded and inspected after workflow: inner distribution ZIP contains 17 entries; archive integrity check `testzip() == None`; two EXEs have MZ, PE signature and AMD64 machine 0x8664; SHA256 independently computed matches GitHub published digest.
- Release contains `Create.exe`, `BlazePortableLauncher.exe`, `VERSION`, `Configs/default.json`, `Configs/launcher-template.json`, `Configs/Profiles/{generic,synthetic-app}.json`, `Docs/{ARCHITECTURE,CHANGELOG,COMPATIBILITY,DISKLESS_GUIDE,LICENSE,README,TROUBLESHOOTING,USER_GUIDE}`, plus Templates/ and Runtime/ folders.
- GUI runtime clickthrough and dual real-PC SMB / Roblox user sessions not verified. Roblox explicitly UNSUPPORTED and blocked. This release does **not** enable two devices to play the same Roblox account simultaneously. Use separate accounts for simultaneous play and official per-PC installation.
- Donation QR is generated in the compiled native interface from the decoded user-provided PayPal QR URL, no payment information is transmitted by Blaze.

**Resume instructions:** For further code changes, make a new release tag instead of overwriting verified v1.1.0. Read current repo source + this handover; inspect workflow run/asset verification. Enhance Roblox support only if lawful official-client integration can be independently tested on two separate physical Windows accounts and devices; never claim bypass of server-side Error 264. Add real Windows 10/11 UI smoke tests, SMB read-only and diskless reboot persistence tests before stable.
