# PHX-MASTER — ESP8266 boot polarity and live Hardware stack audit

**Checkpoint:** 2026-11-18 UTC13 (13:36Z)  
**Role:** PHX-MASTER — coordination/phoenix only  
**Disposition:** source/tree audit completed; Hardware/QA decisions required; no migration; **PRODUCTION NO-GO**.

## Live exact repository references

| Ref | Exact SHA / state |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master before this audit | `6a73722b7fa990771a94969c4aed11531f184fb4` |
| Master PR #288 | OPEN / DRAFT, base main at `f4e8a891...` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration #26 | OPEN / DRAFT, head `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Ownership manifest | blob `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, Master target null |

## 1. Source finding: ESP8266 polarity is not established at boot

The current #323 review candidate uses source/test SHA `176ad50da2180ee085e2fb63ddb23d17b53dd63d`; the current PR/docs head is `0975fe4416daa72c097d3fee2b631950eb64908c`. The final head commit changes only the Hardware handover file. Exact source blobs read at that head:

- ESP8266 sketch: `8e79b9eb8856e67d966f4c6385f89fccdc8be7fc`
- ESP32 sketch: `bd74b11c1496b0943404ff387ee72bb45d4743e5`
- #323 poll-fault host lab: `2688ced2b3b605276144c8fda0bbdbd9b96142b7`

### ESP8266

- At source line 46, `runRelayActiveHigh=true` and `runLedActiveHigh=true` are initialized as active-high defaults.
- The only subsequent runtime polarity assignments are inside `applyRemoteConfig()` (lines 587–605). The source explicitly labels that function intentionally dormant because the returned configuration object is not authenticated.
- `setup()` reaches `configureRuntimePins()` without loading a persisted/local relay/LED polarity. No independent boot-time polarity authority was found in this sketch.

This means the source currently establishes the OFF-preload sequence only for the active-high default. It does not establish a safe active-low ESP8266 profile. If the actual relay wiring is active-low, the active-high default may drive the wrong physical level at startup. This report does **not** assume the physical board is active-low; the wiring/profile is UNKNOWN until Hardware provides evidence.

### ESP32 distinction

ESP32 has a different source path: `loadConfig()` reads `relayhi` / `ledhi` from Preferences, and `setup()` loads configuration before assigning runtime polarity and calling `configureRuntimePins()`. This is a source-level persisted configuration path, not proof of safe behavior for missing/corrupt NVS or a physical board.

### What the current #323 lab proves — and does not prove

The exact-source `poll_loop_blocking_inhibit_lab.py` records relay/LED state when the secondary `writePollFaultBackup()` writer begins and when LittleFS opens `/pollpulse.fault`. It asserts that neither operation begins while relay or LED is ON. This is useful source-extracted control-flow evidence for the fault latch. It does not prove that the production ESP8266 boot path loads the correct physical polarity before the first output enable, and it is not electrical acceptance.

**Required owner actions:**

1. PHX-HARDWARE: either document an active-high-only ESP8266 target profile with exact board/wiring/BOM evidence, or implement a validated persistent local polarity source that is loaded before the first output configuration. Do not use unauthenticated remote config as the polarity authority.
2. PHX-QA: independently test cold boot with default, missing, corrupt and every supported polarity value; observe the first logical/physical output level before OUTPUT mode and after reboot.
3. Hardware acceptance owner: verify actual relay/LED reset levels, pull resistors and GPIO transitions on the physical boards. Host simulation is not a substitute.

Until those actions are complete, active-low ESP8266 support remains UNKNOWN / NOT ACCEPTED. Preserve default-deny and do not flash or enable coin admission.

## 2. Current Hardware ancestry and stale PR descriptions

