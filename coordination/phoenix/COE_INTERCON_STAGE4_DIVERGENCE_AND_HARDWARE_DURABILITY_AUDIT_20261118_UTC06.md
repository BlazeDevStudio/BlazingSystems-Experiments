# PHX-MASTER — COE INTERCON Stage-4 divergence and exact-head Hardware review

**Audit window:** 2026-11-18 UTC06  
**Disposition:** Master-only architecture/provenance audit; candidate-only; no migration, merge, release or production authorization.

## Scope and authority

Re-read: uploaded 00_MASTER_PROJECT_PHOENIX(1).txt, README_FIRST, BLAZE-COMMS/1, Experiments root AGENTS.md, live #172 and #266, PR #288, ownership routing manifest, current role PRs and exact-head CI, COE main and integration PR #26. The canonical private Drive registry v11 and newer corrections were not accessible. No private registry contents or identifiers are reproduced.

All edits in this report are restricted to coordination/phoenix/. No subsystem source, QA test, workflow, COE file or ownership manifest was modified. The separate CORE continuation retains CORE ownership.

## Exact repository state at audit start

| Ref | Exact state |
|---|---|
| Experiments default main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development | blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| PHX-MASTER / PR #288 | phoenix/master-coordination @ c1500a585b07a5ecb2772bf58bf25c0e9df816e8; OPEN / DRAFT; base main @ f4e8a891... |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | OPEN / DRAFT; head b382d233ff06c8791b1028bed3c617cc7b670d12; base main @ a6513ab4... |
| OWNERSHIP_ROUTES.json | e4db324315a1b3543fec17a148fbf960170fcb29; DRAFT_REVIEW_ONLY; PHX-MASTER destination null |

Before this audit PR #288 contained 71 changed paths, all under coordination/phoenix/. Experiments main reports branch protection disabled and no required status checks. Cleanup issue #266 remains an open cleanup-first checklist, not proof of completion.

## HARDWARE #323 — latest exact-head CI correction

Current PR #323 is OPEN / DRAFT, head 82b0ed15e4aeb8b9b5af40e457e19d308d4a2cfb, source/test SHA 30fb7cd2de0af13c70aa8716da8d7cd9e43ce548, based directly on #322 at 50d93e0de3d682550b6f02fb43484e76ad9c7e08.

| Exact-head run | Result | Verified scope |
|---|---|---|
| [44246998831 — Relay/output and poll lab](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44246998831) | SUCCESS | 48/48 polarity scenarios per board; 4/4 OFF-preload/output-enable checks; poll drain 11/11; pulse capture 8/8; blocked-poll fault marker 7/7 per board; source-only |
| [44246999048 — Quarantine/readback](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44246999048) | SUCCESS | 72/72 source-extracted quarantine scenarios; pending-attempt marker 56/56; fake-LittleFS mount/relay 16/16; dual-store lab pass with explicit current-boot-only limitation; boot recovery and pending-clear helpers; no actual flash |
| [44246998969 — Full BlazePwifi build](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44246998969) | FAILURE | Validation fails at QA-owned legacy Missing poll signature check; all 14 target/platform build jobs succeeded; downstream simulation, update, import, signing and publishing jobs skipped |

The latest exact-head Full run supersedes the earlier role checkpoint that reported the ESP32 target job cancelled: on run 44246998969 the ESP32 and ESP8266 target jobs both completed successfully. Full validation remains blocked by the stale QA-owned positive poll-signature fixture. Firmware default-deny must not be weakened to satisfy that fixture.

These focused runs are source-extracted host simulations, not physical GPIO, relay, coin acceptor, flash-brownout or power-cut evidence. The dual-store helper explicitly reports EXPECTED_CURRENT_BOOT_ONLY when both same-chip stores fail. NVS/EEPROM emulation is not an independent physical witness.

## COE INTERCON — three incompatible Stage-3 journals and two divergent Stage-4 candidates

| Stage-3 PR | Exact head | Record format | Adapter / CI |
|---|---|---:|---|
| #39 | 33e87fbd7f287955d85509cbb05ff5ca20a26a4b | 64 bytes | InterconJournalFS; [44234479271](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44234479271) SUCCESS |
| #40 | 85f38c6e2ba879fca9f26f708c1cbeb1736dd01c | 76 bytes | InterconLittleFSJournal; [44235077999](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44235077999) SUCCESS |
| #42 | a35672fb60228fb8f84801405d032293f0266023 | 92 bytes | InterconFlashJournal + InterconJournalCodec; [44235625165](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44235625165) SUCCESS |

All three also have successful shared/firmware and case-collision workflows. These are incompatible candidate formats, not one selected canonical journal.

There are now two Stage-4 candidates on different Stage-3 parents:

| Stage-4 PR | Exact head / base | Functional boundary | Exact-head CI |
|---|---|---|---|
| #41 | 021e2474c5bc8df37ab016a586db516fb4f2445f / #39 @ 33e87fbd... | Journal-only SHADOW credit; no customer countdown, sales, coin input or relays | [44235451605](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44235451605) SUCCESS |
| #43 | 8f5eec790dc2a3e25c219a6f51651113cd1c90cd / #42 @ a35672fb... | Authenticated CRED/ACKN path; Slave journal updates paid time + receipt/sequence before live timer/output changes | [44246962253](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44246962253) SUCCESS |

Their shared/firmware and case-collision checks also pass. Both remain OPEN / DRAFT / NO-GO. #41 shadow-only is not equivalent to #43 live timer/relay. #43 depends on the 92-byte #42 codec and cannot be treated as a successor to #39/#40 without an explicit owner decision and format migration plan.

