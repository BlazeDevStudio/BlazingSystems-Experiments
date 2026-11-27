#!/bin/sh
# Transactional BlazePwifi remote-access activation.
# dev.5 supports WireGuard and modern-UCI ZeroTier live apply with rollback.

BP_REMOTE_APPLY_ROOT=${BP_REMOTE_APPLY_ROOT:-$BP_STATE/remote-apply}
BP_REMOTE_PENDING=${BP_REMOTE_PENDING:-$BP_STATE/remote-apply.pending}
BP_REMOTE_RUNTIME=${BP_REMOTE_RUNTIME:-$BP_STATE/remote-runtime.tsv}
BP_REMOTE_WG_KEY=${BP_REMOTE_WG_KEY:-$BP_STATE/remote-wireguard.key}
BP_REMOTE_ZT_RUNTIME=${BP_REMOTE_ZT_RUNTIME:-$BP_STATE/remote-zerotier-runtime.tsv}
BP_REMOTE_NETWORK_CONFIG=${BP_REMOTE_NETWORK_CONFIG:-/etc/config/network}
BP_REMOTE_FIREWALL_CONFIG=${BP_REMOTE_FIREWALL_CONFIG:-/etc/config/firewall}
BP_REMOTE_ZT_CONFIG=${BP_REMOTE_ZT_CONFIG:-/etc/config/zerotier}
BP_REMOTE_WG_IF=${BP_REMOTE_WG_IF:-blazewg}
BP_REMOTE_WG_PEER=${BP_REMOTE_WG_PEER:-blazewg_peer}
BP_REMOTE_FW_ZONE=${BP_REMOTE_FW_ZONE:-blazewg}
BP_REMOTE_FW_ADMIN=${BP_REMOTE_FW_ADMIN:-blazewg_admin}
BP_REMOTE_ZT_SECTION=${BP_REMOTE_ZT_SECTION:-blazepwifi}
BP_REMOTE_ZT_FW_ZONE=${BP_REMOTE_ZT_FW_ZONE:-blazezt}
BP_REMOTE_ZT_FW_ADMIN=${BP_REMOTE_ZT_FW_ADMIN:-blazezt_admin}

bp_remote_apply_init() {
  bp_init_dirs
  mkdir -p "$BP_REMOTE_APPLY_ROOT/snapshots"
  chmod 700 "$BP_REMOTE_APPLY_ROOT" "$BP_REMOTE_APPLY_ROOT/snapshots"
  if [ ! -f "$BP_REMOTE_RUNTIME" ]; then
    cat > "$BP_REMOTE_RUNTIME" <<'EOF'
state	staged
apply_id	
profile_sha	
applied_at	0
last_error	
wg_listener	
public_key	
last_handshake	0
EOF
    chmod 600 "$BP_REMOTE_RUNTIME"
  fi
  if [ ! -f "$BP_REMOTE_ZT_RUNTIME" ]; then
    cat > "$BP_REMOTE_ZT_RUNTIME" <<'EOF'
active	0
network_id	
node_id	
interface	
address	
status	staged
EOF
    chmod 600 "$BP_REMOTE_ZT_RUNTIME"
  fi
}

bp_remote_zt_runtime_get() {
  key="$1"; fallback="${2:-}"
  bp_remote_apply_init
  value="$(awk -F '\t' -v k="$key" '$1==k {sub(/^[^\t]*\t/,""); print; exit}' "$BP_REMOTE_ZT_RUNTIME")"
  [ -n "$value" ] && printf '%s' "$value" || printf '%s' "$fallback"
}

bp_remote_zt_runtime_write() {
  active="$1"; network_id="$2"; node_id="$3"; interface="$4"; address="$5"; status="$6"
  tmp="$BP_STATE/.remote-zerotier-runtime.$(bp_tmp_suffix)"
  {
    printf 'active\t%s\n' "$active"
    printf 'network_id\t%s\n' "$network_id"
    printf 'node_id\t%s\n' "$node_id"
    printf 'interface\t%s\n' "$interface"
    printf 'address\t%s\n' "$address"
    printf 'status\t%s\n' "$status"
  } > "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$BP_REMOTE_ZT_RUNTIME"
  bp_durable_sync
}

bp_remote_runtime_get() {
  key="$1"; fallback="${2:-}"
  bp_remote_apply_init
  value="$(awk -F '\t' -v k="$key" '$1==k {sub(/^[^\t]*\t/,""); print; exit}' "$BP_REMOTE_RUNTIME")"
  [ -n "$value" ] && printf '%s' "$value" || printf '%s' "$fallback"
}

bp_remote_runtime_write() {
  state="$1"; apply_id="$2"; profile_sha="$3"; applied_at="$4"; last_error="$5"
  listener="$6"; public_key="$7"; last_handshake="$8"
  tmp="$BP_STATE/.remote-runtime.$(bp_tmp_suffix)"
  {
    printf 'state\t%s\n' "$state"
    printf 'apply_id\t%s\n' "$apply_id"
    printf 'profile_sha\t%s\n' "$profile_sha"
    printf 'applied_at\t%s\n' "$applied_at"
    printf 'last_error\t%s\n' "$last_error"
    printf 'wg_listener\t%s\n' "$listener"
    printf 'public_key\t%s\n' "$public_key"
    printf 'last_handshake\t%s\n' "$last_handshake"
  } > "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$BP_REMOTE_RUNTIME"
  bp_durable_sync
}

bp_remote_profile_hash() {
  {
    printf 'mode=%s\n' "$(bp_remote_get mode disabled)"
    printf 'management=%s\n' "$(bp_remote_get management 0)"
    printf 'terminal=%s\n' "$(bp_remote_get terminal 0)"
    printf 'source_allowlist=%s\n' "$(bp_remote_get source_allowlist)"
    printf 'wg_endpoint=%s\n' "$(bp_remote_get wg_endpoint)"
    printf 'wg_port=%s\n' "$(bp_remote_get wg_port 51820)"
    printf 'wg_address=%s\n' "$(bp_remote_get wg_address)"
    printf 'wg_peer_public_key=%s\n' "$(bp_remote_get wg_peer_public_key)"
    printf 'wg_allowed_ips=%s\n' "$(bp_remote_get wg_allowed_ips)"
    printf 'wg_keepalive=%s\n' "$(bp_remote_get wg_keepalive 25)"
    printf 'wg_dns=%s\n' "$(bp_remote_get wg_dns)"
    printf 'wg_mtu=%s\n' "$(bp_remote_get wg_mtu 1420)"
    printf 'zt_network_id=%s\n' "$(bp_remote_get zt_network_id)"
  } | bp_sha256
}

bp_remote_wg_live_supported() {
  command -v uci >/dev/null 2>&1 || return 1
  command -v wg >/dev/null 2>&1 || return 1
  command -v ifup >/dev/null 2>&1 || return 1
  command -v ifdown >/dev/null 2>&1 || return 1
  command -v ip >/dev/null 2>&1 || return 1
  return 0
}

bp_remote_zt_live_supported() {
  command -v uci >/dev/null 2>&1 || return 1
  command -v zerotier-cli >/dev/null 2>&1 || return 1
  command -v zerotier-idtool >/dev/null 2>&1 || return 1
  command -v ip >/dev/null 2>&1 || return 1
  [ -x /etc/init.d/zerotier ] || [ -n "${BP_REMOTE_ZT_SERVICE_HOOK:-}" ] || return 1
  return 0
}

bp_remote_live_supported() {
  case "$(bp_remote_get mode disabled)" in
    wireguard) bp_remote_wg_live_supported ;;
    zerotier) bp_remote_zt_live_supported ;;
    *) return 1 ;;
  esac
}

bp_remote_wg_private_key_ensure() {
  bp_remote_apply_init
  command -v wg >/dev/null 2>&1 || return 127
  if [ -r "$BP_REMOTE_WG_KEY" ]; then
    [ "$(wc -c < "$BP_REMOTE_WG_KEY" 2>/dev/null)" -le 128 ] || return 2
    wg pubkey < "$BP_REMOTE_WG_KEY" >/dev/null 2>&1 || return 2
    chmod 600 "$BP_REMOTE_WG_KEY"
    return 0
  fi
  umask 077
  tmp="$BP_STATE/.remote-wireguard-key.$(bp_tmp_suffix)"
  wg genkey > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  wg pubkey < "$tmp" >/dev/null 2>&1 || { rm -f "$tmp"; return 1; }
  chmod 600 "$tmp"
  mv "$tmp" "$BP_REMOTE_WG_KEY"
  bp_durable_sync
}

