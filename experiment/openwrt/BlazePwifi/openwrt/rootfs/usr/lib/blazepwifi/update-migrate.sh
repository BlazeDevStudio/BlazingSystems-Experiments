#!/bin/sh
# Idempotent v0.5.1 configuration migration. Never overwrites operator values.
ensure_opt(){ key="$1"; value="$2"; uci -q get "blazepwifi.main.$key" >/dev/null 2>&1 || uci set "blazepwifi.main.$key=$value"; }
ensure_opt update_source_url 'https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/'
ensure_opt update_stability_seconds 600
ensure_opt update_retention 3
ensure_opt update_max_mb 64
uci commit blazepwifi
mkdir -p /etc/blazepwifi/update
chmod 700 /etc/blazepwifi/update
/etc/init.d/blazepwifi-update-guard enable 2>/dev/null || true
exit 0
