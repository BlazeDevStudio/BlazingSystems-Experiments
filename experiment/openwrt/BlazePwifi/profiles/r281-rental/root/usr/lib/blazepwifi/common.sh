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

# Legacy standalone v1 fail-closed paid-state quarantine. This DOES NOT make
# rental-devices.tsv + rental-events.tsv crash-atomic or replace a v2 WAL.
# Never clear this marker on startup or retry: operator must reconcile.
BP_PAID_UNCERTAIN="$BP_STATE/paid-state-uncertain"
bp_paid_begin() {
	mkdir -p "$BP_STATE" "$BP_RUN" || return 8
	exec 6>"$BP_RUN/paid-financial.lock" || return 8
	if ! flock -n 6; then exec 6>&-; return 8; fi
	if [ -e "$BP_PAID_UNCERTAIN" ] || [ -L "$BP_PAID_UNCERTAIN" ]; then
		flock -u 6 2>/dev/null || true; exec 6>&-; return 9
	fi
	bp_paid_temp="$BP_STATE/.paid-pending-$"
	umask 077
	if ! printf 'PENDING\t%s\n' "$(date +%s)" >"$bp_paid_temp" ||
	   ! chmod 600 "$bp_paid_temp" ||
	   ! mv "$bp_paid_temp" "$BP_PAID_UNCERTAIN" ||
	   ! sync; then
		rm -f "$bp_paid_temp" 2>/dev/null || true
		flock -u 6 2>/dev/null || true; exec 6>&-; return 8
	fi
	return 0
}
bp_paid_abort() {
	# Disputed money requires explicit authenticated operator reconciliation.
	flock -u 6 2>/dev/null || true
	exec 6>&-
	return 0
}
bp_paid_commit() {
	# Balance and receipt must both reach storage before any success ACK.
	# Target-specific fsync/dirsync/powercut contract remains pending.
	if ! sync || ! rm -f "$BP_PAID_UNCERTAIN" || ! sync; then
		bp_paid_abort
		return 8
	fi
	flock -u 6 2>/dev/null || true
	exec 6>&-
	return 0
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
	# This is a materialized paid-credit store. Never replace it from a
	# symlink, a partially decoded source, or a duplicated account ID. Keep
	# the old bytes for manual reconciliation if any source row is corrupt.
	[ -f "$BP_ACCOUNTS" ] && [ ! -L "$BP_ACCOUNTS" ] || return 8
	printf '%s\n' "$d" | LC_ALL=C grep -Eq '^[A-Za-z0-9_.:-]{2,96}$' || return 8
	case "$credit:$expiry:$remaining:$paused:$pause_started" in
	  *[!0-9:]*|'') return 8 ;;
	esac
	case "$paused" in 0|1) ;; *) return 8;; esac
	# Future v2 migration MUST use authenticated structured records. Current
	# v1 caller strings cannot contain a TSV row separator or line break.
	for field in "$mac" "$ipaddr" "$events"; do
	  case "$field" in *"$(printf '\t')"*|*"
"*) return 8;; esac
	done
	tmp="$BP_STATE/.accounts.$(bp_tmp_suffix)"
	umask 077
	# Exit nonzero even if a duplicated target is found after writing part
	# of the temporary snapshot. No rename is allowed on any such error.
	if ! awk -F '\t' -v OFS='\t' -v d="$d" -v c="$credit" -v e="$expiry" -v r="$remaining" -v p="$paused" -v ps="$pause_started" -v m="$mac" -v ip="$ipaddr" -v ev="$events" '
		BEGIN {found=0; malformed=0}
		{
		  if (NF!=9 || $1 !~ /^[A-Za-z0-9_.:-]+$/ || length($1)>96 ||
		      $2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/ ||
		      $4 !~ /^[0-9]+$/ || $5 !~ /^(0|1)$/ ||
		      $6 !~ /^[0-9]+$/ || ++seen[$1]>1) malformed=1
		  if ($1==d) {print d,c,e,r,p,ps,m,ip,ev;found++;next}
		  print
		}
		END {
		  if (malformed || found>1) exit 8
		  if (!found) print d,c,e,r,p,ps,m,ip,ev
		}
	' "$BP_ACCOUNTS" > "$tmp"; then
		rm -f "$tmp" 2>/dev/null || true
		return 8
	fi
	if ! chmod 600 "$tmp" || ! mv "$tmp" "$BP_ACCOUNTS"; then
		rm -f "$tmp" 2>/dev/null || true
		return 8
	fi
	bp_durable_sync || return 8
	return 0
}

# Legacy MAC financial source is NOT a v2 migration. Do not silently
# coerce malformed/duplicate credit records into a zero balance.
bp_legacy_value() {
  legacy_file="$1"; legacy_mac="$2"
  [ -f "$legacy_file" ] && [ ! -L "$legacy_file" ] || return 8
  awk -F '\t' -v m="$legacy_mac" '
    $1==m {
      if (NF<2 || $2 !~ /^[0-9]+$/ || ++matches>1) invalid=1
      value=$2
    }
    END {if (invalid) exit 8; print matches?value:0}
  ' "$legacy_file"
}

