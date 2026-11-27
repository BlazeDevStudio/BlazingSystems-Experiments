#!/bin/sh
set -eu
json_escape(){ printf '%s' "$1" | sed 's/\\/\\\\/g;s/"/\\"/g'; }
board="unknown"; model="unknown"; release="unknown"; arch="unknown"
[ -r /tmp/sysinfo/board_name ] && board=$(cat /tmp/sysinfo/board_name)
[ -r /tmp/sysinfo/model ] && model=$(cat /tmp/sysinfo/model)
[ -r /etc/openwrt_release ] && release=$(sed -n "s/^DISTRIB_RELEASE='\(.*\)'/\1/p" /etc/openwrt_release)
arch=$(uname -m 2>/dev/null || echo unknown)
manager=none; command -v apk >/dev/null 2>&1 && manager=apk; command -v opkg >/dev/null 2>&1 && [ "$manager" = none ] && manager=opkg
wifi=0; [ -d /sys/class/ieee80211 ] && [ "$(find /sys/class/ieee80211 -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)" -gt 0 ] && wifi=1
cellular=0
for p in /dev/cdc-wdm* /dev/ttyUSB* /dev/ttyACM*; do [ -e "$p" ] && cellular=1 && break; done
if command -v ubus >/dev/null 2>&1; then ubus call network.interface dump 2>/dev/null | grep -Eqi 'wwan|qmi|mbim|ncm|rndis|cell' && cellular=1 || true; fi
nics=0; [ -d /sys/class/net ] && nics=$(find /sys/class/net -mindepth 1 -maxdepth 1 ! -name lo 2>/dev/null | wc -l)
profile=generic
if [ "$arch" = x86_64 ] || [ "$arch" = i386 ] || [ -r /sys/class/dmi/id/product_name ]; then profile=pc
elif [ "$cellular" -eq 1 ]; then profile=cellular
elif [ "$wifi" -eq 0 ] && [ "$nics" -ge 2 ]; then profile=switch
elif [ "$wifi" -eq 1 ] && [ "$nics" -le 2 ]; then profile=ap
elif [ "$wifi" -eq 1 ] && [ "$nics" -ge 3 ]; then profile=router
fi
printf '{"board":"%s","model":"%s","release":"%s","arch":"%s","package_manager":"%s","wifi":%s,"cellular":%s,"netdev_count":%s,"recommended":"%s"}\n' "$(json_escape "$board")" "$(json_escape "$model")" "$(json_escape "$release")" "$(json_escape "$arch")" "$manager" "$wifi" "$cellular" "$nics" "$profile"
