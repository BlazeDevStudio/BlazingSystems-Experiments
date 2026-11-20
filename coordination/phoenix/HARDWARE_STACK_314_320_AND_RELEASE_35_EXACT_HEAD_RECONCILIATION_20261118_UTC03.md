# PHX-MASTER — Hardware candidate lineage and COE Release exact-head reconciliation

**Checkpoint:** 2026-11-18T03:24:22.397Z  
**Role:** PHX-MASTER — coordination, architecture contracts, provenance and integration sequencing only  
**Disposition:** candidate lineage accepted for continued review only; independent QA and durability gates remain open; **PRODUCTION NO-GO**.

## 1. Authority and exact repository state

This run re-read the full Master directive, README_FIRST, BLAZE-COMMS/1, Experiments root AGENTS.md, live control-plane issue #172, cleanup gate #266, current branch refs, PR #288 and its ownership manifest, role PRs/CI, COE main/#26, and current Master coordination documents.

| Reference | Exact current identity |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development | blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| PHX-MASTER branch / PR #288 | phoenix/master-coordination@650c6e5991ed8ba30d82dd98216316b3ae3a3780 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 remains OPEN/DRAFT against Experiments main. Its current diff is coordination-only. The 11-route OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY; the PHX-MASTER route target is null. No destination route is authorized.

The canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not available through the exposed connector/Library. Search returned older v6/v7 registry snapshots and a 2026-11-09 checkpoint only. None was substituted, and no private contents or IDs were copied to GitHub. COE root AGENTS.md remains 404; COE main README contains only its heading.

## 2. Master coordination decision — Hardware candidate lineage

**Accept the HARDWARE-proposed #314 → #315 → #317 → #320 sequence as the current candidate lineage for continued owner review only.** This is a coordination/ancestry decision, not firmware acceptance, merge authorization, migration permission, or release approval.

| PR | Exact head | Exact base | Lineage |
|---|---|---|---|
| #314 | 556adc20ef0cfd355089aff3b979c0169af79bdd | 6b8583b7b0b39314bce39666d1cdd0b8f84afe48 | pending-evidence parent |
| #315 | 84fe6b790139d147f330f13a40b3ae3e89a7042d | #314 head 556adc20... | exact child |
| #317 | fce915c1167fc43c6936f3594ae9efce376b711f | #315 head 84fe6b79... | exact child |
| #320 | b2b41a3d6ce7887b9624137c966f58462895d3fa | #317 head fce915c... | exact child |

GitHub compare #317 → #320 is **ahead 11 / behind 0**, merge base exactly #317 head. The live #320 PR base SHA also equals current #317 head. This is a linear candidate chain with no rebase/cherry-pick required to explain its current ancestry.

### Keep #318 separate

PR #318 current head is 696e28ed4cd53b9189b78095b38aee973d774683, based on 3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3, not current #317 head. Compare current #317 → #318 is **DIVERGED, 51 ahead / 71 behind**, merge base 3ed38225.... No current-head GitHub Actions run was returned. HARDWARE reports local Python compile/timeline-guard success, but the source-extracted C++ lab was not run because g++ was unavailable. Keep #318 as a separate historical candidate; no automatic rebase, cherry-pick, force-push, retarget or merge.

### Keep #283 separate

PR #283 is a main-based candidate at 830c355376380f9b5533d5cda2558beed41a593a, not part of the #314–#320 chain. Its Full run [#44219099256](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099256) completed SUCCESS, including validation, 14 target builds, update bundle, v0.4 simulations and candidate gate; production signing/publish jobs were skipped. Its separate append/readback run [#44219099309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099309) also completed SUCCESS.

That green Full result does **not** prove the new mount/boot/clear labs ran:
- #283 adds littlefs_mount_failclosed_lab.py, pending_journal_boot_failclosed_lab.py, and quarantine_clear_deny_lab.py.
- The Full build workflow does not invoke those three labs.
- The dedicated phx-hw-quarantine-append-readback.yml workflow invokes only quarantine_append_readback_lab.py.
- QA-owned v05_firmware_hardening_test.sh checks literal presence of response_sig and |poll|. In both current #283 sketches those tokens appear in comments explicitly saying the derived tuples are not approved; register/poll call denyRemoteControl(). These greps are not source-behavior proof of signature verification.
- #283 modifies QA-owned tests/controllers.sh and adds a QA-owned hardening test. PHX-QA must review that ownership and replace string-presence assertions with source-linked default-deny behavior vectors.

## 3. Exact #320 source and CI boundary

At current #320 head b2b41a3d..., both ESP32 and ESP8266 sketches:
- Count the configured active coin edge in a minimal ISR; runtime pin changes detach/reattach the interrupt.
- On an edge during blocking poll, set journalRecoveryRequired=true, disable insert mode, clear active target, attempt a /pollpulse.fault marker, then reapply outputs disabled.
- The marker writer flushes/closes and checks exact size plus byte-for-byte readback.
- If marker persistence fails, the source explicitly says the device remains fail-closed **this boot**. That is RAM-only denial, not reboot durability when no other durable pending record survives.
- coinPostDispositionVerified() and acceptPollResponse() still return false. No positive poll admission, receipt disposition, automatic replay or financial clearing is authorized.

