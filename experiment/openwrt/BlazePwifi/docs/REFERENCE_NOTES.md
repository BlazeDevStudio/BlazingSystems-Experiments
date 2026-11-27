# Public reference notes

BlazePwifi is implemented from its own source code while using public, documented interfaces and open-source projects as engineering references.

## Reference categories

- OpenWrt 25.12 documentation and source for UCI, uHTTPd, firewall4/nftables, DSA/VLAN configuration, image building and supported hardware.
- Android Developers / Android Enterprise documentation for fully managed devices, Device Owner provisioning, lock task mode and dedicated-device policy.
- Espressif and Arduino documentation for ESP8266/ESP32 Wi-Fi, persistent settings and flash filesystems.
- libgpiod documentation for Linux GPIO character-device access.
- Tabler's MIT-licensed core UI components for Standard/Full administration, with optional third-party chart/plugin bundles excluded unless separately reviewed.
- open-source captive-portal projects for general captive-detection and portal-flow interoperability concepts.

## Design rules taken from public behavior

- Client accounts must not depend only on a MAC address because modern devices can use private/random MAC addresses.
- A physical coin event needs an unambiguous client target and replay/idempotency protection.
- Provider/walled-garden hosts change over time and therefore belong in configuration.
- Network topology and VLAN assignment stay separate from monetary accounting.
- Low-flash routers should not be forced to carry optional analytics, large UI frameworks or heavyweight traffic-shaping packages.
- Management interfaces stay local by default and must not rely on a universal production credential.

## Clean-room boundary

No closed server executable, licensing system, private key, database, proprietary artwork, JavaScript bundle, firmware image or private controller firmware is copied into BlazePwifi.
