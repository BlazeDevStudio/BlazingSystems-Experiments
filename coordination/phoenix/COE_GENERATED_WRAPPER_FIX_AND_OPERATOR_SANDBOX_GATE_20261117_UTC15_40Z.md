# COE generated-wrapper fix and operator sandbox boundary recheck

**Role:** PHX-MASTER — coordination, architecture contract and integration gate only  
**Checkpoint:** 2026-11-17 UTC15 (live re-read around 15:40Z)  
**Source repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Destination repository:** `BlazeDevStudio/CoinOperatedEcosystem`  
**Master branch / exact head:** `phoenix/master-coordination@86b91edd2864d796487a9da56a8267ae44ca771c`  
**COE integration:** #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` (open/draft)  
**COE RELEASE:** #31 `06d8b7c593f8e139891a6a659bf79e694ee229d5` (open/draft; based on #26)

## 1. Live refs and governing inputs

- Experiments default `main`: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments development `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- `blazepwifi-v0.6.0-audit-foundation`: `2fbd2475e9f54878c316fa7cea2f228386b0e859`, comparison-only.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`; the root tree contains `README.md` and `Pisonet/`, with no root `AGENTS.md`.
- Master #288: open/draft, base main `f4e8a891...`, head `86b91edd...`; no PR-triggered runs returned.
- `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`; PHX-MASTER target remains null; broad Rental parent remains non-copyable.
- Governing #172 and cleanup-first #266 were reread. The uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`, latest Library `README_FIRST`, and `COMMUNICATION_PROTOCOL` were read. Experiments root `AGENTS.md` was read. The COE main tree has no root AGENTS.md.

## 2. Previous generated-shell defect: source correction present, CI pending

At prior COE #31 head `d45b84c67dc587fca6226662cb1d8bc59bdb11ae`, the generated shell template embedded literal backslash-n text. A minimal reproduction had `sh -n=0` but runtime exit 2 (`Syntax error: Bad fd number`). The release owner responded on the existing branch:

1. Test-first [293a006d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/293a006d6809493ba164f10d1e2917e8979e1633).
2. Source correction [b14841e7](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b14841e75d57144f8c72867ef54fdff796b9483d).
3. Current narrow handover [06d8b7c5](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/06d8b7c593f8e139891a6a659bf79e694ee229d5).

Exact current blobs:
- `tools/package_appliance_firmware.py`: `66fc283eb52add75caee6131b78dcadbb5d8a7fc`.
- `tools/test_package_appliance_firmware.py`: `3e917c30654ce629391c3fbd864d5b671b0a2e46`.
- `tools/run_imagebuilder_sandbox.py`: `f20267d26185238bc82bcaccebf857fee67d929a`.
- `.github/workflows/release-imagebuilder-sandbox.yml`: `151c052f36664c1cb70138e7f135a5570909e09e`.
- `tools/RELEASE_PACKAGER_HANDOVER.md`: `31d887d0ab1cf35bf08c84a558373b3fbac6e416`.

The generated template now contains real line breaks around the empty-image guard. The test source contains `test_generated_wrapper_emits_empty_image_guard_as_real_shell_lines`. The prior literal-newline defect is **corrected in source**, but do not call it CI-verified until the exact final-head sandbox run completes.

## 3. Exact-head CI

| Run | Current result | What it proves |
|---|---|---|
| [#44113058229](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058229), job `134155724688` | IN_PROGRESS | Final-head sandbox regression not yet concluded |
| [#44113058271](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058271) | SUCCESS | Shared contracts and ESP8266/ESP32 builds only |
| [#44113058276](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058276) | SUCCESS | Case-collision guard only |

No conclusion is inferred from an in-progress job. COE #26's five workflows remain QUEUED with zero jobs returned.

## 4. Separate P0: test harness is sandboxed; generated operator build is not

Source inspection of the exact #31 head confirms:

- `generate_build_script()` emits a shell wrapper that changes into `$BUILD_DIR` and invokes `{cmd}` directly.
- The generated wrapper contains no `run_imagebuilder_sandbox.py` or bubblewrap invocation.
- The test harness invokes the runner only when `PHX_REQUIRE_BWRAP=1`; the dedicated workflow sets that flag.
- Therefore the CI harness's sandbox attempt does not establish that an operator who runs the generated build script gets the same boundary.
- The runner uses `--share-net`; network isolation is not configured or claimed. Its read-only root is a write boundary, not a confidentiality boundary.

**Required owner action:** PHX-RELEASE must either make the supported generated/operator entrypoint invoke the sandbox fail-closed, or define a mandatory external isolated build-host boundary and prove that exact invocation. PHX-QA independently verifies the supported path on the exact final SHA. PHX-MASTER does not edit RELEASE implementation.

## 5. Separate P0: ULA remains invalid

The exact current packager still emits `fd00:db8:blaze::/48`; `blaze` is not a hexadecimal hextet. The exact packaging test blob contains no ULA parser assertions. Preserve Architecture Contract §6.9: a ULA /48 is installation/site identity, not a shared router-profile property. Require a valid locally assigned RFC 4193 /48, durable across reboot/upgrade/restore, shared by devices on the same LAN and distinct across independent sites. Do not invent a fixed replacement.

**Owner action:** PHX-RELEASE owns implementation/tests; PHX-CORE and COE owner define provisioning; PHX-QA independently verifies; PHX-HARDWARE validates only after correction and authorization.

## 6. Bounded validation and limitations

**13/13 static source/manifest assertions passed** against the exact blobs listed above. They checked the generated template's real multiline guard, direct operator invocation, absence of runner invocation in the generated wrapper, test-harness runner references, workflow flag, shared-network setting, invalid ULA, missing ULA test coverage, and routing-manifest invariants.

This is static source inspection—not the COE Python packaging suite, Master Python suite, OpenWrt UCI/netifd execution, or physical acceptance. A local Git clone failed because DNS could not resolve GitHub. The final sandbox CI job is still running. No physical hardware or payment system was touched.

## 7. Role and migration disposition

- PHX-MASTER #288: `86b91edd...`, no PR-triggered run.
- PHX-CORE #252: `c82705f2...`, scoped run 42698139210 SUCCESS; CORE source remains separately owned.
- PHX-RENTAL #240/#287/#289: scoped exact-head runs SUCCESS.
- PHX-PISONET #255: scoped run 42462978704 SUCCESS; native COM acceptance unverified.
- PHX-HARDWARE #317: focused quarantine and relay-polarity runs SUCCESS; Full run 44097182945 FAILURE at the inherited positive poll-signature fixture. Preserve default-deny; QA owns fixture correction.
- PHX-QA #279/#292: no PR-triggered runs returned; #290 scoped SUCCESS.
- PHX-RELEASE #242/#291: scoped SUCCESS; signing/publishing remain closed.
- COE #26 remains draft; #31 is a separate child candidate, not merged or accepted into #26.

No source blobs were copied, moved, overwritten or deleted. No license or import-completeness approval was inferred. `OWNERSHIP_ROUTES.json` remains review-only.

## 8. Private registry and release gate

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed Library/connector surface; only older snapshots were visible. No Google Drive file connector was exposed, no older registry was substituted, and no private identifiers or contents were published.

**PRODUCTION NO-GO** remains mandatory pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates. No merge, release, secret provisioning, flashing, physical testing or live financial migration occurred.
