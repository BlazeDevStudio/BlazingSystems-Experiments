# EasyMode v7.0.0 - Traffic Intelligence Edition

**Validation candidate. Publication follows successful integration checks.**

EasyMode Traffic Intelligence adds real WAN, WiFi, device, domain and inferred-service monitoring to the existing router management interface. One shared ucode backend and lightweight JavaScript dashboard serve all six editions. No React, Bootstrap, Node or Python runtime is installed on routers.

Open `/traffic/` on the router and sign in with OpenWrt administrator credentials. Existing EasyMode SMS, cellular, repeater, WiFi, LED and access controls remain in their installed management page; Advanced opens LuCI. Installation adds a link to recognized existing EasyMode pages without replacing their code.

## Install and build

- [Installation, privacy and measurement guide](traffic/README.md)
- [Compatibility and limitations](COMPATIBILITY.md)
- [Actual test results](traffic/TEST-REPORT.md)
- [Current handover](HANDOVER-v7.md)
- [GitHub build workflow](../../../.github/workflows/easymode-v7.yml)

Run `python3 traffic/tools/build.py` to construct deterministic architecture-independent IPKs and one offline archive per edition. `sh traffic/tests/run.sh` runs accounting, UI-model and payload checks. `sh traffic/tools/image.sh` uses the pinned official OpenWrt 24.10.8 x86/64 ImageBuilder. GitHub Actions builds and boots disposable BIOS/UEFI images, installs the actual packages and tests the authenticated dashboard.

The supported package runtime is OpenWrt 24.10, with exact integration verification on 24.10.8. APK-only systems and Chaos Calmer are not supported by these IPKs. Offline archives require matching runtime dependencies already installed; they are not universal firmware.

## What the shared module does

Eight views: Overview, WiFi, Internet Data, Devices, Websites, Apps, Reports and Settings. WAN accounting deduplicates IPv4/IPv6 logical interfaces and keeps local wireless activity separate. Device counters use optional bounded forwarding observations. Domain logging is off by default, with explicit administrator consent and user notice. Domain/app traffic is estimated only from recent matching observations; ambiguous, encrypted or invisible traffic stays unknown. Historical files are private, retained within configured bounds and checkpointed in batches.

## Editions

| Edition | Observable scope |
|---|---|
| Generic | Lightweight common collector, detected interfaces and optional detailed accounting |
| AP | Wireless clients and visible link traffic; no invented upstream consumption |
| Router | WAN, WiFi, device accounting and optional domain/service estimates |
| Cellular | Router measurements for the cellular L3 upstream; existing modem controls preserved |
| Switch | Visible interfaces and clients; bridged hardware traffic may be invisible |
| PC | Shared monitoring with configurable capacity; official x86/64 BIOS and UEFI build paths |

## Preserved history

The latest established R281 management source remains [4.2.6 consolidated](releases/v4.2.6-r281-consolidated/). It is the functional baseline, not a universal flash image. Earlier release directories are immutable history. The old 5.0 alpha toolkit was scaffolding; current installers now point to the v7 package process. Version numbers do not rank the completeness of historical branches.

No physical device is automatically flashed. Private passwords, SMS, live browsing metadata and personal recovery images are excluded from public artifacts.
