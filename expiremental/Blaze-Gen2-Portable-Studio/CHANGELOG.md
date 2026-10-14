# Changelog
## Unreleased 1.2.0 (Roblox concurrent station launch)
- Roblox is no longer rejected by analysis, package generation, or the launcher. Compatibility warnings remain visible; unsupported dependencies no longer prevent the user from building a package.
- Roblox packages automatically use per-client writable state, a verified local executable cache, and station-private APPDATA / LOCALAPPDATA overrides.
- Client writable data paths now include `BLAZE_STATION_ID` (fallback: computer name), allowing diskless boot managers to assign stable unique station identities to cloned images.
- Removed the exclusive lock held for the entire application lifetime. Launching a second instance no longer makes Blaze refuse to run it or close the first instance.
- Added Windows integration coverage for two simultaneous Roblox-named fixtures, independent station folders, and concurrent instances from the same station.
- Real Roblox service behavior, Windows registry/profile isolation, and two physical diskless PCs remain unverified; Blaze does not bypass Roblox account/session policy.

## 1.1.0 (Experimental — diskless isolation / session safety)
- Per-client copy of application binaries into local client cache before process launch, content-addressed by bundled SHA256 manifest; separated per machine and Windows user.
- New manifest generated and verified; failures fail closed and clean incomplete staging.
- Reject sharing writable package data or unisolated executable from network paths.
- Roblox packages now explicitly unsupported and blocked: no account/session migration across clients, no unsupported "fix" for Roblox Error 264.
- Visible native Studio DONATE section and donation dashboard card with QR re-encoded from user-supplied PayPal QR.
- Synthetic independent-client cache, server source preservation, corruption, safety regression tests.

## 1.0.0 (Experimental source candidate)
- Initial WPF generator source; analyzer, package staging, reusable WinExe launcher.
- Registry-based application discovery and local source selection.
- Per-client/portable/temporary data policies and version-folder resolution.
- Synthetic process execution and packaging QA test harness.
- Release requires confirmed Windows Actions execution and published assets. See handover for actual status.

