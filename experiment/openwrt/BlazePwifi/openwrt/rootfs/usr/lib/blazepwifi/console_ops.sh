#!/bin/sh
# BlazePwifi management-console operational helpers.
# Advanced Terminal is disabled by default and never exposed to the captive portal.

BP_TERMINAL_SESSIONS=${BP_TERMINAL_SESSIONS:-$BP_RUN/terminal-sessions.tsv}
BP_REMOTE_STATE=${BP_REMOTE_STATE:-$BP_STATE/remote-access.tsv}

bp_console_uint() {
  value="$1"; min="$2"; max="$3"
  case "$value" in ''|*[!0-9]*) return 1;; esac
  [ "$value" -ge "$min" ] 2>/dev/null && [ "$value" -le "$max" ] 2>/dev/null
}

bp_console_bool() {
  case "$1" in 0|1) return 0;; *) return 1;; esac
}

bp_console_no_controls() {
  value="$1"
  stripped="$(printf '%s' "$value" | tr -d '\t\r\n')"
  [ "$stripped" = "$value" ] || return 1
  ! printf '%s' "$value" | grep -q '[[:cntrl:]]'
}

bp_console_reauth() {
  password="$1"; ip="${REMOTE_ADDR:-unknown}"
  [ -n "${BP_AUTH_USER:-}" ] || return 1
  bp_auth_lock || return 3
  if bp_auth_is_locked "$BP_AUTH_USER" "$ip"; then
    bp_auth_audit console_reauth_locked "$BP_AUTH_USER" "$ip" "active_lock"
    bp_auth_unlock
    return 2
  fi
  if ! bp_auth_verify_password "$BP_AUTH_USER" "$password"; then
    bp_auth_record_failure "$BP_AUTH_USER" "$ip"
    bp_auth_audit console_reauth_failure "$BP_AUTH_USER" "$ip" "invalid_credentials"
    bp_auth_unlock
    return 1
  fi
  bp_auth_clear_failures "$BP_AUTH_USER" "$ip"
  bp_auth_audit console_reauth_success "$BP_AUTH_USER" "$ip" ""
  bp_auth_unlock
  return 0
}

bp_terminal_init() {
  bp_init_dirs
  touch "$BP_TERMINAL_SESSIONS"
  chmod 600 "$BP_TERMINAL_SESSIONS"
}

bp_terminal_cfg_uint() {
  key="$1"; fallback="$2"; min="$3"; max="$4"
  value="$(bp_cfg "$key" 2>/dev/null || true)"
  bp_console_uint "$value" "$min" "$max" || value="$fallback"
  printf '%s' "$value"
}

bp_terminal_enabled() {
  [ "$(bp_cfg advanced_terminal_enabled 2>/dev/null || true)" = 1 ]
}

bp_terminal_auth_hash() {
  printf '%s' "${BP_AUTH_TOKEN:-}" | bp_sha256
}

bp_terminal_lock() {
  mkdir -p "$BP_RUN"
  exec 7>"$BP_RUN/terminal.lock"
  flock -w 5 7 || { exec 7>&-; return 1; }
}

bp_terminal_unlock() {
  flock -u 7 2>/dev/null || true
  exec 7>&-
}

bp_terminal_exec_lock() {
  mkdir -p "$BP_RUN"
  exec 5>"$BP_RUN/terminal-exec.lock"
  flock -n 5 || { exec 5>&-; return 1; }
}

bp_terminal_exec_unlock() {
  flock -u 5 2>/dev/null || true
  exec 5>&-
}

bp_terminal_cleanup_unlocked() {
  now="$(bp_now)"
  idle="$(bp_terminal_cfg_uint terminal_idle_seconds 60 15 900)"
  tmp="$BP_RUN/.terminal-sessions.$(bp_tmp_suffix)"
  awk -F '\t' -v OFS='\t' -v n="$now" -v idle="$idle" '
    NF>=7 && $7>n && (n-$6)<=idle {print}
  ' "$BP_TERMINAL_SESSIONS" > "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$BP_TERMINAL_SESSIONS"
}

