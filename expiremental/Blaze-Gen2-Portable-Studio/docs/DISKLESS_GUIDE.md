# Diskless deployment guide (v1.1.0)

**Roblox is not a supported portable target.** Before testing, stop using old v1.0 portable Roblox packages. Roblox may disconnect another PC if the same Roblox account attempts to join a game on multiple devices. Running two PCs from the same local/network files is a separate data collision issue; the v1.1 client-local cache guards against that file-level problem for other eligible programs, but does not bypass Roblox session rules. Use Roblox official per-client installations and separate accounts.

**For other eligible applications**, use PerClientWritable mode and keep "Diskless safety: run copied application from this PC's local cache" enabled. First launch validates and caches package files in each machine's local Windows user directory. This requires sufficient per-client disk/overlay space; data persistence still depends on your diskless setup. A network/UNC data root is rejected for safety. Legacy v1.0 packages do not opt in automatically and must be rebuilt.


For a shared application share such as Z:\\Games\\Portable, generate a package locally, test it, then deploy it to a share with read-only permissions for client accounts. Keep DataMode as PerClientWritable. Each package config includes a random PackageId and writes under %LOCALAPPDATA%\\BlazeGen2\\Packages\\<PackageId>. If that location is nonpersistent after reboot, settings and saves will be lost. Configure a persistent writable data location in PortableConfig.json on each client if needed. Use FullyLocal only on writable persistent package storage. TemporarySession deletes its data on normal target exit but can leave remnants after forced termination.

No driver/service installation, anti-cheat support, or simultaneous-session locking is provided. Test with multiple accounts and multiple clients before wider use. UNC path compatibility is intended, but not validated by CI.

