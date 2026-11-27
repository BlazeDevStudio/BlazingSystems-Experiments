#!/bin/sh
# Lightweight structured portal configuration for BlazePwifi.

BP_PORTAL_DIR=${BP_PORTAL_DIR:-/etc/blazepwifi/portal}
BP_PORTAL_FILE=${BP_PORTAL_FILE:-$BP_PORTAL_DIR/portal.json}
BP_PORTAL_KEYS="template brand tagline accent accent2 background text radius show_voucher show_details show_pause coin_label buy_label voucher_label details_title footer"

bp_portal_defaults() {
	cat <<'JSON'
{
  "template": "neon-simple",
  "brand": "BlazePwifi",
  "tagline": "Fast Wi-Fi. Add time in seconds.",
  "accent": "#7c5cff",
  "accent2": "#22d3ee",
  "background": "#07111f",
  "text": "#f8fbff",
  "radius": "24",
  "show_voucher": "1",
  "show_details": "1",
  "show_pause": "1",
  "coin_label": "Insert Coin",
  "buy_label": "Buy Time",
  "voucher_label": "Voucher",
  "details_title": "Connection details",
  "footer": "Powered by BlazePwifi"
}
JSON
}

bp_portal_init() {
	mkdir -p "$BP_PORTAL_DIR" || return 1
	chmod 700 "$BP_PORTAL_DIR" 2>/dev/null || true
	if [ ! -s "$BP_PORTAL_FILE" ]; then
		tmp="$BP_PORTAL_DIR/.portal.$$"
		bp_portal_defaults > "$tmp" || return 1
		chmod 600 "$tmp" 2>/dev/null || true
		mv "$tmp" "$BP_PORTAL_FILE" || return 1
	fi
	chmod 600 "$BP_PORTAL_FILE" 2>/dev/null || true
}

bp_portal_key_allowed() {
	key="$1"
	for k in $BP_PORTAL_KEYS; do [ "$k" = "$key" ] && return 0; done
	return 1
}

bp_portal_get() {
	key="$1"
	bp_portal_key_allowed "$key" || return 1
	bp_portal_init || return 1
	sed -n 's/^[[:space:]]*"'"$key"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$BP_PORTAL_FILE" | head -n1
}

bp_portal_safe_text() {
	value="$1"; max="$2"
	[ "${#value}" -le "$max" ] || return 1
	printf '%s' "$value" | grep -q '[<>"]' && return 1
	printf '%s' "$value" | grep -q '\\' && return 1
	printf '%s' "$value" | grep -q '[&=%]' && return 1
	LC_ALL=C printf '%s' "$value" | grep -q '[[:cntrl:]]' && return 1
	return 0
}

bp_portal_validate() {
	key="$1"; value="$2"
	bp_portal_key_allowed "$key" || return 1
	case "$key" in
		template) printf '%s' "$value" | grep -Eq '^[a-z0-9][a-z0-9._-]{0,31}$' ;;
		accent|accent2|background|text) printf '%s' "$value" | grep -Eq '^#[0-9A-Fa-f]{6}$' ;;
		radius)
			case "$value" in ''|*[!0-9]*) return 1;; esac
			[ "$value" -ge 8 ] 2>/dev/null && [ "$value" -le 40 ] 2>/dev/null
			;;
		show_voucher|show_details|show_pause) case "$value" in 0|1) return 0;; *) return 1;; esac ;;
		brand) bp_portal_safe_text "$value" 48 ;;
		tagline) bp_portal_safe_text "$value" 120 ;;
		coin_label|buy_label|voucher_label) bp_portal_safe_text "$value" 32 ;;
		details_title) bp_portal_safe_text "$value" 64 ;;
		footer) bp_portal_safe_text "$value" 100 ;;
		*) return 1 ;;
	esac
}

bp_portal_set() {
	key="$1"; value="$2"
	bp_portal_validate "$key" "$value" || return 2
	bp_portal_init || return 1
	old="$(bp_portal_get "$key")"
	[ -n "$old" ] || return 1
	tmp="$BP_PORTAL_DIR/.portal.$$.$(date +%s 2>/dev/null || echo 0)"
	awk -v k="$key" -v v="$value" '
		BEGIN { changed=0 }
		$0 ~ "^[[:space:]]*\"" k "\"[[:space:]]*:" {
			comma = ($0 ~ /,[[:space:]]*$/) ? "," : ""
			printf "  \"%s\": \"%s\"%s\n", k, v, comma
			changed=1
			next
		}
		{ print }
		END { if (!changed) exit 3 }
	' "$BP_PORTAL_FILE" > "$tmp" || { rm -f "$tmp"; return 1; }
	chmod 600 "$tmp" 2>/dev/null || true
	mv "$tmp" "$BP_PORTAL_FILE" || { rm -f "$tmp"; return 1; }
	if command -v sync >/dev/null 2>&1 && [ "${BP_PORTAL_SYNC:-1}" = 1 ]; then sync; fi
	return 0
}

bp_portal_json_escape() {
	printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

bp_portal_json() {
	bp_portal_init || { printf '{}'; return 1; }
	first=1
	printf '{'
	for key in $BP_PORTAL_KEYS; do
		value="$(bp_portal_get "$key")"
		[ "$first" = 1 ] || printf ','
		first=0
		printf '"%s":"%s"' "$key" "$(bp_portal_json_escape "$value")"
	done
	printf '}'
}
