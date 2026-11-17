# PHX-MASTER — poll-response producer/consumer contract and exact-head CI audit

**Snapshot:** 2026-11-17T02:33:59Z  
**Role:** PHX-MASTER  
**Task:** #172 / #177 / #266 / #288 / #294 / #315 / #316  
**Scope:** coordination/phoenix/, architecture contracts and cross-repository migration provenance only  
**State:** BLOCKED / PRODUCTION NO-GO

## 1. Exact refs and ownership

| Ref | Exact SHA / state |
|---|---|
| Experiments default main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Experiments v0.6.0 audit-foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master branch / PR #288 before this audit | d047c49419c920a546ff9438f2fc9e708566f78a |
| COE default main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration draft #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

Issue #172 and cleanup issue #266 remain open. PR #288 remains open/draft, based on Experiments main. Root AGENTS.md blob is d8777e3b58efc41caa5aa3c969c932aee9103d5f. OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29 remains DRAFT_REVIEW_ONLY; PHX-MASTER has coordination/phoenix/ only. No migration route authorizes a copy or move.

## 2. Exact poll producer comparison

The poll action body was inspected separately from other signed actions in the same CGI file:

| Source/destination ref | cgi-bin/vendo Git blob | Poll action includes response_sig |
|---|---|---|
| Experiments main f4e8a891... | 2e3a1430d08cc6606429a042df3b5848f53c7267 | No |
| Experiments v0.5.3 development aad3aade... | a1c19180385e618c412b4af21c0e91c1f47da1dd | No |
| Experiments v0.6 audit-foundation 2fbd2475... | db58041c0575ad0a1101d99cb85403e03c8dcb22 | No |
| COE PR #26 candidate b382d233... | 0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e | Yes |

The COE candidate defines vendo_poll_sig and includes response_sig in its poll response. This is a derived implementation and a real source/destination behavior difference; it is not byte-identical migration evidence.

The candidate producer expression is structurally ordered as secret, poll, id, nonce, insert, target, expires, secret. The current hardware consumer computes the corresponding ordered expression from cfg.key, cfg.id, lastSentNonce, insert, target and expires. No shared golden vector was executed, and exact key/id/nonce binding plus canonical serialization still need owner verification. The candidate construction is a keyed SHA-256 expression, not standard HMAC; do not describe it as HMAC without an approved design change.

The root PisoWiFi LICENSE blob in Experiments main and COE #26 both equals 1ee55b94183417be977ca287cd7391f9a6f7e721. This is one bounded license identity check, not a complete dependency/license audit.

## 3. Exact HARDWARE consumer and CI

Current consolidated HARDWARE draft PR #315 is open/draft at b21d05822772e7c07299331d2a6a1670da2b077e.

- ESP8266 firmware blob: 226c068731666d20eb91a2544ecb8ef9f9c11432.
- ESP32 firmware blob: 54308cc5153c11889d107af1e15e560f39ebb327.
- Both acceptPollResponse implementations initialize signatureOk=false, require a nonempty cfg.key and response_sig, require top-level ok=true, reject targetless positive responses, and clear stale insert/target state on rejection.
- Focused run 43997886923, job 133754358681, completed SUCCESS. Its log explicitly reports poll-response 10/10 per board and strict root JSON 13/13 per board; quarantine, mount/output, boot recovery, pending-clear, pending write/readback and coin POST gates also passed in this source-extracted lab.
- Full run 43997886963 completed FAILURE at validation job 133754360411. Exact log: tests/controllers.sh extracts loop() but omits acceptPollResponse(), so generated ESP8266 and ESP32 harnesses fail with “acceptPollResponse was not declared in this scope”. ESP8266 and ESP32 compile jobs passed; Android and returned target-image jobs passed. Production sign/import/publish and candidate/simulation jobs were skipped.
- PR #316 remains open/draft at 888e6941e3a7a81641682c23d937f97d8117d2ea; its older full run 43972511250 has the same extractor failure. PR #315 is the reported consolidated stack. Master did not close #316 or edit firmware.

