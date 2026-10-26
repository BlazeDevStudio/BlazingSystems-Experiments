# EasyMode R281 10.2.0 and Traffic Intelligence 7.0.2

**Public R281 candidate and six Traffic edition archives are published.** The R281 application and Cellular Traffic edition are running on one physical R281; the public firmware has passed its exact-device compatibility test but has not been flashed or boot-tested.

The EasyMode application currently installed on the R281 is [EasyMode 10.2.0 — R281 app profile](releases/v10.2.0-r281-candidate/). Its installer intentionally refuses other board profiles. Generic OpenWrt installs use the shared Traffic Intelligence monitor below; the six Traffic editions are **not** six full EasyMode management firmware variants. Full R281 management parity on other boards is not claimed.

For the current release, use the [R281 handoff](releases/v10.2.0-r281-candidate/HANDOFF.md), [public candidate assets](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/easymode-r281-v10.2.0-5b1e4ab15bf2) and [feature reconciliation](releases/v10.2.0-r281-candidate/FEATURE-GAP.md). A credential-free R281 firmware candidate is published; the device-specific reset-persistent image is held separately because it includes router identities. Neither image has been flashed.

EasyMode Traffic Intelligence adds real WAN, WiFi, device, domain and inferred-service monitoring to the existing router management interface. One shared ucode backend and lightweight JavaScript dashboard serve all six editions. No React, Bootstrap, Node or Python runtime is installed on routers.

Open `/traffic/` on the router and sign in with OpenWrt administrator credentials. Existing EasyMode SMS, cellular, repeater, WiFi, LED and access controls remain in their installed management page; Advanced opens LuCI. Installation adds a link to recognized existing EasyMode pages without replacing their code.

## Install and build

- [Installation, privacy and measurement guide](traffic/README.md)
- [Compatibility and limitations](COMPATIBILITY.md)
- [Actual test results](traffic/TEST-REPORT.md)
- [Current handover](HANDOVER-v7.md)
- [GitHub build workflow](../../../.github/workflows/easymode-v7.yml)

Run `python3 traffic/tools/build.py` to construct deterministic architecture-independent IPKs and one offline archive per edition. `sh traffic/tests/run.sh` runs accounting, UI-model and payload checks. `sh traffic/tools/image.sh` uses the pinned official OpenWrt 24.10.8 x86/64 ImageBuilder. GitHub Actions builds disposable BIOS/UEFI images and exercises an integration test; current check results should be read before calling that VM gate passed. A separate workflow builds and publishes the credential-free R281 candidate on relevant source changes.

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

The established R281 management source is preserved at [4.2.6 consolidated](releases/v4.2.6-r281-consolidated/); the installed, updated copy is [v10.2.0](releases/v10.2.0-r281-candidate/). It is board-specific. Earlier release directories are history. The old 5.0 alpha toolkit was scaffolding; the shared Traffic Intelligence packages are separately versioned as v7.0.2. Version numbers do not rank the completeness of historical branches.

No physical device is automatically flashed. Private passwords, SMS, live browsing metadata and personal recovery images are excluded from public artifacts.
