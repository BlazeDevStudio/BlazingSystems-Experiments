# BlazePwifi v0.3 Architecture Design

Date: 2026-10-04  
Status: Design approved in chat; implementation not yet started  
Project: BlazePwifi  
Repository: BlazingSystems/BlazingSystems-Experiments

## 1. Purpose

BlazePwifi v0.3 evolves the current OpenWrt prepaid-hotspot platform into a multi-target deployment system that remains reliable on constrained routers while scaling cleanly to x86 PCs and Orange Pi systems.

The main development goals are:

- keep the hardened v0.2 accounting, session and coin path intact;
- make all practical deployment settings configurable rather than source-code constants;
- add real admin brute-force protection and authenticated sessions;
- add a portal/theme builder and public preview gallery;
- support ESP8266 and ESP32 Vendo controllers;
- add Orange Pi hardware families, prioritizing Orange Pi Zero 3, Orange Pi One and Orange Pi PC, with additional supported Orange Pi boards where upstream OpenWrt support is verified;
- keep x86_64 BIOS and UEFI deployments first-class;
- add an owned-device Android phone-rental system with factory-reset QR Device Owner provisioning and a lower-security normal APK mode;
- publish successful build outputs as GitHub Release assets with checksums and versioned manifests;
- keep the public repository free of the commercial vendor name and supplied reference-host URL;
- preserve clean-room implementation boundaries and publication-safe source.

## 2. Inputs reconciled

This design consolidates lessons from the current BlazePwifi code, prior OpenWrt/PisoWiFi work, EasyMode, TokenLauncher, ESP controller work, VLAN deployments, x86 homelab/router designs, and current upstream documentation.

Reusable engineering decisions:

- OpenWrt remains responsible for interface management, DHCP/DNS integration, firewall4/nftables, VLANs, routing, service management and system recovery.
- BlazePwifi remains responsible for client identity, credits, vouchers, sessions, rate plans, portal/API behavior, Vendo coordination, rental-device leases and audit records.
- The existing v0.2 browser device-token + MAC rebinding model remains the user identity baseline.
- Existing idempotent target-bound coin events, durable router target state, ESP pending-event journal and fail-closed clock handling remain mandatory.
- EasyMode's capability-detection, transactional installation, backup, validation and rollback model should be reused instead of writing target-specific installation logic repeatedly.
- Existing DSA/VLAN lessons are retained: prevent duplicate DHCP on captive VLANs, preserve management access during topology changes, support tagged and untagged hybrid links, and make VLAN roles explicit.
- The prior Android TokenLauncher prototype contributes Device Owner, lock-task and launcher concepts but is not reused as production code without redesign.
- Orange Pi direct GPIO must use the Linux GPIO character-device model through libgpiod/gpiod-tools, not deprecated sysfs GPIO.
- ESP32 persistent configuration should use Preferences/NVS for small settings and LittleFS only where journaling or larger content requires it.
- Captive-portal behavior must account for OS captive-portal mini-browser limitations and not assume a full browser survives authentication.

Public external references used by implementation may include upstream OpenWrt, Android Enterprise/Android Developers, openNDS behavior/documentation, Espressif/Arduino platform documentation and GitHub release documentation. Unnamed supplied commercial references may be studied privately for observable behavior only and must not be named or linked in the public repository.

## 3. Capability tiers

v0.3 does not force every feature onto every target.

### 3.1 Lite

Primary target:
- low-flash OpenWrt routers such as RG-EW1200G Pro v1.1.

Characteristics:
- hardened accounting/session core;
- compact admin UI;
- compact schema-based portal editor;
- template selection, colors, text, logos and feature toggles;
- ESP8266/ESP32 Vendo support;
- VLAN/network configuration;
- vouchers, pause/resume, client/session administration;
- anti-bruteforce admin protection;
- no heavy WYSIWYG runtime, large JavaScript frameworks, local image processing, Android fleet database or heavyweight analytics.

Goal:
- preserve stability on approximately 16 MB flash / 128 MB RAM devices.

### 3.2 Standard

Primary targets:
- Orange Pi Zero / Zero2 / Zero2W / Zero3;
- Orange Pi One / One Plus;
- Orange Pi PC / PC Plus / PC2;
- similar supported ARM SBCs.

Characteristics:
- all Lite functions;
- richer live portal preview;
- GPIO Vendo agent through libgpiod;
- configurable hardware profiles;
- Android rental lease service;
- fuller audit/history view;
- optional local backups/export.

### 3.3 Full

Primary targets:
- x86_64 PCs, thin clients, mini PCs and VMs.

