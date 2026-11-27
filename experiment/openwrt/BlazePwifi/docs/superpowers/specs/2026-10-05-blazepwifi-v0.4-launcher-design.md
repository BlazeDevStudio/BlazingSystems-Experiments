# BlazePwifi v0.4.0 / BlazeRental Launcher Edition — Production Design

**Date:** 2026-10-05  
**Status:** Approved architecture, implementation not started  
**Supersedes:** BlazeRental v0.3.0 launcher UI only; v0.3.0 remains a preserved stable release  
**Target release:** BlazePwifi v0.4.0  
**Primary goal:** Replace the stripped-down BlazeRental customer UI with a real Android launcher derived from Launcher3, keep coin/time enforcement server-authoritative, provide strong Device Owner kiosk controls, add on-device administration and QR enrollment, modernize BlazePwifi administration around a lightweight TailAdmin-derived UI, and ship validated installable artifacts plus restorable simulation backups for supported hardware.

---

## 1. Product intent

BlazeRental must behave like an actual Android HOME launcher, not a menu of buttons.

The customer should see a normal launcher experience while paid, including a workspace and swipe-up app drawer, but that experience must be explicitly rental-aware:

- no credit means the app drawer cannot open;
- paid credit means the drawer opens and exposes only allowed applications;
- when time expires, paid apps become unavailable and the launcher returns to its locked rental page;
- the notification shade must not provide an escape route in managed mode;
- essential settings must be surfaced inside BlazeRental through safe controls that do not expose unrestricted Android Settings;
- notifications must be rendered inside BlazeRental rather than depending on the blocked shade;
- a small optional timer overlay may remain visible while paid apps are open;
- administrators must be able to configure the phone locally and from BlazePwifi;
- onboarding must prefer QR-based enrollment instead of typing long tokens;
- a deliberate "Use device as is" mode must turn the phone back into a normal launcher experience with rental restrictions removed.

The system remains a multilayer BlazePwifi product: Android Launcher + BlazePwifi server/accounting + ESP/Linux coinslot controllers + OpenWrt/router/SBC/x86 images.

---

## 2. Scope and non-goals

### 2.1 In scope

This release changes:

1. **Android BlazeRental**
   - replace the current `MainActivity` menu-style UI with a Launcher3-derived HOME launcher;
   - add three fixed system pages;
   - gate the app drawer on active rental time;
   - synchronize a revisioned allowed/hidden app policy;
   - add an on-device admin application/settings surface;
   - add QR enrollment scanning;
   - add notification mirror page;
   - add safe quick controls;
   - add optional floating timer;
   - add unrestricted "Use device as is" mode;
   - preserve Device Owner / Lock Task enforcement;
   - preserve server-authoritative lease and targeted coin transactions.

2. **BlazePwifi server**
   - extend rental device policy schema;
   - support bidirectional policy revisions;
   - generate QR enrollment payloads directly from the rental device page;
   - provide richer device/app inventory;
   - provide on-device/server conflict handling;
   - support launcher mode, hidden apps, quick-control policy, timer overlay policy and admin-entry policy.

3. **BlazePwifi admin UI**
   - replace the current compact cards on Standard/Full builds with a lightweight static TailAdmin-derived dashboard;
   - retain a compact fallback for Lite targets;
   - add a first-class Rental Devices section;
   - add app allow/hide switches instead of package-ID text entry;
   - add QR Add Device flow;
   - retain controller management.

4. **Builds and release**
   - compile signed production APK;
   - build ESP8266/ESP32 binaries;
   - build supported OpenWrt router/SBC/x86 images;
   - run browser/UI simulation;
   - run Android emulator Device Owner simulation;
   - run x86 BIOS/UEFI QEMU boot validation;
   - run Orange Pi image/userspace validation;
   - validate Ruijie image/config structure;
   - publish installation-ready assets;
   - publish configured backup images only after the matching simulation gate passes.

### 2.2 Out of scope

The following are explicitly not promised:

- surviving a hardware recovery wipe, bootloader reflash, OEM service tool or physical storage replacement;
- intercepting or redefining the physical Android Power button on all OEM devices;
- guaranteeing Notification Listener or overlay permission can be silently granted on every Android/OEM build;
- CPU-accurate GitHub-hosted emulation of every Orange Pi, ESP8266, ESP32 or MT7621 peripheral;
- cloning proprietary commercial PisoWiFi firmware, assets, protocols, license checks or secrets;
- adding arbitrary JavaScript execution to the captive portal;
- turning the EW1200G Pro into a heavy all-in-one UI target at the expense of flash/RAM reliability.

