# PHX-HARDWARE UTC05 — active v0.6 poll intake deny

**Task:** P0 coin-pulse loss during synchronous poll — [Issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Control plane:** [Issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Cleanup gate:** [Issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**Draft:** [PR #354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354)  
**Role:** PHX-HARDWARE  
**Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`  
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**Source implementation commit:** `dc619870a096f01d0d1cba24f0bf3c0c981a08d2`  
**Test-matcher correction:** `f381f6d38699e953b32e1d0c603524bc6da86541`

## Why this is a separate active-branch PR

Existing [PR #340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/340) already contains a deny-only poll candidate, but it is a child of #283. The active v0.6 branch remains separate and still had synchronous poll-before-sample, unsigned register/poll consumption, and automatic pending coin POST/clear. This PR applies the bounded deny-only mitigation directly to the active branch without changing or rebasing #239, #254, #283, #340, #352 or #353.

## Test-first evidence

- Test-only PR head `95a32f53824591ceacfbc6317b3f80c95a883b75`: [run #45764293566](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45764293566), job `139721362633`, expected RED. The corrected source guard rejected the active loop because pending coin disposition (`clearPending`) was still present. The response-use and remote-config mutation checks ran first and were rejected.
- Earlier run #45764106355 is **not counted**: its harness had an invalid regex escape.
- Intermediate source-head run #45764829147 is **not counted as product failure**: the new global definition-only matcher had an invalid regex escape; corrected in `f381f6d...`.

## Firmware changes on both boards

- Added `denyRemoteControl()`: disable controller, coin, relay and LED flags; clear only the active target; force logical outputs OFF using existing board polarity handling.
- Invoke deny before and after each synchronous `post("poll")`; explicitly discard the poll response.
- Ignore register response and deny after registration; setup denies immediately after pin configuration.
- Retain `applyRemoteConfig()` only as a deny-only compatibility sentinel.
- Remove unused unauthenticated `jsonString/jsonTrue/jsonInt` parsers and `remoteRevision`.
- Remove automatic `post("coin")`, retry and `clearPending()` from the loop. Existing unresolved pending journal state is retained; the deny helper does not modify `pendingPulses`, `pendingNonce`, `pendingTarget` or the durable sequence record.

**Operational consequence:** this is deliberately deny-only. Coin acceptance and automatic event disposition remain unavailable until PHX-CORE publishes the authenticated controller/configuration and event receipt/disposition contracts and PHX-QA independently validates them. This is safer than reopening the relay based on unsigned legacy fields.

## Focused regression scope

The source-extracted host lab checks both board sketches and:
- pre-poll deny, blocking poll, post-poll deny ordering;
- discarded poll response and no unauthenticated remote config use;
- GPIO OFF behavior under both relay polarities;
- pending pulse/nonce/target preservation when deny is applied;
- failure injection for missing deny assignments, missing pre-poll guard, unguarded second poll, response consumption, remote config application, automatic coin POST and pending clear.

The companion remote-config lab verifies the compatibility sentinel remains deny-only. The workflow asserts that the checked-out SHA equals the event SHA.

## Acceptance boundaries

- Host C++ and source-extracted tests: **SIMULATED / CI VERIFIED only**.
- Physical relay polarity, coin acceptor cutoff timing, electrical pulse/recovery, power-loss behavior and actual coin-slot acceptance: **NOT TESTED**.
- 150 controlled power cuts, 30-device/24-hour soak, protected anti-rollback witness, financial migration, durable accounting/replay and independent release signoff remain open.
- No shared API/schema was changed. No finance backend or COE file was modified.
- No physical flash, device reset, live money, signing, migration, merge, deployment or release tagging occurred.

## Review requests

- **PHX-QA:** independently review the source-extracted deny/polarity/pending-preservation tests and mutation vectors at the final PR head.
- **PHX-CORE:** publish the authenticated register/poll and event receipt/disposition contracts before any future re-enable or pending-event disposition.
- **PHX-MASTER:** reconcile this active-branch child with #340 and the #239/#254/#283 stack; do not merge automatically.


## UTC06 preservation correction and current exact-head CI

A source-preservation audit found the UTC05 `CHANGE_LEDGER.md` refresh had replaced the original 1,080,830-character / 400-section ledger with a 2,454-character checkpoint. The original base blob `f16d5774366cf3a4c358dd2a0c2e7ee5e945f668` was recovered and restored byte-for-byte, then this UTC06 entry was appended. Restoration commit: [d718c873](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/d718c873f4def0807ebf0fc40aa6e1ff60bb3122). Restored blob `eee163aba624160ddeccea184a7c21c4c86d59ce`: 1,082,506 characters / 401 section headings.

Exact-head at final docs head `aca9becc35d2c68faeecbf6e14c70b7d71d1d91b`:
- Focused exact-head PR [#45766825375](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45766825375), job `139729611849`, and push [#45766819170](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45766819170), job `139729592701`, PASS at final docs head `aca9becc35d2c68faeecbf6e14c70b7d71d1d91b`. The earlier d718c873 focused run [#45766610880](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45766610880), job `139728911769`, also passed.
- Native exact-head journal [#45766825496](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45766825496), job `139729626660`, FAIL at QA-owned `tests/v060_vendo_sequence_contract.py:20`: the legacy assertion requires active `clearPending(true/false)` callsites, incompatible with this deny-only candidate. The preceding 12 steps passed; Hardware did not edit the QA-owned test.
- Full exact-head build [#45766825536](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45766825536) completed FAILURE at final docs head `aca9becc35d2c68faeecbf6e14c70b7d71d1d91b`. Validation job `139729743548` failed at QA-owned `tests/controllers.sh` / Controller protocol parity: both deny-only sketches intentionally omit the legacy `config_revision` token, but the current QA script still requires it; the other checked loop markers are present. ESP32 job `139729743626` failed under ESP32 core 4.0.0 with `fatal error: mbedtls/sha256.h: No such file or directory`. All other target/Android build jobs passed; update/simulation/signing/release/publication gates were skipped. This is not Full PASS.

No firmware source changed in this UTC06 preservation correction. Keep the candidate deny-only and do not re-enable automatic coin disposition. QA must revise its own sequence invariant; CORE must publish the authenticated response/receipt contract. Physical acceptance remains NOT TESTED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.



## PHX-HARDWARE UTC06 — final deny-candidate exact-head recheck

**Evidence head before this handover-only refresh:** `458fc1fa7b3b0a58c44e6b3f4becfbcacd905d85` on PR #354, branch `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`, base active v0.6 `2fbd2475e9f54878c316fa7cea2f228386b0e859`. The following commits are documentation-only; they do not change the firmware source/test SHA.

- Focused PR [#45768041258](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45768041258), job `139733634481`: PASS.
- Focused push [#45768031076](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45768031076), job `139733600239`: PASS.
- Native journal [#45768041271](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45768041271), job `139733635211`: FAIL at QA-owned `tests/v060_vendo_sequence_contract.py:20`, which still requires active `clearPending(true/false)` callsites. The deny-only source intentionally retains no active clear/disposition callsite; prior 12 native steps passed.
- Full [#45768041351](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45768041351): terminal FAILURE. Validation job `139733743621` failed at QA-owned `tests/controllers.sh` / Controller protocol parity. Source audit confirms both sketches omit `config_revision` while the current QA script still greps for that legacy token; the other checked loop markers remain present. ESP32 job `139733743603` failed on core 4.0.0: `fatal error: mbedtls/sha256.h: No such file or directory`. All other target jobs and Android passed; update bundle, v0.4 simulations, signing, publication and candidate gates skipped. No Full PASS.
- Exact-source loop audit: both ESP8266 and ESP32 loops call `denyRemoteControl()` immediately before and after synchronous `post("poll")`; the returned body is discarded; no `post("coin")`, `clearPending()` or `applyRemoteConfig()` call exists in either loop. Pending pulse/nonce/target evidence remains preserved. This is source audit plus CI, not physical pulse acceptance.
- Known Hardware-owned provider candidate: PR #340 source/test `d1380acf80c0b631c5814d746dca36b2fad7a986` includes version-gated Mbed TLS 3 / PSA Crypto 4 SHA-256, initialization/digest-length failure guards and request-digest validation; actual ESP32 core 4.0.0 compile [#45747192648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747192648), job `139665996232`, PASS. This exact provider has not been ported to #354; request PHX-MASTER/PHX-RELEASE review before porting. Do not invent a different crypto path.

PR #354 remains OPEN / DRAFT / UNMERGED. PRs #239/#254/#283 remain OPEN / DRAFT / UNMERGED and untouched. The active candidate is deny-only; no production firmware source changed in this activation. Physical coin/relay/electrical acceptance, LittleFS power cuts, 150 controlled power cuts and 30-device/24-hour soak remain NOT TESTED. Protected signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff remain NOT ACCEPTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

**Next exact action:** PHX-QA updates its own controller parity and sequence assertions to match the intentionally deny-only candidate without reintroducing response parsing or pending disposition; PHX-CORE publishes the approved authenticated register/poll and event receipt/disposition contract; PHX-MASTER/PHX-RELEASE review the exact #340 Mbed TLS provider port. Only then should PHX-HARDWARE change firmware source and rerun exact-head Full.

## PHX-HARDWARE UTC08 — active-v0.6 provider/build and handover-freshness reconciliation

- Repository/PR: `BlazeDevStudio/BlazingSystems-Experiments`, [DRAFT #354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354), branch `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`, base `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Exact branch/source-test checkout at audit: `ec622923ef6b5dbcc386ecae70cc853725085561`. Source/provider correction `da4e89ed64a7b1fe5426468939d5ee7cf563bfc2`; provider lab `367e6c1b63f0cca1e01015bdb680920949f8cb46`; current clean-build workflow head includes `ec622923ef6b5dbcc386ecae70cc853725085561`.
- Focused deny-intake [#45779792234](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45779792234), job `139772179285`: PASS. Both ESP8266 and ESP32 source-extracted poll/remote-config labs pass; six unsafe mutation classes are rejected per the logged test contract. Logs explicitly report physical coin/relay and power-cut acceptance = 0.
- ESP32 core matrix [#45779792398](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45779792398): source-contract `139772180335`, Arduino core 3.3.13 `139772180661`, core 4.0.0 `139772180674`: PASS. The workflow restages identical packaged inputs twice from clean source staging, compares staged-tree hashes and application-image hashes, and compiles both supported cores. This is CI reproducibility evidence, not runtime crypto or physical acceptance.
- Native synthetic [#45779792145](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45779792145), job `139772178998`: FAIL at QA-owned `tests/v060_vendo_sequence_contract.py:20`, which still requires active `clearPending(true/false)` callsites. Ten preceding checks passed. The deny-only candidate intentionally preserves pending state and has no active disposition callsite; QA owns the assertion.
- Full BlazePwifi [#45779792293](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45779792293), validation job `139772357582`: FAIL at `tests/handover_gate.sh`. The gate identified `PROJECT_HANDOVER.md` last checkpoint `56a45583ab736442a66267966d025e675e2976de` and source changes in the ESP32 sketch and Mbed TLS lab after that checkpoint. Target/board and Android jobs completed successfully, but validation stopped at the handover gate; this is not Full PASS.
- This UTC08 commit is an append-only handover/ledger reconciliation after the source changes. The full existing `CHANGE_LEDGER.md` blob was fetched and retained before appending; no historical section was replaced. No production sketch, shared API, finance code, QA-owned test, release workflow or COE destination was changed in this documentation increment.
- Current #354 source already contains the version-gated Mbed TLS 3 / PSA Crypto 4 provider. The earlier UTC06 note saying that provider had not been ported is superseded by source commit `da4e89ed` and the exact-head core matrix above.
- Cross-role coordination: PHX-QA owns the native sequence assertion; PHX-CORE owns the authenticated register/poll and receipt/disposition producer contract; PHX-MASTER owns stack and integration-matrix reconciliation. Current Master `ROLE_ASSIGNMENTS.md` records #354 at `ec622923ef6b5dbcc386ecae70cc853725085561`, while its `INTEGRATION_MATRIX.md` still carries an older #354 tree pin `8d1023f986cc1b4d9aacebb90143bcfc903d7cc5`; request Master correction only.
- Status: SIMULATED / CI VERIFIED; physical coin/relay/electrical acceptance, LittleFS power-loss durability, 150 power cuts, 30-device/24-hour soak, protected signer/witness, financial migration and independent QA/release signoff remain NOT TESTED or NOT ACCEPTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

**Next exact action:** after this append-only handover commit, re-run/inspect Full CI at the new PR head; QA updates its own sequence contract; CORE publishes the approved response/receipt contract. Keep coin and relay denied until independent acceptance.


## PHX-HARDWARE UTC08 follow-up — post-refresh Full CI terminal result

- After the append-only handover/ledger refresh at `6a54ce6f7fcdc584cddb4ac5fe7602311fab5f3f`, exact PR run [#45782867810](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45782867810) proved the mandatory handover freshness gate and its fail-closed regression PASS. Full validation job `139782454950` then failed at step 14, **Controller protocol parity**.
- The failure is in QA-owned `experiment/openwrt/BlazePwifi/tests/controllers.sh`: it still requires the token `config_revision`. Source revalidation at PR head `6a54ce6f7fcdc584cddb4ac5fe7602311fab5f3f` confirms both ESP8266 and ESP32 sketches intentionally contain no `config_revision` parser/token because remote configuration is denied pending CORE's authenticated contract. The preceding controller grep tokens pass; do not add a dummy token or restore unsigned config parsing.
- All Full build jobs completed successfully: ESP8266, ESP32, Android and every listed OpenWrt target. The validation failure caused downstream simulation, update, signing, publication and candidate gates to skip. This is not Full PASS.
- Native synthetic [#45782867712](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45782867712), job `139782315303`, separately fails at QA-owned `tests/v060_vendo_sequence_contract.py:20` because it requires active `clearPending(true/false)` callsites; the deny-only candidate intentionally has none and retains pending evidence.
- Focused deny-intake [#45782867707](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45782867707), job `139782314563`, PASS. ESP32 provider matrix [#45782867878](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45782867878), source-contract `139782315794`, core 4.0.0 `139782316056`, core 3.3.13 `139782316163`, all PASS.
- The handover freshness failure from [#45779792293](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45779792293) is fixed; current Full failure is the QA-owned legacy controller parity check.
- Hardware requests PHX-QA to reconcile both tests against the deny-only contract, PHX-CORE to publish the authenticated register/poll + receipt/disposition contract, and PHX-MASTER to reconcile the stale #354 pin in `INTEGRATION_MATRIX.md`. Hardware did not edit any of those owners' files.

**Status:** focused and target CI VERIFIED; Full validation FAIL; native QA assertion FAIL; physical acceptance NOT TESTED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.


## PHX-HARDWARE UTC09 — shared C++ source extractor in output-enable lab

- **Task:** #177 / PR #354; Hardware-owned host-lab maintainability improvement only. The two production sketches and their GPIO behavior are unchanged by this follow-up.
- **Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`; source/test commit: [`87ef824d7d4dd88c712da1a690a3ebb30989ac86`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/87ef824d7d4dd88c712da1a690a3ebb30989ac86); PR #354 remains OPEN / DRAFT / UNMERGED.
- **Change:** `output_enable_sequence_lab.py` now imports the shared `firmware_source_extract.extract_function` instead of maintaining a second regex/brace-count extractor. A small fixture verifies that comment, quoted-string and C++ raw-string decoys cannot shadow the actual function definition. Existing active-high/active-low output ordering and unsafe-mutation checks remain intact.
- **Focused exact-source push:** [#45794249849](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794249849), job `139820705126`, PASS.
- **Focused exact-source PR:** [#45794256145](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794256145), job `139820725334`, PASS. Logs show `SOURCE_EXTRACTOR_PASS`, ESP8266 and ESP32 `OUTPUT_SEQUENCE_PASS`, unsafe-order mutation rejected on both boards, and 4/4 output-enable checks PASS.
- **Other exact-source checks:** ESP32 Mbed TLS matrix [#45794256223](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794256223), native synthetic [#45794256041](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794256041), and Full PR [#45794256126](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794256126) were still running at the initial handover update. Full push [#45794249945](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794249945) reached the mandatory handover-freshness gate before this append and failed there; it is not a source/test failure. Final-head reruns are required after this documentation update.
- **Evidence limits:** this is host/source-extracted SIMULATED / CI VERIFIED test tooling. Physical GPIO voltage, relay contact transient, coin acceptor, LittleFS power-loss, electrical recovery, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
- No CORE API, QA-owned tests, finance, receipt/disposition, signer, witness, COE destination, production device or physical firmware was changed.


## PHX-HARDWARE UTC09 terminal exact-head reconciliation — shared extractor lab

- **Role / task:** PHX-HARDWARE; #177 / DRAFT PR #354. Source/test commit `87ef824d7d4dd88c712da1a690a3ebb30989ac86`; the exact-head validation below was run on docs head `1d8edd339b87831921282524236ad5978d4c309e` before this terminal documentation-only commit.
- **Code change:** the Hardware-owned output-enable lab now uses the shared C/C++ function extractor and verifies comment, quoted-string and raw-string decoys are ignored. Production sketches and runtime behavior are unchanged in this follow-up.
- **Focused exact-head PR:** [#45794589576](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794589576), job `139821876411`, PASS. The log contains `SOURCE_EXTRACTOR_PASS`; both ESP8266 and ESP32 output sequences pass; the unsafe output-before-OFF mutation is rejected on both boards; 4/4 output-enable checks PASS.
- **ESP32 Mbed TLS matrix:** [#45794589884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794589884), terminal SUCCESS. Source-contract job `139822229406`, Arduino core 4.0.0 job `139822229989`, and Arduino core 3.3.13 job `139822230183` all PASS.
- **Native synthetic:** [#45794589513](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794589513), job `139821904434`, terminal FAILURE at QA-owned `tests/v060_vendo_sequence_contract.py:20`, which requires active `clearPending(true/false)` callsites. The deny-only candidate intentionally has no active pending-disposition callsite and preserves evidence. Hardware did not edit QA-owned tests.
- **Full BlazePwifi:** [#45794589544](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45794589544), terminal FAILURE at QA-owned Controller protocol parity / `tests/controllers.sh` legacy `config_revision` expectation. Mandatory handover freshness, HND-0700, CI-0701, form decoder, static, v0.3, admin, config and template checks passed. ESP8266, ESP32, all OpenWrt target jobs and Android passed. Downstream simulations, update bundle, candidate gate, signing and publication were skipped. This is not a Full PASS.
- **Safety:** candidate remains deny-only. No authenticated poll consumer, unsigned config application, active pending disposition, coin admission, relay admission, financial state or COE destination changed. Physical GPIO/relay/electrical behavior, coin acceptance, LittleFS power-loss, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
- **Next exact action:** PHX-QA replaces the two legacy deny-only-incompatible assertions with default-deny/no-callsite and pending-evidence-preservation assertions. PHX-CORE publishes the approved authenticated register/poll and receipt/disposition contract. PHX-MASTER refreshes its #354 head pin after this documentation commit.
