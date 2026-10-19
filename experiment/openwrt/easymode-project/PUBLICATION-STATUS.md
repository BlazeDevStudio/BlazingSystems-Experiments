# EasyMode publication status

Checked against the `easymode-v7-production` branch after commit `fa11ca30f71bec513baf9f0f90e4b63f0fab83b8`.

## Edition parity

The six edition builds share the v7 Traffic Intelligence monitoring component and adapt its visible measurements to detected hardware capabilities. This does **not** make each edition a full copy of the R281 EasyMode management portal. The R281 portal includes board- and modem-specific controls which have not been ported and validated across the other editions.

| Edition | Published status | R281 management parity |
|---|---|---|
| Generic | Shared capability-based Traffic Intelligence package/archive | No |
| AP | Shared monitor; only locally observable AP/client traffic is reported | No |
| Router | Shared monitor with supported WAN, Wi-Fi, and device counters | No |
| Cellular | Shared monitor; cellular measurements depend on available modem interfaces | No |
| Switch | Shared monitor limited to observable interface/VLAN counters | No |
| PC | Shared monitor with expanded storage/build capability | No |

The R281 source snapshot and `EasyMode-v10.0.0-R281-app-update.tar.gz` are published under `releases/v10.0.0-r281/`. The archive is an application update gated to the verified Notion R281 / OpenWrt 24.10.8 profile. It is not a generic installer or firmware image.

## R281 one-click installer and firmware

There is no current one-click R281 unlock-and-OpenWrt installer, no public device-specific unlock kit, and no v10 reset-persistent R281 firmware image in this repository. The only similarly named repository artifact is a historical encrypted v4.2.3 installer archive; it is not the current kit and is not represented as a working v10 installer. The regular source installers under `installers/` install the shared monitoring packages; they do not unlock a modem or flash firmware.

This repository status does not assert that hard-reset persistence has been installed or hardware-tested. The v10 application update resides in writable overlay storage and can be removed by factory reset. A reset-persistent image requires a board-compatible firmware build and verified reset/recovery testing.

## Publication boundary

Public source and generic installers must not contain passwords, Wi-Fi keys, private SSH/TLS keys, SIM/IMEI or unlock records, live SMS/log data, or device-specific recovery images. These values are not required to build the shared editions. Any device-specific installer work must use a reviewed, sanitized source package and explicit board/image validation before publication.