bp_remote_wg_public_key_existing() {
  [ -r "$BP_REMOTE_WG_KEY" ] || return 1
  command -v wg >/dev/null 2>&1 || return 127
  wg pubkey < "$BP_REMOTE_WG_KEY" 2>/dev/null
}

bp_remote_wg_public_key() {
  bp_remote_wg_private_key_ensure || return $?
  bp_remote_wg_public_key_existing
}

bp_remote_runtime_set_public_key() {
  public="$1"
  bp_remote_runtime_write \
    "$(bp_remote_runtime_get state staged)" "$(bp_remote_runtime_get apply_id)" \
    "$(bp_remote_runtime_get profile_sha)" "$(bp_remote_runtime_get applied_at 0)" \
    "$(bp_remote_runtime_get last_error)" "$(bp_remote_runtime_get wg_listener)" \
    "$public" "$(bp_remote_runtime_get last_handshake 0)"
}

# IPv4 route helpers deliberately avoid caller variable names. POSIX shell
# function variables are global, so generic names such as "cidr" can corrupt
# the outer Allowed-IP validation loop.
bp_remote_ipv4_bounds() {
  printf '%s' "$1" | awk -F/ '
    function ipnum(s, a,i,n) {
      n=split(s,a,"."); if(n!=4) return -1
      v=0
      for(i=1;i<=4;i++){
        if(a[i] !~ /^[0-9]+$/ || a[i]<0 || a[i]>255) return -1
        v=v*256+a[i]
      }
      return v
    }
    {
      if(NF!=2 || $2 !~ /^[0-9]+$/ || $2<0 || $2>32) exit 1
      v=ipnum($1); if(v<0) exit 1
      size=2^(32-$2)
      start=int(v/size)*size
      end=start+size-1
      printf "%.0f %.0f %d",start,end,$2
    }'
}

bp_remote_ipv4_cidr_valid() {
  bp_remote_ipv4_bounds "$1" >/dev/null 2>&1
}

bp_remote_ipv4_overlap() {
  bp_ip_a="$(bp_remote_ipv4_bounds "$1")" || return 2
  bp_ip_b="$(bp_remote_ipv4_bounds "$2")" || return 2
  bp_ip_as="$(printf '%s' "$bp_ip_a" | awk '{print $1}')"
  bp_ip_ae="$(printf '%s' "$bp_ip_a" | awk '{print $2}')"
  bp_ip_bs="$(printf '%s' "$bp_ip_b" | awk '{print $1}')"
  bp_ip_be="$(printf '%s' "$bp_ip_b" | awk '{print $2}')"
  [ "$bp_ip_as" -le "$bp_ip_be" ] 2>/dev/null && [ "$bp_ip_bs" -le "$bp_ip_ae" ] 2>/dev/null
}

bp_remote_ipv4_contains() {
  bp_ip_outer="$(bp_remote_ipv4_bounds "$1")" || return 2
  bp_ip_inner="$(bp_remote_ipv4_bounds "$2")" || return 2
  bp_ip_os="$(printf '%s' "$bp_ip_outer" | awk '{print $1}')"
  bp_ip_oe="$(printf '%s' "$bp_ip_outer" | awk '{print $2}')"
  bp_ip_is="$(printf '%s' "$bp_ip_inner" | awk '{print $1}')"
  bp_ip_ie="$(printf '%s' "$bp_ip_inner" | awk '{print $2}')"
  [ "$bp_ip_os" -le "$bp_ip_is" ] 2>/dev/null && [ "$bp_ip_oe" -ge "$bp_ip_ie" ] 2>/dev/null
}