Characteristics:
- all Standard functions;
- full portal builder;
- larger local history/audit retention;
- Android rental fleet management;
- more detailed diagnostics;
- optional installer ISO;
- multi-NIC hardware detection;
- BIOS and UEFI images;
- larger template library and asset storage.

A target may automatically downgrade features based on available flash, RAM, packages or unsupported hardware. Unsupported features must be hidden or disabled with an explanation rather than exposed as broken controls.

## 4. Core configuration model

All practical deployment values become configuration data.

Configuration groups:

- system:
  - edition/capability tier;
  - hostname;
  - timezone;
  - NTP requirements;
  - state paths;
  - durable-write policy;
  - log retention;
  - backup/restore policy.

- network:
  - WAN interface(s);
  - management interface;
  - hotspot bridge;
  - Vendo/controller interface;
  - Android rental-device interface;
  - LAN addresses;
  - DHCP ranges;
  - DNS;
  - firewall zones;
  - client isolation;
  - STP/RSTP where appropriate;
  - VLAN IDs;
  - tagged/untagged/PVID membership;
  - SSID mapping;
  - optional flat-network mode.

- captive portal:
  - portal/admin/controller ports;
  - CPD endpoints;
  - walled-garden domains/IPs;
  - rate cards;
  - feature visibility;
  - theme/template selection;
  - text labels;
  - language strings;
  - images/assets.

- accounting:
  - currency display;
  - coin pulse value;
  - rate plans;
  - voucher rules;
  - session-transfer policy;
  - simultaneous-device policy;
  - pause policy;
  - bandwidth profiles;
  - retention.

- hardware:
  - controller type;
  - GPIO chip/line;
  - input polarity;
  - debounce;
  - pulse grouping;
  - relay polarity;
  - LED GPIO and polarity;
  - coin-window duration;
  - controller heartbeat.

- security:
  - administrator accounts/roles;
  - login lockout thresholds;
  - session idle/absolute expiry;
  - TOTP enablement where supported;
  - management VLAN;
  - allowed admin subnets;
  - audit retention.

No production secret is committed as a universal default. First boot must generate or require creation of secrets.

## 5. Admin authentication and brute-force defense

### 5.1 Authentication model

Default first-run account name: `admin`.

The password is not fixed. Installation must either:
- generate a high-entropy one-time bootstrap credential and force replacement; or
- require password creation before the admin console becomes active.

Management remains HTTPS-only and bound to a configured management/LAN address, never a WAN wildcard by default.

### 5.2 Rate limiting

Failed authentication is tracked by:
- source IP;
- username/account;
- global failure rate.

Default policy:
- 5 failed attempts in 5 minutes -> 15-minute account+IP lock;
- subsequent lockouts escalate to 30 and 60 minutes;
- global failure threshold can temporarily reject new login attempts;
- successful login clears only the appropriate short-term counter, not audit history.

Thresholds are configurable.

The implementation must use RAM-backed active lock state with durable audit records where reasonable so flash is not rewritten on every failed request.

### 5.3 Sessions

Successful authentication issues a cryptographically random admin session token.

Defaults:
- secure cookie;
- HttpOnly;
- SameSite=Strict;
- configurable idle timeout;
- configurable absolute timeout;
- CSRF token for state-changing operations;
- logout invalidates session server-side.

Roles:
- Admin: all configuration and security changes.
- Operator: sessions, credits, vouchers, controllers and rentals.
- Viewer: status/audit read-only.

Lite builds may initially expose Admin + Operator only if Viewer adds unnecessary complexity, but the underlying ACL format must remain extensible.

### 5.4 Audit

Record:
- successful and failed admin logins;
- lockouts;
- configuration changes;
- manual credit/time changes;
- voucher generation;
- controller enrollment/removal;
- rental-device enrollment/release;
- backup/restore operations.

Sensitive secrets must never be written to audit logs.

## 6. Client/session handling

Retain v0.2 behavior:
- browser device token;
- current MAC/IP binding;
- private/random MAC rebinding;
- durable credit;
- timed sessions;
- pause/resume;
- one-time vouchers;
- target-bound idempotent coin events;
- replay protection;
- fail-closed unsynchronized-clock behavior.

Add:
- admin client search;
- active/expired/paused state;
- manual add/subtract credit with audit;
- manual add/subtract time with audit;
- block/allow status;
- optional speed profile;
- session transfer enable/disable;
- maximum simultaneously active devices;
- configurable stale-account cleanup;
- exportable session/account history on Standard/Full targets.

No request to view the public portal may create permanent zero-balance state.

## 7. Portal builder and templates

### 7.1 Storage format

Portal configuration is stored as structured data rather than directly editing the production HTML.

