#!/bin/sh
# Validated, capability-neutral BlazePwifi configuration layer.

BP_CONFIG_KEYS="capability_tier lan_if management_if hotspot_if controller_if rental_if portal_port vendo_port admin_port coin_window pulse_value_centavos rental_seconds_per_pulse event_history pause_max_seconds walled_refresh_seconds durable_sync firewall_zone management_vlan hotspot_vlan controller_vlan rental_vlan gpio_chip coin_line relay_line led_line coin_active_low relay_active_low led_active_low coin_debounce_ms pulse_group_ms default_speed_limit_kbps update_source_url update_stability_seconds update_retention update_max_mb advanced_terminal_enabled terminal_ttl_seconds terminal_idle_seconds terminal_command_timeout_seconds terminal_output_max_bytes"

bp_config_key_allowed() {
	key="$1"
	for k in $BP_CONFIG_KEYS; do [ "$k" = "$key" ] && return 0; done
	return 1
}

bp_config_uint_range() {
	value="$1"; min="$2"; max="$3"
	case "$value" in ''|*[!0-9]*) return 1;; esac
	[ "$value" -ge "$min" ] 2>/dev/null && [ "$value" -le "$max" ] 2>/dev/null
}

bp_config_iface() {
	printf '%s' "$1" | grep -Eq '^[A-Za-z0-9_.:-]{1,32}$'
}

bp_config_validate() {
	key="$1"; value="$2"
	bp_config_key_allowed "$key" || return 1
	case "$key" in
		capability_tier) case "$value" in auto|lite|standard|full) return 0;; *) return 1;; esac ;;
		lan_if|management_if|hotspot_if|controller_if|rental_if|firewall_zone|gpio_chip)
			bp_config_iface "$value"
			;;
		portal_port|vendo_port|admin_port) bp_config_uint_range "$value" 1 65535 ;;
		coin_window) bp_config_uint_range "$value" 5 3600 ;;
		pulse_value_centavos) bp_config_uint_range "$value" 1 100000 ;;
		rental_seconds_per_pulse) bp_config_uint_range "$value" 1 86400 ;;
		event_history) bp_config_uint_range "$value" 8 512 ;;
		pause_max_seconds) bp_config_uint_range "$value" 0 31536000 ;;
		walled_refresh_seconds) bp_config_uint_range "$value" 30 86400 ;;
		durable_sync|coin_active_low|relay_active_low|led_active_low|advanced_terminal_enabled) case "$value" in 0|1) return 0;; *) return 1;; esac ;;
		management_vlan|hotspot_vlan|controller_vlan|rental_vlan) bp_config_uint_range "$value" 0 4094 ;;
		coin_line|relay_line|led_line) bp_config_uint_range "$value" 0 4095 ;;
		coin_debounce_ms) bp_config_uint_range "$value" 1 2000 ;;
		pulse_group_ms) bp_config_uint_range "$value" 10 10000 ;;
		default_speed_limit_kbps) bp_config_uint_range "$value" 0 10000000 ;;
		update_source_url)
			case "$value" in https://*) [ "$(printf '%s' "$value" | wc -c)" -le 512 ] && ! printf '%s' "$value" | grep -q '[[:space:][:cntrl:]]';; *) return 1;; esac ;;
		update_stability_seconds) bp_config_uint_range "$value" 60 604800 ;;
		update_retention) bp_config_uint_range "$value" 1 10 ;;
		update_max_mb) bp_config_uint_range "$value" 8 512 ;;
		terminal_ttl_seconds) bp_config_uint_range "$value" 60 1800 ;;
		terminal_idle_seconds) bp_config_uint_range "$value" 15 900 ;;
		terminal_command_timeout_seconds) bp_config_uint_range "$value" 2 60 ;;
		terminal_output_max_bytes) bp_config_uint_range "$value" 1024 65536 ;;
		*) return 1 ;;
	esac
}

bp_config_get() {
	key="$1"
	bp_config_key_allowed "$key" || return 1
	uci -q get "blazepwifi.main.$key"
}

bp_config_restore() {
	key="$1"; had_old="$2"; old="$3"
	if [ "$had_old" = 1 ]; then
		uci set "blazepwifi.main.$key=$old" || return 1
	else
		uci -q delete "blazepwifi.main.$key" >/dev/null 2>&1 || true
	fi
	uci commit blazepwifi
}

bp_config_apply() {
	if [ -n "${BP_CONFIG_APPLY_HOOK:-}" ]; then
		sh -c "$BP_CONFIG_APPLY_HOOK"
		return
	fi
	if [ -x /usr/lib/blazepwifi/apply-config.sh ]; then
		/usr/lib/blazepwifi/apply-config.sh || return 1
	fi
	return 0
}

bp_config_set() {
	key="$1"; value="$2"
	bp_config_validate "$key" "$value" || return 2
	if old="$(uci -q get "blazepwifi.main.$key" 2>/dev/null)"; then had_old=1; else old=""; had_old=0; fi
	uci set "blazepwifi.main.$key=$value" || return 1
	if ! uci commit blazepwifi; then
		bp_config_restore "$key" "$had_old" "$old" >/dev/null 2>&1 || true
		return 1
	fi
	if ! bp_config_apply; then
		bp_config_restore "$key" "$had_old" "$old" >/dev/null 2>&1 || true
		return 1
	fi
	if command -v bp_auth_audit >/dev/null 2>&1; then
		bp_auth_audit config_change "${BP_AUTH_USER:-local}" "${REMOTE_ADDR:-local}" "$key"
	fi
	return 0
}
