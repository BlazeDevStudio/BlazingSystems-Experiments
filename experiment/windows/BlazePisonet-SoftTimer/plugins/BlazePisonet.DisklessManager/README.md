# BlazePisonet Diskless Manager — Optional Add-on

This is a **separately compiled Windows application**. It is not loaded into the paid timer process and is never required for BlazePisonet SoftTimer to run, lock a kiosk, recognize hardware, or preserve paid time.

The original diskless source was extracted from the historical `pisonet-diskless-manager` branch. The main customer branch must **not** merge that older embedded diskless implementation.

## Features

- FOG server inventory and explicitly confirmed imaging requests that may overwrite a client disk.
- Read-only targetd iSCSI mapping inspection and restricted LIO SSH status.
- Per-client iSCSI target/initiator profiles, DHCP option 017 and iPXE script generation.
- Separate profile file: `%ProgramData%\BlazeSystems\BlazePisonetDisklessManager\profiles.json`.
- Explicit read-only legacy-profile import from SoftTimer's old `config.json`; only copied profiles are written into the new add-on store.

## Installation

Publish `BlazePisonet.DisklessManager.csproj` for Windows x64. Install the add-on EXE under `%ProgramFiles%\BlazeSystems\BlazePisonet Diskless Manager\BlazePisonet.DisklessManager.exe` to enable the SoftTimer administrator **Add-ons → Open Diskless Manager** command. It can also run independently. There is no automatic add-on installer yet.

## Operational safety

This add-on does not configure PXE, iSCSI, CHAP secrets, DHCP, storage ACLs, or real Windows diskless boot. Those require a separately provisioned server and physical acceptance tests. FOG deployment may overwrite data and requires explicit operator confirmation. Do not deploy to a customer without checking host/backup and physical storage isolation.

SoftTimer's timer and financial protocols remain unchanged. The add-on preview is not a production release.