Files:
- `/etc/blazepwifi/portal/portal.json`
- `/etc/blazepwifi/portal/theme.css`
- uploaded assets in a size-limited asset directory.

### 7.2 Lite builder

The Lite admin page supports:
- template selection;
- logo;
- site/business name;
- headings and notices;
- colors;
- font scale;
- border radius;
- background/image;
- button text;
- visibility toggles;
- rate-card layout;
- voucher visibility;
- pause/resume visibility;
- contact/social text;
- language strings;
- live iframe preview using the same renderer.

No drag/drop framework is required on Lite.

### 7.3 Standard/Full builder

Adds:
- reorderable sections;
- device-size preview;
- reusable blocks;
- advanced CSS overrides;
- import/export template JSON;
- template duplication;
- versioned drafts;
- preview before publish.

Raw JavaScript injection is not supported. Optional raw HTML/CSS editing may be provided only in an explicitly unsafe advanced mode and must be disabled by default.

### 7.4 Repository template gallery

Create:

`experiment/openwrt/BlazePwifi/portal-templates/`

Required previewable screens:
- gallery/index;
- first-run setup;
- admin login;
- admin dashboard;
- portal home;
- rates;
- inserting coin;
- Vendo selection;
- voucher redemption;
- active session;
- pause/resume;
- expired/disconnected state;
- Vendo setup;
- ESP controller setup;
- Orange Pi GPIO controller setup;
- Android rental enrollment;
- Android rental locked/expired screen;
- common error/offline state.

Each template folder contains:
- README;
- structured template JSON;
- preview HTML;
- screenshot/static preview where useful.

The gallery must work as a static GitHub Pages/HTML preview with no live router required.

## 8. Vendo/controller abstraction

One protocol contract serves ESP8266, ESP32 and Linux GPIO agents.

Common logical operations:
- enroll/register;
- heartbeat;
- poll coin window;
- report coin event;
- configuration read/update;
- health/status;
- firmware/version info.

Coin events retain:
- controller ID;
- event nonce;
- target/session nonce;
- pulse count;
- signature/authentication;
- idempotent replay handling.

### 8.1 ESP8266

Retain existing:
- Arduino ESP8266 core;
- WPA2 setup AP;
- LittleFS pending-event journal;
- configurable GPIO/polarity;
- signed requests;
- retry with stable event ID.

### 8.2 ESP32

Create equivalent firmware using:
- Arduino ESP32;
- Preferences/NVS for configuration;
- LittleFS for pending coin journal where needed;
- Wi-Fi STA + temporary protected setup AP;
- same logical protocol as ESP8266;
- configurable pins;
- support for common ESP32, ESP32-S2/S3/C3 variants when compilation allows.

No ESP32-only feature may become required by the server protocol.

### 8.3 Linux/Orange Pi GPIO agent

Use:
- `/dev/gpiochip*`;
- libgpiod/gpiod-tools;
- profile-based chip+line mappings;
- no hard-coded sysfs GPIO number assumptions.

Agent behavior:
- monitor coin line;
- debounce/group pulses;
- control relay/LED;
- persist one unacknowledged coin event;
- register/heartbeat to BlazePwifi core;
- expose health diagnostics.

## 9. Orange Pi targets

Priority hardware:
1. Orange Pi Zero 3;
2. Orange Pi One;
3. Orange Pi PC;
4. Orange Pi PC Plus;
5. Orange Pi PC2;
6. Orange Pi Zero;
7. Orange Pi Zero2;
8. Orange Pi Zero 2W;
9. Orange Pi One Plus;
10. Orange Pi R1 where useful.

Upstream support must be verified per release before publishing an image.

Primary OpenWrt architecture:
- sunxi / appropriate subtarget;
- standard OpenWrt networking stack;
- BlazePwifi overlay/package injected through ImageBuilder or supported image-generation path.

Hardware profiles describe:
- board identifier;
- CPU family;
- Ethernet capabilities;
- known Wi-Fi support limits;
- GPIO chip/lines;
- default management/hotspot interface proposal;
- minimum power guidance;
- capability tier.

Orange Pi Zero 3, One and PC are release-gating boards for v0.3 image generation. Other Orange Pi targets may be published only after successful builds; unsupported/untested targets remain documented source profiles rather than fake release binaries.

## 10. x86_64 targets

x86_64 remains a first-class Full target.

Required images:
- legacy BIOS squashfs combined image;
- UEFI squashfs combined image;
- legacy BIOS ext4 combined image;
- UEFI ext4 combined image.

Optional installer:
- bootable x86_64 installer ISO if the CI implementation is reproducible and verified.