---

## 3. Versioning and compatibility

### 3.1 Version policy

- BlazePwifi production line becomes **v0.4.0**.
- BlazeRental becomes **BlazeRental Launcher Edition 0.4.0**.
- v0.3.0 remains unchanged as a stable rollback release.
- v0.4.0 state migration must be forward-compatible with existing v0.3.0 rental device records.
- An upgrade from v0.3.0 must preserve:
  - device ID;
  - per-device secret;
  - lease expiration;
  - device label;
  - preferred coinslot;
  - existing phone admin verifier;
  - controller registrations;
  - hotspot accounts and voucher data.

### 3.2 Android support

The upstream Launcher3 source baseline is:

- repository: `amirzaidi/Launcher3`
- branch: `o-mr1`
- upstream commit: `5605dd10845b2ed841cadaf3dddcb0205c057c60`
- license: Apache License 2.0

The upstream tree has a historical minimum Android 5.0 baseline, but BlazeRental's production minimum may remain higher if required by Device Owner, lock-task or notification/overlay implementation. The release documentation must state the actual compiled `minSdk` and must not claim support below what CI/emulator validation covers.

The production package remains:

`com.blazesystems.blazerental`

Future signed updates must use the same production signing identity as the v0.4.0 APK lineage.

---

## 4. Source provenance and Launcher3 preservation

### 4.1 Upstream preservation

The original Launcher3 source must be preserved separately from the BlazeRental derivative.

Desired location:

`BlazingSystems/Forked-Projects`

Because the installed GitHub connector currently does not expose GitHub's native "fork repository" operation, the repository must contain an upstream-preservation mirror/reference with:

- original repository URL;
- original branch;
- exact upstream commit;
- original Apache-2.0 LICENSE;
- no rebranding of the upstream snapshot as original BlazingSystems work.

If a true GitHub fork operation later becomes available, this preserved snapshot may be replaced by a native fork without changing BlazeRental.

### 4.2 BlazeRental derivative

Production launcher code lives under:

`experiment/openwrt/BlazePwifi/android/BlazeRentalLauncher/`

The current v0.3.0 Android project stays preserved until the v0.4.0 launcher passes the full Android production gate.

---

## 5. Android launcher architecture

### 5.1 Base architecture

BlazeRentalLauncher derives from Launcher3 rather than wrapping Launcher3 in another activity.

Primary integration points include:

- Launcher HOME activity;
- Workspace;
- All Apps transition controller;
- All Apps container;
- launcher model/app inventory;
- launcher settings surface;
- notification listener;
- Device Owner receiver/service;
- rental lease/policy client;
- fixed BlazeRental system pages.

The resulting application must behave like a real HOME launcher.

### 5.2 Main launcher pages

The customer workspace has three fixed system pages.

#### Page 1 — Rental

Non-removable contents:

- BlazeRental branding;
- rental state;
- remaining time;
- Insert Coin button;
- Add Time button while already paid;
- server/coinslot status in compact form;
- optional offline/reconnecting indicator;
- optional device label.

The built-in rental controls are not normal Android widgets and must not be draggable, removable or resized by customers.

#### Page 2 — Quick Controls

Only controls that can be implemented without exposing an unsafe path are allowed.

Candidate controls:

- flashlight;
- brightness;
- media volume;
- ring volume where allowed;
- orientation lock;
- floating-timer toggle;
- Bluetooth status/toggle only where Android/OEM APIs permit without handing the user unrestricted Settings;
- Wi-Fi connection/status presentation;
- battery status;
- current server connectivity;
- current coinslot availability.

Rules:

- unsupported controls are hidden;
- controls that require a dangerous Settings activity are not exposed in rental mode;
- no control may be a bridge into unrestricted Settings;
- Device Owner mode may expose a narrow operator-granted settings flow only during admin mode.

#### Page 3 — Notifications

BlazeRental uses `NotificationListenerService` to mirror notifications into a launcher page.

The page shows:

- app icon;
- app name;
- notification title;
- short body;
- timestamp;
- dismiss action where allowed.

Behavior:

