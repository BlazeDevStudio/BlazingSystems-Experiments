# ESPHole

Experimental ESP8266 DNS sinkhole, captive setup portal, and Wi-Fi NAPT repeater.

> **Release policy:** every release is kept as its own numbered source file. A new release must be added as a new file such as `ESPHole_v1.2.0.ino`; older numbered releases must never be deleted, renamed, or overwritten.

## Current status

**Latest experimental release:** v1.3.0  
**Target board:** NodeMCU 1.0 / ESP-12E-class ESP8266  
**Reference build environment:** ESP8266 Arduino Core 3.1.2, GCC 10.3, 160 MHz CPU build  
**Promotion rule:** ESPHole stays in `BlazingSystems-Experiments` until the user confirms successful real-board testing. A validated version may then be copied to `BlazingSystems-Projects`.

## Release files

| Version | File | Status |
| --- | --- | --- |
| v1.3.0 | `ESPHole_v1.3.0.ino` | Experimental / Wi-Fi scan fix; hardware validation pending |
| v1.2.0 | `ESPHole_v1.2.0.ino` | Experimental / Wi-Fi connection fix; preserved |
| v1.1.0 | `ESPHole_v1.1.0.ino` | Experimental / preserved |
| v1.0.0 | `ESPHole_v1.0.0.ino` | Experimental stabilization baseline |
| Rolling copy | `ESPHole.ino` | Legacy convenience copy; not the permanent release record |

### Versioning rules

- Never overwrite a numbered release.
- Never delete an older numbered release just because a newer one exists.
- Every future version gets a new file: `ESPHole_vX.Y.Z.ino`.
- The README must be updated for each release.
- Each release note must state:
  - features added
  - bugs fixed
  - known bugs / limitations
  - dependency or library changes
  - compile/test status
  - real-hardware validation status
- If a future release adds a third-party library, its exact library name, source, version if pinned, and installation steps must be documented under **Libraries and installation** before that release is considered complete.
- `ESPHole.ino` must not replace the historical numbered files. Numbered files are the authoritative snapshots.

## Libraries and installation

### External libraries

**ESPHole v1.3.0 requires no third-party/external Arduino libraries.**

Everything currently included by the sketch comes with the ESP8266 Arduino core:

| Include | Source | Separate install? | Purpose |
| --- | --- | --- | --- |
| `Arduino.h` | ESP8266 Arduino core | No | Arduino runtime |
| `ESP8266WiFi.h` | ESP8266 Arduino core | No | STA/AP Wi-Fi, scanning, RSSI and connection state |
| `WiFiClient.h` | ESP8266 Arduino core | No | Internet reachability test over TCP/HTTP |
| `ESP8266WebServer.h` | ESP8266 Arduino core | No | Local EasyMode-style web interface |
| `WiFiUdp.h` | ESP8266 Arduino core | No | DNS UDP listener and upstream forwarding |
| `LittleFS.h` | ESP8266 Arduino core | No | Persistent settings and blocklist |
| `NetDump.h` | ESP8266 Arduino core | No | Lightweight PHY/network activity observation |
| `lwip/napt.h` | ESP8266 Arduino core / lwIP2 | No separate library | IPv4 NAPT repeater support |

Do **not** install random Library Manager packages with similar names. ESPHole is written against the versions bundled with the selected ESP8266 core.

### Install the ESP8266 Arduino platform

In Arduino IDE:

1. Open **File > Preferences**.
2. Add this URL under **Additional Boards Manager URLs**:

   `https://arduino.esp8266.com/stable/package_esp8266com_index.json`

3. Open **Tools > Board > Boards Manager**.
4. Search for **esp8266** and install the ESP8266 platform.
5. ESPHole development currently targets **ESP8266 Arduino Core 3.1.2**.
6. Select **NodeMCU 1.0 (ESP-12E Module)** or the matching ESP8266 board.
7. Use a 4 MB flash configuration where available.
8. Use an IPv4 lwIP2 configuration with features/NAPT enabled.

If a later release requires an external library, installation instructions will be added here, including the exact version if compatibility requires pinning.

## v1.3.0 — Experimental Wi-Fi scan stabilization

File: `ESPHole_v1.3.0.ino`

### Bug observed in v1.2.0

The Wi-Fi scan could visibly run but return `0 networks` even when nearby access points were available.

