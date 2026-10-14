# Diskless deployment guide (v1.2.0 experimental candidate)

Roblox is no longer blocked by Blaze Gen2. For each diskless station, use a different Roblox account, a separate Windows user profile, and a persistent client-local writable overlay. Configure the diskless boot/session manager to provide a stable, unique `BLAZE_STATION_ID` to each station. If unset, Blaze uses the computer name; cloned clients with the same name must be assigned distinct station IDs.

For Roblox packages, the builder automatically selects PerClientWritable data, enables a verified per-station local executable cache, and redirects APPDATA / LOCALAPPDATA into that station's writable data root. The shared application package can therefore remain on a read-only server share while each station gets its own local copy and user-data folders. Leave enough local writable space for the full application copy and cache.

This is local best-effort isolation, not a Windows sandbox. It cannot redirect Windows registry hives, APIs that resolve Known Folders through Windows, services, or browser profiles. It also cannot change Roblox's server-side account/session rules; Roblox documents [Error 264](https://en.help.roblox.com/hc/en-us/articles/36665660855700-Error-Code-264-Same-account-launched-experience-from-different-devices) for the same account joining an experience from multiple devices. Do not reuse one Roblox account across simultaneous stations.

The launcher no longer holds an exclusive package lock while a game is open, so Blaze itself permits multiple launches. A third-party app can still enforce its own single-instance behavior. The synthetic regression suite checks launcher concurrency and station data separation; this candidate has not yet been tested with two real Roblox clients on separate diskless PCs.

For other applications, review the analyzer warnings, select PerClientWritable for shared package storage, and keep local executable isolation enabled. A writable data location on a server share is rejected. Persistence after reboot depends on the diskless system's write-overlay configuration. Always deploy the application package with read-only permissions for client users.