- locked/expired session: notification content may display, but tapping cannot launch a blocked application;
- paid session: tapping may launch the source app only when that package is allowed by the active rental policy;
- unrestricted mode: normal launcher notification behavior may be restored;
- notification access state must be visible in on-device admin diagnostics.

### 5.3 App drawer

The Launcher3 swipe-up All Apps transition is the gating point.

When no active paid lease:

- swipe-up gesture is consumed/rejected;
- no All Apps view is shown;
- app drawer cannot be opened by keyboard/accessibility shortcut or internal launcher route;
- launcher remains on the fixed system pages.

When paid:

- All Apps may open;
- only currently allowed, launchable packages are visible;
- packages excluded by policy are hidden from the drawer;
- Android Settings, package installers and other administrative escape packages remain hidden unless admin mode or unrestricted mode explicitly permits them.

### 5.4 Workspace editing

Rental mode disables:

- customer long-press app placement;
- app drag to workspace;
- shortcut pinning;
- arbitrary widget add;
- workspace rearrangement of fixed BlazeRental controls;
- Launcher settings;
- app info shortcuts that open unrestricted settings;
- drag-to-uninstall;
- deep shortcuts that bypass policy.

Admin mode may expose controlled layout options, but customer rental mode must remain immutable.

### 5.5 Floating timer

During a paid session, BlazeRental may show a small draggable overlay timer above allowed applications.

Requirements:

- tiny, low-distraction default footprint;
- configurable opacity/edge position;
- remaining time only by default;
- persisted last position;
- customer toggle in Quick Controls only if operator policy allows;
- administrator can force always-on, allow user toggle or disable;
- if overlay permission is unavailable, rental enforcement still works;
- overlay must disappear in locked state if the rental page already shows the timer.

---

## 6. Device Owner and lock enforcement

### 6.1 Managed mode

QR-provisioned phones use Android Device Owner where supported.

Managed mode applies:

- BlazeRental as persistent preferred HOME;
- Lock Task package allowlist;
- status bar disabled during rental mode;
- safe boot restriction where supported;
- add-user restriction;
- unknown-source install restriction;
- debugging restriction where appropriate;
- normal Settings factory-reset restriction where supported;
- keyguard policy as required by kiosk operation;
- removal of blocked apps from the Lock Task allowlist after lease expiry.

### 6.2 Expiry behavior

When the server-authoritative lease reaches zero:

1. lease state becomes invalid;
2. BlazeRental reapplies managed policy;
3. non-BlazeRental packages are removed from the active Lock Task allowlist;
4. current disallowed app task is ended/left;
5. HOME returns to BlazeRental;
6. app drawer is locked;
7. Page 1 displays Insert Coin.

The same behavior must happen after:

- reboot;
- activity restart;
- launcher process kill/restart;
- temporary server loss once cached lease expires;
- system clock manipulation.

### 6.3 Unrestricted mode

On-device admin contains:

**Use device as is**

When enabled by an authenticated administrator:

- rental drawer gate is disabled;
- full app inventory may be shown;
- Settings may be visible;
- status bar may be re-enabled;
- Lock Task restrictions are removed or reduced appropriately;
- the rental lease no longer gates app access;
- BlazeRental continues functioning as a standard launcher;
- server enrollment may remain for management/diagnostics if the admin chooses.

Returning to Rental Mode must reapply managed policy immediately.

---

## 7. On-device administrator

### 7.1 Admin entry

Do not rely on physical Power-button interception.

Default admin trigger:

- long-press a hidden launcher-owned hotspot such as the remaining-time/BlazeRental mark for a configurable duration;
- then require the phone administrator password.

Configurable trigger options may include:

- logo long-press;
- timer long-press;
- N-tap hidden corner sequence;
- two-corner sequence.

The trigger configuration itself is accessible only from authenticated admin mode.

### 7.2 Brute-force protection

Phone admin authentication must retain or improve v0.3.0 protections:

- password verifier, not plaintext;
- minimum password length;
- failure counter;
- temporary lockout;
- no password in logs;
- no password in QR payload;
- short admin session timeout;
- leaving admin mode reapplies the current customer policy.

### 7.3 Native admin sections

The on-device admin UI is native Android but visually follows the TailAdmin dashboard style:

- dark/light capable dashboard;
- sidebar or tabbed sections;
- metric/status cards;
- compact tables/lists;
- clear warning banners;
- consistent forms and toggles.

