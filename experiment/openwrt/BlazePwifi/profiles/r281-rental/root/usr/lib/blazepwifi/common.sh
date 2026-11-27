#!/bin/sh

BP_STATE=${BP_STATE:-/etc/blazepwifi/state}
BP_RUN=${BP_RUN:-/tmp/blazepwifi}
BP_ACCOUNTS="$BP_STATE/accounts.tsv"
BP_VOUCHERS="$BP_STATE/vouchers.tsv"
BP_VENDOS="$BP_RUN/vendos.tsv"
BP_TARGET_DIR="$BP_STATE/targets"
BP_LEGACY_CREDITS="$BP_STATE/credits.tsv"
BP_LEGACY_SESSIONS="$BP_STATE/sessions.tsv"
BP_POST_BODY=""
if [ "${REQUEST_METHOD:-GET}" = POST ]; then IFS= read -r BP_POST_BODY; fi

bp_cfg() { uci -q get "blazepwifi.main.$1"; }
bp_now() { date +%s; }
bp_time_sane() {
	now="${1:-$(bp_now)}"
	[ "$now" -ge 1700000000 ] 2>/dev/null
}
bp_sha256() { sha256sum | awk '{print $1}'; }
bp_json_escape() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
bp_json() { printf 'Content-Type: application/json\r\nCache-Control: no-store\r\n\r\n%s\n' "$1"; }
bp_fail() { bp_json "{\"ok\":false,\"error\":\"$(bp_json_escape "$1")\"}"; exit 0; }

bp_init_dirs() {
	mkdir -p "$BP_STATE" "$BP_RUN" "$BP_TARGET_DIR"
	chmod 700 "$BP_STATE" "$BP_RUN" "$BP_TARGET_DIR"
	touch "$BP_ACCOUNTS" "$BP_VOUCHERS" "$BP_VENDOS"
	chmod 600 "$BP_ACCOUNTS" "$BP_VOUCHERS" "$BP_VENDOS"
}

bp_tmp_suffix() {
	hexdump -n 6 -e '6/1 "%02x"' /dev/urandom 2>/dev/null || date +%s
}

bp_lock() {
	mkdir -p "$BP_RUN"
	exec 9>"$BP_RUN/account.lock"
	if ! flock -w 10 9; then
		exec 9>&-
		return 1
	fi
}
bp_unlock() {
	flock -u 9 2>/dev/null || true
	exec 9>&-
}

bp_durable_sync() {
	[ "$(bp_cfg durable_sync 2>/dev/null || true)" = 1 ] || return 0
	sync
}

bp_mac_norm() {
	printf '%s' "$1" | tr 'A-F' 'a-f' | grep -Eq '^[0-9a-f]{2}(:[0-9a-f]{2}){5}$' || return 1
	printf '%s' "$1" | tr 'A-F' 'a-f'
}

bp_device_norm() {
	printf '%s' "$1" | tr 'A-F' 'a-f' | grep -Eq '^[0-9a-f]{32,64}$' || return 1
	printf '%s' "$1" | tr 'A-F' 'a-f'
}

bp_mac_for_ip() {
	ipaddr="$1"
	lan_if="$(bp_cfg lan_if)"; [ -n "$lan_if" ] || lan_if=br-lan
	ip neigh show "$ipaddr" dev "$lan_if" 2>/dev/null | awk '/lladdr/ {print $5; exit}' | tr 'A-F' 'a-f'
}

bp_url_decode() {
	printf '%s' "$1" | awk '
	function hx(c, p) { c=toupper(c); p=index("0123456789ABCDEF",c); return p ? p-1 : -1 }
	{
		s=$0; out=""
		for(i=1;i<=length(s);i++){
			c=substr(s,i,1)
			if(c=="%" && i+2<=length(s)){
				a=hx(substr(s,i+1,1)); b=hx(substr(s,i+2,1))
				if(a>=0 && b>=0){ out=out sprintf("%c",a*16+b); i+=2; continue }
			}
			if(c=="+") c=" "
			out=out c
		}
		printf "%s",out
	}'
}

bp_param() {
	key="$1"; data="${QUERY_STRING:-}"
	[ "${REQUEST_METHOD:-GET}" = POST ] && data="$BP_POST_BODY"
	raw="$(printf '%s' "$data" | tr '&' '\n' | awk -F= -v k="$key" '$1==k {sub(/^[^=]*=/,""); print; exit}')"
	bp_url_decode "$raw"
}

bp_account_line() {
	awk -F '\t' -v d="$1" '$1==d {print; exit}' "$BP_ACCOUNTS"
}

bp_account_field() {
	d="$1"; n="$2"
	awk -F '\t' -v d="$d" -v n="$n" '$1==d {print $n; exit}' "$BP_ACCOUNTS"
}