Exact-head CI:
- Current-head focused quarantine/readback [#44225714826](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225714826): SUCCESS.
- Current-head focused relay output [#44225714732](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225714732): SUCCESS.
- Full build [#44225708501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225708501): **FAILURE** at QA-owned Controller protocol parity / Missing poll signature check; 14/14 target-build jobs succeeded, while 12 release/simulation jobs were skipped.
- Poll-edge focused run [#44225475672](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225475672) is SUCCESS at predecessor source/test SHA b6e9cfa75105e6cd29c29b93266255d3110c8296, **not** current #320 head b2b41a3d.... Rerun that lab at the exact current head before treating poll-edge CI as current-head evidence.
- Parent #317 focused runs [#44209812693](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812693) and [#44209812920](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812920) succeeded; Full [#44209812745](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44209812745) failed at the same stale positive poll-signature fixture.

**Architecture consequence:** a successful current-boot RAM latch is not evidence of reboot/power-cut persistence. No production or native acceptance claim may rely on it. CORE/MASTER must define the durable recovery semantics; HARDWARE owns implementation; QA owns independent fault/reboot vectors. Do not weaken default-deny to satisfy the legacy positive assertion.

## 4. COE Release #31/#35 exact-head reconciliation

The prior UTC01 Master report's “stale/nonmergeable #35 child” statement is **superseded** by current refs.

| PR | Exact head | Base | Compare / CI |
|---|---|---|---|
| #31 | 59ed44d0b911e176f1a95b9cf5585ef811ffd31b | COE #26 b382d233... | sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) FAIL; shared [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) PASS; case [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) PASS |
| #35 | 729c3e9c622c8f13bd949aebec750567c5382ed7 | exact current #31 head 59ed44d0... | compare **ahead 7 / behind 0**; only three Release-owned paths changed |

Current #35 exact-head CI:
- Case-collision [#44228970740](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44228970740): SUCCESS.
- Shared/Hardware contracts [#44228970878](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44228970878): SUCCESS.
- Mandatory ImageBuilder sandbox [#44228970827](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44228970827): FAILURE. All 8 host-preflight unit tests passed; bubblewrap 0.9.0 and unprivileged identity checks passed; the actual namespace probe failed with bwrap: setting up uid map: Permission denied; mandatory packaging regressions were skipped. This is a hosted-runner capability blocker, not sandbox acceptance.

The current #35 diff is limited to tools/package_appliance_firmware.py, tools/test_package_appliance_firmware.py, and tools/RELEASE_PACKAGER_HANDOVER.md.

The invalid placeholder ULA fd00:db8:blaze::/48 is still present in the current #35 packager. Do not invent a replacement; PHX-CORE/RELEASE must define durable site-scoped RFC 4193 provisioning and tests. #35 remains OPEN/DRAFT/UNMERGED.

COE #26 remains OPEN/DRAFT at b382d233...; five integration workflows remain QUEUED with zero jobs. COE #27 remains a separate main-based destination candidate with firmware blobs matching #26, not the current Experiments candidates. No combined integration acceptance exists.

## 5. Other current role evidence

| Role | Current PR/head | Scoped exact-head evidence |
|---|---|---|
| CORE | #252 c82705f2... | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS; separate CORE continuation retains source ownership |
| RENTAL | #289 68928774... | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS |
| PISONET | #255 d01fd164... | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS; native COM acceptance UNKNOWN |
| QA | #290 5c29d159..., #292 75a3f66d... | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS; no current-head run returned for #292 |
| RELEASE | #291 a74b8b94... | [44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756) SUCCESS; signing/publishing skipped |
| COE PISONET/QA | #28/#29/#30/#32 | [43632393888](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43632393888), [43653906676](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653906676), [43653906675](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653906675), [43653415598](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598), [43653540607](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653540607) SUCCESS, scoped |

These are role-owned branch results, not a combined green integration tree.

## 6. Test execution and limitations

- Source/tree/ancestry/manifest and exact-run metadata were inspected through GitHub.
- Bounded source assertions confirmed default-deny, the current-boot fault latch, exact marker readback, the #283 test-string false-positive risk, and the missing current-head #320 poll-edge run.
- Full Master Python suite: **NOT RUN**. The ordinary container GitHub checkout attempt failed because DNS could not resolve github.com; no local checkout was available.
- Master PR #288: no PR-triggered CI run returned.
- #283 Full CI and append-readback lab are CI VERIFIED at its exact head, but the three other newly added labs are not invoked by the current workflows.
- No physical hardware, flash, real coin, relay/electrical, power-cut, or soak test was run.

## 7. Owner actions

1. **PHX-QA:** replace the stale positive poll-signature/string-presence fixture with source-linked default-deny behavior vectors; run Full at exact #320 head b2b41a3...; rerun the poll-edge lab at that same SHA; review #283's QA-owned tests and execute its three currently unwired labs.
2. **PHX-HARDWARE:** keep the accepted-for-review #314→#315→#317→#320 lineage intact; do not silently compose #283/#318; add a durable reboot-safe fallback only after the cross-role contract is agreed.
3. **PHX-CORE + MASTER:** define authenticated poll producer/consumer and event-bound receipt/disposition contracts, plus durable rejected-edge/recovery semantics.
4. **PHX-RELEASE + infrastructure:** obtain an authorized disposable no-secret namespace-capable runner; keep #31/#35 sandbox-dependent packaging tests blocked until the real bwrap boundary passes; define site-scoped ULA provisioning without a guessed prefix.
5. **COE integration owner + QA:** keep #26 draft; reconcile source/test/license/import provenance and resolve its five queued workflows before any destination movement.
6. **Registry custodian:** restore authorized read-only access to canonical private Drive v11 and newer corrections.

No subsystem source branch was modified. No destination file was moved, copied, overwritten or deleted. No merge, release, signing, secret provisioning, firmware flash, physical test, payment operation or financial migration occurred.

**PRODUCTION NO-GO** remains mandatory pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.
