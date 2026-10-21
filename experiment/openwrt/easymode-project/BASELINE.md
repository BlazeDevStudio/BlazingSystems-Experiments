# EasyMode source baselines

## R281 management application — installed reference: **10.0.0**

- Authoritative current R281 source: `releases/v10.0.0-r281/` on branch `easymode-v7-production`.
- Built from the working R281 4.2.6 management snapshot and its later features/fixes. Do **not** rebuild an existing V10 release from 4.2.6 or overwrite the published release.
- The 2026-10-19 audit documents EasyMode V10 installed on `notion,r281`, OpenWrt 24.10.8; homepage, assets, services and SIM connectivity passed immediate read-only checks.
- R281 V10 is an application update in overlay; **not firmware and not factory-reset persistent**. Long-duration stability, full installed-file readback, reboot/reset acceptance and other-board compatibility remain unverified.

## Shared Traffic Intelligence — development line: **7.0.0**

- Source: `traffic/`, six capability-specific editions (Generic, AP, Router, Switch, PC, Cellular).
- `VERSION` and `MANIFEST.json` at project root refer to this shared line; their 7.0.0 identifier does not supersede or demote R281 V10.
- The shared monitor does not provide all R281 V10 modem, Wi-Fi, repeater, device-access and SMS management features on arbitrary hardware.

## Historical baselines and compatibility lessons

- `releases/v4.2.6-r281-consolidated/` is the prior consolidated R281 management source and must be preserved.
- Earlier 4.1.4 restored `ubus` backend `blaze` with `blaze.status` and exposed router-side ucode constraints.
- R281 ucode compatibility: avoid default arguments such as `args={}`, router-side `??` and unsupported three-variable `for ... in`; validate source with device ucode and preserve frontend RPC / backend / ACL parity.
- `5.0.0-alpha.1` was a historical incomplete six-edition toolkit scaffold, not the replacement for the live R281 management application.

See `releases/v10.0.0-r281/AUDIT.md`, `releases/v10.0.0-r281/HANDOFF.md` and `PUBLICATION-STATUS.md` for specific evidence and remaining acceptance gates.
