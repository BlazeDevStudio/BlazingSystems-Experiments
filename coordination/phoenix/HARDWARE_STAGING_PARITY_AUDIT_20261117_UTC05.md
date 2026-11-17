# PHX-MASTER — Hardware staging parity audit (2026-11-17 UTC05)

**Disposition: BLOCKED / DRAFT / PRODUCTION NO-GO.** This is a source-grounded coordination and migration-provenance audit. It changes no subsystem firmware, tests, financial code, release workflow, destination tree, or private registry.

## 1. Exact repository and branch pins

| Ref | Exact SHA |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development (blazepwifi-v0.5.3-development) | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Experiments v0.6 audit-foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master PR #288 branch before this commit | 381827401d1733a716675e2e33932e472339d8ce |
| HARDWARE PR #315 source branch | 75dc5f0b888f16e2c85e4321f62df4685639ad33 |
| HARDWARE PR #316 separate draft | 888e6941e3a7a81641682c23d937f97d8117d2ea |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 remains open/draft on phoenix/master-coordination. Its base is Experiments main. COE #26 remains open/draft; its target main is still structure-only. OWNERSHIP_ROUTES.json remains DRAFT_REVIEW_ONLY, with source_ref pinned to Experiments main. The newer owner-controlled HARDWARE #315 branch is a separate source candidate and must not be silently conflated with that main pin.

## 2. Exact firmware blob and mode comparison

| Board | HARDWARE #315 source blob | COE #26 destination blob | Mode |
|---|---|---|---|
| ESP32 | 38a2d239eed6af876d421f9f908bbb62b3ae27e1 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | 100644 / 100644 |
| ESP8266 | f59e624ae2da04bddc70ddc2809bf6d8ff486aac | c8be98f72596681e36a3ad1f8939bf8046c96887 | 100644 / 100644 |

Both destination blobs differ from the current owner source. The source sketches are 931 and 1001 lines; the COE candidates are 410 and 489 lines. This is not a byte-identical migration. Do not overwrite either side or propose a blind folder copy.

## 3. P0 finding A — remote configuration remains callable in COE #26

### Current owner source: HARDWARE #315

- ESP32 source: applyRemoteConfig() has exactly one occurrence (its definition at line 464); the comment at lines 461–463 explicitly keeps it dormant. connectSta() at lines 862–874 verifies only the register tuple and does not apply the returned configuration. acceptPollResponse() initializes signatureOk=false and keeps poll admission separate from configuration.
- ESP8266 source: applyRemoteConfig() has exactly one occurrence (definition at line 336); the helper is explicitly dormant at lines 333–335. connectSta() at lines 734–746 keeps register tuple authentication fail-closed and does not apply the response. acceptPollResponse() also defaults signatureOk=false and does not authorize configuration.

### COE #26 destination candidate

- ESP32: applyRemoteConfig() occurs three times (definition plus register and poll call sites). Register and poll each initialize bool sigOk=true. Register can call the mutator at lines 319–331; poll can call it at lines 352–367.
- ESP8266: the same three occurrences and two bool sigOk=true defaults remain. Register call site is at lines 352–364; poll call site is at lines 408–423.

A positive ok:true response with an empty key can therefore bypass conditional signature verification and reach the destination configuration mutator. A register-tuple signature also does not bind the returned configuration fields. The owner-side #315 correction has not reached COE #26.

**Disposition:** keep response-driven remote configuration disabled. Do not reuse poll/register admission signatures as configuration authorization. A future config envelope needs a separate domain, canonical serialization, controller identity, nonce, revision/freshness, every behavior-changing field, strict bounds, atomic persistence, and independent positive/negative vectors from PHX-CORE and PHX-QA.

## 4. P0 finding B — COE #26 can delete unpaid-coin quarantine evidence

### Current owner source: HARDWARE #315

- ESP32 POST /quarantine/clear handler at lines 827–832 always returns HTTP 403. No LittleFS.remove("/quarantine.log") call exists. Setup-AP request checks are present for the quarantine read and configuration routes.
- ESP8266 POST /quarantine/clear handler at lines 699–704 always returns HTTP 403. No LittleFS.remove("/quarantine.log") call exists. Setup-AP request checks are present for quarantine read and save routes.

### COE #26 destination candidate

- ESP32 POST /quarantine/clear at lines 293–296 calls LittleFS.remove("/quarantine.log") and returns HTTP 200.
- ESP8266 POST /quarantine/clear at lines 326–329 does the same.
- The destination handlers do not call requireSetupApRequest(); the candidate therefore has no explicit AP-origin check at these sensitive route handlers.

This is a source-confirmed difference in preservation of unpaid-coin reconciliation evidence. The destination route must not be treated as setup-AP-only merely because the README describes it that way. A hostile POST can reach a handler that deletes the log and reports success; the exact network exposure should be independently reproduced by PHX-QA on a disposable host harness and then on authorized noncustomer hardware.

**Disposition:** preserve the source-side 403/no-delete behavior. Do not migrate the destination route or permit a clear operation until a separately approved authenticated reconciliation and durable-receipt contract exists. No deletion or physical request was performed in this audit.