Evidence: [#315 focused run 43997886923](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43997886923), [#315 full run 43997886963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43997886963), [failing validation job](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43997886963/job/133754360411).

## 4. Master decision and owner actions

**MASTER DECISION:** keyless/bootstrap is never coin authority. An empty/unprovisioned key or unsigned positive response cannot authorize coin intake, active target or relay output. Setup/bootstrap may configure a device but must remain non-authorizing. This is a shared admission invariant, not a claim that current integration is complete.

- PHX-CORE: implement or propose the canonical signed poll producer on the owner branch; verify key provisioning, controller identity, request nonce, insert bit, target nonce, expiry and exact digest bytes with golden positive/negative vectors. Review whether the current keyed SHA-256 construction should be retained or replaced by a standard MAC; do not call it HMAC by assumption.
- PHX-HARDWARE: retain default-deny consumer behavior and target/freshness checks; do not add a keyless fallback. Durable rejected-event disposition remains separate and unresolved.
- PHX-QA: update the canonical controller source extractor to include acceptPollResponse; independently run the poll and stale-state matrices at exact #315 head b21d058..., including empty key, missing/bad signature, valid provisioned signature, targetless positive, expiry and both boards.
- COE integration owner: treat the signed poll producer in #26 as a derived candidate; reconcile it against the canonical owner source, exact key/nonce binding, licenses, tests and rollback before any move. Do not overwrite the candidate with an unsigned source blob.

## 5. Current role CI observations

| Role / PR | Exact head | Observed workflow result |
|---|---|---|
| MASTER #288 | d047c49419c920a546ff9438f2fc9e708566f78a | No PR-triggered workflow runs |
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | 42698139210 success |
| RENTAL #240 / #287 / #289 | a7d113fb8ae3f0c5e838e64d31cae7a154e37b56; a4fffd01c8fb1818c32a53522e0590c1dc8a77cd; 68928774d0d7cf65adb26bc6b54199a3159d066c | 40910311141/40910311159; 43754089203; 43653329235/43653329229 success |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | 42462978704 success |
| HARDWARE #314 / #315 / #316 | 556adc20ef0cfd355089aff3b979c0169af79bdd; b21d05822772e7c07299331d2a6a1670da2b077e; 888e6941e3a7a81641682c23d937f97d8117d2ea | #314 43782088731/43782088748 success; #315 focused success, full failure; #316 focused success, full failure |
| QA #267 / #292 / #279 | ff5367990c2d27b8ebbb822ee208251af0c890e2; 75a3f66d9563e38a0a48b9cf487b0b057a91ea96; 8f476ef05893193325ef3d1f65a35e144ae7a568 | #267 41452247439 success; #292/#279 no PR-triggered runs |
| RELEASE #242 / #291 | 734b89d9e7792247e8376335c3f3685500ab3f89; 2c4edff231d9b2819415086825530d80b8801307 | 40882814472 and 43744993487 success |

COE role PRs re-read: #27 009f70cc2c2775039a5fb072c9d4fdedee76cfc7 (43079646393/43079646264 success); #29 d0830332dee8a1844a85606150681b41d91fe796 (43653906676/43653906675 success); #31 f3f995c91e38b5c5908bf8910056523015c8f0fd (44002215761/44002215760 success); #32 29b6fe08b10688182d981a66745f482758bd6630 (43653540607 success). COE #26 has five queued workflows: 43096752609, 43096752632, 43096752800, 43096752563 and 43096752557.

## 6. Master audit execution and limits

Seven read-only structural assertions were executed against freshly fetched GitHub file contents: unsigned poll action on main/v0.5.3/v0.6, signed poll action on COE #26, default-deny key requirement on both hardware consumers, and identical root LICENSE blob. Result: 7/7 PASS. These are Master audit assertions, not the Project Phoenix Python suite, not the canonical controller lab, and not CI.

The full Master Python suite was not executed; Master PR #288 has no PR-triggered workflow runs.

The exact private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not retrievable: no Google Drive connector/read action was exposed, and exact-name Library search did not return v11. No older Library registry was substituted; no private contents or identifiers were published.

No subsystem source branch was modified. No merge, release, firmware flash, physical test, secret provisioning, live payment operation or migration occurred.

## 7. Production gate

Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. **PRODUCTION NO-GO.**

Next Master activation: refresh exact refs and issue checkpoints; verify the PHX-CORE signed producer and PHX-QA extractor changes when published; rerun the same field-order/golden-vector audit at their exact SHAs.