Sections:

1. Dashboard
   - rental mode;
   - lease state;
   - BlazePwifi connectivity;
   - Device Owner status;
   - notification permission;
   - overlay permission;
   - preferred coinslot;
   - policy revision.

2. Apps
   - installed launchable apps;
   - allow/hide toggle;
   - search;
   - select all;
   - hide sensitive/system/admin packages by default.

3. Binding
   - Scan BlazePwifi QR;
   - server endpoint;
   - device ID;
   - rebind/revoke status;
   - connectivity test.

4. Rental
   - Rental Mode / Use device as is;
   - preferred Vendo;
   - floating timer behavior;
   - customer toggle permissions;
   - offline grace policy if supported.

5. Security
   - change phone admin password;
   - configure secret admin gesture;
   - show Device Owner state;
   - reapply kiosk policy;
   - security diagnostics.

6. Notifications / Quick Controls
   - permission state;
   - enabled controls;
   - customer visibility policy.

7. Diagnostics
   - app/version/build;
   - last server sync;
   - policy revision;
   - lease server time;
   - inventory sync;
   - recent policy errors;
   - export safe diagnostic report.

---

## 8. Enrollment and binding

### 8.1 BlazePwifi Add Device flow

BlazePwifi Admin → Rental Devices → **Add Device**

The server creates a one-time short-lived enrollment record.

The admin page displays:

- QR code;
- expiration timer;
- device label field;
- optional preselected controller/Vendo;
- optional initial policy template;
- copyable fallback token for recovery only.

### 8.2 QR payload

QR data must contain only what is necessary:

- server endpoint;
- one-time enrollment ID/secret;
- label/template hints;
- optional Wi-Fi provisioning fields when using Android enterprise provisioning;
- package download URL and APK checksum for factory-reset provisioning.

It must not contain:

- permanent device secret;
- phone administrator password;
- reusable master secret;
- admin portal credentials.

### 8.3 Factory-reset managed enrollment

Preferred flow:

1. reset/unprovisioned phone;
2. enter Android enterprise QR provisioning;
3. scan BlazeRental provisioning QR;
4. Android downloads and verifies BlazeRental;
5. BlazeRental becomes Device Owner where supported;
6. one-time enrollment token binds device to BlazePwifi;
7. operator completes required special-access grants not silently provisionable by Android/OEM;
8. BlazeRental applies rental policy;
9. phone enters locked launcher state.

### 8.4 Manual-installed enrollment

For an already running phone:

1. install signed BlazeRental APK;
2. make BlazeRental default HOME;
3. enter on-device admin;
4. Scan BlazePwifi QR;
5. bind using one-time enrollment token;
6. apply all available policies.

This mode must remain clearly marked **lower security** because Device Owner cannot be assumed.

---

## 9. Policy model and synchronization

### 9.1 Policy authority

Each phone has one logical rental policy.

The policy can be edited from:

- on-device authenticated admin;
- BlazePwifi Admin.

The system must not maintain two unrelated allowlists.

### 9.2 Revision model

Each policy includes:

- `policy_revision` integer;
- `updated_at` server timestamp;
- `updated_by` source descriptor;
- signed policy payload.

Core fields:

- launcher mode: `rental` or `unrestricted`;
- allowed packages;
- hidden packages;
- sensitive packages forced hidden;
- preferred Vendo;
- overlay timer mode;
- customer overlay toggle allowed;
- quick-control allowlist;
- notification page enabled;
- admin gesture type;
- admin gesture parameter;
- phone admin verifier metadata;
- optional offline grace policy;
- workspace/theme settings that are safe to synchronize.

### 9.3 Conflict resolution

The BlazePwifi server is the source of truth for policy revisions.

On-device edits use a compare-and-set model:

1. phone submits current known revision plus requested change;
2. server accepts only if the revision matches;
3. server increments revision and returns canonical signed policy;
4. on stale revision, phone fetches latest policy and shows a conflict message rather than silently overwriting remote changes.

Server-admin changes increment the same revision.

### 9.4 Offline behavior

The phone caches the last valid signed policy.

If server is unreachable:

- current paid lease remains valid only according to existing server-synchronized monotonic lease logic;
- policy remains at last valid signed revision;
- no new unrestricted-mode activation is granted from a stale unauthenticated server response;
- on-device administrator may make local changes only if the device has an authenticated admin session; such edits are marked pending and must reconcile with compare-and-set when connectivity returns.

