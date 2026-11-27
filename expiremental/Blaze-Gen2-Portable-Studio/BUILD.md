# Windows build and QA

Requires a Windows 10/11 x64 development environment, supported .NET 10 SDK, and Git.

```powershell
dotnet publish src/PortableLauncher/PortableLauncher.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o out/launcher
dotnet publish src/Studio/Studio.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o out/studio
dotnet publish tests/SyntheticApp/SyntheticApp.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -o out/sample
dotnet run --project tests/Integration/Integration.csproj -c Release -- out/sample/SyntheticApp.exe out/launcher/BlazePortableLauncher.exe out/studio/Create.exe
```

Execute commands from this project's root directory (the path under `expiremental/`).

CI workflow: repository-root `.github/workflows/blaze-gen2-v100-release.yml`. It runs on `windows-2025`, validates real PE headers, launches synthetic app packages, stages compiled binaries, verifies ZIP and hash, uploads artifacts, and conditionally creates a prerelease on a green main branch run.

A green compiler by itself does not establish GUI usability or successful diskless-client deployment.

