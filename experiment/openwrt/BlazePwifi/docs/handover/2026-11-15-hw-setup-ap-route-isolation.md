# PHX-HARDWARE handover — setup route interface isolation

**Date:** 2026-11-15 Asia/Manila  
**Role:** PHX-HARDWARE  
**Task:** restrict firmware setup HTTP surface  
**Branch:** `phoenix/hardware-setup-ap-route-isolation-20261115`  
**Stack base:** DRAFT #296 at `a4989c815b7348cf780c34ec6b7b84c83ebe62d4`  
**Classification:** DRAFT / LAB ONLY / PRODUCTION NO-GO

## Proven defect

The ESP web server binds while Wi-Fi is in AP+station mode and continues handling
requests after the temporary setup AP is closed. The root setup form,
`POST /save`, and quarantine view did not distinguish the protected setup AP
from the normal station interface. A LAN client could therefore read setup and
coin-reconciliation data or submit configuration changes and trigger reboot.

## Bounded correction

- `setupRequestAllowed()` requires the setup AP to be active and compares the
  accepted connection's local interface address with `WiFi.softAPIP()`.
- `requireSetupApRequest()` returns HTTP 403 for inactive-AP or station-side
  requests.
- Root setup form, quarantine view, and configuration save all run this guard
  before reading or changing sensitive state.
- The quarantine clear route remains unconditionally denied by parent DRAFT
  #296.
- No router API, receipt schema, journal format, financial authority, or
  migration source changed.

## Verification

`tests/v060_esp_setup_ap_route_guard.py` compiles the exact two production
predicates from each sketch and injects: active setup-AP request, inactive AP,
and station-interface request. It also verifies each sensitive handler checks
the guard before form generation, LittleFS access, or request argument parsing.

At handover creation, exact-head Actions are **NOT RUN / PENDING**. Arduino
target compilation is required because host stubs cannot prove the board web
server exposes identical interface-address behavior.

## Explicit limits

- Host interface modeling and Arduino compilation are not physical RF/network
  acceptance. A noncustomer ESP board must verify AP and station requests using
  separate clients before HARDWARE ACCEPTED.
- Signed durable receipt ACK remains a MASTER/CORE/QA coordinated blocker and
  was not modified here.
- No merge, flash, reset, customer money, deployment, tag, or release.