---

## 10. Rental time and coin flow

The existing server-authoritative model remains.

1. user presses Insert Coin;
2. BlazeRental sends authenticated `coin_start`;
3. BlazePwifi selects preferred/available Vendo;
4. temporary target nonce binds the coinslot to the phone;
5. ESP8266/ESP32/Linux controller accepts pulses;
6. controller reports signed coin event;
7. BlazePwifi idempotently credits the phone lease;
8. phone receives signed lease update;
9. launcher unlocks app drawer and allowed apps.

No phone-local action may mint rental time without a server-authorized lease update.

---

## 11. BlazePwifi rental server changes

### 11.1 State

Existing v0.3.0 rental files are preserved/migrated.

A v0.4.0 policy store may use TSV/JSON according to target tier, but Lite targets must remain safe for flash/RAM.

The server must support:

- device record;
- lease;
- app inventory;
- policy revision;
- allowed/hidden packages;
- launcher mode;
- Vendo preference;
- quick-control policy;
- notification policy;
- timer overlay policy;
- admin gesture metadata;
- admin password verifier metadata;
- last seen/sync;
- Device Owner/manual mode;
- build/version.

### 11.2 API actions

The rental API is extended to support authenticated actions equivalent to:

- enroll;
- status/sync;
- coin_start;
- policy_get;
- policy_patch with expected revision;
- inventory_update;
- device_capabilities;
- diagnostics summary.

Admin API is extended to support:

- rental_device_add;
- rental_device_qr;
- rental_device_list;
- rental_device_get;
- rental_policy_set;
- rental_policy_template_apply;
- rental_lease_add;
- rental_lease_expire;
- rental_device_rename;
- rental_device_revoke;
- rental_admin_password_set;
- rental_events;
- controller list/config as already supported.

### 11.3 Security

All device API changes must remain per-device authenticated.

Requirements:

- one-time enroll tokens;
- per-device secret;
- signed requests;
- signed policy responses;
- nonce/replay protection where state-changing;
- rate limits for enrollment/admin-sensitive actions;
- no permanent secret returned to browser UI;
- no phone admin password in logs;
- all portal/admin input validated and escaped.

---

## 12. BlazePwifi admin UI

### 12.1 UI framework

Use the free/open-source TailAdmin static Tailwind dashboard as the visual/system basis for Standard/Full targets.

Reference:

- project: TailAdmin free dashboard template;
- license: MIT;
- use a trimmed static build;
- do not ship unnecessary charts/libraries on constrained targets.

### 12.2 Capability tiers

**Lite**
- EW1200G Pro and similarly constrained OpenWrt hardware;
- compact static UI;
- no heavy charts;
- no large client frameworks;
- rental CRUD, QR, policies and controllers remain available.

**Standard**
- Orange Pi family;
- fuller TailAdmin layout;
- app inventory UI;
- QR modal;
- richer diagnostics/history.

**Full**
- x86_64;
- full management UX;
- larger history;
- richer diagnostics;
- device fleet views.

### 12.3 Rental Devices page

The page must include:

- Add Device button;
- QR enrollment modal;
- online/offline badge;
- paid/expired state;
- remaining lease;
- device label;
- Android build/mode;
- Device Owner/manual status;
- installed app inventory;
- app allow/hide switches;
- preferred Vendo;
- launcher mode;
- floating timer setting;
- notification/quick-control policy;
- phone admin password reset;
- add time;
- expire time;
- rename;
- revoke;
- last sync;
- policy revision;
- recent device events.

Package IDs may still be shown in technical detail, but operators should not be forced to edit comma-separated package IDs manually.

---

## 13. ESP8266 / ESP32 behavior

The v0.3.0 controller architecture remains compatible.

v0.4.0 must retain:

- protected setup AP;
- Wi-Fi verification before saving;
- fallback to setup after configured reconnect failures;
- server-managed runtime GPIO/polarity/debounce/retry policy;
- local verified configuration as fallback;
- pending coin event journal;
- stable idempotent retries;
- target-bound rental/hotspot coin events;
- configurable relay/LED/coin input.

Production release assets include:

- ESP8266 `.ino`;
- ESP8266 compiled `.bin`;
- ESP32 `.ino`;
- ESP32 application `.bin`;
- ESP32 merged factory `.bin`;
- checksums.