## 5. Documentation, crypto label, tests and licensing

- COE Hardware README blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb describes the response construction as HMAC/SHA256 and says operators can clear quarantine via POST. The source code uses a hexDigest(key | action | id | nonce | fields | key) construction; that is not a standard HMAC primitive. Do not describe it as HMAC without a standard HMAC implementation or vetted equivalence. The README also conflicts with the current owner-side 403/no-delete rule.
- Current HARDWARE #315 contains source-extracted register_config_failclosed_lab.py (blob ea413137ab18e153ac4ee1625c28f16ce35101ab; seven cases per board) and poll_response_failclosed_lab.py (blob 86e0581de8e426987508e47c703b8309c47cd2eb; eleven poll cases per board).
- COE #26 has only Hardware/tests/test_firmware_hardening.sh (blob f921c56cecc19cab1989507b9b4ade1f45dac54e, mode 100755). It checks strings, route presence, brace balance and a digest-format simulation; it does not test keyless denial, absence of response-driven applyRemoteConfig calls, HTTP 403/no-delete, or setup-AP-origin enforcement. The source-extracted regression identities have not been imported into COE.
- Experiments source contains experiment/openwrt/BlazePwifi/LICENSE (MIT, blob 1ee55b94183417be977ca287cd7391f9a6f7e721) and repository NOTICE.md. COE #26 contains Pisowifi/LICENSE and vendor notices, but no root LICENSE/NOTICE or Hardware/LICENSE/NOTICE. Hardware license/notice scope is unresolved; this is a provenance review item, not a finding of infringement.

## 6. CI and role evidence at exact heads

- HARDWARE #315 focused [run 44013351048](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44013351048), job 133805326507: completed success. It reports register-config denial 7/7 per board, poll/config 11/11 per board, strict JSON 13/13 per board, debounce 8/8, poll-window 8/8, quarantine 34/34, mount/output 14/14, boot recovery 32/32, pending-clear 22/22, write/readback 44/44, and coin POST gate 18/18. These are source-extracted host/fake-filesystem checks, not physical acceptance.
- HARDWARE #315 full [run 44013351035](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44013351035), validation job 133805413831: completed failure. The raw log shows the QA-owned extractor does not include acceptPollResponse(), producing an undeclared-function error in both generated board harnesses. ESP32 and ESP8266 compilation jobs passed; signing/publishing jobs were skipped.
- HARDWARE #316 focused [run 43972511337](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511337) succeeded; full [run 43972511250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511250) failed at the same extractor. The current #315 handover says #316 behavior was consolidated onto #315; #316 remains open/draft and must not be merged independently.
- COE #26 returned five queued workflows: [43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632), [43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557). None had a completed result in this read.
- Master #288 has no PR-triggered workflow runs at its inspected head.

Other exact-head role observations: CORE #252 run 42698139210 success; RENTAL #240 runs 40910311141/40910311159 success, #289 runs 43653329235/43653329229 success, #287 run 43754089203 success; PISONET #255 run 42462978704 success; HARDWARE #283 run 43634101437 success; QA #267 run 41452247439 success, #292 and #279 returned no runs; RELEASE #242 run 40882814472 success and #291 run 43744993487 success. These are isolated role checks, not integrated acceptance.

## 7. Executed audit checks and limits

A bounded source-readback script executed 24/24 assertions against the exact GitHub file contents: source-only dormant config helpers, source 403/no-delete, destination register/poll config call sites, keyless true defaults, destination quarantine deletion/HTTP 200, missing setup-AP guard, and the destination test/documentation gaps. These are static source-readback assertions, **not** Python unit tests, compiler runs, GitHub Actions, or hardware tests.

A local GitHub clone/read attempt failed because github.com DNS could not be resolved. The complete Master Python suite was therefore NOT RUN. The exact private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not accessible through the exposed connectors or Library search; no older registry was substituted, no Drive artifact was created, and no private IDs or contents were published.

## 8. Owner-routed next actions

1. PHX-HARDWARE: keep #315 as the single consolidated owner stack; preserve default-deny configuration and quarantine evidence. Do not merge #316 independently.
2. PHX-QA: repair the canonical controller extractor to include acceptPollResponse(); independently reproduce both register and poll keyless/config-injection denial plus quarantine-clear hostile POST, positive read/export, and AP/station-origin cases at exact source and proposed destination SHAs.
3. PHX-CORE: define and review the canonical poll producer/consumer vectors and separate configuration authorization domain; do not call the custom keyed SHA construction HMAC without an approved standard construction.
4. COE integration owner: keep #26 draft; reconcile exact blobs, source test imports, README claims, license/notice scope and CI before any per-file transplant. Preserve the original source history.
5. Registry custodian: restore authorized access to the exact private v11 registry and newer corrections; do not publish its contents.

No subsystem source branch, destination file, payment system, secret, release, or hardware was changed. No merge, flash, physical test, or migration was performed. Production remains NO-GO pending independent protected signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak, and owner-authorized release gates.
