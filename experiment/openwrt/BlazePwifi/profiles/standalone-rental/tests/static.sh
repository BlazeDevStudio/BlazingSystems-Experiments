#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

for f in "$ROOT/openwrt/install.sh" "$ROOT/openwrt/upgrade-to-full.sh" "$ROOT/openwrt/uninstall.sh" "$ROOT/openwrt/install-r281.sh" "$ROOT/openwrt/install-ew1200g-pro.sh" "$ROOT/openwrt/install-generic-openwrt.sh" "$ROOT/openwrt/rental-profile"; do
  sh -n "$f"
done

! grep -Eq 'uci (set|add_list|delete) (network|wireless|firewall)\.' "$ROOT/openwrt/install.sh"
! grep -Eq 'uci commit (network|wireless|firewall)' "$ROOT/openwrt/install.sh"

grep -q "edition='rental-standalone'" "$ROOT/openwrt/install.sh"
grep -q "enabled='0'" "$ROOT/openwrt/install.sh"
grep -q "admin_port='443'" "$ROOT/openwrt/install.sh"
grep -q 'Rental console:.*rental/' "$ROOT/openwrt/install.sh"
grep -q 'Android server:.*http://' "$ROOT/openwrt/install.sh"
! grep -q ':8090' "$ROOT/openwrt/install.sh"
! grep -q ':8444' "$ROOT/openwrt/install.sh"

grep -q 'blazepwifi-rental-upgrade --full' "$ROOT/README.md"
grep -q 'full-uci-defaults.sh' "$ROOT/openwrt/install.sh"
grep -q 'FULL_DEFAULTS=/usr/share/blazepwifi/full-uci-defaults.sh' "$ROOT/openwrt/upgrade-to-full.sh"
grep -q 'policy_sig_v3' "$ROOT/esp8266/BlazeRentalStandalone8266/BlazeRentalStandaloneCore.h"
grep -q 'mode=="rental_coin"' "$ROOT/esp8266/BlazeRentalStandalone8266/BlazeRentalStandaloneCore.h"
grep -q 'mode=="coin_interface"' "$ROOT/esp8266/BlazeRentalStandalone8266/BlazeRentalStandaloneCore.h"
grep -q 'remoteCoins' "$ROOT/esp8266/BlazeRentalStandalone8266/BlazeRentalStandaloneCore.h"
grep -q 'BlazeRental-Setup-' "$ROOT/esp8266/BlazeRentalStandalone8266/BlazeRentalStandaloneCore.h"
grep -q 'for(int attempt=1;attempt<=5;attempt++)' "$ROOT/esp8266/BlazeRentalStandalone8266/BlazeRentalStandaloneCore.h"
! grep -q 'BLAZE_SLOT_COUNT' "$ROOT/esp8266/BlazeRentalStandalone8266/BlazeRentalStandaloneCore.h"
grep -q 'Remote ESP coin binding' "$ROOT/openwrt/rental-standalone.html"

test -f "$ROOT/windows/Install-BlazePwifi-Rental.bat"
test -f "$ROOT/windows/Install-BlazePwifi-Rental.ps1"
grep -q 'pwfile' "$ROOT/windows/Install-BlazePwifi-Rental.ps1"
grep -q 'hostkey' "$ROOT/windows/Install-BlazePwifi-Rental.ps1"

echo "Standalone Rental rc.2 static checks passed"
