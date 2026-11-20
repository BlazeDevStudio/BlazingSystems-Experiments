# PHX-MASTER UTC03 — Hardware/COE migration provenance and toolchain reconciliation

**Checkpoint:** 2026-11-19 UTC03  
**Task:** PHX-MASTER-UTC03-COE26-HW327-PROVENANCE  
**Disposition:** Master coordination update committed to existing draft PR #288; COE #26 migration BLOCKED; PRODUCTION NO-GO.  
**Scope:** coordination/phoenix only. No subsystem source, test, workflow, destination or ownership manifest was changed.

## 1. Exact control-plane refs

| Ref | Exact SHA / state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Current development label v0.6.0 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 — 1,876 ahead / 22 behind main |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 — 0 ahead / 293 behind |
| Master before UTC03 | 49a508b90d01b1d314484786b5f2fb45962498cf |
| Master PR #288 | OPEN / DRAFT, base main at f4e8a891... |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |
| COE Release #35 | a270b547fb5ff570bd2bc49c2e96219043d7c9bd; source/test head 3b83a408583091f2b2e8a7cf4ef73833f2eb9e39 |
| COE Release #44 | 582fd5d5e83e36b36546ac28534740298ba94af4 |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce |
| Experiments Hardware #327 | 11fae729df415cc26b9e1675b1758cd8e4d22648; base #326 58c558fb6a237935214621adc3dee65a10fe1a51 |
| Experiments Release #291 | fe940216e9e250b5df48c633b669ef3dd34fb299 |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96; stale base b1ca02e2087f3b1a7169ceab9c34e52646e700df |

Ownership manifest remains e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER destination null.

## 2. Corrected release-toolchain finding

UTC02 identified unpinned ESP32 core drift between source and COE #35. That specific failure is now corrected on #35 only.

Current #35 hardware workflow blob e16e6e0f97092bd63a5dec8b871f98be2149847f pins Arduino CLI 1.6.0, ESP8266 core 3.1.2 and ESP32 core 3.3.13, with runtime version checks. Setup action is immutable at b3cda96fddef6af6c56b4c5efb5c47e2357935db. Guard test blob 983f12ead5e76e59f5d1dec0b42b3facda66fd32 checks the exact pins.

- Shared/firmware #44451317780: PASS, including both board compile/artifact-upload jobs.
- Case collision #44451317996: PASS.
- Mandatory sandbox #44451317807: FAIL CLOSED because bwrap is absent (exit 125); no unsandboxed fallback.

The current #35 handover at a270 records these pins, but the PR description still contains older head and CI text. PHX-RELEASE must refresh its own PR description.

COE #26 does not inherit this fix. Its hardware workflow blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 uses arduino/setup-arduino-cli@v2 and unversioned core-install commands. Its Hardware README blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb documents ESP32 3.3.12 and ESP8266 3.1.2. The workflow does not enforce those versions, and its ESP32 documentation disagrees with #35's 3.3.13 pin.

## 3. Current Hardware #327 exact-head update

The current branch head is 11fae729df415cc26b9e1675b1758cd8e4d22648. The PR description still reports a3597125fef3964ab08f05b3300c8de3e47516ae, so its handover is stale.

Commit 11fae729 changes the ESP32 Mbed TLS selection:
- Major 4 uses PSA Crypto.
- Major 3 uses the legacy SHA-256 API.
- Any other major fails compilation.

Current ESP32 sketch blob f54805b17cac45388dfacc5e65eff9b731234316 is 60,326 bytes. The current ESP8266 source blob is 1b32cb90be11da79ba7ea1155f128aee9e495dd2, 67,300 bytes.

Exact current-head CI:
- Quarantine/readback #44453235563: PASS.
- Relay/output #44453235544: PASS.
- Full build #44453235564: FAILURE at QA-owned Controller protocol parity / Missing poll signature check.
- ESP32 job 135322011864: SUCCESS under esp32:esp32@4.0.0; artifact 14496054232 uploaded.
- ESP8266, Android and all firmware target jobs completed successfully; update bundle, simulations, signing, candidate and publishing jobs were skipped.

The 4.0.0 compile verifies the Mbed TLS 4 branch. It does not independently verify the Mbed TLS 3 branch or unsupported-major rejection. The latest source-extracted lab head remains 071a711d6598c67124e84ffd995fd48aa7d9f054; no dedicated unsupported-major test was added. The Full workflow remains red because the positive poll-signature fixture conflicts with the current default-deny source.

PHX-HARDWARE owns the source and PR description. PHX-QA owns independent version-branch and negative/default-deny tests. Master made no Hardware source or QA test change.

## 4. Exact source/destination comparison for COE #26

| Platform | Experiments #327 source | COE #26 destination |
|---|---|---|
| ESP8266 | 1b32cb90be11da79ba7ea1155f128aee9e495dd2 / 67,300 bytes | c8be98f72596681e36a3ad1f8939bf8046c96887 / 18,394 bytes |
| ESP32 | f54805b17cac45388dfacc5e65eff9b731234316 / 60,326 bytes | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 / 18,505 bytes |