bp_terminal_open() {
  password="$1"
  bp_terminal_enabled || return 10
  [ "${BP_AUTH_ROLE:-}" = admin ] || return 11
  [ -n "${BP_AUTH_TOKEN:-}" ] || return 11
  [ "${BP_AUTH_MUST_CHANGE:-0}" != 1 ] || return 12
  bp_console_reauth "$password" || return $?

  bp_terminal_init
  bp_terminal_lock || return 3
  bp_terminal_cleanup_unlocked
  now="$(bp_now)"
  ttl="$(bp_terminal_cfg_uint terminal_ttl_seconds 300 60 1800)"
  expires=$((now+ttl))
  token="$(bp_auth_random_hex 24)" || { bp_terminal_unlock; return 3; }
  auth_hash="$(bp_terminal_auth_hash)"
  ip="${REMOTE_ADDR:-unknown}"
  tmp="$BP_RUN/.terminal-sessions.$(bp_tmp_suffix)"
  awk -F '\t' -v OFS='\t' -v u="$BP_AUTH_USER" '$2!=u {print}' "$BP_TERMINAL_SESSIONS" > "$tmp"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$token" "$BP_AUTH_USER" "$auth_hash" "$ip" "$now" "$now" "$expires" >> "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$BP_TERMINAL_SESSIONS"
  bp_terminal_unlock
  bp_auth_audit terminal_open "$BP_AUTH_USER" "$ip" "ttl=$ttl"
  printf '%s' "$token"
}

bp_terminal_validate() {
  provided="$1"
  [ -n "$provided" ] || return 1
  bp_terminal_enabled || return 1
  bp_terminal_init
  bp_terminal_lock || return 1
  bp_terminal_cleanup_unlocked
  now="$(bp_now)"; auth_hash="$(bp_terminal_auth_hash)"; ip="${REMOTE_ADDR:-unknown}"
  line="$(awk -F '\t' -v t="$provided" -v u="${BP_AUTH_USER:-}" -v h="$auth_hash" -v ip="$ip" \
    '$1==t && $2==u && $3==h && $4==ip {print; exit}' "$BP_TERMINAL_SESSIONS")"
  if [ -z "$line" ]; then bp_terminal_unlock; return 1; fi
  tmp="$BP_RUN/.terminal-sessions.$(bp_tmp_suffix)"
  awk -F '\t' -v OFS='\t' -v t="$provided" -v n="$now" '$1==t {$6=n} {print}' \
    "$BP_TERMINAL_SESSIONS" > "$tmp"
  chmod 600 "$tmp"; mv "$tmp" "$BP_TERMINAL_SESSIONS"
  bp_terminal_unlock
  return 0
}

bp_terminal_close() {
  provided="$1"
  bp_terminal_validate "$provided" || return 1
  bp_terminal_init
  bp_terminal_lock || return 1
  tmp="$BP_RUN/.terminal-sessions.$(bp_tmp_suffix)"
  awk -F '\t' -v t="$provided" '$1!=t {print}' "$BP_TERMINAL_SESSIONS" > "$tmp"
  chmod 600 "$tmp"; mv "$tmp" "$BP_TERMINAL_SESSIONS"
  bp_terminal_unlock
  bp_auth_audit terminal_close "${BP_AUTH_USER:-unknown}" "${REMOTE_ADDR:-unknown}" ""
}

bp_terminal_close_all() {
  bp_terminal_init
  bp_terminal_lock || return 1
  : > "$BP_TERMINAL_SESSIONS"
  chmod 600 "$BP_TERMINAL_SESSIONS"
  bp_terminal_unlock
}

bp_terminal_active_count() {
  bp_terminal_init
  bp_terminal_lock || { printf '0'; return; }
  bp_terminal_cleanup_unlocked
  count="$(awk 'END{print NR+0}' "$BP_TERMINAL_SESSIONS")"
  bp_terminal_unlock
  printf '%s' "$count"
}

bp_terminal_command_safe_wrapper() {
  cmd="$1"
  [ -n "$cmd" ] || return 1
  [ "$(printf '%s' "$cmd" | wc -c)" -le 512 ] || return 1
  bp_console_no_controls "$cmd" || return 1
  # No detached/background jobs. Advanced Terminal is a bounded request/response runner.
  case "$cmd" in *'&'*) return 2;; esac
  # High-risk appliance lifecycle/storage operations use dedicated guarded controls.
  printf '%s' "$cmd" | grep -Eiq '(^|[^A-Za-z0-9_.-])(reboot|poweroff|halt|firstboot|jffs2reset|sysupgrade|mtd|fw_setenv)([^A-Za-z0-9_.-]|$)' && return 2
  return 0
}

