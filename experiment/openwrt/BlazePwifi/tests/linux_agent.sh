#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
A="$ROOT/linux-agent/blazepwifi-gpio-agent.sh"
S="$ROOT/linux-agent/blazepwifi-gpio-agent.init"
P="$ROOT/linux-agent/profiles"

[ -x "$A" ] || { echo "missing Linux GPIO agent" >&2; exit 1; }
[ -f "$S" ] || { echo "missing procd init service" >&2; exit 1; }
[ -d "$P" ] || { echo "missing Orange Pi profiles" >&2; exit 1; }

grep -q 'gpiomon' "$A"
grep -q 'gpioset' "$A"
grep -q 'pending' "$A"
grep -q 'cgi-bin/vendo' "$A"
grep -q 'debounce' "$A"
grep -q 'pulse_group' "$A"
! grep -q '/sys/class/gpio' "$A"

for p in orangepi-zero3 orangepi-one orangepi-pc; do
  [ -f "$P/$p.conf" ] || { echo "missing priority profile: $p" >&2; exit 1; }
  grep -q '^BOARD=' "$P/$p.conf"
  grep -q '^GPIO_CHIP=' "$P/$p.conf"
  grep -q '^CAPABILITY_TIER=standard' "$P/$p.conf"
done

# Source-only self-test must not touch actual GPIO hardware.
OUT="$(BP_GPIO_SELFTEST=1 sh "$A" --selftest)"
echo "$OUT" | grep -q 'selftest:ok'
echo "$OUT" | grep -q 'signature:64'

echo "BlazePwifi Linux GPIO agent checks passed"