Hardware detection must not assume `eth0`/fixed NIC roles. The setup flow enumerates:
- physical NICs;
- link state;
- MAC addresses;
- PCI/USB adapters;
- wireless interfaces;
- existing bridges/VLANs.

First-run setup assigns roles and preserves a management path before applying changes.

## 11. Android phone-rental subsystem

Package name:
- `com.blazesystems.blazerental`

### 11.1 Managed / robust mode

Intended for devices owned or explicitly authorized for rental use.

Provisioning:
1. factory reset;
2. enter Android provisioning flow;
3. scan BlazeRental enrollment QR;
4. Android downloads/verifies the DPC APK;
5. BlazeRental becomes Device Owner / fully managed DPC where supported;
6. enrollment extras bind the device to the BlazePwifi server using a one-time enrollment token;
7. DPC applies configured rental policy.

Managed controls may include:
- persistent preferred launcher/home;
- lock task allowlist;
- hide/disable status-bar features according to supported API;
- block creation of overlay windows while locked;
- restrict unknown app installation;
- restrict safe boot where Device Owner API supports it;
- restrict adding users/accounts where appropriate;
- keep rental launcher active after reboot;
- boot-completed reconciliation;
- policy-controlled allowed-app set.

Authoritative rental time is server-side. The Android app stores only a signed/cached lease sufficient for short offline tolerance if the administrator enables offline grace.

Changing device clock, clearing ordinary app preferences or restarting the launcher must not create additional paid time.

QR generator outputs:
- provisioning JSON;
- PNG QR asset;
- package download URL;
- package checksum;
- server enrollment endpoint;
- one-time enrollment extras.

### 11.2 Normal APK / companion mode

The same APK can be installed manually without factory reset.

This mode:
- does not claim Device Owner;
- uses only permissions available to a normally installed application;
- may provide launcher/app-lock guidance and lease UI;
- clearly labels itself lower-security;
- cannot promise resistance to uninstall, safe mode, settings access or user reset.

The server records provisioning mode per rental device.

### 11.3 Honest enforcement boundary

The project does not claim protection against:
- bootloader unlock;
- recovery flashing;
- OEM-specific maintenance interfaces;
- physical storage replacement;
- exploits outside Android management APIs.

## 12. Release layout

Repository source layout:

`experiment/openwrt/BlazePwifi/releases/<version>/`

The version folder contains lightweight distributable material and the definitive asset index:
- README;
- ASSETS.md;
- manifest.json;
- SHA256SUMS;
- installer scripts;
- `.ino` sources;
- provisioning samples;
- migration notes;
- release notes.

Large generated binaries are attached to the matching GitHub Release and indexed from ASSETS.md rather than duplicated indefinitely in Git history.

Required successful release assets where supported:
- source `.tar.gz`;
- source `.zip`;
- OpenWrt installer bundle;
- Ruijie bootstrap/install `.bin` as applicable;
- Ruijie BlazePwifi sysupgrade `.bin`;
- Orange Pi `.img.gz` per successful supported target;
- x86 BIOS/UEFI `.img.gz`;
- x86 installer `.iso` only when its build/test gate passes;
- ESP8266 `.ino`, `.bin`;
- ESP32 `.ino`, `.bin` per compiled board family;
- BlazeRental `.apk`;
- Android provisioning QR PNG/JSON example;
- portal-template archive;
- checksum manifest;
- build manifest;
- optional SBOM.

No failed or placeholder binary is uploaded merely to satisfy a file list.

## 13. Installation and README requirements

Main README must document:

- supported hardware;
- capability tiers;
- first-run workflow;
- management URLs;
- no fixed production password;
- how first admin credentials are created;
- admin lockout recovery;
- network/VLAN examples;
- management VLAN;
- hotspot VLAN;
- controller/Vendo VLAN;
- rental-device VLAN;
- flat-network alternative;
- Wi-Fi/SSID mapping;
- ESP8266 default/example pins;
- ESP32 default/example pins;
- Orange Pi GPIO profile examples;
- electrical warning for 12 V coin acceptors;
- Ruijie flash/recovery path;
- Orange Pi SD-card imaging;
- x86 BIOS/UEFI imaging;
- optional ISO installation;
- ESP flashing;
- BlazeRental QR provisioning;
- BlazeRental normal APK mode;
- backup/restore;
- upgrade/migration;
- uninstall/recovery;
- release asset verification with SHA-256.

Pin configurations are defaults/profile examples only; all supported assignments are editable.

## 14. Installer architecture

Reuse EasyMode-style transactional deployment:

