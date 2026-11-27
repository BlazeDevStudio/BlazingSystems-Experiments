# Shared by recovery jobs, diagnostics and the health monitor.
# A single blocked ICMP endpoint is not enough evidence to tear down a link.
probe_link() {
 BLAZE_PROBE=no-address
 ip -4 addr show dev "$1" 2>/dev/null | grep -q 'inet ' || return 1
 /usr/libexec/blaze-probe-route "$1" >/dev/null 2>&1 || { BLAZE_PROBE=no-probe-route;return 1; }
 TARGETS="$(uci -q get blaze.main.watchdog_targets || true)"
 [ -n "$TARGETS" ] || TARGETS='1.1.1.1 8.8.8.8'
 N=0
 for T in $TARGETS; do
  case "$T" in ''|*[!A-Za-z0-9._:-]*) continue;; esac
  ping -I "$1" -c1 -W1 "$T" >/dev/null 2>&1 && { BLAZE_PROBE="icmp:$T"; return 0; }
  N=$((N+1)); [ "$N" -ge 4 ] && break
 done
 URL="$(uci -q get blaze.main.watchdog_url || true)"
 [ -n "$URL" ] || URL='https://www.gstatic.com/generate_204'
 CODE=$(curl -4 --interface "$1" --noproxy '*' --connect-timeout 2 --max-time 4 --silent -o /dev/null -w '%{http_code}' "$URL" 2>/dev/null || true)
 case "$CODE" in 200|204|301|302) BLAZE_PROBE="http:$CODE";return 0;;esac
 BLAZE_PROBE=unreachable
 return 1
}