bp_account_write() {
	d="$1"; credit="$2"; expiry="$3"; remaining="$4"; paused="$5"; pause_started="$6"; mac="$7"; ipaddr="$8"; events="$9"
	tmp="$BP_STATE/.accounts.$(bp_tmp_suffix)"
	awk -F '\t' -v OFS='\t' -v d="$d" -v c="$credit" -v e="$expiry" -v r="$remaining" -v p="$paused" -v ps="$pause_started" -v m="$mac" -v ip="$ipaddr" -v ev="$events" '
		BEGIN{f=0}
		$1==d {print d,c,e,r,p,ps,m,ip,ev;f=1;next}
		{print}
		END{if(!f) print d,c,e,r,p,ps,m,ip,ev}
	' "$BP_ACCOUNTS" > "$tmp" && mv "$tmp" "$BP_ACCOUNTS"
	chmod 600 "$BP_ACCOUNTS"
	bp_durable_sync
}

bp_remove_legacy_mac() {
	mac="$1"
	if [ -f "$BP_LEGACY_CREDITS" ]; then
		tmp="$BP_STATE/.legacy-credits.$(bp_tmp_suffix)"; awk -F '\t' -v m="$mac" '$1!=m' "$BP_LEGACY_CREDITS" > "$tmp" && mv "$tmp" "$BP_LEGACY_CREDITS"
	fi
	if [ -f "$BP_LEGACY_SESSIONS" ]; then
		tmp="$BP_STATE/.legacy-sessions.$(bp_tmp_suffix)"; awk -F '\t' -v m="$mac" '$1!=m' "$BP_LEGACY_SESSIONS" > "$tmp" && mv "$tmp" "$BP_LEGACY_SESSIONS"
	fi
}

bp_authorize_mac() { [ -n "$1" ] && nft add element inet blazepwifi auth_macs "{ $1 }" 2>/dev/null || true; }
bp_deauthorize_mac() { [ -n "$1" ] && nft delete element inet blazepwifi auth_macs "{ $1 }" 2>/dev/null || true; }

bp_pause_limit_expired() {
	d="$1"; paused="$(bp_account_field "$d" 5)"; ps="$(bp_account_field "$d" 6)"
	[ "$paused" = 1 ] || return 1
	limit="$(bp_cfg pause_max_seconds)"; [ -n "$limit" ] || limit=0
	[ "$limit" -gt 0 ] 2>/dev/null || return 1
	now="$(bp_now)"
	[ $((now-ps)) -gt "$limit" ]
}

bp_bind_device() {
	d="$1"; mac="$2"; ipaddr="$3"; create="${4:-1}"
	line="$(bp_account_line "$d")"
	if [ -z "$line" ]; then
		credit=0; expiry=0
		claimed=""
		[ -n "$mac" ] && claimed="$(awk -F '\t' -v m="$mac" '$7==m {print $1; exit}' "$BP_ACCOUNTS")"
		if [ -z "$claimed" ] && [ -n "$mac" ] && [ -f "$BP_LEGACY_CREDITS" ]; then credit="$(awk -F '\t' -v m="$mac" '$1==m {v=$2} END {print v+0}' "$BP_LEGACY_CREDITS")"; fi
		if [ -z "$claimed" ] && [ -n "$mac" ] && [ -f "$BP_LEGACY_SESSIONS" ]; then expiry="$(awk -F '\t' -v m="$mac" '$1==m {v=$2} END {print v+0}' "$BP_LEGACY_SESSIONS")"; fi
		if [ -n "$claimed" ] && [ -n "$mac" ]; then
			bp_remove_legacy_mac "$mac"
			bp_durable_sync
		fi
		if [ "$create" != 1 ] && [ "$credit" -eq 0 ] 2>/dev/null && { [ -z "$expiry" ] || [ "$expiry" -le "$(bp_now)" ] 2>/dev/null; }; then
			return 0
		fi
		bp_account_write "$d" "$credit" "$expiry" 0 0 0 "$mac" "$ipaddr" ""
		[ -n "$mac" ] && [ -z "$claimed" ] && bp_remove_legacy_mac "$mac"
		bp_durable_sync
		[ "$expiry" -gt "$(bp_now)" ] 2>/dev/null && bp_authorize_mac "$mac"
		return 0
	fi

	oldmac="$(printf '%s' "$line" | cut -f7)"
	if bp_pause_limit_expired "$d"; then
		credit="$(printf '%s' "$line" | cut -f2)"
		events="$(printf '%s' "$line" | cut -f9)"
		bp_account_write "$d" "$credit" 0 0 0 0 "$mac" "$ipaddr" "$events"
		bp_deauthorize_mac "$oldmac"
		return 0
	fi

	if [ -n "$mac" ] && [ "$oldmac" != "$mac" ]; then
		credit="$(printf '%s' "$line" | cut -f2)"
		expiry="$(printf '%s' "$line" | cut -f3)"
		remaining="$(printf '%s' "$line" | cut -f4)"
		paused="$(printf '%s' "$line" | cut -f5)"
		ps="$(printf '%s' "$line" | cut -f6)"
		events="$(printf '%s' "$line" | cut -f9)"
		bp_account_write "$d" "$credit" "$expiry" "$remaining" "$paused" "$ps" "$mac" "$ipaddr" "$events"
		bp_deauthorize_mac "$oldmac"
		if [ "$paused" != 1 ] && [ "$expiry" -gt "$(bp_now)" ] 2>/dev/null; then bp_authorize_mac "$mac"; fi
	fi
}

