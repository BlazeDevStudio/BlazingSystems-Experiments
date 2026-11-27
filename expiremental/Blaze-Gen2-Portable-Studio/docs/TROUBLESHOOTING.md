# Troubleshooting

- Create.exe does not start: verify Windows 10/11 x64 and extract the full ZIP. Check Windows event logs.
- Analysis fails: selected folder may be inaccessible or contain junctions, reparse points or protected content.
- Build fails: check destination does not exist, no source/destination overlap, adequate space, and source readability. Staging is deleted after a failed build.
- Launcher cannot find its EXE: inspect PortableConfig.json (relative names), App/Executables and requiredFiles. Failed launches log under %LOCALAPPDATA%/BlazeGen2/Errors.
- Game fails after launching: external runtimes, registry, anti-cheat, machine licenses and additional data may be needed. This tool does not bypass those dependencies.
- Shared client loses saves: test storage persistence and the PerClientWritable data root.

