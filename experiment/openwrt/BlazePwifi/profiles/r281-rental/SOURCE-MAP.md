# Source map

The R281 profile points to the exact shared BlazePwifi blobs for:

- `common.sh` ← `openwrt/rootfs/usr/lib/blazepwifi/common.sh`
- `auth.sh` ← `openwrt/rootfs/usr/lib/blazepwifi/auth.sh`
- `config.sh` ← `openwrt/rootfs/usr/lib/blazepwifi/config.sh`
- `rental.sh` ← `openwrt/rootfs/usr/lib/blazepwifi/rental.sh`
- `controller.sh` ← `openwrt/rootfs/usr/lib/blazepwifi/controller.sh`
- `/cgi-bin/rental` ← the shared BlazeRental server endpoint
- `/cgi-bin/vendo` ← the shared ESP8266/ESP32 controller endpoint
- QR library/vendor license ← shared BlazePwifi UI vendor assets

Profile-specific adapters:

- `root/www/cgi-bin/rental-admin` — rental/controller-only adaptation of the BlazePwifi admin API.
- `root/www/cgi-bin/rental-login`, `rental-session`, `rental-logout` — BlazePwifi authentication/session flow adapted to the R281's existing HTTPS listener.
- `root/www/rental/index.html` — R281 rental-focused management UI using the real BlazePwifi APIs.
- Installer/uninstaller — deployment glue only.

No parallel rental accounting engine is included.