bp_terminal_exec() {
  token="$1"; cmd="$2"
  BP_TERMINAL_OUTPUT=""; BP_TERMINAL_RC=1
  bp_terminal_validate "$token" || return 4
  bp_terminal_command_safe_wrapper "$cmd" || return $?
  command -v timeout >/dev/null 2>&1 || return 127
  bp_terminal_exec_lock || return 5

  limit="$(bp_terminal_cfg_uint terminal_command_timeout_seconds 12 2 60)"
  max_bytes="$(bp_terminal_cfg_uint terminal_output_max_bytes 16000 1024 65536)"
  outfile="$BP_RUN/.terminal-output.$(bp_tmp_suffix)"
  : > "$outfile"; chmod 600 "$outfile"
  if PATH=/usr/sbin:/usr/bin:/sbin:/bin HOME=/root TERM=dumb \
    timeout "$limit" sh -c "$cmd" >"$outfile" 2>&1; then
    BP_TERMINAL_RC=0
  else
    BP_TERMINAL_RC=$?
  fi
  BP_TERMINAL_OUTPUT="$(head -c "$max_bytes" "$outfile" 2>/dev/null || true)"
  rm -f "$outfile"
  bp_terminal_exec_unlock
  audit_verb="$(printf '%s' "$cmd" | awk '{print $1}' | cut -c1-48)"
  audit_hash="$(printf '%s' "$cmd" | bp_sha256)"
  bp_auth_audit terminal_exec "${BP_AUTH_USER:-unknown}" "${REMOTE_ADDR:-unknown}" "verb=$audit_verb sha256=$audit_hash"
  export BP_TERMINAL_OUTPUT BP_TERMINAL_RC
  return 0
}

bp_remote_lock() {
  mkdir -p "$BP_RUN"
  exec 6>"$BP_RUN/remote.lock"
  flock -w 5 6 || { exec 6>&-; return 1; }
}

bp_remote_unlock() {
  flock -u 6 2>/dev/null || true
  exec 6>&-
}

bp_remote_init() {
  bp_init_dirs
  if [ ! -f "$BP_REMOTE_STATE" ]; then
    cat > "$BP_REMOTE_STATE" <<'EOF'
mode	disabled
monitoring	1
management	0
terminal	0
node_name	BlazePwifi
site_label	
source_allowlist	
heartbeat_seconds	30
offline_seconds	120
wg_endpoint	
wg_port	51820
wg_address	
wg_peer_public_key	
wg_allowed_ips	
wg_keepalive	25
wg_dns	
wg_mtu	1420
zt_network_id	
EOF
    chmod 600 "$BP_REMOTE_STATE"
  fi
}

bp_remote_get() {
  key="$1"; fallback="${2:-}"
  bp_remote_init
  value="$(awk -F '\t' -v k="$key" '$1==k {sub(/^[^\t]*\t/,""); print; exit}' "$BP_REMOTE_STATE")"
  [ -n "$value" ] && printf '%s' "$value" || printf '%s' "$fallback"
}

bp_remote_text() {
  value="$1"; max="$2"
  [ "$(printf '%s' "$value" | wc -c)" -le "$max" ] || return 1
  bp_console_no_controls "$value"
}

bp_remote_host() {
  value="$1"; [ -z "$value" ] && return 0
  printf '%s' "$value" | grep -Eq '^[A-Za-z0-9._:-]{1,253}$'
}

bp_remote_cidr_list() {
  value="$1"; [ -z "$value" ] && return 0
  [ "$(printf '%s' "$value" | wc -c)" -le 512 ] || return 1
  printf '%s' "$value" | grep -Eq '^[0-9A-Fa-f:./, -]+$'
}

