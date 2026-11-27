#!/bin/sh
set -u

STATE_DIR="${BP_STATE:-/etc/blazepwifi/state}"
RUN_DIR="${BP_RUN:-/tmp/blazepwifi}"
PENDING="$STATE_DIR/linux-vendo.pending"

sha256(){ sha256sum | awk '{print $1}'; }
randhex(){
  bytes="${1:-8}"
  out="$(od -An -N "$bytes" -tx1 /dev/urandom 2>/dev/null | tr -d ' \n' || true)"
  [ "${#out}" -ge $((bytes*2)) ] || out="$(printf '%s|%s' "$(date +%s)" "$$" | sha256)"
  printf '%s' "$out" | cut -c1-$((bytes*2))
}
sign(){
  action="$1"; id="$2"; nonce="$3"; pulses="$4"; target="$5"; key="$6"
  printf '%s|%s|%s|%s|%s|%s|%s' "$key" "$action" "$id" "$nonce" "$pulses" "$target" "$key" | sha256
}

if [ "${1:-}" = "--selftest" ] || [ "${BP_GPIO_SELFTEST:-0}" = 1 ]; then
  s="$(sign ping gpio-test 0011223344556677 0 "" selftest-key)"
  echo "selftest:ok"
  echo "signature:${#s}"
  exit 0
fi

cfg(){
  key="$1"; def="${2:-}"
  v="$(uci -q get "blazepwifi.main.$key" 2>/dev/null || true)"
  [ -n "$v" ] && printf '%s' "$v" || printf '%s' "$def"
}

CONTROLLER_ID="${BP_CONTROLLER_ID:-$(cfg controller_id gpio-01)}"
SERVER="${BP_CONTROLLER_SERVER:-$(cfg controller_server 127.0.0.1)}"
PORT="${BP_CONTROLLER_PORT:-$(cfg vendo_port 4455)}"
KEY="${BP_CONTROLLER_KEY:-$(cfg vendo_key '')}"
GPIO_CHIP="${BP_GPIO_CHIP:-$(cfg gpio_chip gpiochip0)}"
COIN_LINE="${BP_COIN_LINE:-$(cfg coin_line '')}"
RELAY_LINE="${BP_RELAY_LINE:-$(cfg relay_line '')}"
LED_LINE="${BP_LED_LINE:-$(cfg led_line '')}"
COIN_ACTIVE_LOW="${BP_COIN_ACTIVE_LOW:-$(cfg coin_active_low 1)}"
RELAY_ACTIVE_HIGH="${BP_RELAY_ACTIVE_HIGH:-$(cfg relay_active_low 0)}"
LED_ACTIVE_HIGH="${BP_LED_ACTIVE_HIGH:-$(cfg led_active_low 0)}"
DEBOUNCE_MS="${BP_COIN_DEBOUNCE_MS:-$(cfg coin_debounce_ms 40)}"
PULSE_GROUP_MS="${BP_PULSE_GROUP_MS:-$(cfg pulse_group_ms 400)}"

# Stored config uses *_active_low; convert output fields to active-high booleans.
[ "$RELAY_ACTIVE_HIGH" = 1 ] && RELAY_ACTIVE_HIGH=0 || RELAY_ACTIVE_HIGH=1
[ "$LED_ACTIVE_HIGH" = 1 ] && LED_ACTIVE_HIGH=0 || LED_ACTIVE_HIGH=1

case "$CONTROLLER_ID" in ''|*[!A-Za-z0-9._-]*) echo "invalid controller_id" >&2; exit 2;; esac
[ -n "$KEY" ] || { echo "vendo_key is not configured" >&2; exit 2; }
case "$COIN_LINE" in ''|*[!0-9]*) echo "coin_line must be configured as a gpiochip line offset" >&2; exit 2;; esac
case "$RELAY_LINE" in ''|*[!0-9]*) echo "relay_line must be configured as a gpiochip line offset" >&2; exit 2;; esac
case "$LED_LINE" in ''|*[!0-9]*) echo "led_line must be configured as a gpiochip line offset" >&2; exit 2;; esac

for c in gpiomon gpioset sha256sum wget; do command -v "$c" >/dev/null 2>&1 || { echo "missing required command: $c" >&2; exit 2; }; done
mkdir -p "$STATE_DIR" "$RUN_DIR"; chmod 700 "$STATE_DIR" "$RUN_DIR"

supports_v2(){
  "$1" --help 2>&1 | grep -q -- '--chip'
}