The v1.2 implementation started `WiFi.scanNetworks(...)` directly inside the `/api/scan` HTTP request handler. ESP8266 scan behavior is more reliable when the radio scan is started from the main Arduino loop rather than from the web-server callback path.

### Fixed / changed

- The HTTP endpoint no longer starts the ESP8266 radio scan.
- `/api/scan?start=1` only queues a scan request.
- A new loop-driven scan service starts and polls the async scan from `loop()`.
- Scanning explicitly requests:
  - async mode
  - hidden SSID discovery
  - channel `0` = all 2.4 GHz channels
- STA reconnect attempts and internet probes are paused while scanning so they do not fight the same ESP8266 radio.
- A first scan that genuinely returns zero results automatically retries once before reporting zero networks.
- Scan results are cached before `WiFi.scanDelete()` frees the ESP8266 scan buffer.
- Duplicate SSIDs from multiple BSSIDs are collapsed in the web list, keeping the strongest result first.
- The scan UI now has a separate **start** and **poll** flow instead of repeatedly re-triggering the scan endpoint.
- Added serial diagnostics:
  - scan queued
  - scan started from loop
  - Wi-Fi mode / STA state / current channel
  - raw network count
  - scan duration
  - zero-result retry
  - scan error codes

### Root-cause evidence

The ESP8266 Arduino project's own async-scan example starts `WiFi.scanNetworks(true)` from `loop()` and polls `WiFi.scanComplete()` later. Historical ESP8266 reports also document zero-result scans when scanning is initiated from a web-server handler in AP+STA use.

v1.3 follows the loop-driven pattern instead.

### Libraries / dependencies

No new library was added.

v1.3.0 still uses only libraries bundled with ESP8266 Arduino Core 3.1.2 and therefore requires **no separate Library Manager installation**.

### Validation performed

- A regression check was first run against v1.2.0 and confirmed:
  - `handleWifiScan()` directly started `WiFi.scanNetworks()`
  - no loop-driven scan service existed
  - no HTTP-to-radio request flag existed
- v1.3.0 source gates then verified:
  - the HTTP scan handler contains no `WiFi.scanNetworks()` call
  - the loop-driven scan service exists
  - `loop()` invokes the scan service
  - scans explicitly use channel `0` for all channels
  - a zero-result scan retries once
  - STA maintenance is paused while scanning
  - the browser uses a start/poll scan protocol

Real NodeMCU scan results remain the authoritative hardware test.

### Known limitations

- ESP8266 is a single-radio AP+STA device, so client traffic may briefly pause while the radio scans other channels.
- A hidden network with no broadcast SSID can still require manual SSID entry even when its BSSID is detected.
- 5 GHz Wi-Fi is not supported by ESP8266; only 2.4 GHz networks can be discovered.
- Hardware validation is still pending for v1.3.0.

## v1.2.0 — Experimental Wi-Fi stabilization

File: `ESPHole_v1.2.0.ino`

### Bug cause found in v1.1.0

v1.1.0 saved the submitted SSID/password and then immediately called `ESP.restart()` after about 350 ms. It did **not** verify any of these steps before rebooting:

- that the configuration could be read back correctly from LittleFS
- that the ESP8266 actually associated with the selected Wi-Fi
- that DHCP supplied a usable STA address
- that DNS resolution worked
- that the upstream network actually had internet access

The presence of a saved SSID was also treated as equivalent to a completed setup. Therefore a wrong password or failed association could leave the device in a confusing state after restart.

### Fixed / changed

- Removed the automatic reboot after first-run Wi-Fi setup.
- Removed the automatic reboot after ordinary Settings saves.
- Credentials are now written to LittleFS and **read back for verification** before ESPHole attempts to use them.
- Added a persistent `setup_complete` flag.
  - It remains false while Wi-Fi/internet setup has not succeeded.
  - It is set true only after upstream internet verification succeeds and that state is saved successfully.
- The ESPHole AP and setup/recovery interface remain available when a Wi-Fi attempt fails.
- Added a connection state machine with visible states for:
  - settings saved
  - connecting
  - Wi-Fi associated
  - checking internet
  - internet online
  - connected but limited/no verified internet
  - failed
- Added explicit failure reporting for:
  - SSID unavailable
  - authentication/connection failure
  - connection timeout
  - DNS resolution failure
  - Wi-Fi connected but internet unavailable
  - captive/intercepted HTTP response
