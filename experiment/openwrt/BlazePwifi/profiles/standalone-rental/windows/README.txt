BlazePwifi Standalone Rental Server - Windows One-Click Installer

1. Extract the ZIP completely.
2. Double-click Install-BlazePwifi-Rental.bat.
3. Enter the OpenWrt router IP/hostname, SSH username and password.
4. Confirm the router SSH host-key fingerprint on first connection.
5. The installer uploads the pinned OpenWrt bundle, detects R281/EW1200G Pro/generic OpenWrt, installs the full BlazePwifi software in Rental Standalone mode, and opens the Rental console.

Normal Rental Standalone installation does not intentionally modify network, wireless or firewall UCI packages.

After installation:
  Rental console: https://ROUTER-IP/rental/
  Android server: http://ROUTER-IP

The SSH password is written only to a temporary local file for plink/pscp and is overwritten/deleted at the end of the run.

The package includes PuTTY command-line SSH tools (plink/pscp) solely for deployment. See the included PuTTY licence file.


rc.3 hotfix:
- First-time PuTTY host-key output is captured instead of becoming a PowerShell NativeCommandError.
- A GUI trust dialog is shown automatically on the first SSH connection.
- No manual PuTTY launch or host-key pre-caching is required.
