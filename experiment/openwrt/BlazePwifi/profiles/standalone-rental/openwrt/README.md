# OpenWrt Rental Standalone — rc.2

The installer is intentionally **network-neutral**. It does not change the router's WAN, LAN, Wi-Fi, cellular, repeater or firewall UCI packages.

After installation:

- existing router/basic UI stays at whatever routes the device already uses;
- BlazePwifi Rental management is added at `https://LocalIP/rental/`;
- BlazeRental phones use `http://LocalIP` as their server URL;
- authenticated remote ESP coinslot interfaces use `http://LocalIP:4455/cgi-bin/vendo`.

The complete BlazePwifi v0.5 payload is installed, but the hotspot core is disabled. Conversion to full BlazePwifi is explicit:

```sh
/usr/sbin/blazepwifi-rental-upgrade --full
```

Only that conversion step is allowed to activate BlazePwifi firewall/hotspot ownership.

Supported installer target hints are `r281`, `ew1200g-pro`, `generic`, and `auto` (default). OpenWrt 24.10.x and 25.12.x are accepted by the RC installer.

The preferred release path is the Windows one-click installer package; manual tarball installation remains supported.