- Added `/api/connect-status` so the setup page can show connection progress without rebooting.
- Added live dashboard distinction between:
  - **Internet online**
  - **Wi-Fi connected / checking**
  - **Setup / offline**
- Wi-Fi credentials changed in Settings are applied live through the STA interface instead of rebooting the ESP8266.
- ESPHole periodically rechecks internet availability after connection.
- AP SSID/password changes are saved but intentionally require the existing **manual Reboot** control before taking effect. This avoids unexpectedly disconnecting the administrator from the ESPHole AP.

### Internet verification

After Wi-Fi association:

1. ESPHole resolves `connectivitycheck.gstatic.com` using the upstream DNS.
2. It requests `/generate_204` over HTTP.
3. HTTP 204 is treated as verified internet access.
4. If that endpoint cannot provide an HTTP response, ESPHole performs a secondary TCP reachability check to `1.1.1.1:80`.
5. A real non-204 HTTP response is treated as limited/captive/intercepted rather than automatically declaring the connection healthy.

### Libraries / dependencies

v1.2.0 adds an explicit include for `WiFiClient.h`.

**This is not an external dependency.** `WiFiClient` is bundled with ESP8266 Arduino Core 3.1.2, so no additional Library Manager installation is required.

v1.2.0 still uses **no third-party Arduino libraries**.

### Validation performed

- Regression tests created for the v1.1 forced-reboot/setup failure.
- Verified that quick setup saves before attempting a connection.
- Verified that normal Settings saves no longer auto-reboot.
- Verified that only the manual Reboot and Factory Reset flows retain `ESP.restart()`.
- Verified that setup completion occurs only after successful internet verification.
- Verified explicit Wi-Fi failure-state handling.
- Verified DNS + HTTP internet-check code paths.
- Embedded JavaScript syntax checks passed.
- Host GCC C++17 syntax pass completed.
- Host Clang C++17 syntax pass completed.
- Simulated Arduino auto-prototype pass completed.

The user's exact ESP8266 `xtensa-lx106-elf-g++` compiler and physical NodeMCU remain the authoritative final compile/runtime test.

### Known limitations

- Real hardware behavior is still pending confirmation.
- Some upstream networks deliberately block Google's connectivity-check endpoint; the secondary reachability check exists for this reason.
- Captive portals can intentionally return a non-204 page and are reported as limited rather than verified.
- ESP8266 AP+STA uses one radio/channel. Changing the STA's upstream Wi-Fi can cause a brief client-side AP interruption while the radio changes channel even though the MCU itself is not rebooting.
- Changing ESPHole's own AP SSID/password still needs a manual reboot to activate those AP identity changes.
- DNS-over-HTTPS / Private DNS can still bypass DNS filtering.

## v1.1.0 — Experimental

File: `ESPHole_v1.1.0.ino`

### Added

- Nearby Wi-Fi scanning.
- First-boot Wi-Fi setup with selectable scan results rather than requiring every field to be typed manually.
- Strongest-first Wi-Fi results with:
  - SSID
  - RSSI
  - estimated signal quality
  - channel
  - security status
- Default ESPHole LAN changed to `10.6.20.1/24`.
- Friendly local hostname: `blaze.iot`.
- Default web credentials:
  - Username: `root`
  - Password: `mnbvcxZ123`
- Configurable admin username and password.
- EasyMode-style at-a-glance dashboard.
- Live metrics for:
  - free heap
  - heap fragmentation
  - maximum free heap block
  - uptime
  - STA connection state
  - upstream SSID
  - STA IP
  - gateway
  - upstream DNS
  - Wi-Fi channel
  - RSSI
  - estimated Wi-Fi signal quality
  - AP client count
  - AP address / SSID
  - NAPT state
  - RX packets and bytes
  - TX packets and bytes
  - DNS queries
  - blocked queries
  - forwarded queries
  - DNS replies
  - errors / timeouts
  - last blocked domain
  - LED activity count
  - buzzer activity count
- Built-in ESP8266 LED activity blinking.
- D5 / GPIO14 activity buzzer.
- Short first-boot/startup chime.
- Independent LED and buzzer activity settings.
- PHY-level RX/TX activity counters for more realistic network-activity indication.

### Fixed / improved

