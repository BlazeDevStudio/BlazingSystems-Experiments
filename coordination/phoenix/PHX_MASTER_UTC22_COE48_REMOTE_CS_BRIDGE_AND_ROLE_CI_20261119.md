# PHX-MASTER UTC22 — COE #48 Remote CS bridge boundary and live role CI

**Observed:** 2026-11-19T22:40Z  
**Role:** PHX-MASTER · coordination-only  
**Repository/branch:** `BlazeDevStudio/BlazingSystems-Experiments` / `phoenix/master-coordination`  
**Pre-change HEAD:** `9bff8bb8b47783d860be3725c139b58a576c7333`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Scope:** `coordination/phoenix/**`, architecture/interface contracts, exact-head integration matrix and migration provenance only  
**Codex:** NOT USED

## 1. Live refs and control-plane state

| Ref | Exact SHA / state |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Generic `development` branch | 404 — does not exist |
| v0.6.0 audit-foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| v0.5.3 development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master coordination | `9bff8bb8b47783d860be3725c139b58a576c7333` before this report |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| COE #47 | `1c10f7421dfaa87fcb2ce89d4a8b2d22422d1597` |
| COE #48 | `b72ca86a141329b4b401f5d790cfb04a58423331` |

Issue #172 remains the [PHX control plane](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172); cleanup #266 remains OPEN. Issue #172 still has a v0.5.3/v0.6.0 development designation conflict. Both refs are recorded; Master did not promote or relabel either. Existing draft PR #288 was OPEN/DRAFT at the pre-change head. `OWNERSHIP_ROUTES.json` remains `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`.

## 2. COE #48 is a separate Hardware candidate, not a #26 migration

COE #48 is 15 commits ahead and 0 behind #47. Its 13 changed paths are confined to Hardware ESP8266 staging, its tests and the Stage 5 workflow:

- Existing INTERCON sketch, arm guard, discovery and peer-auth files modified.
- New `RemoteCsCodec.h`, `RemoteCsJournal.h`, `RemoteCsRuntime.h`.
- New `REMOTE_CS_BLAZEPWIFI_BRIDGE_CONTRACT.md` and `REMOTE_CS_PISOWIFI_STAGE5.md`.
- New C++ protocol test, Python source-contract test and diagnostic `remote_cs_client.py`.
- `.github/workflows/intercon-stage1-ci.yml` modified.

No `Pisowifi/` backend path is changed. The bridge contract is documentation, not an implementation. #48 is not listed in `OWNERSHIP_ROUTES.json`; Master did not add a route or silently assign the branch to a role.

## 3. Interface mismatch and required adapter

Stage 5 uses HMAC-SHA256 `BLZCS1` frames:

```
BLZCS1|KIND|SOURCE8|DEST8|COMMAND16|SESSION16|EVENT16|VALUE|HMAC64
```

The existing COE #26 backend uses `/cgi-bin/vendo` with `action/id/nonce/pulses/target/sig` and returns `insert/target_nonce/expires/controller/response_sig`. The contracts are not wire-compatible. Existing poll sets `insert=0` unless the controller is enabled and `coin_enabled=1`.

A real adapter must durably map device ID + BLZCS1 session to the existing vendo/customer/target nonce/expiry and denomination. The device's `EVNT` is a physical pulse receipt, not money or seconds. The router must commit exactly-once credit under `(device_id,event_id)` to the correct customer before matching `ACKN`. `ACKN` clears the ESP's pending event; it does not prove financial credit. Unknown timeout/replay outcomes require durable readback and reconciliation. The diagnostic CLI explicitly does not implement billing or automatic ACK.

## 4. Source-level safety limitations

- `RemoteCsJournal.h` uses two LittleFS slots with temporary write/readback/rename/readback, but its record checksum is CRC32. This detects accidental corruption; it is not a protected signing or anti-tamper witness.
- `remoteHardLocked` and `remoteJournalWriteFailed` are RAM flags. The boot arm guard requires AP-only physical reconciliation each boot, but a pulse lost before its first durable journal commit does not become a recoverable receipt.
- The Stage 5 document explicitly acknowledges that physical coins may be lost between electrical pulse and first completed flash commit.
- `intercon_remote_cs_protocol_test.cpp` tests frame parsing, wrong key/identity, corruption and record codec round-trip. `test_intercon_remote_cs_source.py` is static source-pattern validation. Neither executes actual LittleFS rename/write-failure recovery or the full controller/backend transaction.
- No real coin acceptor, brownout, power-cut, reboot, router-credit or 30-device soak test was run.

