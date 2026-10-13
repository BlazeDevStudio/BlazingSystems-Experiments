#!/bin/sh
# Run on OpenWrt with ucode, from this tests directory. Never uses live UCI.
set -eu
mkdir -p /tmp/ssid-test/config
cp ../../releases/v4.2.6-r281-consolidated/root/usr/share/blaze/ssid.uc /tmp/ssid-test/ssid.uc
cat >/tmp/ssid-test/config/wireless <<'EOF'
config wifi-device 'radio0'
 option type 'mac80211'
config wifi-device 'radio1'
 option type 'mac80211'
config wifi-iface 'primary'
 option device 'radio0'
 option network 'lan'
 option mode 'ap'
config wifi-iface 'sta'
 option device 'radio1'
 option mode 'sta'
EOF
cat >/tmp/ssid-test/config/network <<'EOF'
config interface 'lan'
 option proto 'static'
config interface 'blaze_repeat'
 option proto 'static'
EOF
cat >/tmp/ssid-test/config/blaze <<'EOF'
config main 'main'
 option mode 'standard'
 option wifi_uplink_mode 'relay'
 option wifi_relay_scope 'ssid'
EOF
ucode ssid.uc