---

## 14. OpenWrt and hardware targets

### 14.1 Required release targets

v0.4.0 production requires successful build/validation for:

- Ruijie RG-EW1200G Pro v1.1;
- x86_64 BIOS;
- x86_64 UEFI;
- Orange Pi Zero 3;
- Orange Pi One;
- Orange Pi PC;
- ESP8266;
- ESP32;
- BlazeRental Android.

Additional Orange Pi targets may be published only when their corresponding build/image validation passes.

### 14.2 Orange Pi

Priority family:

1. Zero 3;
2. One;
3. PC;
4. PC Plus;
5. PC2;
6. Zero;
7. Zero2;
8. Zero 2W;
9. One Plus;
10. other supported Xunlong targets where the upstream OpenWrt release provides a usable image.

Do not claim onboard Wi-Fi functionality for boards where upstream support is incomplete.

### 14.3 x86

Publish:

- BIOS combined image;
- UEFI combined image;
- configured backup images after QEMU validation;
- optional ISO only if independently reproducible and tested.

NIC roles must remain detected/configurable rather than assuming `eth0`.

### 14.4 Ruijie

Publish:

- documented bootstrap/initramfs where required;
- BlazePwifi sysupgrade;
- matching configuration backup after simulation;
- checksums.

Do not embed mutable site state into a generic production sysupgrade solely to create the appearance of a full backup.

---

## 15. Backup strategy

Backups are generated only after the matching environment simulation passes.

### x86

Create:

- configured BIOS `.img.gz`;
- configured UEFI `.img.gz`.

The backup contains the simulated configured filesystem state and a `SIMULATION_OK` marker.

### Orange Pi

For each validated image:

- mount/execute target userspace under qemu-user where possible;
- write a simulation marker/config state;
- unmount cleanly;
- produce configured `.img.gz`.

These are image/userspace validated, not claimed as full board-peripheral emulation.

### Android

The primary distributable is the signed APK, not an emulator disk image.

For reproducibility, the simulation pipeline may retain an Android emulator userdata backup after successful Device Owner/UI validation.

### ESP

Publish compiled firmware binaries.

A "backup" binary is the exact validated factory/merged firmware image, not a fake runtime flash dump.

### Ruijie

Publish:

- production sysupgrade;
- configuration backup archive;
- audit metadata.

---

## 16. Environment simulation and production gates

### 16.1 Browser click-through

Use a headless browser against built/static BlazePwifi pages and mocked or live test APIs as appropriate.

Audit:

- login/logout;
- dashboard;
- rental device list;
- Add Device QR;
- app allow/hide controls;
- lease add/expire;
- phone admin password reset;
- controller configuration;
- portal builder;
- captive portal;
- Insert Coin;
- Done Inserting;
- Buy Time;
- voucher;
- pause/resume/end;
- relevant links;
- no console errors on required flows.

### 16.2 Android emulator

Install the signed production APK into a fresh Android emulator.

Required checks:

- Device Owner provisioning where emulator supports it;
- HOME registration;
- initial locked rental page;
- three fixed pages;
- swipe-up drawer blocked while expired;
- coin/lease simulation unlocks drawer;
- hidden/allowed app filtering;
- long-press workspace editing blocked in rental mode;
- admin secret gesture opens password challenge;
- wrong-password lockout;
- admin settings page;
- QR/manual binding flow;
- notification page behavior;
- floating timer behavior where overlay permission is available;
- reboot returns to correct state;
- lease expiry while another app is foregrounded returns to BlazeRental;
- Use Device As Is mode restores normal launcher behavior;
- returning to Rental Mode reapplies restrictions.

### 16.3 x86 QEMU

Boot both BIOS and UEFI images.

Verify:

- OpenWrt boot;
- BlazePwifi service starts;
- captive listener;
- admin HTTPS listener;
- Vendo API listener;
- config writes;
- admin login;
- portal page;
- rental API;
- shutdown/reboot persistence.

Only then create configured x86 backups.

### 16.4 Orange Pi

GitHub does not provide CPU/peripheral-accurate emulation for exact Orange Pi boards.

For each release image:

- inspect partition table;
- mount rootfs;
- verify BlazePwifi files/config;
- execute target userspace via qemu-user where architecture permits;
- validate basic busybox/shell/config execution;
- write simulation config marker;
- create configured image backup.