bp_get_credit() { v="$(bp_account_field "$1" 2)"; printf '%s' "${v:-0}"; }

bp_remaining() {
	d="$1"; paused="$(bp_account_field "$d" 5)"
	if [ "$paused" = 1 ]; then
		r="$(bp_account_field "$d" 4)"; printf '%s' "${r:-0}"; return
	fi
	e="$(bp_account_field "$d" 3)"; now="$(bp_now)"
	if [ -n "$e" ] && [ "$e" -gt "$now" ] 2>/dev/null; then printf '%s' $((e-now)); else printf '0'; fi
}

bp_event_hash() { printf '%s' "$1" | bp_sha256; }

bp_events_has() {
	events="$1"; event="$2"
	[ -n "$events" ] || return 1
	printf ',%s,' "$events" | grep -Fq ",$event,"
}

bp_events_push() {
	events="$1"; event="$2"; max="$(bp_cfg event_history)"; [ -n "$max" ] || max=64
	out="$event"; coin_count=0
	case "$event" in c:*) coin_count=1;; esac
	oldIFS="$IFS"; IFS=','
	for e in $events; do
		[ -n "$e" ] || continue
		[ "$e" = "$event" ] && continue
		case "$e" in
			v:*) out="$out,$e" ;;
			c:*)
				[ "$coin_count" -ge "$max" ] && continue
				out="$out,$e"; coin_count=$((coin_count+1))
				;;
			*) out="$out,$e" ;;
		esac
	done
	IFS="$oldIFS"
	printf '%s' "$out"
}

bp_find_event_device() {
	event="$1"
	awk -F '\t' -v e="$event" '{
		n=split($9,a,",");
		for(i=1;i<=n;i++) if(a[i]==e){print $1; exit}
	}' "$BP_ACCOUNTS"
}

bp_rate_seconds() {
	want="$1"
	for s in $(uci -q show blazepwifi | sed -n "s/^blazepwifi\.\([^.=]*\)=rate$/\1/p"); do
		c="$(uci -q get blazepwifi.$s.cents)"
		[ "$c" = "$want" ] && { uci -q get blazepwifi.$s.seconds; return; }
	done
	return 1
}

bp_rates_json() {
	first=1; printf '['
	for s in $(uci -q show blazepwifi | sed -n "s/^blazepwifi\.\([^.=]*\)=rate$/\1/p"); do
		c="$(uci -q get blazepwifi.$s.cents)"; sec="$(uci -q get blazepwifi.$s.seconds)"; label="$(uci -q get blazepwifi.$s.label)"
		[ "$first" = 1 ] || printf ','; first=0
		printf '{"cents":%s,"seconds":%s,"label":"%s"}' "${c:-0}" "${sec:-0}" "$(bp_json_escape "$label")"
	done
	printf ']'
}

bp_online_vendos_json() {
	now="$(bp_now)"; first=1; printf '['
	while IFS="$(printf '\t')" read -r id seen ipaddr; do
		[ -n "$id" ] || continue
		[ $((now-seen)) -le 30 ] 2>/dev/null || continue
		[ "$first" = 1 ] || printf ','; first=0
		printf '{"id":"%s","ip":"%s","last_seen":%s}' "$(bp_json_escape "$id")" "$(bp_json_escape "$ipaddr")" "$seen"
	done < "$BP_VENDOS"
	printf ']'
}

bp_choose_vendo() {
	now="$(bp_now)"; chosen=""; count=0
	while IFS="$(printf '\t')" read -r id seen ipaddr; do
		[ -n "$id" ] || continue
		[ $((now-seen)) -le 30 ] 2>/dev/null || continue
		chosen="$id"; count=$((count+1))
	done < "$BP_VENDOS"
	[ "$count" -eq 1 ] || return 1
	printf '%s' "$chosen"
}

bp_vendo_sig_expected() {
	action="$1"; id="$2"; nonce="$3"; pulses="$4"; target="$5"; secret="$(bp_cfg vendo_key)"
	printf '%s|%s|%s|%s|%s|%s|%s' "$secret" "$action" "$id" "$nonce" "$pulses" "$target" "$secret" | bp_sha256
}

bp_check_vendo_sig() {
	action="$1"; id="$2"; nonce="$3"; pulses="$4"; target="$5"; got="$6"
	[ -n "$nonce" ] && [ -n "$got" ] || return 1
	exp="$(bp_vendo_sig_expected "$action" "$id" "$nonce" "$pulses" "$target")"
	[ "$got" = "$exp" ]
}