## 5. Exact COE #48 CI

- [44629292767](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44629292767): Stage 5 workflow **PASS**, all 3 jobs (static-contract, signed-wire, ESP8266 compile).
- [44629291957](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44629291957): case-collision guard **PASS**.
- [44629291962](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44629291962): shared Hardware/Contracts **FAIL**. ESP8266 Stage 5 compile passed; shared ESP32 compile failed at `Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino:6` because `mbedtls/sha256.h` is absent under ESP32 core 4.0.0. The ESP32 file is outside #48's changed paths.

COE #26 exact-head run list still has 8 queued attempts across 5 unique workflows and zero jobs. #35 remains blocked by site-scoped ULA authority and missing Bubblewrap; #44 remains a separate older-base ULA candidate.

## 6. Current Experiments role PRs and CI

| Role | PR / exact head | Current evidence |
|---|---|---|
| CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS |
| RENTAL | #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229), [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS |
| HARDWARE | #327 `ac7e94ff416a81ddbe535ca9795d99a2092adf31` | [44622826723](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44622826723) and [44622826935](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44622826935) PASS; [44622826708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44622826708) FAIL |
| QA | #290 `5c29d159...`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; #292 no exact-head run |
| RELEASE | #291 `66f622fe2ba727e7a37e9431aebfeb5d3782e23a` | Windows [44626386129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44626386129) FAIL; ESP32 [44626386215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44626386215) and BlazePwifi [44626386217](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44626386217) PASS |

### Current owner-failure details

**HARDWARE #327:** the Full job enters `controllers.sh` and then `v05_firmware_hardening_test.sh`, which still requires positive `response_sig` and `|poll|` markers. Exact ESP8266 source blob `284f4337bc9e2aa4d78c61f0d7e4c4163ffb0a82` deliberately makes `acceptPollResponse()` return false and clears `insertMode` until CORE defines the canonical config-auth contract and QA approves positive/negative vectors. QA must update the fixture to assert default-deny; do not re-enable positive poll admission to make the test green.

**RELEASE #291:** the handover step passes, but `negative-selftest.ps1` fails because `$buildWorkflow` is uninitialized. The publisher mock and all build/sign/publish steps after the failure are skipped. PISONET owns the test file; RELEASE reruns after the owner correction.

## 7. Governance and private registry

Both main branch APIs report `protected=false` and required status-check enforcement off. No protection settings were changed. The private canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer authoritative corrections were not surfaced by Library search; the visible 2026-11-09 checkpoint and 2026-10-26 artifact metadata are not replacements. The AGENTS-linked cloud policy/handover were read; they require an authorized private registry and remote readback. No Google Drive connector is available, so registry verification is **BLOCKED**. No private registry data or IDs were published.

## 8. Master changes, tests and next owners

**Master change:** coordination documentation only; no subsystem source, test, manifest, branch, CI workflow, migration staging or destination tree changed. `OWNERSHIP_ROUTES.json` is unchanged.

**Master validation:** exact refs, PRs, source paths, CI run/job outcomes, protocol field differences and ownership routing were re-read. No Master-specific Python suite or GitHub Actions run was available; no local subsystem test is claimed.

**Next actions:**
1. PHX-HARDWARE: add fault-injection/reboot coverage for RemoteCsJournal and physical coin-inhibit/hold-up acceptance.
2. PHX-PISONET/COE integration: define the router bridge in owned paths only after CORE approves durable transaction semantics.
3. PHX-CORE: define exactly-once `(device,event)` credit and receipt/reconciliation behavior; the separate CORE continuation remains owner.
4. PHX-QA: update #327's stale positive poll fixture to default-deny and review Stage 5 runtime/journal paths at exact SHA.
5. PHX-RELEASE: preserve no-publisher behavior and rerun #291 after PISONET fixes `$buildWorkflow`.
6. Repository administrator: enable/verify branch protections. Registry custodian: restore authorized v11 access.

**Disposition:** COE #48 remains draft/LAB/NO-GO; COE #26 remains frozen; no merge, release, flash, payment operation, secret provisioning, physical test or migration was performed. **PRODUCTION NO-GO.**
