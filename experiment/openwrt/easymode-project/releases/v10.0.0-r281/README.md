# EasyMode v10.0.0 — R281 application profile

This source snapshot recreates the EasyMode application currently installed on the verified Notion R281, including SMS, cellular controls, bands, Wi-Fi, repeater, ports/VLAN, device filtering, sessions, and Traffic Intelligence navigation. Version 10 is a product revision label; it does not imply universal hardware support.

## Install on the verified R281

The archive is an application update, not firmware. It supports only `notion,r281` running OpenWrt 24.10.8 and EasyMode 4.2.6 or v10. Run `./install.sh --check`, then `./install.sh --apply`. The script backs up replaced files, preserves UCI/network/Wi-Fi settings and SMS histories, and does not reboot or reload networking. Roll back by extracting the printed `/root/easymode-before-v10-*.tar.gz` archive and restarting rpcd/EasyMode services.

## Other OpenWrt devices

The R281 application contains modem, switch-port, antenna, and repeater integrations that are specific to this board and its installed packages. The installer refuses other boards. For other devices, use the shared capability-detected Traffic Intelligence edition under `traffic/`; that does not reproduce every R281 management feature. A unified cross-device control profile and hardware-specific validation are still required before claiming the same complete experience on arbitrary OpenWrt hardware.

## Reset and firmware limits

An application installed into `/overlay` is erased by a factory reset. Hard-reset persistence requires these files and defaults to be built into a board-compatible firmware image under `/rom`. This release contains no R281 flashable image and does not claim reset-proof behavior. Back up configuration and SMS archives before reset or firmware replacement.

See `AUDIT.md`, `HANDOFF.md`, `SOURCE-MANIFEST.json`, and `SHA256SUMS`. No live logs, credentials, SMS, or SIM identity records are included.