### Source-grounded #43 limitations

1. The end-to-end test uses an in-memory Node with two byte arrays for journal slots and memcpy to simulate the rename boundary. It tests the codec/credit algorithms and modeled crash points, not actual LittleFS metadata atomicity, ESP8266 flash behavior or brownouts.
2. The unresolved pulse count is a runtime RAM variable and is not represented in the journal record. If a physical pulse burst cannot be staged because the journal is unavailable or commit fails, the alarm count is not shown to survive reboot.
3. The pairing config contains a raw 32-byte key field read/written as a LittleFS config record. The inspected files show no protected key store or independent signer. HMAC transport and a checksum are not a protected P-256 signing witness or anti-rollback authority.
4. The PR documents a 650 ms quiet-burst assumption and 60-second countdown checkpoints; the latter can restore up to about 60 seconds of previously consumed time after sudden power loss.
5. The PR states that a physical coin can fall before the Master's first journal commit; acceptor CS inhibit / electrical hold-up and actual pulse timing require hardware validation.
6. It supports one paired Master/Slave and explicitly leaves the BlazePwifi router payment adapter / multi-target accounting integration separate. No canonical CORE receipt/event reconciliation was demonstrated.

These are acceptance blockers, not reasons for PHX-MASTER to alter COE subsystem code. COE root LICENSE and Hardware/LICENSE paths returned 404; license/NOTICE applicability is unresolved. No code was copied or migrated.

## Ownership and routing boundary

OWNERSHIP_ROUTES.json maps PHX-HARDWARE only to BlazePwifi ESP32/ESP8266 and PHX-PISONET only to Windows SoftTimer. It contains no route for COE Hardware/BlazePisonetUniversal INTERCON. PHX-MASTER must not infer that either worker owns this new COE subtree. The COE integration owner must nominate an accountable owner and reconcile source/license/test boundaries before any integration into #26.

## Other current role and release evidence

| Role | Current PR / exact head | Exact-head evidence |
|---|---|---|
| CORE | Experiments #252 @ c82705f2... | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) scoped SUCCESS |
| RENTAL | Experiments #289 @ 68928774... | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235), [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS |
| PISONET | Experiments #255 @ d01fd164... | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) scoped SUCCESS |
| HARDWARE | Experiments #323 @ 82b0ed15... | Two focused SUCCESS; Full validation FAILURE as above |
| QA | Experiments #290 @ 5c29d159...; #292 @ 75a3f66d... | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS; #292 has no current-head run |
| RELEASE | Experiments #291 @ a74b8b94... | [44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756) scoped SUCCESS |
| COE RELEASE | #35 @ d73986d2...; source/test @ aaecb633... | Shared/board [44251684647](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44251684647) SUCCESS (84 tests, two intentional skips, 10/10 profiles, both board compiles); case [44251684645](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44251684645) SUCCESS; mandatory sandbox [44251684871](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44251684871) FAILED CLOSED at bubblewrap UID-map permission denial (exit 125); packaging regressions skipped |

COE #35 remains 17 commits ahead / 0 behind parent #31 @ 59ed44d0... and OPEN/DRAFT. Sandbox preflight passes 8/8, but the actual unprivileged namespace probe is denied. No privileged mapping or unsandboxed fallback is approved. Invalid ULA fd00:db8:blaze::/48 remains unresolved. COE #26 still has five workflows QUEUED with zero jobs; there is no combined integration acceptance.

## Registry, instructions and execution limits

- Experiments AGENTS.md was read. Its linked cloud artifact policy and storage handover could not be fetched through the exposed GitHub connector.
- COE root AGENTS.md returned 404 on main and the #43 candidate.
- Canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in the accessible Library; no Google Drive connector was exposed. A private checkpoint dated 2026-11-09 references v11 but is not the canonical registry or a current correction. It was not substituted.
- Cleanup issue #266 remains an open cleanup-first checklist; its pinned refs are historical and do not prove completion.
- Bounded source/provenance assertions executed in this run: **12/12 PASS** (branch lineage, 64/76/92-byte formats, RAM-only unresolved pulse state, raw peer-key config, in-memory host journal model, timer/pulse caveats and router-adapter boundary).
- Full Master Python coordination suite: **NOT RUN**. A shallow Git clone failed because the execution container could not resolve github.com. No Master PR #288 CI run was returned. The 12/12 checks are not a substitute for the repository Python suite or independent QA.

## Required next actions

1. PHX-QA: independently review HARDWARE #323 source/test SHA 30fb7cd2...; add reboot-after-primary, secondary and both-store failure cases; repair the stale poll-signature fixture without restoring positive admission.
2. PHX-CORE: define canonical receipt/event identity, unresolved-coin disposition and reconciliation before any Intercon-to-router accounting integration.
3. COE integration owner: nominate an explicit INTERCON owner; choose one Stage-3 journal and one Stage-4 path only after format, replay, key custody and timer semantics are reviewed. Keep #41/#43 drafts separate.
4. COE INTERCON maintainer + QA: make unresolved pulse evidence durable, provide protected key custody / anti-rollback design, and obtain actual ESP8266 flash/coin/relay/power acceptance. Host CI is not physical proof.
5. PHX-RELEASE / infrastructure: obtain an authorized disposable no-secret runner with unprivileged user namespaces for #35; do not bypass the sandbox. Resolve installation-scoped ULA contract with CORE.
6. Registry custodian: restore authorized read access to the canonical private Drive v11 registry and newer corrections.

**Production status: STRICT NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

No Codex, subsystem source takeover, COE migration, merge, release, signing, secret provisioning, hardware flash, physical test or real-payment operation occurred.