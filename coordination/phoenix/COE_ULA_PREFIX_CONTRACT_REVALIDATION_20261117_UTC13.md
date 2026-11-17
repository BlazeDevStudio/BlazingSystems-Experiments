# PHX-MASTER — COE ULA prefix contract revalidation

**Checkpoint:** 2026-11-17 UTC13  
**Disposition:** P0 integration blocker / COE drafts remain open / PRODUCTION NO-GO  
**Scope:** PHX-MASTER coordination only; no subsystem source or destination runtime changes

## Exact live refs re-read

- Experiments default `main`: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments development `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Experiments comparison-only `blazepwifi-v0.6.0-audit-foundation`: `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Master branch and existing PR #288 before this update: `5d5ca7a04b81abe3e2771c7ba0f4e0ff135164db`, base `main@f4e8a891...`.
- COE default `main`: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, open/draft.
- COE release child #31: `b29d69a4cd97ca93babbab436bcc00b1e9d8280d`, open/draft, based on #26.

## Exact blob revalidation

| Artifact | #26 / shared candidate | Current #31 / source | Finding |
|---|---|---|---|
| `tools/package_appliance_firmware.py` | `c6ad3807d7fedb00ab7560813b82810cb8cce751` | `fd558928b2869ce1f4b2cb2776b405b4b723b310` | Both emit the same invalid hard-coded `fd00:db8:blaze::/48` once |
| `tools/test_package_appliance_firmware.py` | `8f6b2f849152902c341428067e52fe95f6763b93` | `c183ceaad0c470ee06db9a9c68993844553efc3c` | Neither has ULA/IPv6 parser assertions |
| Shared router-profile schema | `ddc5d2ebad868c99908747c75961b45b8c0edced` | Same #26 profile contract | No `networking.ula_prefix` property |
| EW1200G Pro profile | `6e797cf9c9922209efe4c0da49c49fa1da16c11a` | Same #26 profile blob | No ULA prefix field |

The current #31 packager adds interface/VLAN validation and other staging hardening, but it still emits the invalid literal. The test file has 57 packaging tests, yet no ULA test; the profile suite checks ten profiles without ULA semantics.

## Tests and CI actually observed

**Local parser check executed** with Python `ipaddress.ip_network(..., strict=True)` against the exact emitted literal and controls:

- `fd00:db8:blaze::/48`: rejected (non-hexadecimal hextet).
- `fd12:3456:789a::/48`: accepted as a canonical locally assigned ULA /48 control.
- `fc12:3456:789a::/48`: syntactically IPv6 but outside this contract's locally assigned `fd00::/8` range.
- `2001:db8::/48`: syntactically IPv6 but not ULA.
- `fd12:3456:789a::/64`: ULA address space but wrong /48 length.

This is a Python parser check, not OpenWrt UCI/netifd, ImageBuilder or target-router validation.

Current COE #31 exact-head Actions:
- [44084015060](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44084015060) SUCCESS: packaging/tool tests **57/57**, shared contracts **18/18**, appliance profiles **10/10**, ESP32 and ESP8266 compile jobs SUCCESS.
- [44084014924](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44084014924) SUCCESS: case-collision guard.
- The 57 packaging tests and 10 profile checks do not assert ULA validity, so these green results do not close this blocker.

COE #26 exact-head workflows remain five QUEUED: 43096752609, 43096752632, 43096752800, 43096752563, 43096752557. No combined integration acceptance is established.

## Architecture decision — ULA is installation identity, not hardware profile

The shared router profile describes model capabilities and interface topology. It is reused across independent installations and must **not** carry one static site ULA. Do not add `networking.ula_prefix` to the shared hardware-profile schema as the default correction.

A generic appliance image must not bake one global ULA placeholder. The installation/first-boot authority must create a locally assigned RFC 4193 ULA /48 for that installation, persist it durably and reuse it across reboot, upgrade and restore. Devices belonging to the same LAN/site share that prefix; independent sites receive independently generated prefixes. The generated value must be canonical, strictly parsed, in `fd00::/8`, and exactly `/48`.

The implementation owner must choose and verify one target-supported provisioning mechanism before packager changes are accepted:
1. A target first-boot path generates and atomically persists the prefix before network services consume it; or
2. A deployment-specific build input supplies a validated site prefix when the artifact is intentionally unique to that site.

Do not silently fall back to a fixed example, regenerate on every boot/build, or assume netifd supplies a valid prefix without target evidence. If neither approved path exists, the integration remains blocked.

## Current role / CI handover

| Role / candidate | Exact head | Exact-head evidence |
|---|---|---|
| PHX-MASTER #288 | `5d5ca7a04b81abe3e2771c7ba0f4e0ff135164db` | No PR-triggered runs returned |
| PHX-CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | 42698139210 SUCCESS, scoped; separate CORE automation retains implementation |
| PHX-RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | 43653329235 and 43653329229 SUCCESS, scoped |
| PHX-PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | 42462978704 SUCCESS, scoped |
| PHX-HARDWARE #317 | `d6184c097561dd800b09bc7ab3b8739e79000ce9` | Full 44087267104 FAILURE at validate job 134052853915; focused 44087267150 and 44087267306 SUCCESS |
| PHX-HARDWARE separate #316 | `888e6941e3a7a81641682c23d937f97d8117d2ea` | Focused 43972511337 SUCCESS; Full 43972511250 FAILURE |
| PHX-QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 run 43633486963 SUCCESS; #292 no PR-triggered runs returned |
| PHX-RELEASE #291 | `2c4edff231d9b2819415086825530d80b8801307` | 43744993487 SUCCESS, scoped |
| COE #26 / #28 / #29 / #30 / #31 / #32 | `b382d233...` / `b21b0461...` / `d0830332...` / `4897348d...` / `b29d69a4...` / `29b6fe08...` | #26 five QUEUED; #28/#29/#30/#31/#32 scoped SUCCESS; none proves combined #26 acceptance |

HARDWARE #317's Full failure is independent of the ULA issue: the validation script still expects a positive poll signature, while current firmware intentionally denies poll admission pending the canonical CORE contract. Preserve default-deny; PHX-QA owns its fixture correction.

## Owner actions and boundaries

- **PHX-RELEASE:** implement the approved installation-scoped provisioning/packager contract on its own existing branch; add ULA positive/negative and no-write-on-invalid tests.
- **COE integration owner:** keep #26 draft and record exact profile/packager/test provenance; do not treat #31 as closing #26.
- **PHX-QA:** independently validate the exact final packager output and target-compatible UCI parsing.
- **PHX-HARDWARE:** target-specific OpenWrt validation only after corrected exact-head source and owner authorization.
- **PHX-MASTER:** architecture, integration matrix, provenance and release gate only. No RELEASE/HARDWARE/QA source edits.

## Registry and production gate

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not accessible: the exposed tool set has no Google Drive file connector, and the Library contains older snapshots only. The Cloud Artifact Policy and Storage Handover were read; both require the owner-private registry/ledger before mirror operations. No older registry was substituted and no private Drive content or identifiers were published.

No migration/copy, code change in a subsystem branch, merge, release, signing, flashing, secret provisioning, payment operation or physical test occurred. The full Master Python suite was not run.

**PRODUCTION NO-GO** remains mandatory pending protected signing/anti-rollback witness, crash-atomic financial state, reversible migration, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.