| PR | Current API head | Base | Audit result |
|---|---|---|---|
| #317 | `fce915c1167fc43c6936f3594ae9efce376b711f` | #315 `84fe6b790139d147f330f13a40b3ae3e89a7042d` | Current parent of #320/#321 |
| #318 | `de428b7a3e15854804f09935a36a6afeb67d8cbe` | `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3` | Diverged from #317; compare #318 → #317 is 71 ahead / 57 behind; stale base |
| #320 | `b2b41a3d6ce7887b9624137c966f58462895d3fa` | #317 `fce915c1167fc43c6936f3594ae9efce376b711f` | Parent of #322 |
| #321 | `4c54d6299388617e9ff3d41d5501358ea545c54a` | #317 `fce915c1167fc43c6936f3594ae9efce376b711f` | Alternate output-preload child |
| #322 | `50d93e0de3d682550b6f02fb43484e76ad9c7e08` | #320 `b2b41a3d6ce7887b9624137c966f58462895d3fa` | Parent of selected #323 review candidate |
| #323 | `0975fe4416daa72c097d3fee2b631950eb64908c` | #322 `50d93e0de3d682550b6f02fb43484e76ad9c7e08` | Review candidate; source/test SHA `176ad50...` |
| #324 | `8e7f02201cb9295f15672dc21f8a75fc4e5cd0ba` | #322 `50d93e0de3d682550b6f02fb43484e76ad9c7e08` | Divergent sibling; compare #324 → #323 is 41 ahead / 8 behind |
| #325 | `f66b45ecbae8cdc6e4d78db976903bb41c7a75b0` | #283 `830c355376380f9b5533d5cda2558beed41a593a` | Separate pending-clear child of #283, not part of #322 → #323 |

**Correction to earlier Master direction:** #323 already contains the direct output-off assertion at both secondary backup-write and LittleFS marker-open boundaries. The test records those boundaries and fails if relay/LED is ON. The prior request to port that specific #324 regression is superseded; no port is needed. #324 still has an eight-commit delta and remains a separate draft until Hardware reconciles its remaining changes.

PR bodies also contain stale embedded head/base strings: #317, #318, #323, #283 and COE #35. Current PR API heads above are authoritative. The owning roles should refresh their descriptions; Master did not edit owner PR bodies.

## 3. Exact-head CI evidence

| Candidate | Exact evidence | Result |
|---|---|---|
| #318 `de428b7a...` | [44313531583](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44313531583) push event | PASS; no PR-triggered run returned by the PR-only wrapper |
| #323 `0975fe44...` | [44301775875](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44301775875), [44301775918](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44301775918) | Focused PASS |
| #323 `0975fe44...` | [44301775872](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44301775872) | Full FAIL: inherited `Missing poll signature check`; all 13 firmware targets and Android passed, downstream simulation/signing/publishing skipped |
| #325 `f66b45ec...` | [44311211095](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44311211095) | Focused PASS |
| #325 `f66b45ec...` | [44311211166](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44311211166) | Full FAIL at controller protocol parity; target builds passed, downstream jobs skipped |
| COE #35 `7e41b9ac...` | [44312869909](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44312869909), [44312868745](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44312868745) | Case/shared PASS |
| COE #35 `7e41b9ac...` | [44312868726](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44312868726) | Mandatory sandbox FAILS before preflight: bubblewrap missing, exit 125; no fallback |
| COE #26 `b382d233...` | five PR workflows | QUEUED, zero jobs returned |

The Full validation failure is a QA fixture/contract issue. Do not introduce a synthetic positive poll signature or weaken firmware default-deny to satisfy it.

Other scoped role runs refreshed this activation: CORE #252 [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; PISONET #255 [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; RENTAL #289 [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) PASS; QA #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; RELEASE #291 [44296971291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44296971291) SUCCESS with publishing skipped; QA #292 has no runs returned.

## 4. Governance, migration and availability

- Experiments main remains `f4e8a891...`; development remains `aad3aade...`; COE main remains `a6513ab4...`. PR #288 remains OPEN/DRAFT before this commit; PR #26 remains OPEN/DRAFT.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No source/destination files moved, copied or deleted.
- Branch-protection readback for Experiments main returned 403; rulesets endpoint returned `[]`. Classic branch protection is UNKNOWN, not proven enabled or disabled. Repository administrator must inspect Settings → Branches or grant the integration read permission.
- The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found in the accessible Library search. No Google Drive connector was exposed. Older v3/v4/v7 snapshots are not substitutes. No private identifiers or contents were published.
- Experiments root `AGENTS.md` was read. COE root `AGENTS.md` returned 404.

## 5. Master disposition and next actions

**No migration, merge, rebase, source takeover, firmware flash, signing, secret provisioning, financial operation or physical test occurred.** Master changes are coordination documentation only.

1. PHX-HARDWARE: resolve ESP8266 boot polarity and refresh stale PR descriptions; reconcile #318 and #324 ancestry; keep #325 separate.
2. PHX-QA: replace positive poll-signature fixture with negative deny tests and add boot-time polarity tests at exact source SHAs.
3. PHX-RELEASE / infrastructure: provide a runner with bubblewrap and usable unprivileged namespaces; retain fail-closed behavior.
4. Repository administrator: verify branch protection; registry custodian: restore authorized private Drive v11 and newer corrections.

**PRODUCTION NO-GO** remains mandatory pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.
