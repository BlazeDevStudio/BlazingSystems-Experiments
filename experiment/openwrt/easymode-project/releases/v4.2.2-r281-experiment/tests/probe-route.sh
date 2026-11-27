#!/bin/sh
set -eu
N=blaze-route-audit
cleanup(){ ip netns del "$N" 2>/dev/null || true; }
trap cleanup EXIT HUP INT TERM
ip netns add "$N"
ip -n "$N" link add eth1 type veth peer name upstream
ip -n "$N" addr add 192.0.2.2/24 dev eth1
ip -n "$N" link set eth1 up
ip -n "$N" link set upstream up
ip -n "$N" route add default via 192.0.2.1 dev eth1 metric 20
ip -n "$N" route add unreachable default metric 5
echo 'Bound probe route with outage policy:'
ip -n "$N" route get 198.51.100.1 oif eth1 2>&1 || true
ip -n "$N" route replace table 300 default via 192.0.2.1 dev eth1 onlink
ip -n "$N" rule add pref 0 oif eth1 lookup 300
echo 'Bound probe with independent source route:'
AFTER=$(ip -n "$N" route get 198.51.100.1 oif eth1)
printf '%s\n' "$AFTER"
case "$AFTER" in *'via 192.0.2.1 dev eth1 table 300'*) ;;*) echo 'FAIL: source gateway route missing';exit 1;;esac
echo 'Unbound traffic stays blocked:'
if ip -n "$N" route get 198.51.100.1 2>/dev/null;then echo 'FAIL: unbound traffic escaped outage policy';exit 1;fi
echo 'PASS: bound probe reaches its gateway; normal traffic remains blocked.' 
