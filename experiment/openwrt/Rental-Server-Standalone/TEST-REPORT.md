v0.1.3-preview.1 exact CI addendum (2026-10-18 Manila)
- Old-code expected RED #39083519007: admin issued enrollment token without random bytes.
- First corrected head #39083853101: negative refusal/checksum/syntax PASS, healthy enrollment FAIL of unknown cause.
- Diagnostic-only head #39083975140: SUCCESS attempts 1 and 2 without source change.
- Ten-issuance head #39084229748: SUCCESS attempts 1 and 2 at literal SHA; no-RNG refusal, positive admin/app issuance, checksum and syntax PASS.
- Physical R281 install, Android enrollment, lease crash recovery and customer acceptance remain untested. Draft preview only.

BlazeRental R281 Test Hub v0.1.3-preview.1 - Entropy addendum
==========================================================
- Expected RED: literal PR #107 #39083519007 issued an enrollment token after forced kernel entropy reader failure.
- Corrected source #39083853101 passed checksum/syntax and missing-entropy refusal but failed healthy admin issuance; root cause unknown.
- Diagnostic-only head #39083975140 succeeded twice at the same literal SHA. Ten healthy-issuance stress test pending exact CI.
- This preview has no physical R281/Android install, crash-atomic lease, or production acceptance.

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
v0.1.3-preview.1 OpenSSL entropy addendum (2026-10-18 Manila)
- Test `608fa44c`, synced `6c20603c` literal Ubuntu #39084787348 FAILED entropy step (checksum/syntax passed); current source lacked OpenSSL fallback when byte readers failed.
- Source `c44b741f` now prefers OpenSSL, retains checked kernel-reader fallbacks and all-source refusal; exact Ubuntu CI PENDING. Earlier diagnostic #39084567668 failed before CGI diagnostics, so its cause is not established.
- Draft preview only. No physical R281/Android, powercut or production proof.


- Source c44b741f, synced b5acadf9: literal Ubuntu #39085021978, #39085068843, #39085071424 SUCCESS; preview only. No hardware or lease crash atomicity proof.

- R281-STANDALONE-0003 test e39c1e64, synced bdcf7d04 literal Ubuntu #39086623050 expected RED: admin lost newer lease at lock edge; checksum/syntax/entropy passed. Source 16fff7b4 moves read under lock and refuses revoked phone, exact retest pending.

- R281-STANDALONE-0003 source 16fff7b4, synced 856c2687: literal Ubuntu #39086946962, #39086991742, #39086993426 all SUCCESS at exact SHA. Admin/phone status preserve newer lease and refuse revoke under synthetic lock-edge writer; no physical durability claim.

- R281-STANDALONE-0004 test ecf12969, synced 1e53358b literal Ubuntu #39090790627 expected RED: status rewrote devices.tsv; preceding checks passed. Source 1c05f69a separates advisory activity from lease, exact CI pending.
