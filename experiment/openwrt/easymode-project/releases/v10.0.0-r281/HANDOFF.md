# EasyMode v10.0.0 handoff

- Source: this directory, copied from `releases/v4.2.6-r281-consolidated/root` and updated to v10.0.0.
- Reference target: verified Notion R281 (`notion,r281`), OpenWrt 24.10.8, kernel 6.6.144.
- Current runtime after deployment: EasyMode 10.0.0 on the verified R281; online cellular interface; 30,252 KiB MemAvailable at the pre-install audit; 90,624 KiB free overlay before the package backup.
- Confirmed recovery issue and candidate fixes are in `AUDIT.md` and `root/usr/libexec/blaze-health`.
- Regression tests: `traffic/tests/health-routing.sh`; executed on the R281 against the candidate copied to `/tmp`. Installer `--check` passed on the exact target before applying.
- Build: `python traffic/tools/build-r281-v10.py`; package is `openwrt/EasyMode-v10.0.0-R281-app-update.tar.gz`.
- Installer preflight is exact-board and exact-release gated. It preserves UCI, network/Wi-Fi settings, and private `/etc/blaze` data. No reboot is requested.
- Live installation verified: EasyMode version file 10.0.0, root page version marker, JS/CSS HTTP 200, health and SMS archive services active, and SIM ping passed after installation. Backup: `/root/easymode-before-v10-20261019-081032.tar.gz`. No reboot or network config change. A complete per-file source-to-device hash comparison was not run.
- Not complete: extended stability observation, hardware reset persistence, R281 firmware build, or universal parity on other hardware. The app archive is not firmware.
- Private current router logs and collected state remain outside GitHub.
