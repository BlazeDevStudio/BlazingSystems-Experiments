# Diskless deployment guide (v1.1.0)

The published v1.1.0 release blocks Roblox. The current development branch allows it and automatically uses a station-local executable copy and private APPDATA / LOCALAPPDATA roots. Do not treat this branch as a verified Roblox release: the real two-PC Roblox test is still required.

For each station:
1. Give the PC a unique Windows computer name or set a unique `BLAZE_STATION_ID`.
2. Configure the diskless system with a private writable overlay for that station's Windows profile. Persist `%LOCALAPPDATA%\\BlazeGen2\\Clients\\<station-id>\\<package-id>` across reboots, and keep its Windows profile and HKCU hive private to that PC.
3. Use a different Roblox account on each station and sign into the official client separately. Never copy a signed-in Roblox profile or browser profile between stations.
4. Use PerClientWritable mode. Roblox packages force a private local client cache and app-data environment roots even if the option is unchecked.

Roblox documents [Error 264](https://en.help.roblox.com/hc/en-us/articles/36665660855700-Error-Code-264-Same-account-launched-experience-from-different-devices) for the same account joining the same game from multiple devices. Blaze cannot change this service-side behavior. The launcher does not virtualize HKCU, all Windows Known Folder APIs, or browser profile storage, so the diskless platform must keep each station's profile overlay separate.

For other eligible applications, use PerClientWritable mode and keep client-local execution enabled. A network/UNC writable data root is rejected.


For a shared application share such as Z:\\Games\\Portable, generate a package locally, test it, then deploy it to a share with read-only permissions for client accounts. Keep DataMode as PerClientWritable. Each package config includes a random PackageId and writes under %LOCALAPPDATA%\\BlazeGen2\\Clients\\<station-id>\\<PackageId>. If that location is nonpersistent after reboot, settings and saves will be lost. Configure a persistent writable data location in PortableConfig.json on each client if needed. Use FullyLocal only on writable persistent package storage. TemporarySession deletes its data on normal target exit but can leave remnants after forced termination.

No driver/service installation, anti-cheat support, or simultaneous-session locking is provided. Test with multiple accounts and multiple clients before wider use. UNC path compatibility is intended, but not validated by CI.