Label result accurately as **image/userspace validated**, not hardware-boot validated.

### 16.5 ESP

For ESP8266 and ESP32:

- compile;
- parse binary with esptool;
- run controller protocol/state tests;
- verify pending journal/retry semantics;
- verify server runtime configuration fields;
- verify setup fallback logic in source/unit state tests.

ESP32 may additionally use an available emulator where compatible.

ESP8266 must not be claimed CPU-emulated when the GitHub-hosted environment lacks a reliable compatible emulator.

### 16.6 Ruijie

Validate:

- firmware structure;
- target identity;
- squashfs/FIT/DT structure;
- BlazePwifi payload/config;
- configuration backup.

Physical MT7621 router boot remains a separate real-hardware validation step.

---

## 17. Release asset layout

Repository index:

`experiment/openwrt/BlazePwifi/releases/0.4.0/`

Simulation/backup index:

`experiment/openwrt/BlazePwifi/releases/0.4.0/images/`

GitHub Release assets should include successful applicable outputs such as:

- `BlazeRental.apk`;
- `BlazeRental-QR-Setup.html`;
- signing certificate/fingerprint;
- ESP8266 `.ino`;
- ESP8266 `.bin`;
- ESP32 `.ino`;
- ESP32 app/merged `.bin`;
- Ruijie sysupgrade `.bin`;
- Ruijie bootstrap/initramfs where applicable;
- Ruijie config backup `.tar.gz`;
- x86 BIOS `.img.gz`;
- x86 UEFI `.img.gz`;
- validated configured x86 backup `.img.gz`;
- Orange Pi per-board `.img.gz`;
- validated configured Orange Pi backup `.img.gz`;
- source `.tar.gz`;
- portal/admin static asset archive where useful;
- checksums;
- manifest;
- simulation report;
- optional emulator audit screenshots/reports.

Failed, placeholder or untested binaries must not be uploaded merely to satisfy a filename list.

---

## 18. Migration from v0.3.0

Upgrade sequence:

1. backup current BlazePwifi state;
2. install v0.4.0 server code;
3. migrate rental policy rows into revisioned policy representation;
4. keep existing device ID/secret/lease records;
5. existing v0.3.0 APK continues to receive compatible lease/status fields during transition;
6. upgrade phones individually to BlazeRental Launcher Edition;
7. after successful launcher enrollment/sync, mark device capability as v0.4 launcher;
8. only use v0.4-only policy fields for capable devices.

A server upgrade must not instantly invalidate all deployed v0.3.0 rental phones.

---

## 19. Security requirements

- no public repository secrets;
- no signing private key committed;
- no permanent enrollment credential in QR;
- no plaintext phone admin password at rest or in logs;
- server admin only on management network;
- CSRF on authenticated browser state changes;
- session cookies Secure/HttpOnly/SameSite where applicable;
- lockout/rate limiting for admin login and phone admin;
- device policy updates authenticated and revision-checked;
- lease remains server-authoritative;
- notification taps respect allowed package policy;
- quick controls cannot open unrestricted settings in Rental Mode;
- app drawer and launcher shortcut paths share the same allow/hide policy;
- no customer workspace-edit route may bypass policy;
- unrestricted mode requires authenticated administrator action.

---

## 20. UI quality requirements

### BlazeRental launcher

Must feel like an Android launcher, not a web page.

Requirements:

- smooth Launcher3 workspace gestures;
- real app icons/labels;
- real app drawer;
- clear rental state;
- minimal first-glance clutter;
- no giant endless list of full-width app buttons;
- fixed rental widget/page;
- modern dark/light visual treatment;
- readable on low-resolution phones;
- performant on older 2–4 GB Android devices, with reasonable behavior on lower-memory devices where Android version permits.

### On-device admin

Must look like a real management dashboard:

- TailAdmin-inspired visual system;
- grouped settings;
- cards and switches;
- app inventory with icons;
- no raw package-ID textbox as the primary control;
- status summaries;
- warnings for lower-security/manual install mode.

### BlazePwifi web admin

Standard/Full:

- TailAdmin-derived static management shell;
- mobile responsive;
- no mandatory external CDN at runtime;
- assets bundled locally;
- avoid large chart dependencies unless the page uses them.

Lite:

- same information architecture;
- reduced CSS/JS weight;
- no heavy visual dependencies.