bp_remote_save() {
  mode="$1"; monitoring="$2"; management="$3"; terminal="$4"; node="$5"; site="$6"
  allowlist="$7"; heartbeat="$8"; offline="$9"; wg_endpoint="${10}"; wg_port="${11}"
  wg_address="${12}"; wg_peer="${13}"; wg_allowed="${14}"; wg_keepalive="${15}"
  wg_dns="${16}"; wg_mtu="${17}"; zt_network="${18}"

  case "$mode" in disabled|wireguard|zerotier) ;; *) return 2;; esac
  bp_console_bool "$monitoring" && bp_console_bool "$management" && bp_console_bool "$terminal" || return 2
  [ "$terminal" = 0 ] || [ "$management" = 1 ] || return 2
  [ -n "$node" ] || return 2
  bp_remote_text "$node" 64 || return 2
  bp_remote_text "$site" 96 || return 2
  bp_remote_cidr_list "$allowlist" || return 2
  bp_console_uint "$heartbeat" 10 3600 || return 2
  bp_console_uint "$offline" 30 86400 || return 2
  [ "$offline" -ge "$heartbeat" ] 2>/dev/null || return 2
  bp_remote_host "$wg_endpoint" || return 2
  bp_console_uint "$wg_port" 1 65535 || return 2
  [ -z "$wg_address" ] || printf '%s' "$wg_address" | grep -Eq '^[0-9A-Fa-f:.]+/[0-9]{1,3}$' || return 2
  [ -z "$wg_peer" ] || { [ "$(printf '%s' "$wg_peer" | wc -c)" -ge 43 ] && [ "$(printf '%s' "$wg_peer" | wc -c)" -le 44 ] && printf '%s' "$wg_peer" | grep -Eq '^[A-Za-z0-9+/]+={0,2}$'; } || return 2
  bp_remote_cidr_list "$wg_allowed" || return 2
  bp_console_uint "$wg_keepalive" 0 3600 || return 2
  bp_remote_text "$wg_dns" 128 || return 2
  [ -z "$wg_dns" ] || printf '%s' "$wg_dns" | grep -Eq '^[A-Za-z0-9._:, -]+$' || return 2
  bp_console_uint "$wg_mtu" 576 9000 || return 2
  [ -z "$zt_network" ] || printf '%s' "$zt_network" | grep -Eq '^[0-9A-Fa-f]{16}$' || return 2

  if [ "$mode" = wireguard ]; then
    [ -n "$wg_endpoint" ] && [ -n "$wg_address" ] && [ -n "$wg_peer" ] && [ -n "$wg_allowed" ] || return 3
  fi
  if [ "$mode" = zerotier ]; then
    [ -n "$zt_network" ] || return 3
  fi

  bp_remote_init
  bp_remote_lock || return 4
  tmp="$BP_STATE/.remote-access.$(bp_tmp_suffix)"
  {
    printf 'mode\t%s\n' "$mode"
    printf 'monitoring\t%s\n' "$monitoring"
    printf 'management\t%s\n' "$management"
    printf 'terminal\t%s\n' "$terminal"
    printf 'node_name\t%s\n' "$node"
    printf 'site_label\t%s\n' "$site"
    printf 'source_allowlist\t%s\n' "$allowlist"
    printf 'heartbeat_seconds\t%s\n' "$heartbeat"
    printf 'offline_seconds\t%s\n' "$offline"
    printf 'wg_endpoint\t%s\n' "$wg_endpoint"
    printf 'wg_port\t%s\n' "$wg_port"
    printf 'wg_address\t%s\n' "$wg_address"
    printf 'wg_peer_public_key\t%s\n' "$wg_peer"
    printf 'wg_allowed_ips\t%s\n' "$wg_allowed"
    printf 'wg_keepalive\t%s\n' "$wg_keepalive"
    printf 'wg_dns\t%s\n' "$wg_dns"
    printf 'wg_mtu\t%s\n' "$wg_mtu"
    printf 'zt_network_id\t%s\n' "$(printf '%s' "$zt_network" | tr A-F a-f)"
  } > "$tmp"
  chmod 600 "$tmp"
  if ! mv "$tmp" "$BP_REMOTE_STATE"; then
    rm -f "$tmp"
    bp_remote_unlock
    return 4
  fi
  bp_durable_sync
  bp_remote_unlock
  return 0
}