1. inspect hardware/capabilities;
2. verify OS/release;
3. verify free storage/RAM;
4. check package dependencies;
5. create backup;
6. stage files;
7. validate syntax/schema;
8. validate configuration without losing management access;
9. apply services/firewall/network;
10. run health check;
11. automatically roll back on failure.

Installers:
- OpenWrt shell installer;
- image-based target installers;
- optional offline HTML helper for supported browser/SSH workflows;
- x86 ISO installer where successful;
- Android QR enrollment generator;
- ESP flashing instructions/packages.

No installer modifies bootloader/raw MTD unless an exact supported device procedure requires it and the path is explicitly documented.

## 15. Security boundaries

- Admin is management-network only by default.
- WAN admin exposure remains disabled.
- Captive clients are treated as untrusted.
- Vendo/controller network separation is recommended and configurable.
- Android enrollment tokens are one-time and expire.
- Secrets are not committed to source/release examples.
- Release manifests contain no private credentials.
- Portal custom content cannot execute arbitrary JavaScript by default.
- Rental management applies only to owned/authorized devices.
- Payment integrations remain redirects/callbacks; BlazePwifi does not store card credentials.
- Public repository content must not contain the prohibited commercial vendor name, supplied reference-host URL, confidential employer/customer identifiers or proprietary binaries/assets.

## 16. Testing and release gates

### Core
- shell/static syntax;
- schema validation;
- account/session integration;
- private-MAC rotation;
- voucher one-time semantics;
- pause/resume;
- target-bound coins;
- duplicate/replay rejection;
- crash/reboot recovery;
- clock-unsynchronized fail-closed behavior;
- concurrent money-changing operations.

### Admin/security
- correct login;
- incorrect login;
- per-IP lockout;
- per-account lockout;
- lockout expiry;
- global throttle;
- session expiry;
- logout invalidation;
- CSRF rejection;
- role ACL;
- audit generation;
- WAN listener absence.

### Portal
- schema migration;
- template rendering;
- invalid asset rejection;
- preview rendering;
- Lite memory/size budget;
- static preview gallery links.

### Controllers
- ESP8266 compile;
- ESP32 compile on selected reference boards;
- journal recovery;
- retry idempotency;
- configurable polarity/pins;
- Linux GPIO-agent syntax/unit tests.

### Android
- Gradle release APK build;
- managed/unmanaged mode detection;
- enrollment-extra parsing;
- lease expiry;
- reboot recovery;
- server-unavailable policy;
- policy application tests where emulator/device-owner test infrastructure permits.

### Images
- Ruijie build + checksum;
- Orange Pi Zero 3 build + checksum;
- Orange Pi One build + checksum;
- Orange Pi PC build + checksum;
- x86 BIOS/UEFI builds + gzip/checksum;
- any additional Orange Pi image only after its own build succeeds;
- x86 ISO only after ISO boot/build verification.

### Release
- manifest matches uploaded assets;
- every asset checksum verifies;
- no prohibited vendor string/URL in public source or release assets;
- no private credentials;
- README links resolve;
- preview gallery resolves.

## 17. Success criteria

v0.3 may be called a successful software release when:

- all mandatory CI gates for its advertised targets pass;
- GitHub Release assets exist for every advertised successful build;
- Orange Pi Zero 3, Orange Pi One, Orange Pi PC and x86 BIOS/UEFI outputs build successfully;
- ESP8266 and ESP32 firmware build successfully;
- BlazeRental APK builds successfully;
- anti-bruteforce and admin-session tests pass;
- portal builder/templates render and previews are accessible;
- release checksums independently verify;
- the public repository contains no prohibited commercial-vendor reference.

Hardware claims remain narrower:
- a target is “build validated” after CI image generation/checksum;
- a target becomes “hardware validated” only after physical boot/install/recovery testing on that exact board/device revision.

## 18. Implementation sequence

1. Repository/publication scrub + v0.3 schema/capability foundation.
2. Admin authentication, lockout, sessions, ACL and audit.
3. Config API + transactional network/VLAN settings.
4. Portal renderer, Lite builder and template gallery.
5. Full builder enhancements for Standard/Full.
6. Controller protocol refactor.
7. ESP8266 migration to shared protocol adapter.
8. ESP32 implementation and builds.
9. Linux GPIO agent + Orange Pi hardware profiles.
10. Orange Pi image-build matrix, prioritizing Zero 3, One and PC.
11. x86 hardware-detection improvements + BIOS/UEFI images + optional ISO.
12. BlazeRental Android DPC + normal APK mode + QR generator.
13. Release-folder/indexing architecture + GitHub Release automation.
14. README/install/recovery documentation.
15. Full security, regression, image and packaging audit.
16. Publish only assets whose corresponding gates pass.
