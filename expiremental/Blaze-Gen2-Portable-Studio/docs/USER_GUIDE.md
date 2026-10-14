# User guide

This v1.2.0 experimental candidate is source-only until a new Windows build and release is verified. Build it using [BUILD.md](../BUILD.md). On Application Discovery, choose an extracted app folder or EXE. The whole directory containing the selected executable is used as the copy root. Review analyzer findings; warnings never block building. Choose a **new nonexistent** destination under Portable Builder. Conversion is copy-first and leaves the source untouched. For Roblox, Blaze automatically uses per-client writable data, a local executable cache, and APPDATA / LOCALAPPDATA overrides. Set a unique `BLAZE_STATION_ID` per diskless station and use separate Roblox accounts and Windows profiles. Test the generated EXE on a clean client; the synthetic concurrent-launch test is not a real Roblox test.

Profile editor imports and exports JSON definitions. Automatic profile matching/application is not implemented. Modify advanced version settings in PortableConfig.json with suitable technical experience.