bp_remote_wireguard_state() {
  if ! command -v wg >/dev/null 2>&1; then printf 'unavailable'; return; fi
  ifaces="$(wg show interfaces 2>/dev/null || true)"
  [ -n "$ifaces" ] || { printf 'installed'; return; }
  latest="$(wg show all latest-handshakes 2>/dev/null | awk 'BEGIN{m=0} $2+0>m{m=$2+0} END{print m+0}')"
  now="$(bp_now)"
  age=0; [ "${latest:-0}" -gt 0 ] 2>/dev/null && age=$((now-latest))
  printf 'online:%s:last_handshake_age=%s' "$ifaces" "$age"
}

bp_remote_zerotier_state() {
  if ! command -v zerotier-cli >/dev/null 2>&1; then printf 'unavailable'; return; fi
  state="$(zerotier-cli info 2>/dev/null | head -n1 || true)"
  [ -n "$state" ] && printf '%s' "$state" || printf 'installed'
}

bp_remote_ready() {
  mode="$(bp_remote_get mode disabled)"
  case "$mode" in
    disabled) return 1 ;;
    wireguard)
      [ -n "$(bp_remote_get wg_endpoint)" ] &&
      [ -n "$(bp_remote_get wg_address)" ] &&
      [ -n "$(bp_remote_get wg_peer_public_key)" ] &&
      [ -n "$(bp_remote_get wg_allowed_ips)" ]
      ;;
    zerotier) [ -n "$(bp_remote_get zt_network_id)" ] ;;
    *) return 1 ;;
  esac
}

bp_remote_status_json() {
  mode="$(bp_remote_get mode disabled)"
  if bp_remote_ready; then ready=true; else ready=false; fi
  runtime='{"activation_state":"staged","apply_supported":false,"public_key":"","applied_at":0,"last_handshake":0,"last_error":""}'
  if command -v bp_remote_runtime_status_json >/dev/null 2>&1; then
    runtime="$(bp_remote_runtime_status_json 2>/dev/null || printf '%s' "$runtime")"
  fi
  printf '{"mode":"%s","ready":%s,"monitoring":%s,"management":%s,"terminal":%s,"node_name":"%s","site_label":"%s","wireguard":"%s","zerotier":"%s","runtime":%s}' \
    "$(bp_json_escape "$mode")" "$ready" "$(bp_remote_get monitoring 1)" "$(bp_remote_get management 0)" "$(bp_remote_get terminal 0)" \
    "$(bp_json_escape "$(bp_remote_get node_name BlazePwifi)")" "$(bp_json_escape "$(bp_remote_get site_label)")" \
    "$(bp_json_escape "$(bp_remote_wireguard_state)")" "$(bp_json_escape "$(bp_remote_zerotier_state)")" "$runtime"
}

bp_remote_config_json() {
  printf '{"mode":"%s","monitoring":%s,"management":%s,"terminal":%s,"node_name":"%s","site_label":"%s","source_allowlist":"%s","heartbeat_seconds":%s,"offline_seconds":%s,"wg_endpoint":"%s","wg_port":%s,"wg_address":"%s","wg_peer_public_key":"%s","wg_allowed_ips":"%s","wg_keepalive":%s,"wg_dns":"%s","wg_mtu":%s,"zt_network_id":"%s"}' \
    "$(bp_json_escape "$(bp_remote_get mode disabled)")" "$(bp_remote_get monitoring 1)" "$(bp_remote_get management 0)" "$(bp_remote_get terminal 0)" \
    "$(bp_json_escape "$(bp_remote_get node_name BlazePwifi)")" "$(bp_json_escape "$(bp_remote_get site_label)")" "$(bp_json_escape "$(bp_remote_get source_allowlist)")" \
    "$(bp_remote_get heartbeat_seconds 30)" "$(bp_remote_get offline_seconds 120)" "$(bp_json_escape "$(bp_remote_get wg_endpoint)")" "$(bp_remote_get wg_port 51820)" \
    "$(bp_json_escape "$(bp_remote_get wg_address)")" "$(bp_json_escape "$(bp_remote_get wg_peer_public_key)")" "$(bp_json_escape "$(bp_remote_get wg_allowed_ips)")" \
    "$(bp_remote_get wg_keepalive 25)" "$(bp_json_escape "$(bp_remote_get wg_dns)")" "$(bp_remote_get wg_mtu 1420)" "$(bp_json_escape "$(bp_remote_get zt_network_id)")"
}