bp_remove_legacy_mac() {
  legacy_mac="$1"
  for legacy_file in "$BP_LEGACY_CREDITS" "$BP_LEGACY_SESSIONS"; do
    [ -e "$legacy_file" ] || { [ ! -L "$legacy_file" ] || return 8; continue; }
    [ -f "$legacy_file" ] && [ ! -L "$legacy_file" ] || return 8
    legacy_tmp="$BP_STATE/.legacy-remove.$(bp_tmp_suffix)"
    umask 077
    if ! awk -F '\t' -v m="$legacy_mac" '
      {
        if ($1==m) {
          if (NF<2 || $2 !~ /^[0-9]+$/ || ++matches>1) bad=1
          next
        }
        print
      }
      END {if (bad) exit 8}
    ' "$legacy_file" > "$legacy_tmp" ||
       ! chmod 600 "$legacy_tmp" ||
       ! mv "$legacy_tmp" "$legacy_file"; then
      rm -f "$legacy_tmp" 2>/dev/null || true
      return 8
    fi
  done
  bp_durable_sync || return 8
  return 0
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
		if [ -z "$claimed" ] && [ -n "$mac" ] && [ -f "$BP_LEGACY_CREDITS" ]; then credit="$(bp_legacy_value "$BP_LEGACY_CREDITS" "$mac")" || return 8; fi
		if [ -z "$claimed" ] && [ -n "$mac" ] && [ -f "$BP_LEGACY_SESSIONS" ]; then expiry="$(bp_legacy_value "$BP_LEGACY_SESSIONS" "$mac")" || return 8; fi
		if [ -n "$claimed" ] && [ -n "$mac" ]; then
			# MAC already owns another paid identity; preserve original records.
			return 8
		fi
		if [ "$create" != 1 ] && [ "$credit" -eq 0 ] 2>/dev/null && { [ -z "$expiry" ] || [ "$expiry" -le "$(bp_now)" ] 2>/dev/null; }; then
			return 0
		fi
		# Pre-pin operator quarantine across old MAC source and new account.
		# On any failed stage preserve source evidence; do not ACK a cash carry.
		bp_paid_begin || return 8
		if ! bp_account_write "$d" "$credit" "$expiry" 0 0 0 "$mac" "$ipaddr" ""; then
			bp_paid_abort; return 8
		fi
		if [ -n "$mac" ] && ! bp_remove_legacy_mac "$mac"; then
			bp_paid_abort; return 8
		fi
		bp_paid_commit || return 8
		[ "$expiry" -gt "$(bp_now)" ] 2>/dev/null && bp_authorize_mac "$mac"
		return 0
	fi

	oldmac="$(printf '%s' "$line" | cut -f7)"
	if bp_pause_limit_expired "$d"; then
		credit="$(printf '%s' "$line" | cut -f2)"
		events="$(printf '%s' "$line" | cut -f9)"
		bp_account_write "$d" "$credit" 0 0 0 0 "$mac" "$ipaddr" "$events" || return 8
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
		bp_account_write "$d" "$credit" "$expiry" "$remaining" "$paused" "$ps" "$mac" "$ipaddr" "$events" || return 8
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

bp_coin_event_is_live() {
	case "$1" in c:*.*) ;; *) return 1;; esac
	coin_body="${1#c:}"
	coin_window="${coin_body%%.*}"
	coin_digest="${coin_body#*.}"
	coin_pulses="${coin_digest#*:}"
	if [ "$coin_pulses" != "$coin_digest" ]; then
		case "$coin_pulses" in ''|*[!0-9]*) return 1;; esac
		[ "$coin_pulses" -ge 1 ] 2>/dev/null && [ "$coin_pulses" -le 20 ] 2>/dev/null || return 1
	fi
	coin_digest="${coin_digest%%:*}"
	printf '%s' "$coin_window" | grep -Eq '^[A-Fa-f0-9]{8,32}$' || return 1
	printf '%s' "$coin_digest" | grep -Eq '^[a-f0-9]{64}$' || return 1
	for coin_target_file in "$BP_TARGET_DIR"/*.tsv; do
		[ -f "$coin_target_file" ] && [ ! -L "$coin_target_file" ] || continue
		IFS="$(printf '\t')" read -r coin_did coin_mac coin_target coin_expires coin_controller coin_kind < "$coin_target_file"
		if [ "$coin_target" = "$coin_window" ] &&
		   [ "${coin_kind:-hotspot}" = hotspot ] &&
		   [ "$coin_expires" -gt "$(bp_now)" ] 2>/dev/null; then
			return 0
		fi
	done
	return 1
}

bp_events_push() {
	events="$1"; event="$2"; max="$(bp_cfg event_history)"; [ -n "$max" ] || max=64
	case "$max" in ''|*[!0-9]*) max=64;; esac
	[ "$max" -gt 0 ] 2>/dev/null || max=64
	out="$event"; coin_count=0
	case "$event" in
		c:*) if ! bp_coin_event_is_live "$event"; then coin_count=1; fi ;;
	esac
	oldIFS="$IFS"; IFS=','
	for e in $events; do
		[ -n "$e" ] || continue
		[ "$e" = "$event" ] && continue
		case "$e" in
			v:*) out="$out,$e" ;;
			c:*)
				# Historical/expired coins are display-bounded. Active
				# target coins may NOT be forgotten while ACKs can retry.
				if bp_coin_event_is_live "$e"; then
					out="$out,$e"
				else
					[ "$coin_count" -ge "$max" ] && continue
					out="$out,$e"; coin_count=$((coin_count+1))
				fi
				;;
			*) out="$out,$e" ;;
		esac
	done
	IFS="$oldIFS"
	# High active-window volume must fail closed, not prune replay IDs.
	bytes="$(printf '%s' "$out" | wc -c)" || return 8
	[ "$bytes" -le 131072 ] 2>/dev/null || return 8
	printf '%s' "$out"
}

# Detect a controller reusing the same signed nonce for a DIFFERENT
# quantity. An unqualified old receipt without pulse proof is ambiguous.
bp_find_coin_base() {
	base="$1"
	awk -F '\t' -v p="$base" '{
		n=split($9,a,",")
		for(i=1;i<=n;i++)
			if(a[i]==p || index(a[i],p ":")==1) {print $1; exit}
	}' "$BP_ACCOUNTS"
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
