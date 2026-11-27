# PHX-MASTER UTC10 — RELEASE #291 supersession, ULA contract, and sandbox reconciliation

**Updated:** 2026-11-19T10:27:50Z  
**Role:** PHX-MASTER — coordination/phoenix only  
**Task:** #172 / #266 / #288 / COE #26 / COE #31/#35 / HARDWARE #327 / RELEASE #291  
**Disposition:** Master docs review-ready · COE migration BLOCKED · PRODUCTION NO-GO

## 1. Live identities

| Item | Exact ref |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Current development | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master before this follow-up | `phoenix/master-coordination@79a9cbbfba3a0e6e8ad682265bd1b5060030a86b` |
| Master PR #288 | OPEN/DRAFT, 100 paths before this follow-up, all under `coordination/phoenix/`; no Actions run |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE #26 | OPEN/DRAFT `b382d233ff06c8791b1028bed3c617cc7b670d12`, 205 files; five workflows QUEUED / zero jobs |

Ownership manifest remains `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null.

## 2. RELEASE #291 — corrected current-head evidence

Current PR #291 is OPEN/DRAFT at docs/handover head `44a2020c52af6beeaa5e6aedf089f8b03a416ed1`; exact source/test head is parent `ffe4ea8f5eabe23628827e186ebb3f92c9cfcaaf`.

- Exact source/test push [#44503860587](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503860587) is terminal **SUCCESS**. Job readback shows provenance tests, validation, ESP32, ESP8266, Android, 11 OpenWrt target jobs, update bundle and nine v0.4 simulations successful. Production import, sign handoff and publishers were skipped.
- The PHX-RELEASE checkpoint reports 19/19 provenance tests and 133/133 validation steps PASS. ESP8266 artifact [14518906459](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503860587/artifacts/14518906459), ESP32 [14518526948](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503860587/artifacts/14518526948), and Ruijie [14519345289](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503860587/artifacts/14519345289) ZIP readback/checksum verification passed. They remain unsigned `CI_PREVIEW_ONLY` artifacts with `production_authorized=false`.
- Docs-head push [#44504554013](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44504554013) and PR build [#44504561884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44504561884) are terminal SUCCESS; signing and publishing remained skipped.
- Windows docs-head [#44504561855](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44504561855) fails in `build-windows` job `135492741597`; PISONET-owned `negative-selftest.ps1` reads an uninitialized `$buildWorkflow`. Handover passed; publisher skipped.
- ESP32 compatibility [#44504553980](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44504553980) passed both 3.3.13 and 4.0.0, but pins older Hardware source `0e5514adb008`, not current #327 head `47eceaf2ccd3cfdc3403df6b1964610bd32ed24f`.

The earlier UTC10 Master note recorded a then-cancelled run; final role checkpoint #7006125314 and terminal readback supersede it. Master changed no Release or PISONET files.

## 3. New P0 — COE #35 emits invalid IPv6 ULA

At COE Release #35 head `5047af8b5a8296e06294bbda6bf42a6baea2294d`:
- `tools/package_appliance_firmware.py` blob `f1d9c8ef1da7e1d3df11f45dfe36f14f5f11a650`, line 162, emits `option ula_prefix 'fd00:db8:blaze::/48'`.
- `tools/test_package_appliance_firmware.py` blob `e3f625673bd90bb28e107a88aff9ed4d824a2bb7` tests bridge/VLAN output and formatting but has no ULA/IPv6 validation.
- Independent Python `ipaddress.IPv6Network("fd00:db8:blaze::/48", strict=False)` raises `AddressValueError: Only hex digits permitted in 'blaze'`.

### Master interface contract added

Architecture Contracts §6.45 now requires a valid RFC 4193 ULA in `fd00::/8`, a 40-bit Global ID and `/48` length; one stable prefix shared by all appliances at one site; independent Global IDs across sites; persistence through reboot/upgrade/migration/backup/restore; and fail-closed packager validation. Per-device random prefixes and fixed product literals are not acceptable.

**No prefix or provisioning authority was selected.** PHX-CORE and the COE integration owner must choose owner-provisioned site prefix or a first-boot site authority that creates/distributes one durable identity. PHX-RELEASE implements only after that decision; PHX-QA independently verifies. Master did not modify COE #35 source or networking configuration.

## 4. Sandbox runner blockers are distinct

- COE #31 sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263), job `134527611774`: Bubblewrap 0.9.0 exists, but the unprivileged namespace probe fails because setting up the UID map returns `Permission denied` (exit 125).
- COE #35 sandbox [#44465377807](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465377807), job `135361788287`: 14/14 host-preflight tests pass, but Bubblewrap is not installed; the job exits 125 before packaging.

Neither permits privileged namespace setup, privilege escalation or unsandboxed fallback. PHX-INFRA/RELEASE must provide an authorized runner satisfying the approved boundary.

## 5. Other blockers retained

- HARDWARE #327 remains at `47eceaf2ccd3cfdc3403df6b1964610bd32ed24f`: focused quarantine #44501072485 and relay/output #44501072498 PASS; Full #44501072563 fails at QA-owned `Missing poll signature check`. Firmware poll admission and coin disposition remain deny-only.
- COE #26 remains five queued workflows / zero jobs. Exact source/destination sketches differ; 21 source board-local Python labs are not represented by the single destination Hardware shell test; Hardware license/NOTICE scope is incomplete.
- Branch objects for Experiments main, development, Master and COE main report `protected=false`; both rulesets endpoints return empty arrays.
- Private Drive registry v11 and newer corrections remain unavailable through current Library/connector surfaces; no older snapshot substituted.
- Master PR #288 has no Actions run. The full Master Python suite was NOT RUN; local source/configuration assertions only.

## 6. Owner actions

1. PHX-CORE and COE integration owner: decide the site-scoped RFC 4193 ULA provisioning authority and durable sharing/restoration semantics.
2. PHX-RELEASE: after the owner decision, replace the invalid placeholder with validated site configuration; keep #35 sandbox blocked until an approved runner exists.
3. PHX-QA: verify ULA syntax, same-site sharing, distinct-site separation and persistence/restore; continue #327 deny-only fixture correction.
4. PHX-PISONET: bind/read `$buildWorkflow` in its own negative self-test and rerun exact-head Windows CI.
5. PHX-INFRA: provide an authorized runner for UID-map and missing-bwrap constraints without privileged or unsandboxed fallback.
6. COE integration owner: keep #26 blocked until exact per-file provenance, licenses, tests, toolchain pins and executable CI exist.

**No migration, merge, release, signing, flashing, secret provisioning, real payment operation or financial cutover occurred.** Physical acceptance, 150 real power cuts and 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO.**