---

## 21. Error handling

### Android

If server unavailable:

- keep last valid signed policy;
- do not invent paid time;
- show compact offline state;
- preserve current valid lease until monotonic expiry;
- lock when cached lease expires.

If enrollment QR invalid/expired:

- show explicit error;
- do not partially bind;
- allow scanning a new QR.

If notification permission absent:

- notification page shows setup-required state;
- rental enforcement continues.

If overlay permission absent:

- floating timer disabled;
- rental enforcement continues.

If Device Owner absent:

- show persistent lower-security status in admin;
- never claim full managed protections.

### Server

If stale policy revision:

- reject update with current revision/policy;
- client must rebase/retry explicitly.

If controller unavailable:

- Insert Coin reports no controller available;
- no fake time is granted.

If state write fails:

- fail closed on money/time-affecting operation;
- preserve previous state via atomic writes where supported.

---

## 22. Acceptance criteria

v0.4.0 is ready for production publication only when:

1. BlazeRental is a real Launcher3-derived HOME launcher.
2. Locked state blocks the app drawer.
3. Paid state opens the drawer and shows only allowed apps.
4. Lease expiry returns the user to BlazeRental and removes blocked apps from managed access.
5. The three fixed pages exist: Rental, Quick Controls, Notifications.
6. Customer workspace editing is disabled in Rental Mode.
7. On-device admin supports app allow/hide, binding, admin password, admin gesture, rental/unrestricted mode, diagnostics and relevant policy settings.
8. BlazePwifi Admin generates enrollment QR directly from Add Device.
9. On-device QR scanning binds without typing a token.
10. TailAdmin-derived BlazePwifi Rental Devices UI replaces raw package-ID management as the primary workflow.
11. ESP8266/ESP32 compiled firmware still passes controller and binary gates.
12. Ruijie production sysupgrade builds and structure/config audit passes.
13. x86 BIOS and UEFI images boot successfully under QEMU with BlazePwifi services active.
14. Orange Pi Zero 3, One and PC images pass image/userspace validation.
15. Signed BlazeRental APK installs and passes Android emulator UI/Device Owner tests.
16. Browser click-through audit passes required captive/admin interactions.
17. Configured backups are generated only after the related simulation passes.
18. GitHub Release contains compiled install-ready artifacts, not placeholders.
19. SHA-256 checksums and manifest match published assets.
20. Documentation clearly distinguishes build/simulation validation from physical-hardware validation.

---

## 23. Implementation order

1. preserve/reference upstream Launcher3 source and license;
2. create BlazeRentalLauncher project baseline from Launcher3;
3. modernize build toolchain only as much as necessary to compile reproducibly;
4. integrate existing lease/device-secret client;
5. implement revisioned rental policy model/server migration;
6. add three fixed launcher pages;
7. add paid/expired app-drawer gate;
8. implement app inventory allow/hide filtering;
9. integrate Device Owner/Lock Task enforcement into Launcher lifecycle;
10. add secret admin entry and native TailAdmin-inspired on-device admin;
11. add QR scanner/manual binding;
12. add notification listener/page;
13. add safe quick controls;
14. add floating timer;
15. add unrestricted mode;
16. build TailAdmin-derived BlazePwifi web admin;
17. add QR Add Device server/admin flow;
18. extend browser/API/security tests;
19. compile Android/ESP/router/SBC/x86 targets;
20. run Android emulator and browser click-through tests;
21. run x86 QEMU tests;
22. run Orange Pi image/userspace tests;
23. run ESP and Ruijie binary/image tests;
24. create configured backups only from passed environments;
25. publish v0.4.0 assets and checksums;
26. final repository/release audit.

---

## 24. Production truthfulness

This release must use precise validation language.

Allowed claims after successful CI:

- compiled;
- installable;
- signed;
- browser click-tested;
- Android emulator Device Owner validated;
- x86 BIOS/UEFI QEMU boot validated;
- Orange Pi image/userspace validated;
- ESP binary/protocol validated;
- Ruijie firmware structure/config validated.

Do not claim:

- physically field-proven on a board that was not physically tested;
- impossible to factory reset;
- impossible to bypass under bootloader/recovery compromise;
- exact board-peripheral emulation where no accurate emulator exists.

The objective is a real production software release with honest validation boundaries, not a theoretical prototype and not inflated claims.
