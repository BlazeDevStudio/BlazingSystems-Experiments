#!/bin/sh
set -eu
cleanup(){ for n in ac-router ac-client ac-server;do ip netns del "$n" 2>/dev/null || true;done; }
trap cleanup EXIT HUP INT TERM
for n in ac-router ac-client ac-server;do ip netns add "$n";ip -n "$n" link set lo up;done
ip link add ac-c type veth peer name ac-r
ip link set ac-c netns ac-client;ip link set ac-r netns ac-router
ip -n ac-client link set ac-c name eth0;ip -n ac-router link set ac-r name br-lan
ip link add ac-s type veth peer name ac-w
ip link set ac-s netns ac-server;ip link set ac-w netns ac-router
ip -n ac-server link set ac-s name eth0;ip -n ac-router link set ac-w name wan
ip -n ac-client link set eth0 address 02:aa:bb:cc:dd:ee
ip -n ac-client addr add 198.18.0.2/24 dev eth0;ip -n ac-client link set eth0 up
ip -n ac-router addr add 198.18.0.1/24 dev br-lan;ip -n ac-router link set br-lan up
ip -n ac-router addr add 198.18.1.1/24 dev wan;ip -n ac-router link set wan up
ip -n ac-server addr add 198.18.1.2/24 dev eth0;ip -n ac-server link set eth0 up
ip -n ac-client route add default via 198.18.0.1;ip -n ac-server route add default via 198.18.1.1
ip netns exec ac-router sysctl -qw net.ipv4.ip_forward=1
rule(){ ucode -e "import {profile,rules} from '/usr/share/blaze/access.uc'; print(rules(profile({mode:'$1',scope:'all',macs:['$2']})));" >/tmp/blaze-access-packet-test.nft;ip netns exec ac-router nft -f /tmp/blaze-access-packet-test.nft; }
online(){ ip netns exec ac-client ping -c1 -W1 198.18.1.2 >/dev/null; }
online;echo 'PASS baseline wired client forwarded'
rule deny 02:aa:bb:cc:dd:ee
if online;then echo 'FAIL blocklist';exit 1;fi
ip netns exec ac-client ping -c1 -W1 198.18.0.1 >/dev/null;echo 'PASS blocked internet, local admin reachable'
rule deny 02:00:00:00:00:01;online;echo 'PASS unlisted client allowed'
rule allow 02:aa:bb:cc:dd:ee;online;echo 'PASS allowlisted client allowed'
rule allow 02:00:00:00:00:01
if online;then echo 'FAIL allowlist';exit 1;fi
echo 'PASS unlisted client blocked by allowlist'
rule off 02:aa:bb:cc:dd:ee;online;echo 'PASS disabled filter restores forwarding'
rm -f /tmp/blaze-access-packet-test.nft