set_output(){
  name="$1"; line="$2"; on="$3"; active_high="$4"
  pidfile="$RUN_DIR/gpio-$name.pid"
  if [ -f "$pidfile" ]; then old="$(cat "$pidfile" 2>/dev/null || true)"; [ -n "$old" ] && kill "$old" 2>/dev/null || true; rm -f "$pidfile"; fi
  val=0
  if [ "$on" = 1 ]; then [ "$active_high" = 1 ] && val=1 || val=0; else [ "$active_high" = 1 ] && val=0 || val=1; fi
  if supports_v2 gpioset; then
    gpioset -c "$GPIO_CHIP" "$line=$val" >/dev/null 2>&1 &
  else
    gpioset "$GPIO_CHIP" "$line=$val" >/dev/null 2>&1 &
  fi
  echo $! > "$pidfile"
}

outputs(){
  on="$1"
  set_output relay "$RELAY_LINE" "$on" "$RELAY_ACTIVE_HIGH"
  set_output led "$LED_LINE" "$on" "$LED_ACTIVE_HIGH"
}

cleanup(){ outputs 0 2>/dev/null || true; }
trap cleanup EXIT INT TERM

wait_edge(){
  timeout_ms="$1"; edge=rising
  [ "$COIN_ACTIVE_LOW" = 1 ] && edge=falling
  if supports_v2 gpiomon; then
    gpiomon -c "$GPIO_CHIP" -e "$edge" -n 1 -p "${DEBOUNCE_MS}ms" --idle-timeout "${timeout_ms}ms" -F '%E' "$COIN_LINE" 2>/dev/null || true
  else
    if [ "$edge" = falling ]; then eopt=--falling-edge; else eopt=--rising-edge; fi
    timeout_sec=$(( (timeout_ms + 999) / 1000 ))
    timeout "$timeout_sec" gpiomon "$eopt" --num-events=1 "$GPIO_CHIP" "$COIN_LINE" 2>/dev/null || true
  fi
}

post(){
  action="$1"; pulses="${2:-0}"; target="${3:-}"; nonce="${4:-$(randhex 8)}"
  sig="$(sign "$action" "$CONTROLLER_ID" "$nonce" "$pulses" "$target" "$KEY")"
  body="action=$action&id=$CONTROLLER_ID&nonce=$nonce&pulses=$pulses&target=$target&sig=$sig"
  wget -qO- --timeout=4 --post-data="$body" "http://$SERVER:$PORT/cgi-bin/vendo" 2>/dev/null || true
}

json_num(){ printf '%s' "$1" | sed -n "s/.*\"$2\":\([0-9][0-9]*\).*/\1/p"; }
json_str(){ printf '%s' "$1" | sed -n "s/.*\"$2\":\"\([^\"]*\)\".*/\1/p"; }

save_pending(){
  nonce="$1"; target="$2"; pulses="$3"
  tmp="$STATE_DIR/.linux-vendo.pending.$$"
  printf '%s\t%s\t%s\n' "$nonce" "$target" "$pulses" > "$tmp" &&
    chmod 600 "$tmp" && mv "$tmp" "$PENDING" && sync
}

retry_pending(){
  [ -s "$PENDING" ] || return 0
  IFS="$(printf '\t')" read -r nonce target pulses < "$PENDING"
  case "$nonce:$target:$pulses" in *[!A-Fa-f0-9:]*|'::') rm -f "$PENDING"; return 0;; esac
  outputs 0
  while [ -s "$PENDING" ]; do
    r="$(post coin "$pulses" "$target" "$nonce")"
    if printf '%s' "$r" | grep -q '"ok":true'; then rm -f "$PENDING"; sync; return 0; fi
    if printf '%s' "$r" | grep -Eq 'coin window expired|coin target mismatch|no active coin window|another vendo selected'; then
      rm -f "$PENDING"; sync; return 0
    fi
    sleep 1
  done
}

post register >/dev/null
retry_pending

while :; do
  r="$(post poll)"
  insert="$(json_num "$r" insert)"; target="$(json_str "$r" target_nonce)"
  if [ "$insert" = 1 ] && [ -n "$target" ]; then
    outputs 1
    first="$(wait_edge 1000)"
    if [ -n "$first" ]; then
      pulses=1
      while [ "$pulses" -lt 20 ]; do
        more="$(wait_edge "$PULSE_GROUP_MS")"
        [ -n "$more" ] || break
        pulses=$((pulses+1))
      done
      nonce="$(randhex 8)"
      save_pending "$nonce" "$target" "$pulses" || { outputs 0; echo "failed to persist coin event" >&2; sleep 1; continue; }
      outputs 0
      retry_pending
    fi
  else
    outputs 0
    sleep 1
  fi
done