- Reduced the number of fields presented during normal first-time setup.
- Moved less frequently used settings into an advanced section.
- Wi-Fi switching logic no longer silently carries the old Wi-Fi password into a newly selected SSID when the password field is intentionally blank.
- Activity indicators use non-blocking state/timing instead of long delays in normal packet handling.
- Packet activity monitoring records counters/direction only; packet payload contents are not stored.

### Known bugs / limitations

- **Hardware validation still pending.** Compile, flash, boot, NAPT throughput, captive setup, DNS blocking, `blaze.iot`, LED behavior and buzzer behavior must still be confirmed on the physical board.
- DNS-over-HTTPS, Android Private DNS, and applications with built-in encrypted DNS can bypass a DNS sinkhole.
- NAPT is IPv4-only.
- ESP8266 can measure the upstream STA RSSI, but cannot directly know the signal level experienced by each client connected to ESPHole's AP.
- The in-memory blocklist is deliberately limited to conserve ESP8266 RAM.
- `blaze.iot` is a local DNS alias provided by ESPHole, not a public Internet domain.
- Real packet counters depend on the ESP8266 core's PHY capture support.
- A very busy network can generate more traffic events than it is practical to represent as individual buzzer chirps; activity indication is rate-limited deliberately.

### Validation performed before upload

- Feature regression/static checks.
- Embedded dashboard/setup JavaScript syntax check.
- Host GCC C++17 syntax pass with ESP8266/Arduino compatibility stubs.
- Host Clang C++17 syntax pass with ESP8266/Arduino compatibility stubs.
- The user's exact ESP8266 `xtensa-lx106-elf-g++` environment remains the authoritative compile test.

## v1.0.0 — Experimental stabilization baseline

File: `ESPHole_v1.0.0.ino`

### Fixed

- Fixed Arduino auto-prototype problems around the custom `DnsQuestion` type.
- Fixed duplicate default-argument generation for `activityBeep(bool)`.
- Fixed malformed EasyMode HTML/C++ quoting that caused compile failures around the ONLINE/OFFLINE status pill.
- Standardized the buzzer pin internally to GPIO14 / NodeMCU D5.
- Added an ESP8266 target guard.
- Reconciled DNS, LittleFS, ESP8266WebServer, DHCP DNS, `tone()`, and lwIP NAPT structure against ESP8266 Arduino Core 3.1.2.

### Retained

- EasyMode-inspired interface.
- Local DNS filtering.
- Captive setup portal.
- AP+STA operation.
- IPv4 NAPT.
- Persistent configuration.
- Blocklist editor.
- Status API.

### Known bugs / limitations

- Not a full Linux Pi-hole replacement.
- IPv4 DNS/NAPT only.
- Encrypted/private DNS can bypass filtering.
- Real-board validation was still pending.

## Historical compiler bug notes

### Arduino prototype generator

Earlier builds failed because Arduino generated prototypes before it knew about `DnsQuestion`, and because a default argument on `activityBeep(bool force = false)` was repeated in an auto-generated prototype.

Errors included:

- `'DnsQuestion' has not been declared`
- `default argument given for parameter 1 of 'void activityBeep(bool)'`

Resolution:

- Forward-declare / define custom types before generated prototypes can reference them.
- Avoid default arguments on sketch-defined functions that Arduino preprocessing may auto-prototype.

### Dashboard HTML quoting

An early EasyMode status string embedded HTML quotes incorrectly inside an `F("...")` literal.

Errors included:

- `expected primary-expression before '<' token`
- `'span' was not declared in this scope`
- `'ONLINE' was not declared in this scope`

Resolution:

- Correct the embedded HTML quoting.
- Keep ONLINE/OFFLINE output branches separate instead of building the broken ternary flash-string expression.

## Hardware defaults — v1.1.0

- ESPHole AP IP: `10.6.20.1`
- Local hostname: `blaze.iot`
- Admin user: `root`
- Admin password: `mnbvcxZ123`
- Activity buzzer: NodeMCU **D5 / GPIO14**
- Built-in activity LED: `LED_BUILTIN`

Change the default admin password after initial setup on any installation that other people can reach.

## Project scope

ESPHole is intentionally a small ESP8266 network utility. It does not attempt to reproduce Linux Pi-hole feature-for-feature and does not store captured user payloads. Network hooks used for the dashboard and activity indications are intended for counters and activity signaling only.