Both platform blobs differ.

The source #327 diff contains eight Python source-extracted hardware labs:
1. coin_pulse_capture_lab.py
2. config_load_read_failure_lab.py
3. esp8266_boot_polarity_lab.py
4. poll_fault_dual_store_lab.py
5. poll_loop_blocking_inhibit_lab.py
6. poll_response_failclosed_lab.py
7. poll_window_drain_lab.py
8. request_digest_failure_lab.py

COE #26 contains one generic Hardware/tests/test_firmware_hardening.sh test (blob f921c56cecc19cab1989507b9b4ade1f45dac54e, 4,118 bytes). It greps for response_sig, |register|, |poll| and quarantine routes, then performs brace balancing. This is not equivalent to the eight source labs.

Both current #327 sketches have acceptPollResponse() returning false; the current source has no positive |poll| token. The COE #26 test still expects positive string presence and its Hardware README describes positive response-signature verification. Importing current source without replacing the destination test/documentation would create a direct test/contract conflict.

License evidence: source BlazePwifi/LICENSE and COE Pisowifi/LICENSE are byte-identical at blob 1ee55b94183417be977ca287cd7391f9a6f7e721. COE Hardware/LICENSE and Hardware/NOTICE.md are absent; source BlazePwifi/NOTICE.md and COE Pisowifi/NOTICE.md were also not found. The Hardware subtree's explicit license/NOTICE scope is therefore unresolved.

The #26 PR description was edited at 2026-11-19T03:44:46Z to assert the licensing/privacy gate is resolved and 95% software readiness. The exact file review does not establish Hardware license scope, and the five destination workflows remain QUEUED with zero jobs. These narrative claims are not accepted as migration evidence.

## 5. COE #44 ULA and release-stack status

GitHub compare reports #44 is 15 commits ahead and 21 behind current #35; it remains based on 1a5be48d2845781b0b07bad39a37f8440cea4d4. PHX-RELEASE owns history-preserving reconciliation.

The ULA provisioner is generated by tools/package_appliance_firmware.py (blob f2c2467f37137c38856abcad1b101436e50d3970), function generate_ula_firstboot_script(). It creates a random 40-bit RFC 4193 global ID from /dev/urandom and persists a prefix per installation. This does not prove that multiple appliances at one site share a site-scoped prefix. PHX-CORE must define the site identity/distribution authority; PHX-QA must test same-site, different-site, reboot, upgrade and restore.

COE #45 remains a synthetic receipt-v1 contract candidate. Runs 44295049727 and 44295049903 pass, but no approved Master-v2 field/key/ledger mapping exists.

## 6. Other role CI and blockers

| Role | Exact head | Evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped run 42698139210 PASS; separate CORE continuation owns implementation |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Scoped runs 43653329235 / 43653329229 PASS |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Scoped run 42462978704 PASS; native COM bench not established |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Scoped run 43633486963 PASS |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No runs; stale Master base |
| RELEASE #291 | fe940216e9e250b5df48c633b669ef3dd34fb299 | BlazePwifi run 44440710888 PASS; Windows 44440710823 FAIL because $buildWorkflow is uninitialized under PowerShell StrictMode; publisher skipped |

#266 remains OPEN and retains historical 2026-10-31 source pins. Experiments main, v0.5.3, v0.6.0 and COE main branch objects report protected=false; rulesets reads are empty and classic protection reads are unavailable. Repository admin must verify effective protection.

## 7. Registry and execution limits

Experiments AGENTS.md, README_FIRST, the uploaded Master prompt, BLAZE-COMMS/1, current Master coordination docs, and the canonical cloud artifact policy/storage handover were read. COE root AGENTS.md returns 404.

The requested private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections are not available through the connected Library; no Google Drive connector is exposed. Older snapshots were not substituted. No private registry contents or IDs were published.

- 24/24 local coordination/provenance assertions PASS.
- Exact-head role CI and logs inspected at the linked run URLs.
- Full Master Python suite NOT RUN: shallow Git clone failed because the container could not resolve github.com.
- No Master GitHub Actions runs returned.
- No physical hardware, flashing, native acceptance, real power cuts or 30-device/24-hour soak was performed.

## 8. Next actions

1. PHX-QA: replace positive poll-signature presence with negative default-deny assertions; independently review #327 and add Mbed TLS 3/4/unsupported-major tests.
2. PHX-HARDWARE: refresh #327 PR description/handover to 11fae729; retain default-deny and source ownership.
3. PHX-RELEASE: refresh #35 PR description, keep exact toolchain pins, reconcile #44/#35 without force-push, and obtain the authorized Bubblewrap runner.
4. COE integration owner: complete exact source/destination path, mode, blob, license/NOTICE, test identity and pinned-toolchain provenance; unblock #26 workflows before staging.
5. PHX-CORE: define site-scoped ULA authority and receipt-v1/v2 mapping; CORE implementation remains separately owned.
6. Repository administrator: verify branch protection and required checks.
7. Registry custodian: restore authorized private v11 and newer correction access.

**PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.
