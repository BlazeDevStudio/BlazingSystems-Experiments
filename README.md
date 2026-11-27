<div align="center">

# BlazingSystems — Experiments

**Compatibility research, alpha systems, clean-room reconstructions and proof-of-concept engineering**

[Profile](https://github.com/BlazingSystems) ·
[Projects](https://github.com/BlazingSystems/BlazingSystems-Projects) ·
[Labs](https://github.com/BlazingSystems/BlazingSystems-Labs) ·
[Archives](https://github.com/BlazingSystems/BlazingSystems-Archives)

</div>

---

## Experiment Portfolio

| Area | Project | Stage | Entry |
|---|---|---|---|
| [OpenWrt](experiment/openwrt/) | BlazePwifi | 0.1.0-alpha.1 reconstruction | [Project](experiment/openwrt/BlazePwifi/) |
| [OpenWrt](experiment/openwrt/) | EasyMode for OpenWrt | 5.0.0-alpha.1 | [Project](experiment/openwrt/easymode-project/) |
| [Web runtime](web/) | BlazeAPK | Beta 0.6 | [Project](web/blazeapk/) |
| [Web runtime](web/) | BlazeJ2ME | v1.6 | [Project](web/blazej2me/) |
| [Android](android/) | TokenLauncher | Security/device-control prototype | [Project](android/token-launcher/) |
| [Embedded](embedded/) | ESPHole version history | v1.3.0 latest numbered experiment | [Project](embedded/esphole/) |
| [Embedded](embedded/) | ESP8266 Arcade public shell | Recovered-design derivative | [Project](embedded/esp8266-arcade-public/) |
| [Embedded](embedded/) | AP LED Controller | Prototype | [Project](embedded/esp8266-ap-led-controller/) |
| [Embedded](embedded/) | Relay Controller | Prototype | [Project](embedded/esp8266-relay-controller/) |

## Repository Layout

- **[experiment/](experiment/)** — larger system experiments, currently focused on OpenWrt
- **[embedded/](embedded/)** — ESP8266 firmware prototypes and versioned experiments
- **[android/](android/)** — Android + embedded integration prototypes
- **[web/](web/)** — browser runtime and compatibility research
- **[.github/workflows/](.github/workflows/)** — automated build/static-check workflows

## Research Standard

Experimental means the limitation is part of the documentation. A project should state what was tested, what remains uncertain, what hardware/platform it targets, and what evidence is required before promotion.

Versioned release snapshots are preserved rather than silently overwritten. Clean-room projects do not redistribute proprietary source, credentials, certificates or commercial payloads from systems they study.

## Publication Policy

Public experiments exclude employer/client records, private keys, production credentials, raw private backups, commercial ROM/APK/JAR payloads and proprietary operational datasets.

See [NOTICE.md](NOTICE.md) for repository-wide publication notes.
