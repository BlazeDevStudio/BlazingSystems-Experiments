# Upstream component release metadata — research evidence, 2026-10-19

This is an offline snapshot of exact release asset size and SHA-256 fields observed in Acidanthera's official GitHub Release APIs, together with version-pinned LICENSE.txt Git blob identities. It is **not** a supplier-signed manifest, independent publisher identity verification or permission to redistribute every binary inside a release archive.

The checked candidates are OpenCorePkg 1.0.8, Lilu 1.7.2, VirtualSMC 1.3.8, WhateverGreen 1.7.1 and AppleALC 1.9.8. HfsPlus.efi is explicitly excluded pending provenance and redistribution clearance. GitHub asset metadata can support reproducible local SHA-256 checks, but no real third-party signing key has been authenticated out of band.

Command (from experiments/BlazeHackintosh):

    python component_provenance.py --manifest docs/UPSTREAM-ASSET-METADATA-20261019.json

Check an operator-provided local ZIP, without extraction or execution:

    python component_provenance.py --manifest docs/UPSTREAM-ASSET-METADATA-20261019.json --repository OpenCorePkg --archive /path/to/OpenCore-1.0.8-RELEASE.zip

The offline inspector rejects duplicate JSON keys, NaN, extra/unexpected schema fields, forged identity/license clearance claims, malformed URLs/digests/size limits, and unsafe ZIP member structures by delegating ZIP scanning to archive_integrity.py. A passed check is never sufficient to set component-auth_gate_satisfied to true.

For independently authenticated provenance, obtain trust anchors through an out-of-band publisher-controlled channel and inspect actual archive contents and licenses. No macOS, kext, driver or boot image is redistributed by this research manifest.
