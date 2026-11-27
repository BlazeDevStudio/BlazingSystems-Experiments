BLAZEPISONET SOFTTIMER - NATIVE WINDOWS INSTALLER
================================================

Normal installation:
  Run BlazePisonet-SoftTimer-Setup-v0.4.0.exe as Administrator.

The installer is a native Windows EXE. The operator does not need to run
PowerShell, BAT, CMD, or a separate setup script.

Installed components:
  BlazePisonet.SoftTimer.exe
  BlazePisonet.SoftTimer.Watchdog.exe
  Windows Start Menu shortcut
  Optional desktop shortcut
  Automatic logon startup tasks for SoftTimer and its watchdog
  Local-subnet firewall rule for the default centralized Pisonet port 8765

Uninstall:
  Windows Settings -> Apps -> Installed apps -> BlazePisonet SoftTimer
  or use the normal BlazePisonet SoftTimer uninstaller created by Setup.

SoftTimer preserves ProgramData state by default during uninstall so paid-time
state, account hashes and hardware pairing data are not silently destroyed.
Delete that data manually only when intentionally resetting the installation.

Portable package:
  A portable ZIP is also published for diagnostics and controlled deployments.
  It contains EXEs directly and no PowerShell installer. For normal Pisonet
  installation, use the Setup EXE because it creates the startup/recovery entries.
