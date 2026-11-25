# PHX-MASTER UTC20 — active v0.6 poll-response contract audit, HARDWARE #353 stack drift, and COE #26 provenance

**Observed UTC:** 2026-11-25T20:54:03Z  
**Role:** PHX-MASTER — master coordination, architecture/interface contracts, cross-repository migration provenance, and integration sequencing.  
**Execution:** strict NO CODEX.  
**Starting Master branch:** \`phoenix/master-coordination@5ce9361a2e23f21af99ef54f5e33066ac37fe024\`.  
**Disposition:** P0 interface blocker recorded; #353 stack remains owner-blocked; COE #26 remains FROZEN; production remains NO-GO.

## 1. Live references re-read

| Ref | Exact current identity |
|---|---|
| Experiments default branch | \`main@6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5\` |
| Experiments active v0.6 development | \`blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859\` |
| Experiments legacy v0.5.3 development | \`blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5\` |
| Master branch / PR #288 starting head | \`5ce9361a2e23f21af99ef54f5e33066ac37fe024\` |
| COE default branch | \`main@a6513ab4412b4c014eee2863e45cbe32d06cb243\` |
| COE integration draft PR #26 | \`b382d233ff06c8791b1028bed3c617cc7b670d12\` |
| Routing manifest | \`OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29\`, 11 routes, \`DRAFT_REVIEW_ONLY\`, PHX-MASTER destination null |

Control plane #172 and cleanup #266 were re-read. #266 remains OPEN / 0-of-7. PR #288 remains OPEN / DRAFT / UNMERGED; its description was stale at the preceding UTC19 starting head and is refreshed by this activation. The Master branch was 581 ahead / 1 behind main at the start; no rebase, merge, or main synchronization was performed.

## 2. P0 architecture finding — current v0.6 poll response is not authenticated

Exact active development source:
- ESP32 sketch blob: \`29f1125d52ff474a0d028ad41f7af201be1f0f9d\`
- ESP8266 sketch blob: \`12c4bb82b6fddafe813674a0b5f692c1d3634073\`
- CGI \`vendo\` blob: \`db58041c0575ad0a1101d99cb85403e03c8dcb22\`

Source inspection found:

1. CGI \`register|ping\` returns \`ok\`, \`server_time\`, and nested \`controller\`, without \`response_sig\`.
2. CGI \`poll\` returns \`ok\`, \`insert\`, \`target_nonce\`, \`expires\`, and nested \`controller\`, without \`response_sig\`.
3. The same CGI emits \`response_sig\` for member snapshot/authentication/mutation endpoints; those signatures are not a poll-response contract.
4. Neither sketch contains a \`response_sig\` token. \`signedBody()\` signs the request, but \`post()\` returns the response body without authenticating it.
5. Both poll loops read \`insert\` and \`target_nonce\` from that body and call \`applyRemoteConfig()\`.
6. Both \`applyRemoteConfig()\` implementations default top-level \`enabled\`, \`coin_enabled\`, \`relay_enabled\`, and \`led_enabled\` to 1. The CGI returns controller state nested under \`controller\`, not those top-level fields. The first missing \`config_revision\` is not rejected because the early-return guard requires a nonzero prior revision.
7. \`applyOutputs()\` enables the relay according to \`controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady\`, gated by \`relayEnabled\`. An unauthenticated response therefore influences insert/target/configuration and output decisions.

This is a source-derived interface/actuation risk, not a dynamic exploit result. No unauthorized financial credit is claimed; server-side coin-request validation was not audited in this check. The current v0.6 implementation is **not verified deny-only**.

The inherited Full CI failure \`Missing poll signature check\` is a valid safety gate and must not be removed or relaxed. CORE must approve the response contract and golden vectors; HARDWARE must implement fail-closed consumption before any insert/target/config/output mutation; QA must independently test both boards. Do not synthesize a signature or reuse member endpoint signatures.

## 3. HARDWARE #353 exact-head and ancestry reconciliation

Current PR #353:
- Branch: \`phoenix/hw-board-conditional-isr-selector-20261125-utc17\`
- Current docs/PR HEAD: \`dc9cf634248ecc23f51f1477bd1769d63d3fe5ea\`
- Exact source/test HEAD: \`4f361e032c30faa368105775e3646c570f9760a8\`
- Captured base: \`6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec\`
- Parent PR #352 live HEAD: \`0e984e267b3a8fb10c314800d1a7f120806354b7\`

GitHub compare confirms the live #352 parent is 11 commits ahead / 0 behind the #353 captured base, with 13 changed paths. The #353 PR body still reports older docs/source pins \`e2ac0697\` / \`2c9581e9\`; HARDWARE owns refreshing its PR description and handover. No rebase, retarget, force-push, or source-branch write was performed by Master.

Exact #353 source/test CI:
- Expected RED: Quarantine [#45698045060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698045060) and Relay [#45698045073](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698045073).
- Focused GREEN: Quarantine [#45698465435](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698465435) and Relay [#45698465398](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698465398).
- Full [#45698465506](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698465506): FAIL at \`Missing poll signature check\`; 13 target/platform builds and Android pass, downstream simulation/bundle/candidate/signing/publication stages skip.
- Current docs-head Full [#45699196969](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45699196969): FAIL at \`Controller protocol parity\`.

The #353 change extracts the board-conditioned ISR selector into a host-lab module; it does not change production sketches. Focused host CI is simulated evidence only.

## 4. COE #26 exact recursive-tree, test, and license comparison

Complete, non-truncated recursive trees were read at #353 docs head and COE #26:

| Measure | Experiments #353 | COE #26 |
|---|---:|---:|
| Tree entries | 2560 | 286 |
| Blobs | 1981 | 207 |
| ESP32 subtree blobs | 16 | 1 |
| ESP8266 subtree blobs | 61 | 1 |
| Board-local Python helpers | 65 | 0 |
| Mapped test files | 47 | 19 |

Test identity at exact trees: 1 exact same-path blob+mode, 3 divergent same-path, 43 source-only, 15 destination-only. Similar names are not treated as test equivalence.

Firmware sketch blobs:
- ESP32 source \`1412cf57b70c6ee3061da9831b8d9abf6d58d94e\` vs destination \`3cc7ec54b476943dc04a8d1af5e2df5fe054e422\`.
- ESP8266 source \`b99f1f21d8ad1e6df0e403b2b34507f97bd90c16\` vs destination \`c8be98f72596681e36a3ad1f8939bf8046c96887\`.

Source root NOTICE and Tabler LICENSE have no destination counterpart. Product LICENSE, QRCode LICENSE, and TailAdmin LICENSE/NOTICE counterparts are present. COE #26 still lacks Hardware-specific SOURCE_INTAKE and MIGRATION_MAP. The existing PisoWiFi intake is not Hardware provenance.

**Decision:** COE #26 remains FROZEN. No staging, copy, move, overwrite, cherry-pick, or destination write. Five queued workflows / zero jobs remain non-evidence of CI acceptance.

## 5. Other role PR / exact-head CI reconciliation

| Owner | Current head | Current evidence / disposition |
|---|---|---|
| CORE #252 | \`c82705f2\` | Build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) and focused [#42698124709](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698124709) PASS; scoped / older, not financial acceptance. CORE source remains reserved to its separate continuation. |
| RENTAL #328 | \`10fc200b\` | APK/API/auth [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340), [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551) PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL: CORE handover freshness and missing \`mbedtls/sha256.h\`. |
| PISONET #255 | \`d01fd164\` | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM not invoked. |
| HARDWARE #349 | \`2a5c997a\` | Quarantine/Relay PASS; Full [#45603969181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969181) FAIL at poll-signature assertion. |
| HARDWARE #352 | docs \`0e984e26\`, source/test \`8eab8260\` | Four focused workflows PASS; Full [#45683122413](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45683122413) FAIL at Missing poll signature check. |
| HARDWARE #353 | docs \`dc9cf634\`, source/test \`4f361e03\` | Two focused workflows PASS; source Full #45698465506 and docs-head Full #45699196969 fail at poll protocol validation. Stack is stale by 11 parent commits. |
| QA #290 | \`5c29d159\` | Synthetic Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM not invoked. |
| QA #292 | \`75a3f66d\` | No PR-triggered runs. |
| RELEASE #291 | \`9b928c9e\` | Windows [#45669599214](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599214) and Full [#45669599438](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599438) FAIL at CORE CURRENT_STATE freshness; ESP32 compatibility [#45669599322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599322) PASS. |
| COE RELEASE #35 | docs \`ac343dc4\`, source/test \`10fa6ff1\` | Shared [#45694876586](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45694876586): 232 PASS / 2 skips then 10/10 ULA profiles fail closed; sandbox [#45694876614](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45694876614): 40/40 preflight then Bubblewrap unavailable / exit 125; case guard [#45694876828](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45694876828) PASS. |
| COE CORE #45 | \`9d76a134\` | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; focused only. |
| COE INTERCON #49 | \`aeb8ff11\` | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL: missing \`mbedtls/sha256.h\`. |
| COE #26 | \`b382d233\` | Five workflows queued / zero jobs; FROZEN. |

## 6. Storage / registry and instructions

Experiments AGENTS.md, README_FIRST, COMMUNICATION_PROTOCOL, the owner Cloud Artifact Policy, and Cloud Storage Recovery Handover were read. The policy requires the canonical private registry and sync ledger before mirror operations and forbids publishing private IDs/content.

The exact private Drive \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` and newer corrections were **NOT RECOVERED**. No Google Drive connector is exposed in this runtime; Library search found only a later checkpoint that references the canonical registry, not the registry itself. No older snapshot was substituted and no private registry content was written to GitHub. COE has no root \`AGENTS.md\` at main (404).

## 7. Master execution / test boundary

- Master-only changes: architecture contract, its documentation regression test, role/CI table, integration matrix, routing, index, audit summary, and this report.
- No CORE/RENTAL/PISONET/HARDWARE/QA/RELEASE source branch or COE destination changed.
- Exact tree/blob/test/license comparisons and source text inspections were executed through GitHub reads.
- Coordinator-side JavaScript assertions are recorded separately; the repository Python unittest suite was **NOT RUN** because there is no authenticated local checkout and container DNS could not resolve GitHub.
- No Master GitHub Actions run is claimed. No native COM, physical hardware, power-cut, soak, financial migration, signing, release, or payment-system test was executed.

## 8. Next exact owner actions

1. **CORE:** approve the response contract and golden vectors; publish canonical CURRENT_STATE / PROJECT_HANDOVER and freshness handover.
2. **HARDWARE:** fail closed before applying unsigned poll/register response fields; refresh #353's PR body and reconcile its 11-commit stale parent ancestry with #352.
3. **QA:** independently validate both-board negative cases and preserve the Full poll-authentication gate.
4. **RELEASE:** retain ULA and Bubblewrap blockers; rerun only after authorized prerequisites are present.
5. **COE integration owner:** complete Hardware per-file source/destination blob, mode, license/NOTICE, test identity and CI provenance before any staging review.
6. **Registry custodian:** restore authorized access to canonical private v11 and newer corrections.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates have independently verified evidence.
