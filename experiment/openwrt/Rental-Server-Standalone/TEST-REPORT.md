BlazeRental R281 Test Hub v0.1.2 - Test Report
================================================

Packaging regression check
- v0.1.0 correctly failed closed because two embedded payload hashes referred to the pre-GitHub build.
- v0.1.1 pins the SHA-256 of the payload files actually committed on main:
  - rental: 7659e082583a771d9e9aa8ee3b9612d3cbfff2c1807d696c24f3578d5ba92113
  - rental-admin: a794e80ad1dc95cf938cd08f618740bf87d44e30bb3dad4f2c217520225c2059
  - index.html: 687094a3fe151e751f0067baf78666f7233eb4ee8fb767e5a89a0fba307a7ddf
- Payload verification remains mandatory; it was not disabled as a workaround.

R281 dashboard authentication regression
- Dashboard now sends admin_token in the POST body in addition to X-Blaze-Rental-Admin.
- rental-admin already accepts either transport and validates the value against /etc/blazepwifi-rental/admin.token.
- This fixes uHTTPd/CGI environments where the custom request header is omitted.
- Authentication is not bypassed and the token comparison remains mandatory.

Static checks
- POSIX shell syntax: PASS for installer, app CGI, admin CGI.
- Installer does not issue uci set/commit, firewall reload, network reload, wifi reload, modem commands, or reboot.
- Installer verifies existing uHTTPd home=/www and cgi_prefix=/cgi-bin and aborts rather than modifying them.
- Existing /www/index.html and /www/admin are not written.
- Existing non-Blaze /www/rental or /www/cgi-bin/rental endpoints cause a safe abort unless --force is explicitly used.

Protocol integration check (host-side)
- Admin health authentication: PASS.
- One-time enrollment token generation: PASS.
- BlazeRental-compatible HMAC-SHA256 enrollment: PASS.
- Device ID + device secret creation: PASS.
- Signed status response: PASS.
- Expired/zero-time compatibility clamp to server-now: PASS.
- Manual +3600 second lease grant: PASS.
- Signed status reflected >= 3599 seconds remaining: PASS.
- coin_start in manual-only mode returns a clear operator message: PASS.

Target evidence used
- R281 backup: uHTTPd main serves /www on ports 80/443 with cgi_prefix=/cgi-bin.
- R281 backup: LAN IP is 192.168.1.1.
- Existing OpenWrt/EasyMode network, firewall, relay, modem and Wi-Fi configuration remain outside installer write paths.
- Repository R281 baseline: board notion,r281, OpenWrt 24.10.8, EasyMode 4.2.3 experiment.
- Current BlazeRental client API path: BASE_URL/cgi-bin/rental.

Remaining physical validation
- Run installer on the actual R281.
- Open /rental from a LAN client.
- Enroll the actual BlazeRental APK.
- Verify Device Owner/manual APK behavior and lease refresh on the physical Android phone.

This is a rental test hub, not a full hotspot/coinslot BlazePwifi deployment.