bp_remote_ipv4_host() {
  case "$1" in ''|*/*|*:*) return 1;; esac
  bp_remote_ipv4_cidr_valid "$1/32"
}

bp_remote_split_cidrs() {
  printf '%s' "$1" | tr ', ' '\n\n' | awk 'NF'
}

bp_remote_connected_routes() {
  if [ -n "${BP_REMOTE_CONNECTED_ROUTES_HOOK:-}" ]; then
    sh -c "$BP_REMOTE_CONNECTED_ROUTES_HOOK"
    return
  fi
  ip -4 route show scope link 2>/dev/null | awk -v wg="$BP_REMOTE_WG_IF" '
    {
      dev=""
      for(i=1;i<=NF;i++) if($i=="dev" && i<NF) dev=$(i+1)
      if(dev==wg) next
    }
    $1=="default"{next}
    $1 ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+$/ {print $1; next}
    $1 ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/ {print $1"/32"}
  '
}

bp_remote_route_signature() {
  target="$1"
  bp_remote_ipv4_host "$target" || return 1
  if [ -n "${BP_REMOTE_ROUTE_GET_HOOK:-}" ]; then
    BP_REMOTE_ROUTE_TARGET="$target" sh -c "$BP_REMOTE_ROUTE_GET_HOOK"
    return
  fi
  ip -4 route get "$target" 2>/dev/null | head -n1 | awk '{
    via="";dev=""
    for(i=1;i<=NF;i++){
      if($i=="via" && i<NF) via=$(i+1)
      if($i=="dev" && i<NF) dev=$(i+1)
    }
    if(dev!="") printf "via=%s dev=%s",via,dev
  }'
}

bp_remote_default_signature() {
  if [ -n "${BP_REMOTE_DEFAULT_ROUTE_HOOK:-}" ]; then
    sh -c "$BP_REMOTE_DEFAULT_ROUTE_HOOK"
    return
  fi
  ip -4 route show default 2>/dev/null | head -n1 | awk '{
    via="";dev=""
    for(i=1;i<=NF;i++){
      if($i=="via" && i<NF) via=$(i+1)
      if($i=="dev" && i<NF) dev=$(i+1)
    }
    if(dev!="") printf "via=%s dev=%s",via,dev
  }'
}

bp_remote_wg_live_validate() {
  source_ip="${1:-}"
  [ "$(bp_remote_get mode disabled)" = wireguard ] || return 10
  bp_remote_wg_live_supported || return 11
  [ "$(bp_remote_zt_runtime_get active 0)" != 1 ] || return 32

  addr="$(bp_remote_get wg_address)"
  printf '%s' "$addr" | grep -q ':' && return 12
  bp_remote_ipv4_cidr_valid "$addr" || return 12

  allowed="$(bp_remote_get wg_allowed_ips)"
  [ -n "$allowed" ] || return 12
  for cidr in $(bp_remote_split_cidrs "$allowed"); do
    printf '%s' "$cidr" | grep -q ':' && return 12
    bp_remote_ipv4_cidr_valid "$cidr" || return 12
    prefix="$(printf '%s' "$cidr" | cut -d/ -f2)"
    [ "$prefix" -ge 8 ] 2>/dev/null || return 13
    [ "$cidr" != "0.0.0.0/0" ] || return 13

    for local_cidr in $(bp_remote_connected_routes); do
      bp_remote_ipv4_cidr_valid "$local_cidr" || continue
      if bp_remote_ipv4_overlap "$cidr" "$local_cidr"; then
        return 14
      fi
    done
    if bp_remote_ipv4_host "$source_ip" && bp_remote_ipv4_overlap "$cidr" "$source_ip/32"; then
      return 15
    fi
    endpoint="$(bp_remote_get wg_endpoint)"
    if bp_remote_ipv4_host "$endpoint" && bp_remote_ipv4_overlap "$cidr" "$endpoint/32"; then
      return 18
    fi
  done

  if [ "$(bp_remote_get management 0)" = 1 ]; then
    allowlist="$(bp_remote_get source_allowlist)"
    [ -n "$allowlist" ] || return 17
    for source_cidr in $(bp_remote_split_cidrs "$allowlist"); do
      printf '%s' "$source_cidr" | grep -q ':' && return 17
      bp_remote_ipv4_cidr_valid "$source_cidr" || return 17
      source_prefix="$(printf '%s' "$source_cidr" | cut -d/ -f2)"
      [ "$source_prefix" -ge 8 ] 2>/dev/null || return 17
      contained=0
      for cidr in $(bp_remote_split_cidrs "$allowed"); do
        if bp_remote_ipv4_contains "$cidr" "$source_cidr"; then contained=1; break; fi
      done
      [ "$contained" = 1 ] || return 17
    done
  fi

  route_sig="$(bp_remote_route_signature "$source_ip" 2>/dev/null || true)"
  case "$route_sig" in *"dev=$BP_REMOTE_WG_IF"*) return 16;; esac
  return 0
}

bp_remote_snapshot_create() {
  id="$1"
  snap="$BP_REMOTE_APPLY_ROOT/snapshots/$id"
  mkdir -p "$snap"
  chmod 700 "$snap"
  for pair in "network:$BP_REMOTE_NETWORK_CONFIG" "firewall:$BP_REMOTE_FIREWALL_CONFIG" "runtime:$BP_REMOTE_RUNTIME" "zerotier:$BP_REMOTE_ZT_CONFIG" "zt_runtime:$BP_REMOTE_ZT_RUNTIME"; do
    name="${pair%%:*}"; file="${pair#*:}"
    if [ -f "$file" ]; then
      cp -p "$file" "$snap/$name" || return 1
      chmod 600 "$snap/$name" 2>/dev/null || true
    else
      : > "$snap/$name.absent"
    fi
  done
  return 0
}

bp_remote_snapshot_delete() {
  id="$1"
  case "$id" in ''|*[!A-Za-z0-9._-]*) return 1;; esac
  rm -rf "$BP_REMOTE_APPLY_ROOT/snapshots/$id"
}

bp_remote_snapshot_cleanup_orphans() {
  [ ! -e "$BP_REMOTE_PENDING" ] || return 0
  for snap in "$BP_REMOTE_APPLY_ROOT"/snapshots/*; do
    [ -d "$snap" ] || continue
    rm -rf "$snap"
  done
}

bp_remote_config_restore_file() {
  snap="$1"; name="$2"; file="$3"
  if [ -f "$snap/$name.absent" ]; then
    rm -f "$file"
  elif [ -f "$snap/$name" ]; then
    mkdir -p "$(dirname "$file")"
    cp -p "$snap/$name" "$file" || return 1
  fi
}

bp_remote_network_reload() {
  if [ -n "${BP_REMOTE_NETWORK_RELOAD_HOOK:-}" ]; then sh -c "$BP_REMOTE_NETWORK_RELOAD_HOOK"; return; fi
  if command -v ubus >/dev/null 2>&1; then ubus call network reload >/dev/null 2>&1
  elif [ -x /etc/init.d/network ]; then /etc/init.d/network reload >/dev/null 2>&1
  else return 1
  fi
}

bp_remote_ifdown() {
  if [ -n "${BP_REMOTE_IFDOWN_HOOK:-}" ]; then sh -c "$BP_REMOTE_IFDOWN_HOOK"; return; fi
  ifdown "$BP_REMOTE_WG_IF" >/dev/null 2>&1 || true
}

bp_remote_ifup() {
  if [ -n "${BP_REMOTE_IFUP_HOOK:-}" ]; then sh -c "$BP_REMOTE_IFUP_HOOK"; return; fi
  ifup "$BP_REMOTE_WG_IF" >/dev/null 2>&1
}

bp_remote_wg_link_delete() {
  if [ -n "${BP_REMOTE_LINK_DELETE_HOOK:-}" ]; then sh -c "$BP_REMOTE_LINK_DELETE_HOOK"; return; fi
  ip link delete dev "$BP_REMOTE_WG_IF" >/dev/null 2>&1 || true
}

bp_remote_wg_link_precreate() {
  if [ -n "${BP_REMOTE_LINK_PRECREATE_HOOK:-}" ]; then sh -c "$BP_REMOTE_LINK_PRECREATE_HOOK"; return; fi
  ip link show dev "$BP_REMOTE_WG_IF" >/dev/null 2>&1 && return 0
  ip link add dev "$BP_REMOTE_WG_IF" type wireguard >/dev/null 2>&1
}

bp_remote_firewall_reload() {
  if [ -n "${BP_REMOTE_FIREWALL_RELOAD_HOOK:-}" ]; then sh -c "$BP_REMOTE_FIREWALL_RELOAD_HOOK"; return; fi
  /etc/init.d/firewall reload >/dev/null 2>&1
}

bp_remote_admin_start() {
  if [ -n "${BP_REMOTE_ADMIN_START_HOOK:-}" ]; then sh -c "$BP_REMOTE_ADMIN_START_HOOK"; return; fi
  /etc/init.d/blazepwifi-remote-admin restart >/dev/null 2>&1
}

bp_remote_admin_stop() {
  if [ -n "${BP_REMOTE_ADMIN_STOP_HOOK:-}" ]; then sh -c "$BP_REMOTE_ADMIN_STOP_HOOK"; return; fi
  /etc/init.d/blazepwifi-remote-admin stop >/dev/null 2>&1 || true
}

bp_remote_admin_running() {
  if [ -n "${BP_REMOTE_ADMIN_STATUS_HOOK:-}" ]; then sh -c "$BP_REMOTE_ADMIN_STATUS_HOOK"; return; fi
  /etc/init.d/blazepwifi-remote-admin running >/dev/null 2>&1
}

bp_remote_admin_sync() {
  state="$(bp_remote_runtime_get state staged)"
  listener="$(bp_remote_runtime_get wg_listener)"
  case "$state" in
    active|active_staged_changes|applying)
      if [ -n "$listener" ]; then
        bp_remote_admin_start || return 1
        bp_remote_admin_running || return 1
      else
        bp_remote_admin_stop || return 1
      fi
      ;;
    *)
      bp_remote_admin_stop || return 1
      ;;
  esac
}

bp_remote_restore_snapshot() {
  id="$1"; transport="${2:-$(bp_remote_pending_transport)}"
  snap="$BP_REMOTE_APPLY_ROOT/snapshots/$id"
  [ -d "$snap" ] || return 1
  bp_remote_admin_stop || true

  [ "$transport" != zerotier ] || bp_remote_zt_service_stop || true
  bp_remote_config_restore_file "$snap" network "$BP_REMOTE_NETWORK_CONFIG" || return 1
  bp_remote_config_restore_file "$snap" firewall "$BP_REMOTE_FIREWALL_CONFIG" || return 1
  bp_remote_config_restore_file "$snap" runtime "$BP_REMOTE_RUNTIME" || return 1
  bp_remote_config_restore_file "$snap" zerotier "$BP_REMOTE_ZT_CONFIG" || return 1
  bp_remote_config_restore_file "$snap" zt_runtime "$BP_REMOTE_ZT_RUNTIME" || return 1

  bp_remote_ifdown || true
  bp_remote_wg_link_delete || true
  restored_state="$(bp_remote_runtime_get state staged)"
  restored_zt="$(bp_remote_zt_runtime_get active 0)"

  if [ "$restored_zt" = 1 ]; then
    bp_remote_zt_service_restart || return 1
  else
    bp_remote_zt_service_stop || true
    case "$restored_state" in
      active|active_staged_changes)
        bp_remote_wg_link_precreate || return 1
        ;;
    esac
    bp_remote_network_reload || return 1
    case "$restored_state" in
      active|active_staged_changes) bp_remote_ifup || return 1 ;;
    esac
  fi

  bp_remote_firewall_reload || return 1
  bp_remote_admin_sync || return 1
}

bp_remote_pending_write() {
  id="$1"; profile_sha="$2"; source_ip="$3"; source_sig="$4"; default_sig="$5"; transport="${6:-wireguard}"
  case "$transport" in wireguard|zerotier) ;; *) return 1;; esac
  tmp="$BP_STATE/.remote-pending.$(bp_tmp_suffix)"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$id" "$(bp_now)" "$profile_sha" "$source_ip" "$source_sig" "$default_sig" "$transport" > "$tmp"
  chmod 600 "$tmp"
  mv "$tmp" "$BP_REMOTE_PENDING"
  bp_durable_sync
}

bp_remote_pending_transport() {
  line="$(bp_remote_pending_read 2>/dev/null || true)"
  transport="$(printf '%s' "$line" | cut -f7)"
  case "$transport" in wireguard|zerotier) printf '%s' "$transport" ;; *) printf 'wireguard' ;; esac
}

bp_remote_pending_read() {
  [ -r "$BP_REMOTE_PENDING" ] || return 1
  cat "$BP_REMOTE_PENDING"
}

bp_remote_pending_clear() {
  rm -f "$BP_REMOTE_PENDING"
  bp_durable_sync
}

bp_remote_pending_owned() {
  id="$1"
  line="$(bp_remote_pending_read 2>/dev/null || true)"
  [ "$(printf '%s' "$line" | cut -f1)" = "$id" ]
}

bp_remote_guard_spawn() {
  id="$1"
  if [ -n "${BP_REMOTE_GUARD_HOOK:-}" ]; then
    BP_REMOTE_GUARD_ID="$id" sh -c "$BP_REMOTE_GUARD_HOOK"
    return
  fi
  seconds="${BP_REMOTE_GUARD_SECONDS:-90}"
  (
    sleep "$seconds"
    /usr/sbin/blazepwifi-remote-guard "$id"
  ) >"$BP_RUN/remote-guard-$id.log" 2>&1 </dev/null &
}

bp_remote_rollback_pending() {
  id="$1"; reason="${2:-rollback}"
  bp_remote_lock || return 1
  line="$(bp_remote_pending_read 2>/dev/null || true)"
  pending_id="$(printf '%s' "$line" | cut -f1)"
  [ "$pending_id" = "$id" ] || { bp_remote_unlock; return 0; }
  transport="$(bp_remote_pending_transport)"
  if bp_remote_restore_snapshot "$id" "$transport"; then
    bp_remote_pending_clear
    restored_state="$(bp_remote_runtime_get state staged)"
    restored_id="$(bp_remote_runtime_get apply_id)"
    restored_profile="$(bp_remote_runtime_get profile_sha)"
    restored_applied="$(bp_remote_runtime_get applied_at 0)"
    restored_listener="$(bp_remote_runtime_get wg_listener)"
    restored_public="$(bp_remote_runtime_get public_key)"
    restored_handshake="$(bp_remote_runtime_get last_handshake 0)"
    bp_remote_runtime_write "$restored_state" "$restored_id" "$restored_profile" "$restored_applied" "$reason" \
      "$restored_listener" "$restored_public" "$restored_handshake"
    bp_remote_snapshot_delete "$id" || true
    bp_remote_unlock
    return 0
  fi
  public="$(bp_remote_runtime_get public_key)"
  bp_remote_runtime_write rollback_failed "$id" "" "$(bp_now)" "$reason" "" "$public" 0
  bp_remote_unlock
  return 1
}

bp_remote_guard() {
  id="$1"
  line="$(bp_remote_pending_read 2>/dev/null || true)"
  [ "$(printf '%s' "$line" | cut -f1)" = "$id" ] || return 0
  bp_remote_rollback_pending "$id" watchdog-timeout
}

bp_remote_guard_boot() {
  line="$(bp_remote_pending_read 2>/dev/null || true)"
  id="$(printf '%s' "$line" | cut -f1)"
  if [ -z "$id" ]; then
    bp_remote_snapshot_cleanup_orphans
    return 0
  fi
  bp_remote_rollback_pending "$id" reboot-during-apply
}

bp_remote_wg_write_uci() {
  key="$(cat "$BP_REMOTE_WG_KEY" 2>/dev/null)" || return 1
  endpoint="$(bp_remote_get wg_endpoint)"
  port="$(bp_remote_get wg_port 51820)"
  addr="$(bp_remote_get wg_address)"
  peer="$(bp_remote_get wg_peer_public_key)"
  allowed="$(bp_remote_get wg_allowed_ips)"
  keepalive="$(bp_remote_get wg_keepalive 25)"
  mtu="$(bp_remote_get wg_mtu 1420)"
  management="$(bp_remote_get management 0)"
  allowlist="$(bp_remote_get source_allowlist)"
  admin_port="$(bp_cfg admin_port)"; [ -n "$admin_port" ] || admin_port=8443

  uci -q delete "network.$BP_REMOTE_WG_IF" || true
  uci -q delete "network.$BP_REMOTE_WG_PEER" || true
  uci set "network.$BP_REMOTE_WG_IF=interface"
  uci set "network.$BP_REMOTE_WG_IF.proto=wireguard"
  uci set "network.$BP_REMOTE_WG_IF.private_key=$key"
  uci set "network.$BP_REMOTE_WG_IF.mtu=$mtu"
  uci add_list "network.$BP_REMOTE_WG_IF.addresses=$addr"
  uci set "network.$BP_REMOTE_WG_PEER=wireguard_$BP_REMOTE_WG_IF"
  uci set "network.$BP_REMOTE_WG_PEER.public_key=$peer"
  uci set "network.$BP_REMOTE_WG_PEER.endpoint_host=$endpoint"
  uci set "network.$BP_REMOTE_WG_PEER.endpoint_port=$port"
  uci set "network.$BP_REMOTE_WG_PEER.persistent_keepalive=$keepalive"
  uci set "network.$BP_REMOTE_WG_PEER.route_allowed_ips=1"
  for cidr in $(bp_remote_split_cidrs "$allowed"); do
    uci add_list "network.$BP_REMOTE_WG_PEER.allowed_ips=$cidr"
  done

  uci -q delete "firewall.$BP_REMOTE_FW_ZONE" || true
  uci -q delete "firewall.$BP_REMOTE_FW_ADMIN" || true
  uci set "firewall.$BP_REMOTE_FW_ZONE=zone"
  uci set "firewall.$BP_REMOTE_FW_ZONE.name=$BP_REMOTE_FW_ZONE"
  uci set "firewall.$BP_REMOTE_FW_ZONE.input=REJECT"
  uci set "firewall.$BP_REMOTE_FW_ZONE.output=ACCEPT"
  uci set "firewall.$BP_REMOTE_FW_ZONE.forward=REJECT"
  uci add_list "firewall.$BP_REMOTE_FW_ZONE.network=$BP_REMOTE_WG_IF"

  if [ "$management" = 1 ]; then
    uci set "firewall.$BP_REMOTE_FW_ADMIN=rule"
    uci set "firewall.$BP_REMOTE_FW_ADMIN.name=Allow-BlazePwifi-Remote-Admin"
    uci set "firewall.$BP_REMOTE_FW_ADMIN.src=$BP_REMOTE_FW_ZONE"
    uci set "firewall.$BP_REMOTE_FW_ADMIN.proto=tcp"
    uci set "firewall.$BP_REMOTE_FW_ADMIN.dest_port=$admin_port"
    uci set "firewall.$BP_REMOTE_FW_ADMIN.target=ACCEPT"
    for cidr in $(bp_remote_split_cidrs "$allowlist"); do
      uci add_list "firewall.$BP_REMOTE_FW_ADMIN.src_ip=$cidr"
    done
  fi

  uci commit network
  chmod 600 "$BP_REMOTE_NETWORK_CONFIG" 2>/dev/null || return 1
  uci commit firewall
}

bp_remote_wg_listener_apply() {
  management="$(bp_remote_get management 0)"
  listener=""
  if [ "$management" = 1 ]; then
    ipaddr="$(bp_remote_get wg_address | cut -d/ -f1)"
    admin_port="$(bp_cfg admin_port)"; [ -n "$admin_port" ] || admin_port=8443
    listener="$ipaddr:$admin_port"
  fi

  bp_remote_runtime_write applying "$(bp_remote_runtime_get apply_id)" "$(bp_remote_runtime_get profile_sha)" 0 "" \
    "$listener" "$(bp_remote_runtime_get public_key)" "$(bp_remote_runtime_get last_handshake 0)"
  if [ -n "$listener" ]; then
    bp_remote_admin_start || return 1
    bp_remote_admin_running || return 1
  else
    bp_remote_admin_stop || return 1
  fi
  BP_REMOTE_NEW_LISTENER="$listener"
  export BP_REMOTE_NEW_LISTENER
}

bp_remote_wg_wait_health() {
  if [ -n "${BP_REMOTE_WG_HEALTH_HOOK:-}" ]; then
    if BP_REMOTE_HEALTH_IF="$BP_REMOTE_WG_IF" sh -c "$BP_REMOTE_WG_HEALTH_HOOK"; then
      BP_REMOTE_LAST_HANDSHAKE="${BP_REMOTE_LAST_HANDSHAKE:-$(bp_now)}"
      export BP_REMOTE_LAST_HANDSHAKE
      return 0
    fi
    return 1
  fi
  wait_seconds="${BP_REMOTE_WG_HEALTH_SECONDS:-25}"
  start="$(bp_now)"
  while :; do
    if wg show "$BP_REMOTE_WG_IF" >/dev/null 2>&1; then
      latest="$(wg show "$BP_REMOTE_WG_IF" latest-handshakes 2>/dev/null | awk '$2+0>m{m=$2+0} END{print m+0}')"
      [ "${latest:-0}" -gt 0 ] 2>/dev/null && { BP_REMOTE_LAST_HANDSHAKE="$latest"; export BP_REMOTE_LAST_HANDSHAKE; return 0; }
    fi
    now="$(bp_now)"
    [ $((now-start)) -lt "$wait_seconds" ] 2>/dev/null || return 1
    sleep 1
  done
}

bp_remote_route_health() {
  source_ip="$1"; before_source="$2"; before_default="$3"
  after_default="$(bp_remote_default_signature 2>/dev/null || true)"
  [ -n "$before_default" ] && [ "$after_default" = "$before_default" ] || return 1
  if bp_remote_ipv4_host "$source_ip" && [ -n "$before_source" ]; then
    after_source="$(bp_remote_route_signature "$source_ip" 2>/dev/null || true)"
    [ "$after_source" = "$before_source" ] || return 1
  fi
  return 0
}

bp_remote_wireguard_apply() {
  source_ip="${1:-}"
  bp_remote_apply_init
  [ ! -e "$BP_REMOTE_PENDING" ] || return 20
  bp_remote_wg_live_validate "$source_ip" || return $?
  bp_remote_wg_private_key_ensure || return 21
  public="$(bp_remote_wg_public_key)" || return 21
  profile_sha="$(bp_remote_profile_hash)"
  source_sig="$(bp_remote_route_signature "$source_ip" 2>/dev/null || true)"
  default_sig="$(bp_remote_default_signature 2>/dev/null || true)"
  [ -n "$default_sig" ] || return 22

  id="$(date +%Y%m%d%H%M%S)-$(bp_tmp_suffix)"
  bp_remote_lock || return 23
  bp_remote_snapshot_create "$id" || { bp_remote_unlock; return 23; }
  bp_remote_pending_write "$id" "$profile_sha" "$source_ip" "$source_sig" "$default_sig" wireguard || { bp_remote_unlock; return 23; }
  bp_remote_runtime_write applying "$id" "$profile_sha" 0 "" "$(bp_remote_runtime_get wg_listener)" "$public" 0
  bp_remote_unlock
  bp_remote_guard_spawn "$id"

  if ! bp_remote_wg_write_uci; then bp_remote_rollback_pending "$id" uci-write-failed; return 24; fi
  bp_remote_pending_owned "$id" || return 30
  bp_remote_ifdown || true
  bp_remote_wg_link_delete || true
  if ! bp_remote_wg_link_precreate; then bp_remote_rollback_pending "$id" interface-create-failed; return 25; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_ifup; then bp_remote_rollback_pending "$id" interface-up-failed; return 25; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_firewall_reload; then bp_remote_rollback_pending "$id" firewall-reload-failed; return 26; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_wg_wait_health; then bp_remote_rollback_pending "$id" handshake-timeout; return 27; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_wg_listener_apply; then bp_remote_rollback_pending "$id" admin-listener-failed; return 28; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_route_health "$source_ip" "$source_sig" "$default_sig"; then bp_remote_rollback_pending "$id" route-survival-failed; return 29; fi
  bp_remote_pending_owned "$id" || return 30

  bp_remote_lock || { bp_remote_rollback_pending "$id" finalize-lock-failed; return 30; }
  line="$(bp_remote_pending_read 2>/dev/null || true)"
  [ "$(printf '%s' "$line" | cut -f1)" = "$id" ] || { bp_remote_unlock; return 30; }
  handshake="${BP_REMOTE_LAST_HANDSHAKE:-0}"
  listener="${BP_REMOTE_NEW_LISTENER:-}"
  bp_remote_pending_clear
  bp_remote_runtime_write active "$id" "$profile_sha" "$(bp_now)" "" "$listener" "$public" "$handshake"
  bp_remote_snapshot_delete "$id" || true
  bp_remote_unlock
  return 0
}

bp_remote_wireguard_remove_uci() {
  uci -q delete "network.$BP_REMOTE_WG_IF" || true
  uci -q delete "network.$BP_REMOTE_WG_PEER" || true
  uci -q delete "firewall.$BP_REMOTE_FW_ZONE" || true
  uci -q delete "firewall.$BP_REMOTE_FW_ADMIN" || true
  uci commit network
  uci commit firewall
}

bp_remote_wireguard_disable() {
  source_ip="${1:-}"
  bp_remote_apply_init
  [ ! -e "$BP_REMOTE_PENDING" ] || return 20
  source_sig="$(bp_remote_route_signature "$source_ip" 2>/dev/null || true)"
  case "$source_sig" in *"dev=$BP_REMOTE_WG_IF"*) return 31;; esac
  default_sig="$(bp_remote_default_signature 2>/dev/null || true)"
  [ -n "$default_sig" ] || return 22
  public="$(bp_remote_runtime_get public_key)"
  id="$(date +%Y%m%d%H%M%S)-disable-$(bp_tmp_suffix)"
  profile_sha="$(bp_remote_profile_hash)"

  bp_remote_lock || return 23
  bp_remote_snapshot_create "$id" || { bp_remote_unlock; return 23; }
  bp_remote_pending_write "$id" "$profile_sha" "$source_ip" "$source_sig" "$default_sig" || { bp_remote_unlock; return 23; }
  bp_remote_runtime_write disabling "$id" "$profile_sha" 0 "" "$(bp_remote_runtime_get wg_listener)" "$public" 0
  bp_remote_unlock
  bp_remote_guard_spawn "$id"

  if ! bp_remote_admin_stop; then bp_remote_rollback_pending "$id" disable-admin-stop-failed; return 28; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_wireguard_remove_uci; then bp_remote_rollback_pending "$id" disable-uci-failed; return 24; fi
  bp_remote_pending_owned "$id" || return 30
  bp_remote_ifdown || true
  bp_remote_wg_link_delete || true
  if ! bp_remote_network_reload; then bp_remote_rollback_pending "$id" disable-network-reload-failed; return 25; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_firewall_reload; then bp_remote_rollback_pending "$id" disable-firewall-failed; return 26; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_route_health "$source_ip" "$source_sig" "$default_sig"; then bp_remote_rollback_pending "$id" disable-route-survival-failed; return 29; fi
  bp_remote_pending_owned "$id" || return 30

  bp_remote_lock || { bp_remote_rollback_pending "$id" disable-finalize-lock-failed; return 30; }
  bp_remote_pending_clear
  bp_remote_runtime_write staged "$id" "$profile_sha" "$(bp_now)" "" "" "$public" 0
  bp_remote_snapshot_delete "$id" || true
  bp_remote_unlock
  return 0
}


bp_remote_zt_service_restart() {
  if [ -n "${BP_REMOTE_ZT_SERVICE_HOOK:-}" ]; then
    BP_REMOTE_ZT_SERVICE_ACTION=restart sh -c "$BP_REMOTE_ZT_SERVICE_HOOK"
    return
  fi
  /etc/init.d/zerotier restart >/dev/null 2>&1
}

bp_remote_zt_service_stop() {
  if [ -n "${BP_REMOTE_ZT_SERVICE_HOOK:-}" ]; then
    BP_REMOTE_ZT_SERVICE_ACTION=stop sh -c "$BP_REMOTE_ZT_SERVICE_HOOK"
    return
  fi
  /etc/init.d/zerotier stop >/dev/null 2>&1 || true
}

bp_remote_zt_uci_show() {
  uci -q show zerotier 2>/dev/null || true
}

bp_remote_zt_prune_untouched_sample() {
  earth_type="$(uci -q get zerotier.earth 2>/dev/null || true)"
  [ "$earth_type" = network ] || return 0
  global_enabled="$(uci -q get zerotier.global.enabled 2>/dev/null || true)"
  global_secret="$(uci -q get zerotier.global.secret 2>/dev/null || true)"
  [ "${global_enabled:-0}" = 0 ] && [ -z "$global_secret" ] || return 0

  networks="$(bp_remote_zt_uci_show | awk -F= '$2=="network"{print $1}')"
  [ "$(printf '%s\n' "$networks" | awk 'NF{n++} END{print n+0}')" -eq 1 ] || return 0
  [ "$networks" = zerotier.earth ] || return 0
  [ "$(uci -q get zerotier.earth.id 2>/dev/null || true)" = 8056c2e21c000001 ] || return 0
  [ "$(uci -q get zerotier.earth.allow_managed 2>/dev/null || true)" = 1 ] || return 0
  [ "$(uci -q get zerotier.earth.allow_global 2>/dev/null || true)" = 0 ] || return 0
  [ "$(uci -q get zerotier.earth.allow_default 2>/dev/null || true)" = 0 ] || return 0
  [ "$(uci -q get zerotier.earth.allow_dns 2>/dev/null || true)" = 0 ] || return 0

  uci -q delete zerotier.earth || return 1
  uci commit zerotier || return 1
  chmod 600 "$BP_REMOTE_ZT_CONFIG" 2>/dev/null || true
  return 0
}

bp_remote_zt_config_compatible() {
  bp_remote_zt_prune_untouched_sample || return 4
  zt_show="$(bp_remote_zt_uci_show)"
  printf '%s\n' "$zt_show" | grep -Eq '\.join=' && return 2
  for zt_section in $(printf '%s\n' "$zt_show" | awk -F= '$2=="network"{print $1}'); do
    [ "$zt_section" = "zerotier.$BP_REMOTE_ZT_SECTION" ] || return 3
  done
  for zt_section in $(printf '%s\n' "$zt_show" | awk -F= '$2=="zerotier"{print $1}'); do
    [ "$zt_section" = "zerotier.global" ] || return 2
  done
  return 0
}

bp_remote_zt_identity_prepare() {
  bp_remote_apply_init
  bp_remote_zt_live_supported || return 11
  bp_remote_zt_config_compatible || return 40

  dirty=0
  zt_secret="$(uci -q get zerotier.global.secret 2>/dev/null || true)"
  if [ -z "$zt_secret" ]; then
    zt_secret="$(zerotier-idtool generate 2>/dev/null | head -n1 | tr -d '\r\n')" || return 1
    [ -n "$zt_secret" ] || return 1
    uci set "zerotier.global.secret=$zt_secret" || return 1
    dirty=1
  fi

  zt_node="${zt_secret%%:*}"
  printf '%s' "$zt_node" | grep -Eq '^[0-9A-Fa-f]{10}$' || return 2

  zt_global_type="$(uci -q get zerotier.global 2>/dev/null || true)"
  if [ "$zt_global_type" != zerotier ]; then
    uci set zerotier.global=zerotier || return 1
    dirty=1
  fi
  if ! uci -q get zerotier.global.enabled >/dev/null 2>&1; then
    uci set zerotier.global.enabled=0 || return 1
    dirty=1
  fi
  if [ "$dirty" = 1 ]; then
    uci commit zerotier || return 1
    bp_durable_sync
  fi

  chmod 600 "$BP_REMOTE_ZT_CONFIG" 2>/dev/null || return 1
  bp_remote_zt_runtime_write "$(bp_remote_zt_runtime_get active 0)" "$(bp_remote_zt_runtime_get network_id)" \
    "$(printf '%s' "$zt_node" | tr A-F a-f)" "$(bp_remote_zt_runtime_get interface)" \
    "$(bp_remote_zt_runtime_get address)" "$(bp_remote_zt_runtime_get status staged)"
  printf '%s' "$zt_node" | tr A-F a-f
}

bp_remote_zt_cli_get() {
  zt_nwid="$1"; zt_key="$2"
  zerotier-cli get "$zt_nwid" "$zt_key" 2>/dev/null | tail -n1 | tr -d '\r\n'
}

bp_remote_zt_node_info() {
  zerotier-cli info 2>/dev/null | awk '$1==200 && $2=="info" {print $3"\t"$5; exit}'
}

bp_remote_zt_live_validate() {
  source_ip="${1:-}"
  [ "$(bp_remote_get mode disabled)" = zerotier ] || return 10
  bp_remote_zt_live_supported || return 11
  bp_remote_zt_config_compatible || return 40
  current_state="$(bp_remote_runtime_get state staged)"
  current_zt="$(bp_remote_zt_runtime_get active 0)"
  case "$current_state" in active|active_staged_changes) [ "$current_zt" = 1 ] || return 43;; esac
  zt_nwid="$(bp_remote_get zt_network_id)"
  printf '%s' "$zt_nwid" | grep -Eq '^[0-9A-Fa-f]{16}$' || return 12
  if [ "$(bp_remote_get management 0)" = 1 ]; then
    zt_allowlist="$(bp_remote_get source_allowlist)"
    [ -n "$zt_allowlist" ] || return 17
    for zt_source in $(bp_remote_split_cidrs "$zt_allowlist"); do
      printf '%s' "$zt_source" | grep -q ':' && return 17
      bp_remote_ipv4_cidr_valid "$zt_source" || return 17
      zt_prefix="$(printf '%s' "$zt_source" | cut -d/ -f2)"
      [ "$zt_prefix" -ge 8 ] 2>/dev/null || return 17
    done
  fi
  zt_if="$(bp_remote_zt_runtime_get interface)"
  if [ "$current_zt" = 1 ] && [ -n "$zt_if" ]; then
    route_sig="$(bp_remote_route_signature "$source_ip" 2>/dev/null || true)"
    case "$route_sig" in *"dev=$zt_if"*) return 31;; esac
  fi
  return 0
}

bp_remote_zt_write_uci() {
  zt_nwid="$(bp_remote_get zt_network_id)"
  bp_remote_zt_config_compatible || return 1
  bp_remote_zt_identity_prepare >/dev/null || return 1
  zt_global_type="$(uci -q get zerotier.global 2>/dev/null || true)"
  [ "$zt_global_type" = zerotier ] || uci set zerotier.global=zerotier
  uci set zerotier.global.enabled=1
  uci -q delete "zerotier.$BP_REMOTE_ZT_SECTION" || true
  uci set "zerotier.$BP_REMOTE_ZT_SECTION=network"
  uci set "zerotier.$BP_REMOTE_ZT_SECTION.id=$zt_nwid"
  uci set "zerotier.$BP_REMOTE_ZT_SECTION.allow_managed=1"
  uci set "zerotier.$BP_REMOTE_ZT_SECTION.allow_global=0"
  uci set "zerotier.$BP_REMOTE_ZT_SECTION.allow_default=0"
  uci set "zerotier.$BP_REMOTE_ZT_SECTION.allow_dns=0"
  uci commit zerotier || return 1
  chmod 600 "$BP_REMOTE_ZT_CONFIG" 2>/dev/null || return 1
}

bp_remote_zt_remove_uci() {
  bp_remote_zt_config_compatible || return 1
  uci -q delete "zerotier.$BP_REMOTE_ZT_SECTION" || true
  if uci -q get zerotier.global >/dev/null 2>&1; then uci set zerotier.global.enabled=0; fi
  uci commit zerotier || return 1
  chmod 600 "$BP_REMOTE_ZT_CONFIG" 2>/dev/null || return 1
}

bp_remote_zt_wait_health() {
  zt_nwid="$(bp_remote_get zt_network_id)"
  wait_seconds="${BP_REMOTE_ZT_HEALTH_SECONDS:-45}"
  start="$(bp_now)"
  while :; do
    zt_info="$(bp_remote_zt_node_info 2>/dev/null || true)"
    zt_node="$(printf '%s' "$zt_info" | cut -f1)"
    zt_node_status="$(printf '%s' "$zt_info" | cut -f2)"
    zt_status="$(bp_remote_zt_cli_get "$zt_nwid" status 2>/dev/null || true)"
    zt_if="$(bp_remote_zt_cli_get "$zt_nwid" portDeviceName 2>/dev/null || true)"
    zt_addr="$(bp_remote_zt_cli_get "$zt_nwid" ip4 2>/dev/null || true)"
    case "$zt_node_status" in ONLINE|TUNNELED) zt_node_ok=1;; *) zt_node_ok=0;; esac
    if [ "$zt_node_ok" = 1 ] && [ "$zt_status" = OK ] && [ -n "$zt_if" ] && [ "$zt_if" != "-" ] && bp_remote_ipv4_cidr_valid "$zt_addr"; then
      BP_REMOTE_ZT_NODE_ID="$(printf '%s' "$zt_node" | tr A-F a-f)"
      BP_REMOTE_ZT_IF="$zt_if"; BP_REMOTE_ZT_ADDR="$zt_addr"; BP_REMOTE_ZT_STATUS="$zt_status"
      export BP_REMOTE_ZT_NODE_ID BP_REMOTE_ZT_IF BP_REMOTE_ZT_ADDR BP_REMOTE_ZT_STATUS
      return 0
    fi
    now="$(bp_now)"
    [ $((now-start)) -lt "$wait_seconds" ] 2>/dev/null || {
      BP_REMOTE_ZT_STATUS="${zt_status:-unavailable}"; export BP_REMOTE_ZT_STATUS; return 1;
    }
    sleep 1
  done
}

bp_remote_zt_routes() {
  zt_if="$1"
  if [ -n "${BP_REMOTE_ZT_ROUTES_HOOK:-}" ]; then BP_REMOTE_ZT_ROUTE_IF="$zt_if" sh -c "$BP_REMOTE_ZT_ROUTES_HOOK"; return; fi
  ip -4 route show dev "$zt_if" 2>/dev/null | awk '
    $1=="default" {print "default"; next}
    $1 ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+$/ {print $1; next}
    $1 ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/ {print $1"/32"}'
}

bp_remote_zt_other_connected_routes() {
  zt_if="$1"
  if [ -n "${BP_REMOTE_ZT_CONNECTED_ROUTES_HOOK:-}" ]; then BP_REMOTE_ZT_ROUTE_IF="$zt_if" sh -c "$BP_REMOTE_ZT_CONNECTED_ROUTES_HOOK"; return; fi
  ip -4 route show scope link 2>/dev/null | awk -v zt="$zt_if" -v wg="$BP_REMOTE_WG_IF" '
    {dev=""; for(i=1;i<=NF;i++) if($i=="dev" && i<NF) dev=$(i+1); if(dev==zt || dev==wg) next}
    $1=="default"{next}
    $1 ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+$/ {print $1; next}
    $1 ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/ {print $1"/32"}'
}

bp_remote_zt_route_validate() {
  zt_if="$1"; zt_addr="$2"; source_ip="${3:-}"
  zt_routes="$(bp_remote_zt_routes "$zt_if")"
  [ -n "$zt_routes" ] || return 1
  for zt_route in $zt_routes; do
    [ "$zt_route" != default ] || return 2
    bp_remote_ipv4_cidr_valid "$zt_route" || return 2
    zt_prefix="$(printf '%s' "$zt_route" | cut -d/ -f2)"
    [ "$zt_prefix" -ge 8 ] 2>/dev/null || return 2
    for zt_local in $(bp_remote_zt_other_connected_routes "$zt_if"); do
      bp_remote_ipv4_cidr_valid "$zt_local" || continue
      bp_remote_ipv4_overlap "$zt_route" "$zt_local" && return 3
    done
  done
  if [ "$(bp_remote_get management 0)" = 1 ]; then
    zt_allowlist="$(bp_remote_get source_allowlist)"
    for zt_source in $(bp_remote_split_cidrs "$zt_allowlist"); do
      contained=0
      for zt_route in $zt_routes; do
        [ "$zt_route" = default ] && continue
        if bp_remote_ipv4_contains "$zt_route" "$zt_source"; then contained=1; break; fi
      done
      [ "$contained" = 1 ] || return 4
    done
  fi
  route_sig="$(bp_remote_route_signature "$source_ip" 2>/dev/null || true)"
  case "$route_sig" in *"dev=$zt_if"*) return 5;; esac
}

bp_remote_zt_write_firewall() {
  zt_if="$1"; management="$(bp_remote_get management 0)"; allowlist="$(bp_remote_get source_allowlist)"
  admin_port="$(bp_cfg admin_port)"; [ -n "$admin_port" ] || admin_port=8443
  uci -q delete "firewall.$BP_REMOTE_ZT_FW_ZONE" || true
  uci -q delete "firewall.$BP_REMOTE_ZT_FW_ADMIN" || true
  uci set "firewall.$BP_REMOTE_ZT_FW_ZONE=zone"
  uci set "firewall.$BP_REMOTE_ZT_FW_ZONE.name=$BP_REMOTE_ZT_FW_ZONE"
  uci set "firewall.$BP_REMOTE_ZT_FW_ZONE.input=REJECT"
  uci set "firewall.$BP_REMOTE_ZT_FW_ZONE.output=ACCEPT"
  uci set "firewall.$BP_REMOTE_ZT_FW_ZONE.forward=REJECT"
  uci add_list "firewall.$BP_REMOTE_ZT_FW_ZONE.device=$zt_if"
  if [ "$management" = 1 ]; then
    uci set "firewall.$BP_REMOTE_ZT_FW_ADMIN=rule"
    uci set "firewall.$BP_REMOTE_ZT_FW_ADMIN.name=Allow-BlazePwifi-ZeroTier-Admin"
    uci set "firewall.$BP_REMOTE_ZT_FW_ADMIN.src=$BP_REMOTE_ZT_FW_ZONE"
    uci set "firewall.$BP_REMOTE_ZT_FW_ADMIN.proto=tcp"
    uci set "firewall.$BP_REMOTE_ZT_FW_ADMIN.dest_port=$admin_port"
    uci set "firewall.$BP_REMOTE_ZT_FW_ADMIN.target=ACCEPT"
    for zt_source in $(bp_remote_split_cidrs "$allowlist"); do uci add_list "firewall.$BP_REMOTE_ZT_FW_ADMIN.src_ip=$zt_source"; done
  fi
  uci commit firewall
}

bp_remote_zt_remove_firewall() {
  uci -q delete "firewall.$BP_REMOTE_ZT_FW_ZONE" || true
  uci -q delete "firewall.$BP_REMOTE_ZT_FW_ADMIN" || true
  uci commit firewall
}

bp_remote_zt_listener_apply() {
  zt_addr="$1"; management="$(bp_remote_get management 0)"; listener=""
  if [ "$management" = 1 ]; then
    zt_ip="$(printf '%s' "$zt_addr" | cut -d/ -f1)"
    admin_port="$(bp_cfg admin_port)"; [ -n "$admin_port" ] || admin_port=8443
    listener="$zt_ip:$admin_port"
  fi
  bp_remote_runtime_write applying "$(bp_remote_runtime_get apply_id)" "$(bp_remote_runtime_get profile_sha)" 0 "" \
    "$listener" "$(bp_remote_runtime_get public_key)" 0
  if [ -n "$listener" ]; then
    bp_remote_admin_start || return 1; bp_remote_admin_running || return 1
  else
    bp_remote_admin_stop || return 1
  fi
  BP_REMOTE_NEW_LISTENER="$listener"; export BP_REMOTE_NEW_LISTENER
}

bp_remote_zerotier_apply() {
  source_ip="${1:-}"
  bp_remote_apply_init
  [ ! -e "$BP_REMOTE_PENDING" ] || return 20
  bp_remote_zt_live_validate "$source_ip" || return $?
  bp_remote_zt_identity_prepare >/dev/null || return 41
  profile_sha="$(bp_remote_profile_hash)"
  source_sig="$(bp_remote_route_signature "$source_ip" 2>/dev/null || true)"
  default_sig="$(bp_remote_default_signature 2>/dev/null || true)"
  [ -n "$default_sig" ] || return 22
  id="$(date +%Y%m%d%H%M%S)-zt-$(bp_tmp_suffix)"
  bp_remote_lock || return 23
  bp_remote_snapshot_create "$id" || { bp_remote_unlock; return 23; }
  bp_remote_pending_write "$id" "$profile_sha" "$source_ip" "$source_sig" "$default_sig" zerotier || { bp_remote_unlock; return 23; }
  bp_remote_runtime_write applying "$id" "$profile_sha" 0 "" "$(bp_remote_runtime_get wg_listener)" "$(bp_remote_runtime_get public_key)" 0
  bp_remote_unlock
  bp_remote_guard_spawn "$id"
  if ! bp_remote_zt_write_uci; then bp_remote_rollback_pending "$id" zerotier-uci-failed; return 44; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_zt_service_restart; then bp_remote_rollback_pending "$id" zerotier-service-failed; return 45; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_zt_wait_health; then bp_remote_rollback_pending "$id" "zerotier-${BP_REMOTE_ZT_STATUS:-health-timeout}"; return 46; fi
  bp_remote_pending_owned "$id" || return 30
  if bp_remote_zt_route_validate "$BP_REMOTE_ZT_IF" "$BP_REMOTE_ZT_ADDR" "$source_ip"; then :; else
    zt_route_rc=$?; bp_remote_rollback_pending "$id" "zerotier-route-safety-$zt_route_rc"; return 47
  fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_zt_write_firewall "$BP_REMOTE_ZT_IF"; then bp_remote_rollback_pending "$id" zerotier-firewall-write-failed; return 48; fi
  if ! bp_remote_firewall_reload; then bp_remote_rollback_pending "$id" zerotier-firewall-reload-failed; return 48; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_zt_listener_apply "$BP_REMOTE_ZT_ADDR"; then bp_remote_rollback_pending "$id" zerotier-admin-listener-failed; return 49; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_route_health "$source_ip" "$source_sig" "$default_sig"; then bp_remote_rollback_pending "$id" zerotier-route-survival-failed; return 29; fi
  bp_remote_pending_owned "$id" || return 30
  bp_remote_lock || { bp_remote_rollback_pending "$id" zerotier-finalize-lock-failed; return 30; }
  line="$(bp_remote_pending_read 2>/dev/null || true)"
  [ "$(printf '%s' "$line" | cut -f1)" = "$id" ] || { bp_remote_unlock; return 30; }
  listener="${BP_REMOTE_NEW_LISTENER:-}"
  bp_remote_zt_runtime_write 1 "$(bp_remote_get zt_network_id)" "$BP_REMOTE_ZT_NODE_ID" "$BP_REMOTE_ZT_IF" "$BP_REMOTE_ZT_ADDR" OK
  bp_remote_pending_clear
  bp_remote_runtime_write active "$id" "$profile_sha" "$(bp_now)" "" "$listener" "$(bp_remote_runtime_get public_key)" 0
  bp_remote_snapshot_delete "$id" || true
  bp_remote_unlock
}

bp_remote_zerotier_disable() {
  source_ip="${1:-}"
  bp_remote_apply_init
  [ ! -e "$BP_REMOTE_PENDING" ] || return 20
  [ "$(bp_remote_zt_runtime_get active 0)" = 1 ] || return 42
  zt_if="$(bp_remote_zt_runtime_get interface)"
  source_sig="$(bp_remote_route_signature "$source_ip" 2>/dev/null || true)"
  case "$source_sig" in *"dev=$zt_if"*) return 31;; esac
  default_sig="$(bp_remote_default_signature 2>/dev/null || true)"
  [ -n "$default_sig" ] || return 22
  profile_sha="$(bp_remote_profile_hash)"
  id="$(date +%Y%m%d%H%M%S)-zt-disable-$(bp_tmp_suffix)"
  bp_remote_lock || return 23
  bp_remote_snapshot_create "$id" || { bp_remote_unlock; return 23; }
  bp_remote_pending_write "$id" "$profile_sha" "$source_ip" "$source_sig" "$default_sig" zerotier || { bp_remote_unlock; return 23; }
  bp_remote_runtime_write disabling "$id" "$profile_sha" 0 "" "$(bp_remote_runtime_get wg_listener)" "$(bp_remote_runtime_get public_key)" 0
  bp_remote_unlock
  bp_remote_guard_spawn "$id"
  if ! bp_remote_admin_stop; then bp_remote_rollback_pending "$id" zerotier-disable-admin-stop-failed; return 49; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_zt_remove_firewall; then bp_remote_rollback_pending "$id" zerotier-disable-firewall-write-failed; return 48; fi
  if ! bp_remote_zt_remove_uci; then bp_remote_rollback_pending "$id" zerotier-disable-uci-failed; return 44; fi
  if ! bp_remote_zt_service_stop; then bp_remote_rollback_pending "$id" zerotier-disable-service-failed; return 45; fi
  if ! bp_remote_firewall_reload; then bp_remote_rollback_pending "$id" zerotier-disable-firewall-reload-failed; return 48; fi
  bp_remote_pending_owned "$id" || return 30
  if ! bp_remote_route_health "$source_ip" "$source_sig" "$default_sig"; then bp_remote_rollback_pending "$id" zerotier-disable-route-survival-failed; return 29; fi
  bp_remote_pending_owned "$id" || return 30
  bp_remote_lock || { bp_remote_rollback_pending "$id" zerotier-disable-finalize-lock-failed; return 30; }
  zt_node="$(bp_remote_zt_runtime_get node_id)"; zt_nwid="$(bp_remote_get zt_network_id)"
  bp_remote_pending_clear
  bp_remote_zt_runtime_write 0 "$zt_nwid" "$zt_node" "" "" staged
  bp_remote_runtime_write staged "$id" "$profile_sha" "$(bp_now)" "" "" "$(bp_remote_runtime_get public_key)" 0
  bp_remote_snapshot_delete "$id" || true
  bp_remote_unlock
}

bp_remote_activation_state() {
  bp_remote_apply_init
  state="$(bp_remote_runtime_get state staged)"
  if [ "$state" = active ]; then
    applied="$(bp_remote_runtime_get profile_sha)"
    current="$(bp_remote_profile_hash)"
    [ "$applied" = "$current" ] || { printf 'active_staged_changes'; return; }
  fi
  printf '%s' "$state"
}

bp_remote_runtime_status_json() {
  state="$(bp_remote_activation_state)"
  public="$(bp_remote_runtime_get public_key)"
  [ -n "$public" ] || public="$(bp_remote_wg_public_key_existing 2>/dev/null || true)"
  handshake="$(bp_remote_runtime_get last_handshake 0)"
  applied_at="$(bp_remote_runtime_get applied_at 0)"
  last_error="$(bp_remote_runtime_get last_error)"
  zt_active="$(bp_remote_zt_runtime_get active 0)"
  zt_network="$(bp_remote_zt_runtime_get network_id)"
  zt_node="$(bp_remote_zt_runtime_get node_id)"
  zt_if="$(bp_remote_zt_runtime_get interface)"
  zt_addr="$(bp_remote_zt_runtime_get address)"
  zt_status="$(bp_remote_zt_runtime_get status staged)"
  if [ "$zt_active" = 1 ]; then
    transport=zerotier
  else
    case "$state" in active|active_staged_changes|applying|disabling) transport=wireguard ;; *) transport=none ;; esac
  fi
  if bp_remote_live_supported; then supported=true; else supported=false; fi
  printf '{"activation_state":"%s","transport":"%s","apply_supported":%s,"public_key":"%s","applied_at":%s,"last_handshake":%s,"last_error":"%s","zerotier":{"active":%s,"network_id":"%s","node_id":"%s","interface":"%s","address":"%s","status":"%s"}}' \
    "$(bp_json_escape "$state")" "$(bp_json_escape "$transport")" "$supported" "$(bp_json_escape "$public")" "${applied_at:-0}" "${handshake:-0}" "$(bp_json_escape "$last_error")" \
    "$zt_active" "$(bp_json_escape "$zt_network")" "$(bp_json_escape "$zt_node")" "$(bp_json_escape "$zt_if")" "$(bp_json_escape "$zt_addr")" "$(bp_json_escape "$zt_status")"
}
# End of BlazePwifi remote apply engine.
