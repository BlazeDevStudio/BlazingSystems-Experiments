# Compatibility

## OpenWrt
- 24.10.x: primary R281 compatibility baseline; `opkg` generation.
- 25.12+: package manager changed to `apk`; installers must detect it.

## R281 rules
- Avoid ucode default function parameters (`args={}`).
- Avoid router-side `??`.
- Avoid the previously failing 3-variable `for ... in`.
- Validate imported `common.uc` as a module and executable `.uc` files with target `/usr/bin/ucode` where possible.
- Frontend RPC, backend RPC and ACL permissions must stay 1:1.

## Browser installer
A normal local HTML file cannot open arbitrary raw SSH/Telnet TCP sockets. The offline installer uses browser-compatible HTTP JSON-RPC (`/ubus`) when enabled and gives a package/bootstrap fallback otherwise.
