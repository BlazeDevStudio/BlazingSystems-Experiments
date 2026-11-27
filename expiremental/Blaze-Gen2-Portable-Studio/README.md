# Blaze Gen2 Portable Studio

**v1.1.0 • Experimental • Windows 10/11 x64**

A native Windows desktop utility that builds **best-effort portable copies** of legitimately owned Windows applications. Built for portable utilities, extracted games, and diskless-client deployment experiments.

> **Experimental:** Static analysis cannot demonstrate that any particular game is portable. Only the synthetic fixture suite is eligible for automated compatibility claims. This tool does not modify executables, remove DRM, install drivers, or bypass anti-cheat.

## What is implemented in source

- Native WPF desktop workflow: discovery, static analyzer, conversion wizard, profiles view/editor, basic package inspection, diagnostics and settings.
- Windows uninstall registry discovery (32/64-bit machine and user views), folder executable discovery, manual EXE selection.
- Recursive file inventory with symlink rejection, PE direct import DLL enumeration, heuristic compatibility warnings and engineering-level assessments.
- Copy-first staging, source/destination containment checks, SHA-256 buffer verification, cancellation, independent relative-path launcher, environment configuration and per-client/portable/temporary data modes.
- Reusable self-contained .NET launcher copied and renamed for each package. No .NET SDK required at client run time.
- Fixed, configured, manifest and semantic-version folder executable selection.
- Synthetic test applications and automated integration harness in the Windows build workflow.

## Download and use

The downloadable release **must be obtained from GitHub Releases only when the workflow has published and verified the ZIP**. Do not treat the presence of source code as proof of a compiled release.

1. Extract the release ZIP to an empty directory.
2. Run `Create.exe` (no separate .NET runtime required).
3. Browse a source EXE, choose a registered app, or choose an extracted program directory.
4. Analyze the application and read its warnings.
5. Select a new destination folder, arguments and writable-data mode; approve the copy.
6. The generated portable EXE will be placed at the root of the newly created package.
7. Test the output on a clean client and review logs.

The source application's entire containing directory is copied without following junctions or symlinks. Always check that the selected directory contains only content you're licensed to relocate.

## Package directory

```text
ExamplePortable/
  ExamplePortable.exe
  PortableConfig.json
  App/Executables/...
  Data/Roaming/  Data/Local/  Data/Config/  Data/Saves/
  Runtime/  Cache/  Logs/  Backups/
```

## Build

The Windows GitHub Actions workflow compiles on `windows-2025` using the .NET 10 LTS SDK. See [BUILD.md](BUILD.md) and [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md).

## v1.1.0 diskless safety debug fix

The v1.0.0 launcher ran directly from the shared packaged application directory. The v1.1.0 builder defaults **PerClientWritable** packages to client-local execution: each Windows computer/user gets a content-addressed local cache of packaged files verified against FileManifest.json, while the source on the server remains unchanged. The local cache needs enough writable disk space. Files are cached until the package manifest changes; this is not a game updater. No per-client account migration or shared app-state changes are performed.

**Roblox is blocked for portable conversion and execution in this experimental release.** Roblox documents [Error 264](https://en.help.roblox.com/hc/en-us/articles/36665660855700-Error-Code-264-Same-account-launched-experience-from-different-devices): the same account cannot enter the same game from multiple devices simultaneously. No generator-side data redirection can disable that service rule. Use the official Roblox client, distinct Roblox accounts and separate Windows profiles per gaming PC. Stop using any old v1.0 portable Roblox packages; v1.1 cannot retroactively protect their launchers.

## Support development

PayPal donation is completely optional. A **DONATE** section is clearly visible in the native Studio sidebar and the dashboard, including the PayPal QR based on the user-supplied image. The payment link is [PayPal donation](https://www.paypal.com/qrcodes/p2pqrc/AEBWES36GX9K2). The Studio never processes your card information or requests credentials.

## Caveats

This is not an application virtualization engine. It does not capture runtime registry changes, system services, drivers, hidden update dependencies, COM registrations, protected game assets, installers, or universal Known Folder writes. Anti-cheat, activation, licensing, or cloud-dependent applications can fail. Read [COMPATIBILITY.md](COMPATIBILITY.md).

## Layout

Core projects: `src/Studio`, `src/Analyzer`, `src/PackageBuilder`, `src/PortableLauncher`, `src/Shared`.
Modular analysis and packaging code resides in the shared assembly under the functional subfolders above.

## License

Generator source MIT-licensed. Users are responsible for third-party software licenses and intellectual-property rights. No commercial games are distributed here.

