# Sources ledger (checked 2026-10-18)

| ID | Authority / source | Used for | Version / caution |
| --- | --- | --- | --- |
| OPENCORE | https://github.com/acidanthera/OpenCorePkg/releases/tag/1.0.8 | 2026-09-27 release baseline | Latest at research checkpoint; use matching Sample.plist/ocvalidate |
| DORTANIA | https://github.com/dortania/OpenCore-Install-Guide | OpenCore architecture guidance | Front-page documented version still 1.0.6; reconcile drift |
| LIMITS | https://dortania.github.io/OpenCore-Install-Guide/macos-limits.html | CPU/GPU limitations | Not proof of exact-system boot |
| HASWELL | https://dortania.github.io/OpenCore-Install-Guide/config.plist/haswell.html | Intel Haswell primer | Check each macOS GPU boundary |
| SKYLAKE | https://dortania.github.io/OpenCore-Install-Guide/config.plist/skylake.html | Intel Skylake primer | Hardware-specific SSDTs needed |
| COFFEE | https://dortania.github.io/OpenCore-Install-Guide/config.plist/coffee-lake.html | Intel Coffee Lake primer | Hardware-specific configuration |
| AMD | https://github.com/AMD-OSX/AMD_Vanilla | AMD kernel-patch conditions | Version-dependent physical core count |
| APPLE | https://www.apple.com/legal/sla/ | macOS licensing | Version-specific license governs use |
| ICON | https://lucide.dev/license | icon reuse | ISC notice required |

Confidence scope: verified repository documentation and upstream release metadata, **not** independent boot testing.
All entries are subject to later upstream revision.
