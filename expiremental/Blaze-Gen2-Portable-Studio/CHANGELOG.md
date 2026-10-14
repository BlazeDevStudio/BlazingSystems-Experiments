# Changelog

## Unreleased — Roblox station isolation
- Remove the blanket Roblox analyzer, builder, and launcher block.
- Force Roblox packages into per-station local executable caching and private APPDATA / LOCALAPPDATA roots.
- Add a station ID override via `BLAZE_STATION_ID`; default to the Windows computer name.
- Create station-local snapshots for legacy packages without a bundled file manifest.
- Add synthetic checks for separate station roots and app-data environment redirection.
- Real two-PC Roblox account testing is still required; this is not included in CI.

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

