# Architecture

EasyMode 5 uses one shared core plus capability-driven modules and edition profiles.

- `core/` — detection, safe-apply helpers and shared runtime.
- `modules/` — optional network/Wi-Fi/cellular/switch/VLAN/messages/diagnostics/hardware modules.
- `editions/` — small manifests defining module sets and UX emphasis.
- `installers/` — browser, Windows and OpenWrt installation families.
- `releases/` — immutable numbered release output.

Changing a profile changes module/UI availability and must not rewrite unrelated OpenWrt configuration merely because another profile was selected.
