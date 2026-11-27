# BlazePwifi architecture

## Components

1. OpenWrt 25.12.x — WAN/LAN/Wi-Fi, DHCP/DNS, NAT, VLAN/repeater topology and firewall4.
2. BlazePwifi core — lightweight shell/procd service managing authorization and walled-garden nftables sets.
3. Portal uHTTPd — HTTP client portal on the configured LAN port (default 8080).
4. Vendo uHTTPd — HTTP ESP8266 API on the configured LAN port (default 4455).
5. Admin uHTTPd — HTTPS-only admin UI/API on the configured LAN port (default 8443).
6. Persistent accounting — device-token accounts and vouchers under /etc/blazepwifi/state.
7. Runtime state — locks and online Vendo heartbeats under /tmp/blazepwifi.
8. Durable coin windows — short target records under /etc/blazepwifi/state/targets survive router reboot/brownout.
9. ESP8266 Vendo — counts coin pulses, controls LED/relay, journals an unacknowledged event to LittleFS, and retries the exact signed event until acknowledged.

## Client identity

BlazePwifi does not use a private/random Wi-Fi MAC as the permanent account identifier. The captive portal creates a random 128-bit browser token in localStorage. The active MAC/IP is attached to that token as a replaceable network binding.

When the same browser returns with a different private MAC, BlazePwifi removes the previous MAC from the nftables authorization set and binds the current MAC to the same credit/session record.

## Traffic path

Internet
  -> OpenWrt firewall4/NAT
  -> BlazePwifi forward hook at priority 10
     -> paid MAC: allowed if firewall4 also allows it
     -> configured walled-garden IP: allowed
     -> unpaid LAN client: blocked from normal forwarding
  -> LAN/Wi-Fi clients

Unpaid TCP/80 traffic is redirected locally to the portal. HTTPS destinations are not impersonated or TLS-intercepted.

## Accounting path

Client device token -> start coin window -> target nonce + selected Vendo
ESP poll -> target nonce
Coin acceptor -> pulse burst
ESP -> persist event in LittleFS -> signed event ID + target nonce
Server -> same-filesystem atomic account update + durable replay marker
Client -> buy configured rate
Server -> expiry/remaining-time update
Core -> current MAC authorization

A lost server response does not create another credit: the ESP retries the same event nonce and target; the server returns an idempotent duplicate acknowledgement. If either the router or ESP reboots before acknowledgement, the persistent target record plus ESP LittleFS journal allow the same event to be retried without changing the customer association.

## Pause/resume

Active sessions use an absolute expiry timestamp. Paused sessions store frozen remaining seconds and remove the MAC authorization. Resume creates a new expiry from the current time.

## Walled garden

Configured domains are periodically resolved into dedicated IPv4/IPv6 nftables sets. This supports provider-neutral login/e-payment flows without hard-coding one commercial integration into the firmware.

## Why upstream OpenWrt

The Ruijie RG-EW1200G Pro v1.1 is directly supported by upstream OpenWrt. OpenWrt 25.12.x therefore remains the primary base. ImmortalWrt may be added as a secondary target if a specific device or package requires its extra patches.

## Small-router constraints

The RG-EW1200G Pro v1.1 has 16 MB flash and 128 MB RAM. The base runtime therefore uses BusyBox shell, UCI, uHTTPd and nftables rather than Node.js/Python/database servers. Optional SQM/CAKE or richer x86 management layers should remain separate from the money/session core.
