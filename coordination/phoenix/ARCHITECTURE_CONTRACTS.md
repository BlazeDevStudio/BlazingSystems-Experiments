## PHX-MASTER UTC23 final contract review — Hardware #367 head 778220aa (2026-11-27T23:56Z)

The latest #367 Full failure at `tests/controllers.sh:21` is a QA assertion requiring the literal `config_revision` token. The deny-only candidate intentionally removes that unauthenticated controller field. QA must replace token-presence testing with source-linked deny-only vectors; HARDWARE must not restore the field to satisfy the stale assertion.

The #367 source/test matrix rejects 10/10 injected alias mutations per board, but its regex scan does not prove absence of `reinterpret_cast`, C-style casts, opaque alias returns, arbitrary memory corruption or electrical faults. Treat it as bounded source regression evidence, not complete C++ alias proof or physical acceptance. CORE still owns authenticated controller receipt/disposition; HARDWARE owns firmware; QA owns independent vectors.

---

## PHX-MASTER UTC23 follow-up — scope of deny-latch source-contract evidence (2026-11-27T23:52Z)

HARDWARE #367 source/test SHA `1922dcba` rejects 10/10 injected alias forms per board: address/reference wrappers, `decltype(auto)`, `std::move`, `std::forward`, `static_cast` and `const_cast`; logical-AND and comment/string decoys remain accepted. This is a bounded regex/source scan, not C++ AST/dataflow proof. `reinterpret_cast`, C-style casts, opaque helper returns, memory corruption and electrical faults are outside the demonstrated matrix. Do not describe it as complete alias-proof or physical acceptance.

Current #367 head `f7abed43` has Focused PASS and Mbed 3/3 PASS; Full at that head is CANCELLED. Latest terminal docs-head Full `4a78354c` fails the QA-owned `config_revision` assertion. QA owns parity semantics; HARDWARE owns firmware/handover; CORE owns authenticated controller receipt/disposition. No trust contract or production gate changed.

---

## PHX-MASTER UTC23 — controller trust boundary and pulse-loss contract (2026-11-27T23:38Z)

- P0 #177 remains OPEN. Active v0.6 ESP8266 blob `12c4bb82` calls synchronous poll at line 354 before coin sample at 357; ESP32 blob `29f1125d` polls at 314 before sample at 318. Both retain a 3,500 ms timeout. A host reproduction is not physical pulse/relay acceptance.
- Current main CGI blob `2e3a1430`: controller `register|ping` and `poll` response blocks lack `response_sig`; later member endpoint signatures do not authenticate controller poll/disposition.
- HARDWARE #367 deny-only candidate intentionally omits `config_revision`; QA's shared controller test still requires the token. Resolve by changing QA assertion semantics to source-linked deny-only vectors, not by restoring untrusted controller config.
- CORE owns authenticated controller identity/poll/receipt/disposition schema; HARDWARE owns firmware and relay; QA owns independent vectors. Master owns only cross-role contract coordination. No shared API/schema change is approved by this checkpoint.

---

## PHX-MASTER UTC21 — live routing, registry, and automation hold (2026-11-27T21:42Z)

- OWNERSHIP_ROUTES.json remains DRAFT_REVIEW_ONLY with 11 routes and PHX-MASTER target null. No owner or route changed.
- COE #26 branch/head is integration/ecosystem-nonproprietary-candidate-20261111@b382d233; COE main is a6513ab4412b4c014eee2863e45cbe32d06cb243. The intake still names historical destination feature/pisowifi-cleanup-stabilization. Keep all routes review-only; do not stage or copy.
- Exact Library title search did not find canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json or newer corrections. Only v3-v7 registry snapshots, October 26 manifest/ledger and a November 9 checkpoint reference were surfaced. No Google Drive connector is exposed; do not substitute older records or publish private IDs/content.
- Automation inventory: 17 tasks; active Blaze Hourly Production Development is PHX-HARDWARE. No exact-title Blaze Production Continuation entry surfaced. CORE remains untouched; no competing CORE worker or automation was created/modified.
- Repository admin must expose authorized Drive access and a non-Codex Master checkout/test path.

---

## PHX-MASTER UTC20 — deny-only candidate semantics vs stale config_revision parity assertion (2026-11-27T20:39Z)

The exact source comparison corrects the previous broad description of the Full CI failure.

### Source identities

| Source ref | ESP8266 blob | ESP32 blob | config_revision |
|---|---|---|---|
| Experiments main 6be5d19b | bfb94920eb0a189ca01d52e5443954fa133f5423 | 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0 | Present (ESP8266 line 209; ESP32 line 168) |
| Active v0.6 2fbd2475 | 12c4bb82b6fddafe813674a0b5f692c1d3634073 | 29f1125d52ff474a0d028ad41f7af201be1f0f9d | Present (ESP8266 line 238; ESP32 line 201) |
| HARDWARE #354 candidate fc842342 | b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9 | 3edbe38da543ef118b287f3e04c1601692cfa99f | Absent on both |
| HARDWARE #366 candidate 07fef4e8 | 7527dbff41b7f21bdc3d3ed9ee3db1c0d21eb07b | a673e323e1c160cbfe03949d13a9e01b47386596 | Absent on both |

The #366 stack is 228 commits ahead / 0 behind active v0.6, with merge base 2fbd2475e9f54878c316fa7cea2f228386b0e859. The stack changes both sketches to keep controller register/poll responses outside the trusted configuration path and discard the poll response pending an approved authenticated contract. This is a fail-closed candidate behavior, not evidence that the field disappeared from current main or the active-v0.6 base.

### Why Full CI fails

The shared tests/controllers.sh blob is 53a7af25fdee9a650e10e870c4204e0fb43239c6. Its line 21 still runs grep -q 'config_revision' against both sketches. Exact Full runs #45864684497 (#354) and #46059524022 (#366) fail Controller protocol parity at that assertion. The candidate sketches intentionally omit the field. The PR #366 body calls this an inherited current-main/v0.6 mismatch; the exact blobs show the more precise cause is an unchanged QA assertion against the deny-only candidate stack.

Do not add a decoy config_revision string, restore untrusted remote config consumption, or weaken default-deny. PHX-QA owns a source-linked assertion that proves the candidate rejects/discards unsigned controller fields and preserves relay/coin admission denial. PHX-CORE owns the canonical authenticated register/poll/receipt/disposition contract and golden vectors. PHX-HARDWARE owns candidate firmware and host labs. PHX-MASTER owns only this cross-role contract record.

### P0 boundary remains

The active development branch blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859 still performs synchronous post("poll") before the first digitalRead(runCoinPin): ESP8266 lines 354→357; ESP32 lines 314→318. The 3,500 ms timeout remains. Issue #177 is OPEN; its embedded source pin 9df0a7e7 is stale.

The separate #354 candidate remains OPEN / DRAFT / UNMERGED. Its Full run #45864684497 fails Controller parity; Native run #45864684295 fails PAY-0745. Host CI and source inspection do not prove physical coin-acceptor relay-off polarity, pulse retention, durable flash recovery, 150 power cuts or 30-device/24-hour soak.

Current main CGI producer blob 2e3a1430d08cc6606429a042df3b5848f53c7267 still has no controller response_sig in register|ping or poll response blocks; member endpoint signatures do not authenticate controller poll/disposition. Keep controller admission deny-only until CORE contract and independent QA review are complete.

---

## PHX-MASTER UTC19 — poll transport outcomes do not clear P0 or authorize coin admission

HARDWARE #365 is a test-harness-only child of #364. Its source/test SHA is `fcd5d7df210c8521f9c8fcc1019c8db8bdaf7eb0`; evidence docs head `6e5e126199368cbe78f9d46dd6c702c883cfa5cb`; current PR head `e65b0b895af9c3fc5e5632f704cb67b347e69725`. It adds five transport outcomes × four relay/LED polarity combinations (20 cases per board / 40 total): immediate begin failure, empty timeout, malformed body, server-error body and untrusted positive `insert=true`. The same host harness also models six blocking-poll pulse windows × four polarity combinations (24 cases per board / 48 total; `accepted=0`). The transient response-consumption/re-enable mutation is rejected on both boards. No production ESP sketch or CORE API changed.

Exact current-head CI: focused [#46056656161 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056656161); Mbed [#46056656203 PASS, 3/3](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056656203); Full [#46056656151 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056656151) at `Controller protocol parity`; 13 jobs skipped. This is host/CI evidence only, not physical acceptor retention.

P0 #177 remains OPEN. Its embedded source pin `9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed` is stale relative to live active v0.6 branch `2fbd2475e9f54878c316fa7cea2f228386b0e859`:
- ESP8266 blob `12c4bb82b6fddafe813674a0b5f692c1d3634073`: synchronous `post("poll")` at line 354 precedes first `digitalRead(runCoinPin)` at line 357.
- ESP32 blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d`: synchronous `post("poll")` at line 314 precedes first `digitalRead(runCoinPin)` at line 318.
- The blocking poll is configured for 3,500 ms. Candidate #365 does not alter the active v0.6 branch and does not resolve this pulse-loss race.

Current main CGI producer `vendo` blob `2e3a1430d08cc6606429a042df3b5848f53c7267`: `register|ping` and `poll` response blocks (lines 63–86) do not include controller `response_sig`; later `response_sig` fields belong to member endpoints and do not authenticate controller poll/disposition. The current consumer also does not verify a controller poll response signature.

**Contract boundary:** CORE owns authenticated register/poll, receipt identity and disposition semantics; HARDWARE owns firmware intake/relay implementation; QA owns independent golden-vector and source-linked regression review; MASTER owns only cross-role contract coordination. Keep coin admission and relay output deny-only until CORE publishes the contract and QA independently verifies it. Do not add a decoy `config_revision` or `response_sig` token, weaken default-deny, or treat #365 as a P0 fix.

---

## PHX-MASTER UTC17 — observed controller contract divergence (no schema change authorized)

Current main `6be5d19b` includes `config_revision` in ESP8266/ESP32 poll handling, but active v0.6 `2fbd2475` does not. HARDWARE #364 Full CI fails at QA-owned `tests/controllers.sh:21` on this exact branch-parity difference. Do not resolve by adding a decoy field or weakening the assertion; CORE/HARDWARE must establish the authoritative source/base and QA must independently validate the approved semantics.

Current main CGI `vendo` blob `2e3a1430...` has controller `register|ping` and `poll` blocks without `response_sig`; later signatures belong to member endpoints. They do not authenticate controller poll or coin disposition. CORE owns the canonical authenticated event/response contract and golden vectors; HARDWARE owns firmware implementation; QA owns independent source-linked validation. Until that contract is approved and tested, preserve deny-only behavior.

The active v0.6 loop still performs synchronous 3,500 ms poll before first coin sampling on both ESP boards (ESP8266 354→357; ESP32 314→318). This remains P0 #177; no production admission is implied by host-lab CI.

---

## PHX-MASTER UTC14 — active v0.6 poll-order and P0 source-pin reconciliation

Live branch `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` was re-read. Issue #177 remains OPEN, but its body still pins `9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed`; treat that embedded source pin as stale until the issue owner refreshes it.

- ESP8266 source blob `12c4bb82b6fddafe813674a0b5f692c1d3634073`: synchronous `post("poll")` precedes first `digitalRead(runCoinPin)`; 3,500 ms timeout remains.
- ESP32 source blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d`: synchronous `post("poll")` precedes first `digitalRead(runCoinPin)`; 3,500 ms timeout remains.

Preserve the existing interface boundary: untrusted/missing poll authentication cannot enable coin admission; pending evidence is not cleared on ambiguous response or failed durable commit; positive disposition requires CORE-owned authenticated receipt/sequence authority and durable readback. HARDWARE owns firmware intake/relay behavior, CORE owns receipt/authentication and financial state, QA owns independent semantic regression, and MASTER owns only the cross-role contract. The #361 `config_revision` literal failure is QA-owned test semantics; do not add a decoy firmware token or weaken default-deny.

No interface schema or ownership route changed. Physical GPIO/relay/coin acceptance, independent witness and crash-atomic financial migration remain NOT TESTED / NOT VERIFIED. Production remains NO-GO.

---

## PHX-MASTER UTC12 — active v0.6 poll ordering and interface boundary

Read the exact active development branch blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859:
- ESP8266 source blob 12c4bb82b6fddafe813674a0b5f692c1d3634073: post poll at line 354, first digitalRead(runCoinPin) at line 357, HTTP timeout 3,500 ms.
- ESP32 source blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d: post poll at line 314, first digitalRead(runCoinPin) at line 318, HTTP timeout 3,500 ms.
- Issue #177 remains OPEN. This exact source readback confirms the blocking poll-before-sample ordering; no coin pulse, relay, physical power or money was operated.

Preserve the existing boundary: untrusted or missing poll authentication cannot enable coin admission; pending evidence is not cleared on ambiguous response or failed durable commit; a positive disposition requires the CORE-owned authenticated receipt/sequence contract and durable readback. HARDWARE owns firmware intake/relay implementation, CORE owns receipt/authentication and financial state, QA owns independent semantic regression, and MASTER owns only cross-role interface coordination. #358/#359/#360 do not independently establish the missing CORE response/disposition contract.

No interface schema or ownership route changed in this refresh. Physical GPIO/relay/coin acceptance, independent witness and crash-atomic financial migration remain NOT TESTED / NOT VERIFIED. Production remains NO-GO.

---

## PHX-MASTER UTC07 — pending disposition and poll-intake guard (2026-11-27T07:41Z)

The current #357 exact-head Native failure at [#45958868726](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958868726) is a source-presence assertion for `clearPending(true)` and `clearPending(false)`, not proof that an authenticated disposition is absent or that a callsite would be safe. Preserve the existing semantic contract:

1. Missing, unsigned, malformed, stale, replayed or otherwise untrusted poll responses keep admission denied and preserve pending evidence.
2. Positive disposition requires a CORE-owned authenticated receipt bound to device/event/sequence and approved epoch/nonce identity.
3. Clear one pending event only after authenticated disposition acceptance, durable state commit and exact readback/sequence reconciliation; write/readback/crash ambiguity preserves deny hold and evidence.
4. QA tests the state transition, replay/idempotency and failure recovery at the same exact source SHA; never infer correctness from a literal function-call string.

Active v0.6 still blocks in `post("poll")` before the first coin sample: ESP8266 blob `12c4bb82`, lines 354→357; ESP32 blob `29f1125d`, lines 314→318; 3,500 ms timeout. Issue #177 remains P0. HARDWARE owns local intake protection/nonblocking capture; CORE owns authenticated receipt/disposition and durable authority; QA owns independent tests; MASTER owns the interface contract.

---

## PHX-MASTER UTC05 — pending disposition is a semantic contract, not a callsite grep (2026-11-27T05Z)

The current #355/#357 deny-only candidate must not be modified to satisfy a test that merely requires literal `clearPending(true)` and `clearPending(false)` callsites. The #357 Native run #45939854159 logs `Vendo pending sequence contract passed`, then fails at `v060_vendo_sequence_contract.py:20` on that string-presence assertion. A syntactic clear call can erase unresolved evidence without proving authority or durability.

**Required acceptance semantics:**
1. Missing, unsigned, malformed, stale, replayed or otherwise untrusted poll responses leave coin admission denied and preserve pending evidence.
2. A positive disposition requires a canonical CORE-owned authenticated receipt bound to the device/event/sequence and the approved epoch/nonce identity; no unsigned remote field may enable admission.
3. A specific pending event may be cleared only after its authenticated disposition is accepted, the durable state transition is committed, and exact readback/sequence reconciliation succeeds. Any write, readback, crash or ambiguity failure preserves the deny hold and unresolved evidence.
4. QA verifies state transitions, replay/idempotency and failure recovery against the same exact source SHA; it must not infer correctness from the presence of a function-call string.

**Ownership:** CORE defines the producer/receipt/disposition schema and golden vectors; HARDWARE owns the firmware consumer and local intake protection; QA owns independent semantic regressions; MASTER owns this cross-role contract. This clarification does not approve a positive poll path or change firmware. **PRODUCTION NO-GO.**

---

## PHX-MASTER UTC04 — cross-role ledger and coin-intake contracts (2026-11-27T04Z)

### Canonical ledger preservation — invariant retained

Canonical CHANGE_LEDGER history is append-only. Every candidate must preserve the exact base bytes as a prefix; only a newline-separated suffix may be appended. Corrections are dated append-only entries citing the affected prior entry/blob. Historical deletion, middle edits, prepends or reordering are hard blockers.

- #355 has now restored the exact #354 base prefix (3,621 → 3,730 records); its branch-local byte-prefix guard passes at docs head `0adb541a`.
- #356 independently preserves its v0.6 base prefix (3,390 → 3,476 records); its branch-local guard passes at docs head `e5329644`.
- These are two branch-local protections, not a shared repository-wide gate. The current `tests/handover_gate.sh` checks that dated entries exist and that handover records are fresh; it does not compare the candidate ledger to the exact base bytes.
- **Owner action:** PHX-RELEASE implements the shared exact-base prefix check; PHX-QA adds independent RED/GREEN tests for truncation, middle edits, prepend, empty base and malformed append boundary. Hardware retains its own ledger and handover.

### Coin input / authenticated poll — P0 remains open

A blocking network poll must not leave an energized coin acceptor unobserved. The implementation must either (a) locally inhibit coin acceptance before any blocking poll and keep it fail-closed until an authenticated, contract-valid response is accepted, or (b) use nonblocking transport plus edge capture backed by a durable journal. Interrupt-only RAM counting is not durable credit. No coin may be acknowledged/credited until the durable receipt/disposition contract is satisfied.

Current #355 source still performs synchronous `post("poll")` before sampling:
- ESP8266: poll line 403; first `digitalRead(runCoinPin)` line 408.
- ESP32: poll line 410; first `digitalRead(runCoinPin)` line 415.
Both have a 3,500 ms HTTP timeout. `denyRemoteControl()` brackets the call and the response is discarded, but this does not by itself prove the coin relay is inhibited during the wait. Issue #177 remains P0 and host-simulated only.

**Ownership:** HARDWARE owns local intake/pulse-capture firmware; CORE owns authenticated poll, receipt and durable pending-disposition authority; QA independently tests the exact same source SHA; MASTER owns this cross-role contract. Do not add unsigned response enable or active pending-clear calls merely to satisfy an inherited assertion. The #355 Full/Native failure at `v060_vendo_sequence_contract.py:20` requires CORE/QA contract reconciliation.

### Storage preflight evidence boundary

#356 STORCHK-0674 and physical-parent matrices are synthetic sysfs/mountinfo checks only. They reject root/overlay/boot reuse, sibling partitions on the same parent, whole-disk reuse, missing identity and holder ambiguity. The exact Full workflow passed CI, but this is not physical media independence, a real mount/write, a power cut, flash durability or device acceptance. Physical acceptance remains NOT TESTED.

---

## PHX-MASTER UTC02 — cross-role canonical ledger preservation invariant (2026-11-27T02:34Z)

Canonical CHANGE_LEDGER.md history is append-only. A PR that touches the canonical ledger must preserve the exact base content as a byte-identical prefix and may only append new entries. Historical corrections must be added as dated correction entries that cite the affected prior entry/blob; they must not replace, truncate, reorder or silently rewrite prior records. A deliberate non-append rewrite is a hard review blocker unless the owner supplies an independently verified archival snapshot and an explicit, separately reviewed migration plan.

### Source-grounded defect and branch-local mitigation

- HARDWARE #355 base (#354 head fc842342) ledger blob b950f7be47f79d71e6cb8b721801c1bae128df45: 1,132,798 bytes / 3,621 newline-delimited records.
- HARDWARE #355 head fa33bd18 ledger blob 79997c1e90ffb6b7c6ce27749ba59c02b80567cc: 12,319 bytes / 94 records. Exact PR review #7207757946 reports +59 / -3,586. This is confirmed historical truncation; #355 owner must restore the exact base history and append its new entries.
- HARDWARE #356 is a separate branch based on v0.6 2fbd2475. Its base ledger blob f16d5774366cf3a4c358dd2a0c2e7ee5e945f668 is 1,082,274 bytes; head 8ce12c96 blob 652ff79fcab1320c09a77956510a46c81dfbef25 is 1,089,350 bytes. PR patch is additions-only (+52 / -0) and the focused exact-head append-only/holder guard passes in #45926090112. This branch-local guard does not repair #355 and is not yet a repository-wide gate.
- The current shared handover_gate.sh was reported by HARDWARE to check dated entries but not preserve the prior canonical ledger prefix.

### Ownership and proposed shared gate

- PHX-MASTER owns this cross-role invariant and coordination evidence.
- PHX-RELEASE owns any shared workflow/gate implementation in its existing owner scope; PHX-QA independently reviews positive and negative regression fixtures.
- PHX-HARDWARE owns restoring #355 and maintaining its branch-local handover.
- The shared gate should compare exact base/head blobs for canonical ledgers, reject any deleted or rewritten historical bytes, report both blob SHAs and byte/line counts, and permit additions only. It must not treat a focused branch-local test as global acceptance.

No shared workflow, subsystem source, or role-owned branch was modified by PHX-MASTER in this activation.

---

## PHX-MASTER UTC23 — P0 coin-pulse sampling invariant (2026-11-26T23:39Z)

Issue #177 remains OPEN. Active v0.6 source at 2fbd2475 has a blocking synchronous poll before the next coin input sample on both boards: ESP8266 blob 12c4bb82, post("poll") line 354 then digitalRead(runCoinPin) line 357; ESP32 blob 29f1125d, post("poll") line 314 then digitalRead(runCoinPin) line 318. Issue #177 reports a source-extracted host reproduction of a missed active-low pulse during a 3.5s poll while the coin relay remains energized. This is simulated evidence, not physical acceptance.

**Required invariant:** a coin acceptor must not remain energized while blocking network I/O prevents pulse sampling. HARDWARE owns the reversible relay-inhibit/nonblocking-capture implementation and board labs; CORE owns authenticated poll, receipt and pending-disposition authority; QA independently verifies exact source behavior. Physical relay polarity, wiring, coin acceptor and power-cut evidence are mandatory before hardware acceptance. RAM-only ISR capture is not durable credit.

The active v0.6 poll is not an approved authenticated positive-admission contract. Do not trust unsigned poll fields, consume unsigned config_revision, or clear pending evidence merely to satisfy QA. #355 current deny-only sketches omit config_revision, response_sig and active clearPending(true/false) calls; Full/Native CI therefore fails inherited QA assertions. CORE and QA must reconcile the contract before any positive admission.

---

## PHX-MASTER UTC22 — authenticated poll and pending-disposition boundary reaffirmed (2026-11-26T22:34Z)

No new shared interface contract was accepted in this audit. CORE remains the owner of authenticated register/poll and receipt/disposition authority; HARDWARE owns firmware/labs; QA owns independent assertions. Current #355 Native PAY-0745 fails because the QA test requires active `clearPending(true/false)` callsites, while the candidate preserves deny-only behavior. Full validation also fails Controller protocol parity. Do not add unsigned poll-field trust, consume unauthenticated `config_revision`, or clear pending evidence merely to satisfy a test. Keep coin admission denied until CORE publishes the authenticated contract and QA verifies the same exact source SHA. No physical acceptance is implied.

---

## PHX-MASTER UTC20 — authenticated poll and deny-only boundary (2026-11-26T20:34Z)

The active v0.6 poll/register contract is still not approved for positive admission. HARDWARE #354/#355 remain deny-only; do not add unsigned `config_revision`, consume unsigned poll fields, or clear pending evidence merely to satisfy QA assertions. Exact #355 Native CI fails because the current QA sequence assertion demands active `clearPending(true/false)` callsites; Full fails Controller protocol parity. #353 Full still fails the ESP8266 poll-signature check. CORE owns the authenticated register/poll and receipt/disposition contract; HARDWARE owns firmware and labs; QA owns independent assertions. Preserve the fail-closed boundary until the signed contract is approved. No physical acceptance is inferred from CI.

See [UTC20 exact-head audit](PHX_MASTER_UTC20_20261126_LIVE_HEAD_ROLE_CI_COE26_ROUTE_AUDIT.md).

---

## UTC16 contract gate — active v0.6 poll remains unsigned; deny-only candidate retained (2026-11-26T16:33:57Z)

At active v0.6 HEAD 2fbd2475, CGI blob db58041c0575ad0a1101d99cb85403e03c8dcb22 emits poll fields ok, insert, target_nonce, expires and controller, but no response_sig. Member snapshot/auth/mutation endpoints do include response_sig; those signatures do not authenticate poll.

Active v0.6 ESP32 blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d and ESP8266 blob 12c4bb82b6fddafe813674a0b5f692c1d3634073 still read insert/target_nonce and call applyRemoteConfig. This is an unsigned poll trust boundary, not an accepted interface.

HARDWARE #354 deny-only source blobs: ESP32 3edbe38da543ef118b287f3e04c1601692cfa99f; ESP8266 b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9. They have no response_sig/config_revision and only a clearPending function declaration, no active callsites. QA assertions must not be satisfied by adding unsigned config consumption or clearing pending evidence. CORE owns the versioned authenticated register/poll and receipt/disposition contract; HARDWARE implements after approval; QA independently verifies both boards. Physical GPIO/relay/coin/power-cut acceptance NOT TESTED.

HARDWARE #353 current head 5a5f319 has two exact-source remote-config revision lab failures and a Full poll-signature failure. This does not authorize weakening the interface boundary.

---

## UTC13 evidence note — active-v0.6 relay/LED polarity and poll-inhibit lab (LAB ONLY; not production acceptance)

At HARDWARE #354 source/test SHA `9bb46bb27e4be80f6506dbebf2846700efd4cb81` and final documentation HEAD `bbb209f55ddcd48f248eb8d700629db8754dc13a`, the Hardware-owned `poll_preflight_inhibit_lab.py` exercises four independent relay/LED polarity combinations on ESP8266 and ESP32, verifies both outputs are logical OFF after `denyRemoteControl()`, and preserves pending pulse/nonce/target evidence across a simulated 3500 ms synchronous HTTP wait. Focused run [#45836227697](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227697) and ESP32 Mbed TLS matrix [#45836227855](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227855) PASS.

The exact same docs-head Full [#45836227694](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227694) fails QA-owned Controller protocol parity; Native [#45836227876](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45836227876) fails PAY-0745 because its current assertion requires active `clearPending(true/false)` callsites. Do not add an unsafe clear callsite merely to satisfy that stale assertion. QA must assert deny-only behavior and pending-evidence preservation; CORE owns the authenticated register/poll and receipt/disposition contract; HARDWARE owns firmware/labs.

The candidate must not consume unsigned `config_revision`, trust an unsigned poll `insert`, re-enable coin admission, or clear pending evidence before the authenticated contract is approved. The lab is source-extracted/simulated CI evidence only: no physical GPIO polarity, relay, coin acceptor, LittleFS power-loss or native device acceptance was performed. HARDWARE #353's separate unknown-polarity and pin-attachment tests currently fail; therefore no physical fail-safe claim is inferred from #354's host lab.

---

# Project Phoenix — Architecture Contracts & System Invariants

## UTC16 post-checkpoint contract refresh — live source and exact #354 CI (2026-11-26T17:13Z)

Active development remains blazepwifi-v0.6.0-audit-foundation at 2fbd2475e9f54878c316fa7cea2f228386b0e859. The exact CGI source file experiment/openwrt/BlazePwifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo is blob db58041c0575ad0a1101d99cb85403e03c8dcb22. Its poll handler at lines 119–138 returns ok, insert, target_nonce, expires and controller, but no response_sig. The member snapshot response_sig at lines 149–153 is a separate response and does not authenticate poll.

HARDWARE #354 current PR/docs HEAD is fc842342596786e072630179acfbbc4feeb2ba02; owner-declared source/test HEAD is 145aac9607682071e2db05944a6f9db5aa06e524. Current ESP32 and ESP8266 sketch blobs are 3edbe38da543ef118b287f3e04c1601692cfa99f and b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9. The QA controllers.sh blob 53a7af25fdee9a650e10e870c4204e0fb43239c requires config_revision at line 21; neither exact sketch contains it. The QA sequence contract blob 301d6d9287b7a059595e541ab570b9b4dd8fe226 requires active clearPending(true/false) calls at line 20; both sketches only define clearPending and have no active callsite.

At exact current PR/docs HEAD fc842342: poll-intake deny run 45864684458 PASS; ESP32 Mbed TLS 3.3.13/4.0.0 reproducible-build matrix 45864684325 PASS; Native synthetic journal run 45864684295 FAILS at the QA-owned active-clear assertion; Full run 45864684497 FAILS its QA-owned Controller protocol parity validation. Preserve deny-only behavior and pending evidence. Do not consume unsigned poll configuration or add an unsafe pending-clear call merely to satisfy stale QA assertions. CORE owns the authenticated register/poll and receipt/disposition contract; QA owns its assertions; HARDWARE owns firmware and labs. Physical GPIO/coin/power-cut acceptance remains NOT TESTED.

---


**Protocol Specification:** BLAZE-COMMS/1  
**Authority:** Master Auditor / Integration Coordinator (`PHX-MASTER`)  
**Scope:** Cross-subsystem integration rules for BlazePwifi (OpenWrt), BlazeRental (Android), BlazePisonet SoftTimer (Windows), ESP32/ESP8266 Firmware, QA Regression, and Release Engineering.

---

## UTC02 evidence note — provider compile does not close poll-response authentication

The #340 Hardware candidate now has a real ESP32 Arduino core 4.0.0 exact-source compile PASS at source/test SHA `d3168ccb4959fe1eab718912fd04510ef7603253` ([run #45742944327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45742944327)). This replaces the earlier statement that only a source-extracted Mbed TLS guard existed for that candidate. It is still candidate-scoped; #340's current Full build remains in progress, #348 still fails on its separate old header path, and active v0.6 is unchanged.

At active v0.6 exact HEAD `2fbd2475e9f54878c316fa7cea2f228386b0e859`, both board sketches consume unsigned poll fields and call `applyRemoteConfig`; the CGI poll response does not include `response_sig`. COE #26's copied board sketches instead default `sigOk=true` and skip verification for an empty controller key. Neither behavior is an approved authenticated poll contract.

**Contract order remains:** CORE defines the canonical authenticated response, serialization, controller binding, mandatory key provisioning, freshness and replay; HARDWARE implements only after approval; QA independently tests both boards. Deny-only coin/relay admission remains mandatory until then.

---


## 1. Financial Receipt Schema & Accounting Invariants

### 1.1 Single-Authority Durable Ledger
All money, coin pulses, prepaid member balances, and time grants must be authorized by a single durable authority per installation. In-memory mutations must NEVER precede persistent journal entry.

### 1.2 Canonical Receipt Schema
Every coin insertion, member time transfer, or rental payment event must emit a canonical receipt record structured as follows:

```json
{
  "$schema": "https://json-schema.blazing.systems/phx/v1/receipt.json",
  "event_id": "88888888888888888888888888888881",
  "protocol_version": "v2",
  "controller_id": "esp32-vendo-01",
  "target": "192.168.10.45",
  "amount_centavos": 500,
  "pulse_count": 5,
  "seconds_granted": 900,
  "timestamp_utc": "2026-11-13T19:00:00Z",
  "nonce": "a1b2c3d4e5f60718",
  "signature": "3045022100...P256-OR-HMAC-SIGNATURE",
  "replayed": false
}
```

### 1.3 Accounting Invariants
1. **Idempotent Replay Guarantee:**
   Resubmission of an already-committed `event_id` MUST return `{"ok": true, "replayed": true, ...}`. It MUST NOT credit additional balance, lengthen existing leases, or append a duplicate transaction record.
2. **Revocation / Admission Serialization:**
   Controller validation (`bp_controller_paid_allowed`) must occur under the serialization lock (`fd4` controller admission) before debit/credit execution. If an administrative change (`bp_controller_set`) disables a controller between initial client proof and writer lock acquisition, the transfer MUST fail closed with `{"ok": false, "error": "controller_disabled"}` without balance mutation.
3. **No Phantom Grants on Persistence Failure:**
   If storage sync (`fsync` or journal write) fails (e.g. disk full, EIO, power cut), the transaction MUST fail closed and revert all in-memory balance modifications.

---

## 2. Coin Pulse-to-Credit Pipeline

### 2.1 Hardware Timing & Electrical Rules
- **Pulse Width:** 30ms to 100ms per coin pulse.
- **Debounce Threshold:** Minimum 20ms stable signal before edge transition is recognized.
- **Inter-Coin Timeout:** 250ms quiet period marks completion of a pulse train before credit calculation.

### 2.1.1 Relay/LED OFF preload before output enable — provisional software invariant (2026-11-18 UTC03)

For runtime pin reassignment on both ESP32 and ESP8266, the relay and LED must be placed at their polarity-correct logical OFF level before the new output driver is enabled:

1. Drive the old relay and LED pins logically OFF using the old polarity before changing pin assignments.
2. Assign the new coin, relay and LED pin numbers.
3. Preload the new relay and LED logical OFF levels while those pins are not yet configured as OUTPUT.
4. Only then call `pinMode(..., OUTPUT)`.
5. Attach the coin interrupt after the output pins are configured.
6. Reassert logical OFF after output enable.

This is especially important for active-low relay wiring, where a default LOW output latch can energize the relay during an OUTPUT-mode transition. HARDWARE owns the firmware implementation; QA owns independent source-linked verification. This invariant does not authorize relay actuation, coin admission or financial disposition.

Source: HARDWARE PR #322, source/test SHA `7ba56c1ba92dcffa2555e4cce10d3010c3afaf5b`; current docs-only PR head `50d93e0de3d682550b6f02fb43484e76ad9c7e08`. Exact-head focused output-order run [44232877611](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877611) passed on both boards; logs report `OUTPUT_SEQUENCE_PASS` for ESP8266 and ESP32 and the workflow explicitly classifies evidence as SIMULATED ONLY. The companion quarantine/readback run [44232877649](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877649) also passed.

The current-head Full build [44232877624](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232877624) is not a Full pass: its validation job failed at the inherited QA-owned `Missing poll signature check`; 14/14 target/platform jobs completed SUCCESS; 12 downstream simulation/update/publish/signing jobs SKIPPED after the validation failure. Physical GPIO voltage, relay transient, contacts, electrical pulse behavior and hardware acceptance remain NOT TESTED.

### 2.2 Client-side response trust boundary — current deny-only state (2026-11-18 UTC08)

- `bp_check_vendo_sig()` checks the incoming request tuple against a keyed SHA-256 concatenation. This is not standard HMAC, is request-side only, and does not authenticate the JSON body returned to the controller.
- On the current Experiments development producer, `bp_json()` only emits HTTP headers plus the supplied JSON body. The `register|ping`, `poll`, and `coin` response bodies do not include `response_sig`.
- The current HARDWARE #323 candidate is deliberately fail-closed: both board implementations return `false` from `acceptPollResponse()` and `coinPostDispositionVerified()`. The register-tuple check also remains false when the response has no `response_sig`; remote configuration remains disabled.
- Do not describe response verification as implemented, and do not require a positive `|poll|` signature expression, until PHX-CORE defines a versioned response envelope and canonical serialization, PHX-HARDWARE implements the approved consumer, and PHX-QA independently verifies positive/negative golden vectors at the same pinned source SHA.
- Until that gate is met, poll admission and coin POST disposition remain hard-deny. A missing signature is not a reason to weaken firmware or clear pending evidence.

See §6.23 for exact source, candidate, fixture and CI evidence.

### 2.2.1 UTC22 exact branch clarification — deny-only consumer and lab helper are not a response contract (2026-11-25)

- HARDWARE #340 exact head 547148eeb4384df7971d17d762e3f12bc5dcab3c: both board sketches bracket synchronous poll with denyRemoteControl(), explicitly discard the response, and retain applyRemoteConfig() only as a no-op deny stub. This is a conservative consumer-side mitigation, not authenticated response verification.
- HARDWARE #348 exact head 8bdddfb88630c0c9675f7e4a47ab640f5d17f699: ControllerAuthV1Lab.h is a non-actuating helper with null/empty-span guards and a synthetic native test. It supports Mbed TLS 2.x/3.x only; the exact focused run used Mbed TLS 2.28.8. It does not define the full producer envelope, key provisioning, protected freshness, or monetary authority.
- Active v0.6 producer at 2fbd2475e9f54878c316fa7cea2f228386b0e859 still emits unsigned register/ping and poll bodies. Do not infer that #340 or #348 resolves this contract.
- COE #26 remains a separate frozen candidate; its empty-key verification bypass is not repaired by either Hardware branch.

No new signature format, key derivation, response schema, or positive coin/relay admission is approved by this clarification. CORE owns producer schema/key provisioning; HARDWARE owns its consumer; QA owns independent positive/negative golden-vector review.

### 2.3 Swallowed Coin Quarantine (LittleFS)
- If the router returns an error (e.g. `"coin window expired"`, `"controller disabled"`), coins MUST NOT be deleted uncredited.
- The firmware MUST append uncredited coin events to `/quarantine.log` in LittleFS with timestamp, nonce, target, pulse count, and error reason for physical operator auditing.

### 2.3.1 Durable one-shot coin POST attempt marker (provisional; CORE/QA review required)

A firmware coin POST is an ambiguous financial side effect: a timeout or lost reply does not prove that the server did not commit the event. The client MUST NOT automatically replay an event after an uncertain attempt.

1. Before the first network dispatch, persist a LittleFS attempt marker bound to the exact pending record (pulse count, nonce, and target). Flush/close it, read it back through the same bounded record/checksum validator, and compare every bound field. If write, close, readback, or comparison fails, deny dispatch and keep outputs fail-closed.
2. The marker is one-shot. A matching, malformed, mismatched, truncated, or orphan marker discovered at boot MUST block automatic replay and preserve all evidence for operator reconciliation. Do not infer “not sent” from a missing HTTP reply.
3. Remove the pending record first and the attempt marker last, only after an authoritative receipt or a separately durable quarantine disposition has been verified. If either removal fails, retain the remaining evidence and keep admission blocked.
4. A power loss after marker commit but before request transmission is deliberately treated as ambiguous; recovery is operator/CORE reconciliation, not an automatic retry. This conservative client fence does NOT replace server-side idempotency, stable event identity, or durable receipt replay protection.
5. The source-extracted fake-LittleFS lab is simulation evidence only. PHX-CORE must review server receipt/replay semantics; PHX-QA must independently verify the exact same source SHA; native flash/power-cut evidence remains mandatory.

This subsection records the owner-implemented #315 behavior as a **provisional cross-subsystem invariant**, not a claim of financial acceptance or production approval.

### 2.4 Win32 Native Serial Coin Input (Windows SoftTimer)
- SoftTimer MUST bind to hardware via `GUID_DEVINTERFACE_COMPORT` using a single verified, pinned `HANDLE`.
- The serial session MUST handle CTS state changes atomically to prevent CTS reconnection races (V4/V5 race conditions where reconnecting drops or attributes pulses to the wrong session).

---

### 2.5 ControllerAuthV1Lab evidence boundary — 2026-11-25 UTC23

The non-actuating `ControllerAuthV1Lab.h` helper and its native test are not the production poll-response implementation.

- PR #348 test commit `2147c9ae46ae862cb355d2da3b4df1787180689e` and source commit `659b1e646ba6d3efdbe6e03df4ab4f170a89f0e1` reject null pointers and zero-length fixed spans before comparison; nonempty comparisons retain a fixed-length XOR-accumulation pass.
- Focused exact-head run [#45716221522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45716221522) passed using the native helper under C++17, Mbed TLS 2.28.8, warnings-as-errors, ASan and UBSan.
- Full exact-head run [#45716221609](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45716221609) failed at the inherited ESP32 application compile because Arduino core 4.0.0 does not provide the included `mbedtls/sha256.h` at `BlazePwifiVendo32.ino:6`. This is not a failure of the helper's span guard; it is also not a Full pass.
- Therefore a focused Mbed TLS 2.28.8 helper test cannot be used as evidence that the application compiles under ESP32 core 4.0.0, authenticates poll responses, or is safe to admit coins. Do not change provider selection, pin a different core, or relax the failing target gate without the owner-approved PHX-CORE/PHX-RELEASE contract decision.
- Ownership: PHX-CORE approves the response contract and golden vectors; PHX-HARDWARE owns firmware/provider implementation; PHX-RELEASE owns reproducible toolchain/provider policy; PHX-QA independently validates helper and application negative paths. Phase-A admission remains DENY.


## 3. Rental & Pisonet Client Time Grant Contracts

### 3.1 BlazeRental Android Client
1. **Dual Server-Authoritative Countdowns:**
   - Active Purchased Session Countdown: counts down remaining rental usage.
   - Insert Coin Reservation Countdown: temporary reservation window for inserting physical coins.
2. **Authenticated Status Before Persistence:**
   - BlazeRental MUST authenticate server status before persisting local lease state.
   - Stale-revision denial: Responses with outdated revision numbers must be rejected.
   - Zero write on authentication failure.
3. **Device Owner Provisioning:**
   - QR provisioning binds to published signed APK checksum and pins local TLS certificate.
   - Offline QR generator tools must preserve raw APK URLs and never substitute placeholder strings within valid HTTPS URLs.

### 3.2 BlazePisonet Windows SoftTimer
1. **Overflow-Denying Time Math:**
   - All time additions (`AddSeconds`, `BankCurrentTime`, `RestoreMemberTime`, `TransferMemberTime`) MUST pass through `TimeCreditMath.TryAdd` (non-negative, overflow-denying math).
2. **Persistence Integrity:**
   - `Storage.SaveState` must execute transactional writes before updating runtime state to prevent divergence between in-memory and on-disk balances.

---

## 4. Identity, Authentication & Rollback Defense

### 4.1 Cryptographic Identifiers
- **Controller Nonces:** Minimum 64-bit entropy derived from hardware RNG (`ESP.random()` on ESP8266/ESP32, `/dev/urandom` on Linux).
- **Controller Authentication:** HMAC-SHA256 with provisioned keys or P-256 ECDSA signatures.
- **Signer Provenance:** Production APK signing must follow immutable lineage (`BlazeRental-production-lineage2`). SoftTimer Windows executables must follow Authenticode signing pipeline gates.

### 4.2 Standalone Installer Rollback Defense
- Standalone installer backup directories MUST use unique collision-safe naming (timestamp + high-resolution entropy).
- File copy operations during backup MUST verify write success and file size/hash before proceeding with upgrades.

---

## 5. Build, Packaging & Release Promotion Hierarchy

All subsystems must be classified under one of the following five operational states:

| State | Definition | Gate Criteria |
|---|---|---|
| **NOT TESTED** | Source written or drafted without test execution | Default state for new PRs |
| **SIMULATED** | Host C++, mocked shell, or synthetic emulation passing | Passes local unit test suite |
| **CI VERIFIED** | Source-exact SHA green on official GitHub Actions workflow | Passes all lint, security, and integration workflows |
| **HARDWARE ACCEPTED** | Physical hardware testing verified on non-customer test bench | 150 real power cuts, 30-device 24h soak, physical coin test |
| **PRODUCTION READY** | Authorized release signed and approved by Master Auditor | All security, migration, and witness gates cleared |

> [!CAUTION]
> **Production Status: NO-GO**  
> Under no circumstances may code be promoted to commercial production, deployed to live routers, or flashed to customer hardware without independent durable accounting, anti-rollback witness, QA review, and physical hardware acceptance.


## 6. Open P0 poll-response trust and rejected-event durability contract (2026-11-16 UTC22)

**Status: MASTER DECISION (2026-11-17 UTC02): keyless/bootstrap is never coin authority.** This admission invariant is final; implementation acceptance remains pending PHX-CORE / PHX-HARDWARE owner review and independent PHX-QA exact-head verification. See [HARDWARE_POLL_CONTRACT_AND_STACK_HOLD_20261116_UTC22.md](HARDWARE_POLL_CONTRACT_AND_STACK_HOLD_20261116_UTC22.md) for exact PR heads, CI observations and source-diff evidence.

### 6.1 Keyless poll responses cannot authorize coin intake

- An empty or unprovisioned controller key is **not** an authentication success.
- No keyless `ok=true` poll response may set coin admission, active target or relay authorization.
- Coin intake can be enabled only after a fresh response verifies under the approved provisioned key/signature and target/freshness checks.
- Missing, malformed, expired or mismatched authentication must leave intake denied and must not reuse a previous positive poll.
- A separate setup/bootstrap path may remain available, but it cannot authorize coin admission.

### 6.2 Failed quarantine persistence must survive reboot safely

- If the controller rejects an event and local quarantine persistence fails, the event must remain durably pending or durably marked for reconciliation before any process can retry or credit it after reboot.
- A RAM-only `journalRecoveryRequired` latch can inhibit same-boot retries but is not proof of cross-reboot non-replayability.
- While the event's durable disposition is ambiguous, deny retry, duplicate POST, credit and relay admission.

These are **shared interface/accounting invariants**, not permission for PHX-MASTER to edit firmware or financial source. PHX-CORE owns financial/replay semantics; PHX-HARDWARE owns firmware/journal implementation; PHX-QA independently verifies positive, negative and reboot/failure cases. Do not mark either invariant implemented or accepted until the owners agree on the exact contract and QA verifies the combined exact SHA.


### 6.3 Historical poll producer/consumer comparison — 2026-11-16 snapshot; current #323 state in §6.23

This section preserves the earlier #315 comparison as historical evidence. It does not describe the current #323 deny-only candidate. Use §6.23 for the current producer/consumer refs and QA fixture status.

The keyless-deny invariant does not by itself establish that the current server can authorize a provisioned controller. Exact poll-action inspection at this snapshot found:

| Ref | cgi-bin/vendo blob | Poll response signature |
|---|---|---|
| Experiments main f4e8a891... | 2e3a1430d08cc6606429a042df3b5848f53c7267 | Absent |
| Experiments v0.5.3 development aad3aade... | a1c19180385e618c412b4af21c0e91c1f47da1dd | Absent |
| Experiments v0.6 audit-foundation 2fbd2475... | db58041c0575ad0a1101d99cb85403e03c8dcb22 | Absent |
| COE integration PR #26 b382d233... | 0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e | Present; derived candidate |

The source branches emit poll JSON without response_sig. The COE candidate defines vendo_poll_sig and includes response_sig in its poll response. This is a real source/destination behavior difference, not byte parity or proof of semantic equivalence.

The current HARDWARE #315 consumer expects a provisioned cfg.key and verifies response_sig against the ordered fields key, poll, controller id, request nonce, insert bit, target nonce, expiry, key. The COE candidate's producer expression has the same apparent field order using secret, id, nonce, insert, target and expires. This is only a structural comparison: no shared golden vector has been independently executed, and the key/id/nonce binding, canonical serialization and digest implementation still require PHX-CORE and PHX-QA verification.

The observed candidate expression is a keyed SHA-256 construction with key material at both ends; do not describe it as standard HMAC. PHX-CORE and PHX-QA must review the cryptographic construction and publish exact positive/negative test vectors before treating it as an approved shared protocol. Do not silently change the algorithm in one client or copy the derived candidate over canonical source.

Until a canonical producer emits the exact approved authenticated poll response and independent QA verifies both sides at pinned SHAs, configured-key coin admission remains fail-closed. No keyless/bootstrap fallback is permitted. This section does not authorize source migration or firmware edits by PHX-MASTER.


### 6.4 Remote configuration has a separate authorization domain

**Status: MASTER HOLD — implementation and exact cryptographic schema pending PHX-CORE / PHX-HARDWARE / PHX-QA review.**

The poll-admission signature authenticates only the poll admission tuple. The register/ping response signature currently authenticates only its register tuple (action, controller ID, request nonce and server time). Neither signature authenticates the returned controller configuration object.

At the historical HARDWARE PR #315 head `58ade5df83df0c6894dd8d1e2a70617b90dae374`, both ESP `connectSta()` implementations still initialize `sigOk=true`, conditionally verify a register `response_sig` only when a key is configured, then call `applyRemoteConfig(r)` on `ok:true`. Consequently:
- an empty key leaves the register response accepted for configuration application without signature verification;
- a configured-key register signature does not bind the `controller` configuration fields in the COE #26 candidate producer;
- the poll-path config-isolation fix does not close this separate register path.

See [POLL_CONFIG_REGISTER_TRUST_BOUNDARY_AUDIT_20261117_UTC03.md](POLL_CONFIG_REGISTER_TRUST_BOUNDARY_AUDIT_20261117_UTC03.md) for exact file links, heads and CI evidence.

**Binding rules:**
1. Until a separate configuration-authentication envelope is approved and independently tested, `applyRemoteConfig` MUST NOT be invoked from poll or register/ping responses. Keep remote configuration disabled; do not reuse admission or register signatures as a configuration signature.
2. An empty/unprovisioned key never authorizes remote configuration.
3. A future configuration signature must use a domain separate from poll admission and bind a deterministic canonical representation of schema/version, controller identity, request nonce, monotonic configuration revision, freshness/expiry data, key identity/version when applicable, and every behavior-changing configuration field (enable flags, GPIOs, polarity, debounce/timing, pulse grouping, retry settings and future additions).
4. PHX-CORE owns the exact schema and cryptographic construction; PHX-QA independently approves canonical positive/negative golden vectors. Do not describe ad-hoc keyed SHA-256 concatenation as HMAC.
5. Verify identity, signature, freshness, revision and all field bounds before mutation. Persist the complete configuration atomically before runtime activation. Any failure preserves the prior configuration, applies no partial fields and leaves coin admission denied.

This is a shared interface contract and coordination hold, not authorization for PHX-MASTER to edit firmware or CORE source. The exact schema/algorithm remains pending owner review.


### 6.4.1 Live source/staging correction — 2026-11-17 UTC04

The register-path finding above was confirmed at the earlier #315 snapshot 58ade5df83df0c6894dd8d1e2a70617b90dae374. It is now corrected on the current PHX-HARDWARE owner branch #315 head 75dc5f0b888f16e2c85e4321f62df4685639ad33: both sketches retain one dormant applyRemoteConfig definition and have no response call sites. Both connectSta() implementations keep register-tuple authentication fail-closed and do not apply returned configuration.

The exact-head focused source-extracted CI run 44013351048 passed the register-config denial lab 7/7 per board. This is simulated/host CI evidence only. The full run 44013351035 still fails in the QA-owned poll extractor because acceptPollResponse() is not extracted; the full workflow is not green and no physical acceptance is established.

**The COE integration candidate remains blocked.** At PR #26 head b382d233ff06c8791b1028bed3c617cc7b670d12, both destination sketches still have two applyRemoteConfig(r) call sites and two sigOk=true defaults. Positive keyless register or poll replies can reach the configuration mutator. The source-side correction has not been propagated to the destination candidate. Do not treat the #315 focused pass as evidence for COE #26.

The separate configuration authorization domain remains the governing invariant: remote configuration stays disabled until PHX-CORE defines the canonical envelope and PHX-QA independently verifies it. For the current destination candidate, the immediate safe requirement is to remove response-driven configuration application rather than reuse the register or poll admission signature.

See REMOTE_CONFIG_MIGRATION_STAGING_AUDIT_20261117_UTC04.md for exact blob IDs, license and manifest scope, current role CI, and reproduction steps. This correction changes no source ownership and authorizes no copy or merge.


### 6.4.2 Current COE staging still contains the pre-correction paths — 2026-11-17 UTC05

The current HARDWARE owner branch #315 at 75dc5f0b888f16e2c85e4321f62df4685639ad33 has the remote-configuration correction on both boards: applyRemoteConfig() is definition-only, connectSta() does not apply returned configuration, and acceptPollResponse() defaults signatureOk=false. Exact source blobs: ESP32 38a2d239eed6af876d421f9f908bbb62b3ae27e1; ESP8266 f59e624ae2da04bddc70ddc2809bf6d8ff486aac.

COE integration #26 at b382d233ff06c8791b1028bed3c617cc7b670d12 still contains three applyRemoteConfig() occurrences and two bool sigOk=true defaults per board, including register and poll response call sites. Exact destination blobs: ESP32 3cc7ec54b476943dc04a8d1af5e2df5fe054e422; ESP8266 c8be98f72596681e36a3ad1f8939bf8046c96887. This candidate also retains a POST /quarantine/clear handler that deletes /quarantine.log and returns HTTP 200 on both boards; the current #315 source returns HTTP 403 and contains no quarantine-log deletion call.

Keep COE #26 blocked for Hardware migration. See HARDWARE_STAGING_PARITY_AUDIT_20261117_UTC05.md for exact lines, test identities, modes, CI and owner actions. No source/destination copy or firmware edit is authorized by this finding.
 
### 6.5 Quarantine evidence is non-deletable until authenticated reconciliation — 2026-11-17 UTC05

The quarantine log records unpaid coin events and is reconciliation evidence. A network POST must not erase it or claim success without an approved authenticated operator recovery contract, a durable receipt/reconciliation record, and independent negative/positive tests. Current owner source #315 responds HTTP 403 to POST /quarantine/clear and does not call LittleFS.remove("/quarantine.log"). The COE #26 candidate still deletes the log and returns HTTP 200 on both boards, with no explicit setup-AP-origin guard in those handlers.

A future clear/reconciliation flow requires owner-approved identity and authorization, immutable export/readback, durable receipt linkage, replay/idempotency rules, failure atomicity, and independent QA. Until then, preserve the evidence and deny deletion. This contract does not authorize PHX-MASTER to edit firmware or approve a physical/financial operation.

## 6.6 Coin POST disposition requires an event-bound authenticated receipt — 2026-11-17 UTC07

The current HARDWARE #315 source deliberately returns DENY from `coinPostDispositionVerified()` for every response. The present endpoint uses plain HTTP and no approved event-bound signed receipt/disposition contract exists. This is a safe hold, not a completed receipt protocol.

**Authority invariant:** raw HTTP status, root `ok:true`, root `ok:false`, nested `receipt.ok:true`, error text, timeout, empty body or transport success is never financial authority. After the durable `/pending.attempt` marker is written, flushed, closed and read back, any missing/invalid/ambiguous disposition must retain the pending journal and marker, set the recovery hold, keep outputs fail-closed, and deny automatic replay. It must not clear the pending event or delete reconciliation evidence.

Before firmware may accept a coin POST result, PHX-CORE must define a domain-separated authenticated receipt that binds at minimum: protocol/domain version, controller identity, key version, unique event/receipt ID, event nonce, target nonce, pulse count, server ledger epoch/sequence, freshness/expiry, disposition enum and reason. The owner-approved cryptographic construction and canonical serialization must have positive and negative golden vectors. Do not substitute an ad-hoc SHA-256 concatenation or reuse the poll/register admission signature.

Server handling must be idempotent for a repeated event ID and return the same authoritative receipt without duplicate credit. The controller must verify signature, identity, key version, event/target/pulse binding, freshness, sequence and disposition. An accepted receipt can clear pending state only after the receipt and resulting state are durably committed. A rejected receipt can transition to quarantine only after its authenticated negative disposition is durably recorded with reconciliation evidence. Every unknown outcome stays in a recovery hold until operator reconciliation; never automatically replay.

This contract does not authorize remote configuration, which remains a separate authorization domain. PHX-CORE owns the protocol proposal; PHX-QA owns independent vectors and failure tests; PHX-HARDWARE implements only after those owners complete review. This is a Master-level fail-closed requirement, not an implementation claim or release approval.

Exact source/staging evidence and current CI are in [COIN_POST_DISPOSITION_AUTHORITY_AUDIT_20261117_UTC07.md](COIN_POST_DISPOSITION_AUTHORITY_AUDIT_20261117_UTC07.md). COE #26 remains blocked; no firmware copy or destination edit is authorized. **PRODUCTION NO-GO.**



## 6.7 Legacy poll-signature fixture must not override default-deny — 2026-11-17 UTC09

The current PHX-HARDWARE #315 source at `84fe6b790139d147f330f13a40b3ae3e89a7042d` deliberately makes `acceptPollResponse()` return DENY on both ESP8266 and ESP32, clearing the candidate insert/target state. `coinPostDispositionVerified()` also remains default-deny. The derived `response_sig` poll construction is not an approved authorization contract; do not reintroduce it to satisfy an inherited test.

The inherited `tests/v05_firmware_hardening_test.sh` still requires `|poll|` and simulates a positive poll signature. It is invoked by `tests/controllers.sh` and is unchanged in PR #315. Current Full validation fails at this stale assertion before reaching the separate v0.6 extractor omission. This is a real CI failure and a test-contract mismatch, not proof that default-deny firmware should be weakened.

**QA contract:** replace the positive legacy assertion with source-linked negative cases for empty/unprovisioned key, provisioned key with unapproved/forged/missing/malformed/stale response, root/nested `ok:true`, mismatched target/nonce and ambiguous responses. Assert intake remains disabled, candidate target is cleared, no credit/relay/LED output is authorized, and pending/attempt evidence is preserved. Keep positive acceptance vectors blocked until PHX-CORE publishes the canonical producer/consumer contract and PHX-QA independently approves both-board golden vectors. PHX-QA owns test files; PHX-HARDWARE owns firmware. **PRODUCTION NO-GO.**

## 6.8 Appliance ULA prefix must be valid and deployment-scoped — 2026-11-17 UTC11

COE #26 and its current release child #31 both emit the hard-coded option ula_prefix 'fd00:db8:blaze::/48'. The blaze hextet is not hexadecimal. The current profile has no networking.ula_prefix field, and the current #31 packager tests have no ULA/IPv6 assertions. The #31 interface/VLAN validation change does not address this independent defect.

**Contract:** generated ula_prefix must be a strictly parsed RFC 4193 ULA in fd00::/8 with /48 prefix length. Reject malformed, non-ULA, host-bit-set, wrong-length and missing values before any staged UCI write. Do not substitute one globally hard-coded prefix: define a reviewed profile input or deployment-time generation/persistence policy that gives each independent LAN/site a unique prefix while devices on the same LAN share it. PHX-RELEASE owns packager/profile/tests; PHX-CORE and COE owner define provisioning; PHX-QA independently verifies exact-head output; PHX-HARDWARE validates only after correction. Master owns this contract and routing, not implementation.

See [APPLIANCE_IPV6_ULA_PREFIX_CONTRACT_AUDIT_20261117_UTC11.md](APPLIANCE_IPV6_ULA_PREFIX_CONTRACT_AUDIT_20261117_UTC11.md). Keep #26/#31 draft. **PRODUCTION NO-GO.**


## 6.9 ULA prefix is installation identity, not hardware profile — 2026-11-17 UTC13

The shared router profile describes hardware capabilities and is reused across independent installations. A site ULA prefix is deployment identity, not a model property. Do **not** add one static `networking.ula_prefix` to the shared hardware-profile schema as the default fix.

A generic appliance image must not embed a globally shared ULA placeholder. The installation/first-boot authority must create a locally assigned RFC 4193 ULA /48 for that installation, persist it durably before network services consume it, and reuse it across reboot, upgrade and restore. Devices on the same LAN/site share that prefix; independent sites receive independently generated prefixes. Require canonical strict parsing, locally assigned `fd00::/8`, exact `/48` length and network alignment.

The implementation owner must choose and verify one target-supported mechanism: (1) first-boot generation plus atomic persistence, or (2) a validated deployment-specific prefix input when an artifact is intentionally unique to one site. Do not silently fall back to a fixed example, regenerate on each build/boot, or assume netifd supplies a valid prefix without target evidence. If neither mechanism is present, keep integration blocked.

**Owner routing:** PHX-RELEASE owns packager/first-boot implementation and tests; the COE integration owner owns destination staging; PHX-QA independently verifies valid/invalid inputs and generated UCI; PHX-HARDWARE validates target behavior only after correction and authorization. PHX-MASTER owns this cross-repo contract and gate only. Exact evidence is in [COE_ULA_PREFIX_CONTRACT_REVALIDATION_20261117_UTC13.md](COE_ULA_PREFIX_CONTRACT_REVALIDATION_20261117_UTC13.md). **PRODUCTION NO-GO.**


### 6.9.1 Appliance-local randomness is not a site authority — 2026-11-19 UTC11

For this contract, **installation means the LAN/site identity boundary, not each physical router independently**. A first-boot script that independently samples a fresh 40-bit Global ID on every appliance can create different /48 prefixes for two routers on the same site. That does not satisfy the same-site sharing invariant, even if each local UCI write is syntactically valid and durable.

Before acceptance, the selected authority must allocate one site prefix and make the same canonical value available to every appliance on that LAN/site. It must survive reboot, upgrade, backup and restore. Concurrent first boots must not create competing site identities. Failed allocation, write, commit or readback must leave network services blocked and preserve unrelated UCI state. No appliance may silently replace a valid site prefix with a new random value.

Independent QA must prove:
1. Two appliance instances attached to one site receive the same prefix.
2. Two independent sites receive distinct prefixes.
3. Concurrent first-boot attempts converge on one durable value or fail closed.
4. Reboot, upgrade, backup and restore preserve the exact prefix.
5. Failed UCI stage, commit or readback leaves no partial/conflicting identity and preserves unrelated network settings.

A per-appliance first-boot random generator is therefore a local allocation primitive only; it is not evidence of site-level allocation or distribution. This contract does not select the authority design. PHX-CORE and the COE integration owner choose durable authority/distribution; PHX-RELEASE implements it; PHX-QA independently verifies it; PHX-HARDWARE performs target validation only after approval. Until the owner decision and exact-head tests exist, keep COE ULA integration blocked.


## 6.10 ImageBuilder build execution must actually be sandboxed — 2026-11-17 UTC13

ImageBuilder Makefiles and their recipes are executable inputs that can create symlinks and write files. Installing bubblewrap or proving that a trivial 'bwrap ... true' namespace probe succeeds is not containment. The actual Make/ImageBuilder subprocess that processes the candidate workspace must run inside the approved filesystem boundary.

Minimum contract: only a disposable build workspace may be writable inside the namespace; source inputs and toolchain paths are read-only; operator-owned files and sentinels remain outside the writable bind set or are read-only; caller UID/GID and ownership semantics are preserved; the build fails closed when the namespace cannot be established. Network isolation is a separate property and must not be claimed unless separately configured and verified. Do not expose secrets or write credentials into the build workspace.

The regression must execute a synthetic malicious Makefile inside the same sandbox boundary and prove that a symlinked firmware output cannot change an external sentinel. The test harness must invoke the sandbox wrapper, not merely check that bwrap exists. A standalone capability probe followed by a direct Python/test invocation is not sufficient.

Current COE RELEASE #31 exact head 19fc87988e55f47e8c6a512e51b470a91abbf816 has sandbox run 44098939249 failing at the UID/GID probe; packaging tests are skipped. The workflow's subsequent Python test step is direct, and the test launches the generated shell wrapper directly. An earlier exact head edf4a37 run 44098400955 observed the synthetic external sentinel overwritten. Exact source, job and log evidence: COE_IMAGEBUILDER_SANDBOX_EXECUTION_BOUNDARY_AUDIT_20261117_UTC13.md.

PHX-RELEASE owns the wrapper/workflow/test correction; PHX-QA independently verifies the exact final head. PHX-MASTER owns this cross-repo invariant and release gate only. Keep COE #31/#26 draft and **PRODUCTION NO-GO**.

## 6.11 CI test-harness containment is not generated-build enforcement — 2026-11-17 UTC14

At COE RELEASE #31 final head d45b84c67dc587fca6226662cb1d8bc59bdb11ae, the test helper invokes run_imagebuilder_sandbox.py when PHX_REQUIRE_BWRAP=1, and the dedicated workflow sets that variable. This proves only that the synthetic test harness attempts to execute its generated wrapper under the runner.

The production packager blob fd558928b2869ce1f4b2cb2776b405b4b723b310 contains no bubblewrap or runner invocation in generate_build_script(). The generated build script therefore does not enforce the same boundary when an operator runs it directly. Runtime build execution remains NOT SANDBOX-ENFORCED / UNKNOWN until RELEASE either integrates the runner into the generated entrypoint or documents and independently verifies a mandatory external isolated build-host boundary.

The current runner explicitly passes --share-net; network isolation is not present or claimed. Its read-only host-root bind is a write boundary, not a confidentiality boundary. Do not describe this as a full sandbox or run untrusted build inputs on a secret-bearing host. PHX-RELEASE owns implementation; PHX-QA independently verifies the actual supported build invocation; PHX-MASTER owns this contract and release gate only.


## 6.12 Generated shell templates require runtime-path verification — 2026-11-17 UTC15

A successful `sh -n` check proves only that the shell parser accepts the generated file; it does not prove that each generated command path executes correctly. When Python emits a shell script from a triple-quoted template, a literal `\\n` is not a line break: it becomes backslash-plus-`n` in the emitted script. Do not use escaped line-break text inside a multiline template unless the resulting shell bytes are explicitly intended and tested.

For generated ImageBuilder wrappers, require both shell syntax validation and actual execution of each security-relevant branch using a disposable Makefile. In particular, the empty-image denial must return its expected nonzero status and diagnostic, create no release manifest, and preserve external sentinels. A syntax-only test is not a substitute for the runtime regression.

At COE RELEASE #31 exact head `d45b84c67dc587fca6226662cb1d8bc59bdb11ae`, packager blob `fd558928b2869ce1f4b2cb2776b405b4b723b310`, source line 495 contains literal `\\n` sequences between the empty-image guard and checksum command. A minimal local reproduction returned `sh -n=0` but execution exit 2 (`Syntax error: Bad fd number`). The exact-head sandbox workflow [#44104956173](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104956173), job `134126241456`, was IN_PROGRESS at last read; no final CI result is claimed.

PHX-RELEASE owns the correction on COE #31; PHX-QA independently verifies the exact corrected head. PHX-MASTER owns this contract and integration gate only. Keep #31/#26 draft; no migration or release. **PRODUCTION NO-GO.**


### §6.12 exact-head CI follow-up — 2026-11-17 UTC15:14Z

COE #31 sandbox run [#44104956173](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104956173), job `134126241456`, completed `CANCELLED` at exact head `d45b84c67dc587fca6226662cb1d8bc59bdb11ae`. The log shows 15 packaging tests returned `ok`, including the syntax-only generated-wrapper check, then the operation was canceled at 15:14:22Z. The runtime empty-firmware test was not reached. Do not report this as a source-test failure or pass; it is incomplete evidence. Require a non-cancelled exact-head runtime execution after RELEASE corrects the literal `\\n` template sequence, then independent QA review.

## 6.13 Generated-wrapper newline correction is source-only until exact-head sandbox CI completes — 2026-11-17 UTC15

The earlier literal-backslash-n defect in COE RELEASE #31's generated shell template is corrected in the current source candidate. The release-owned test-first commit is [293a006d](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/293a006d6809493ba164f10d1e2917e8979e1633), the source correction is [b14841e7](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/b14841e75d57144f8c72867ef54fdff796b9483d), and the current handover head is [06d8b7c5](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/06d8b7c593f8e139891a6a659bf79e694ee229d5). At that exact head, packager blob `66fc283eb52add75caee6131b78dcadbb5d8a7fc` contains actual multiline shell template text, and test blob `3e917c30654ce629391c3fbd864d5b671b0a2e46` contains `test_generated_wrapper_emits_empty_image_guard_as_real_shell_lines`.

**Current exact-head evidence:** sandbox run [44113058229](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058229), job `134155724688`, is still IN_PROGRESS; do not report a PASS or failure until it concludes. Shared/hardware run [44113058271](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058271) and case-collision run [44113058276](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44113058276) are SUCCESS, scoped only.

A separate execution-boundary blocker remains: `generate_build_script()` still emits a wrapper that changes to `$BUILD_DIR` and invokes the interpolated ImageBuilder command directly. It does **not** invoke `run_imagebuilder_sandbox.py` or bubblewrap. The dedicated workflow sets `PHX_REQUIRE_BWRAP=1`, and the test harness invokes the helper, but that proves only test-harness containment—not that an operator's generated build entrypoint is sandbox-enforced. PHX-RELEASE must enforce the supported operator path or document and independently verify a mandatory isolated build-host boundary; PHX-QA must test that exact invocation. The helper uses `--share-net`; network isolation is not present or claimed, and its read-only host-root bind is a write boundary, not a confidentiality boundary.

The independent ULA blocker is unchanged: the packager still emits `fd00:db8:blaze::/48`, and the exact packaging test file contains no ULA parser assertions. Preserve §6.9: site-scoped RFC 4193 /48 generation/persistence belongs to installation identity, not a shared hardware profile. PHX-RELEASE owns implementation, PHX-CORE/COE define provisioning, PHX-QA independently verifies, PHX-HARDWARE validates only after correction and authorization. PHX-MASTER owns the contract and integration gate only.

Bounded live-source/manifest assertions executed by PHX-MASTER: **13/13 PASS**. These are static source assertions, not Python packaging tests, full Master tests, CI, OpenWrt UCI/netifd execution or hardware acceptance. COE #26 remains draft with five queued workflows and zero jobs returned. Keep #26/#31 draft and **PRODUCTION NO-GO**.


## 6.14 COE #31 operator sandbox correction and runtime timeout — 2026-11-17 UTC16

The earlier UTC14/UTC15 finding that the generated operator wrapper bypassed the sandbox is superseded at current COE RELEASE #31 head `9c2bebf50030c03bc4dd1e827e050863ba482eab`. Packager blob `f819ef1cd5265ff026e8a98ad9541c36ed087617` now validates the runner and routes an uncontained operator invocation through `sudo -- python3 run_imagebuilder_sandbox.py`; runner blob `ce098e44e847c265604e3dbb5d8df505025dd0ad` uses a read-only host-root bind and a writable bind only for the ImageBuilder workspace. The runner uses `--share-net`; network isolation is not provided or claimed. This is a filesystem write-boundary claim, not a confidentiality guarantee.

Runtime acceptance remains **BLOCKED**. Exact-head sandbox run [44125258197](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44125258197), job `134197585782`, was CANCELLED at the workflow's 20-minute timeout after 15 packaging tests reported `ok`. The first unreported test by unittest sort order is `test_generated_wrapper_contains_make_created_symlink_write_to_host`; this does not prove that test is the cause. The test helper's `subprocess.run` and runner's `process.communicate` have no per-invocation timeout. RELEASE must bound each invocation, terminate the complete child process group, preserve diagnostics, and rerun the complete exact-head suite; QA independently verifies the same SHA.

The independent ULA P0 remains open: packager blob `f819ef1c...` still emits invalid `fd00:db8:blaze::/48`, and test blob `a5310f90...` has no IPv6/ULA parser coverage. Preserve §6.9: the RFC 4193 /48 is durable installation/site identity, not a global hardware-profile constant. RELEASE owns implementation; CORE/COE define provisioning; QA independently verifies; HARDWARE validates only after correction and authorization.

This source correction does not establish a real OpenWrt ImageBuilder build, UCI/netifd acceptance, network isolation, signing, hardware acceptance, or production readiness. Keep #26/#31 draft and **PRODUCTION NO-GO**.

## 6.15 ImageBuilder user-namespace ownership must remain unprivileged — 2026-11-17 UTC17

**MASTER DECISION — APPROVED FOR IMPLEMENTATION TRIAL AND INDEPENDENT QA REVIEW ONLY.** The preferred model is an unprivileged runner process whose user namespace maps namespace UID 0 and GID 0 to the invoking host user's UID and GID, exactly one ID each. Do not elevate the runner with `sudo`, require `SUDO_UID`/`SUDO_GID`, invoke `newuidmap`/`newgidmap`, provision subordinate UID/GID ranges, or grant a broader host identity. Preserve the owner probe, path checks, disposable writable ImageBuilder bind, and fail-closed behavior. If the host cannot create the namespace without elevation or extra IDs, stop; the only alternative for review is a disposable isolated no-secret runner with an explicitly provisioned least-privilege namespace policy.

This decision is a design direction, not proof that the Ubuntu hosted runner supports the mapping and not sandbox acceptance. PHX-RELEASE must implement the trial on the existing COE #31 branch; PHX-QA must independently verify the exact resulting SHA, one-ID UID/GID mapping, host ownership, symlink/sentinel confinement, timeout process-group termination, and fail-closed behavior when user namespaces are unavailable.

The current COE #31 runner still requires root, `SUDO_UID`/`SUDO_GID`, and `newuidmap`/`newgidmap`. Exact-head sandbox run [44137935105](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137935105), job `134232499311`, fails with `newuidmap: uid range [0-1) -> [1001-1002) not allowed`; the 1-second real-bwrap timeout path was not reached. The current runner uses `--ro-bind / /` and a writable ImageBuilder bind, but `--share-net` retains the host network and the host root remains readable. This is write-confinement only, not confidentiality or network isolation. Do not run untrusted build inputs on a secret-bearing host.

The separate ULA blocker remains open under §6.9. Keep #31/#26 draft and **PRODUCTION NO-GO**.


## 6.16 Hosted ImageBuilder user-namespace capability is a release prerequisite — 2026-11-17 UTC18

**Status: BLOCKED at the runner substrate; the approved single-ID source trial is present but not runtime accepted.** This section supersedes the older §6.15 description of the root/SUDO/newuidmap implementation for the current COE #31 head; preserve §6.15 as historical decision provenance.

COE #31 now starts the runner as the invoking non-root identity and uses bubblewrap `--unshare-user --uid 0 --gid 0` without sudo, SUDO identity variables, newuidmap/newgidmap, or subordinate-ID helpers. The dedicated workflow requires `PHX_REQUIRE_BWRAP=1` on `ubuntu-24.04`. At exact #31 head `d0491517388479aa44c6c0ede8fc876f0be5950c`, sandbox run [44147379837](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379837), job `134266101493`, fails during bubblewrap UID-map setup with `bwrap: setting up uid map: Permission denied`. The suite ran 53 tests and reported 20 failures because the owner probe was never created; the real symlink and delayed-write timeout integration paths were not reached. Shared/hardware [44147379880](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379880) and case-collision [44147379865](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379865) passed only their scoped jobs.

Do not keep changing runner code to compensate for a host that denies the required namespace. The next prerequisite is an infrastructure-owner-approved disposable, ephemeral, no-secret runner with the unprivileged user namespace explicitly available. Do not reintroduce sudo, mapping helpers, broad subuid/subgid grants, or direct unsandboxed Make fallback. Add a clear early capability diagnostic, but never treat an unsupported host as sandbox acceptance or skip the mandatory exact-head integration test.

The runner uses a read-only host-root bind and `--share-net`; host files remain readable and the host network remains shared. This is write confinement only, not confidentiality or network isolation. No secrets/customer data may be exposed to untrusted build inputs; external egress policy must be reviewed outside bubblewrap.

Independent PHX-QA review remains required on the same exact candidate SHA: one-ID UID/GID mapping, host ownership probe, nested-symlink sentinel confinement, actual timeout/process-group cleanup, and fail-closed behavior when namespaces are unavailable. The invalid ULA `fd00:db8:blaze::/48` remains a separate P0. **PRODUCTION NO-GO.**
## 6.17 Exact-head default-deny, sandbox and migration acceptance hold — 2026-11-17 UTC19

**Poll authority remains default-deny.** Current HARDWARE #317 source has no positive `sigOk=true` default and no active `applyRemoteConfig` call. Its source-extracted poll-response lab keeps empty, unsigned, malformed, replay-like and positive-looking unverified replies from restoring intake or outputs. The current Full workflow still fails at the inherited QA assertion `Missing poll signature check`; this is a stale positive expectation, not authority to re-enable poll admission. PHX-QA must replace it with exact-source negative assertions for default-deny, no remote-config mutation and safe output state. Do not add a permissive signature path until CORE publishes the canonical authenticated producer/consumer contract and QA independently verifies the same SHA.

**ImageBuilder namespace support is an infrastructure prerequisite.** COE #31 uses the unprivileged single-ID bubblewrap runner and now contains bounded build timeout/process-group cleanup, but exact sandbox run 44158649032 fails because the hosted runner denies UID-map setup. Do not change the runner to elevate or silently bypass isolation. Require an infrastructure-owner-approved disposable, ephemeral, no-secret runner with unprivileged user namespaces enabled, then independently verify owner mapping, symlink/sentinel confinement, timeout cleanup and fail-closed behavior.

The runner still uses `--share-net` and read-only binds the host root: host network is shared and host files remain readable. This is write confinement only, not network isolation or confidentiality. Never expose secrets/customer data to untrusted build inputs.

**Site-scoped ULA remains mandatory under §6.9.** The current packager's `fd00:db8:blaze::/48` is invalid; no ULA profile property or parser regression exists. Do not guess a replacement or use one global prefix. CORE/RELEASE must define durable installation identity, persistence across reboot/upgrade/restore, and shared same-LAN provisioning; QA must verify generated UCI and negative cases.

**Migration is evidence-gated.** Current #317 firmware/test blobs differ from COE #26 destination, whose sketches/tests/docs retain positive poll/config and quarantine-clear behavior. No file move or destination overwrite is allowed until exact blobs, license/NOTICE applicability, imported test identities, full CI and owner/QA sign-off reconcile. #318 remains a divergent child and cannot be silently composed.

## 6.18 BLAZE-COMMS/1 exact recipient contract — 2026-11-17 UTC20

The envelope `to` field accepts exactly one registered role ID or the literal `ALL`, as defined by `COMMUNICATION_PROTOCOL.md`. It is not a semicolon-delimited recipient list. Unknown roles, list/object/number values, empty values, case variants and leading/trailing whitespace must fail closed. Current Master validator blob `3a6d0ca34cad54cd113abbda17d90898603547b3` enforces this exact rule. QA #292's original RED belongs to older verifier blob `a8a98996...`; its recorded post-fix 4/4 retest used blob `903df403...` at Master commit `0bc5e3fa...`. Current exact-head independent QA rerun is still required; no approval is inferred from the older retest.

The Master regression suite now additionally covers non-string and empty recipient values. Bounded exact-function execution passed 14/14 recipient cases; this is not the full Master suite or CI. **PRODUCTION NO-GO.**

## 6.9 Clear-helper tests are not disposition authority — 2026-11-18 UTC00

A direct test of clearPending() proves only its deletion preconditions. It does not prove that a coin POST received an authoritative disposition. The normal call path must still pass the event-bound receipt/disposition verifier in §6.6. At current HARDWARE #317 source/test head ddc7ed1f, coinPostDispositionVerified returns false for every response; the loop therefore preserves the pending journal/attempt marker and denies automatic replay. No positive coin-clear or quarantine transition is currently authorized.

The source-extracted pending-journal lab compiles the real readPendingFile, checksum, loadPending, attempt-marker match, clearPending and output-gate helpers against fake LittleFS. Its 16 boot and 17 pending-clear scenarios per board are useful software evidence, but not flash durability, crash atomicity, receipt authority or physical power-cut evidence.

Static presence checks for response_sig, |register| or |poll| are not signature verification. In current #283 source, the |poll| and response_sig tokens appear in comments describing the rejected candidate, while register/poll paths call denyRemoteControl(). QA must assert the actual source behavior: poll admission remains denied, target is cleared, outputs remain off, and ambiguous coin disposition preserves pending evidence. CORE owns the producer/receipt contract; QA owns independent vectors/tests; HARDWARE owns firmware. This clarification does not change the existing default-deny contract or authorize a positive path.


## 6.10 Poll-edge fault marker failure is not a reboot guarantee — 2026-11-18 UTC03

At HARDWARE #320 exact head b2b41a3d6ce7887b9624137c966f58462895d3fa, both ESP32 and ESP8266 sketches latch journalRecoveryRequired, disable insert mode, clear the active target, attempt a /pollpulse.fault write, flush/close it, and verify exact size plus byte-for-byte readback. If persistence fails, the source explicitly describes the device as fail-closed this boot. The RAM latch is not proof that a pulse edge survives reboot when no other durable pending record remains.

The boot path treats an existing marker as a deny latch and does not auto-clear it. The writer's failure path has no independent durable fallback. Therefore:
- Do not claim reboot/power-cut durability from the RAM-only failure latch.
- Do not enable poll/coin intake or clear evidence after an ambiguous marker write/readback.
- Require exact-head QA failure injection for marker open/short-write/readback failure, mount failure, reboot with a valid/partial marker, and reboot when marker persistence failed and no pending record exists.
- CORE/MASTER must define durable recovery semantics; HARDWARE owns implementation; QA owns independent vectors.
- coinPostDispositionVerified() and acceptPollResponse() remain hard false on both boards. No positive poll or financial disposition path is authorized.

This clarifies the durability boundary only; it does not alter firmware or grant production authority.

## 6.11 Poll-fault marker-open failure has no reboot proof — 2026-11-18 UTC03

At HARDWARE PR #320 exact head `b2b41a3d6ce7887b9624137c966f58462895d3fa`, both sketches implement a readback-verified `/pollpulse.fault` marker. The writer checks open, full write length, flush/close, exact file size and byte-for-byte readback. `latchPollPulseFault()` sets `journalRecoveryRequired`, disables insertion, clears the active target and applies outputs before attempting persistence. If marker creation/readback fails, the source explicitly reports only that the device remains fail-closed **this boot**.

The boot loader restores this fault latch only when `/pollpulse.fault` exists. If marker creation itself fails and no other durable pending record survives, the RAM-only latch can disappear on reboot. The current `poll_loop_blocking_inhibit_lab.py` injects `fakeOpenFail` and checks same-boot relay/LED denial, but the open-failure case does not reboot or call `initPendingStore()` afterward. It therefore does not prove reboot-safe recovery for the no-marker case.

Required before any durability claim:
- PHX-QA adds an exact-source reboot/reset vector after marker-open failure and after short-write/readback failure, including the case with no surviving pending record.
- PHX-HARDWARE implements an owner-reviewed durable fallback/witness or preserves another durable record that causes boot to remain denied.
- PHX-CORE reviews event identity, receipt/replay and reconciliation semantics; PHX-QA independently verifies the same exact source SHA.
- Keep poll admission, coin POST disposition, automatic replay and relay output fail-closed until the combined exact-head behavior is verified.

Bounded Master source assertions on the exact #320/#322 files passed 15/15; these were static source checks, not firmware runtime tests. The #320 focused poll-edge workflow [44225475672](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225475672) is attached to predecessor source/test SHA `b6e9cfa75105e6cd29c29b93266255d3110c8296`, not the final #320 head. The current #320 focused quarantine/relay runs passed, but no current-head poll-edge run was returned. This section records a test/contract gap; it does not approve a durable implementation.


## 6.19 COE INTERCON journal formats remain unadopted — 2026-11-18 UTC04

COE draft PRs #39, #40 and #42 independently implement the same Stage-3 staging path from #38 but define different on-flash formats: 64-byte (#39), 76-byte (#40) and 92-byte (#42). Their sketch, workflow and journal/test blobs differ; #41 is a Stage-4 child of #39 only. These are review candidates, **not the canonical Phoenix financial receipt/journal contract**. Do not connect any of them to BlazePwifi Vendo, the live Pisonet timer, customer balances or COE #26 until one format is selected by its owner, independently reviewed by QA, and validated on actual hardware. CRC32 detects corruption; it does not authenticate a peer or authorize money. The host fault-injection runs do not prove real LittleFS/power-cut atomicity. See [COE_INTERCON_STAGE3_PARALLEL_JOURNAL_LINEAGE_AUDIT_20261118_UTC04.md](COE_INTERCON_STAGE3_PARALLEL_JOURNAL_LINEAGE_AUDIT_20261118_UTC04.md). **PRODUCTION NO-GO.**

## 6.20 Poll-fault secondary stores are same-chip fail-closed fallback only — 2026-11-18 UTC05

At PHX-HARDWARE PR #323 current head `f98bc39c29eeb82b292aa83fa680d05d2e36efd5` (source/test change commit `6738171209a748c3c210ac13ebe69450eb6405f5`), both ESP32 and ESP8266 `latchPollPulseFault()` implementations now set the RAM deny state, disable insertion, clear the active target, and invoke `applyOutputs()` before any potentially blocking NVS/EEPROM or LittleFS persistence. This output-inhibit ordering is a required fail-closed invariant; it does not prove the electrical relay has physically deasserted.

The candidate adds:
- ESP32: a fixed 20-byte versioned NVS record at namespace `phx_fault`, key `poll_fault`, with write-length and exact readback checks.
- ESP8266: a 20-byte sticky record at EEPROM-emulation offset 512 in a 544-byte buffer; static assertions keep the existing Config before offset 512, then commit/end/reopen/readback.
- Any existing or malformed record is a deny hold; no auto-clear is added. FNV-1a is corruption detection, not authentication or anti-rollback.

These are separate regions on the same physical flash chip, **not an independent physical witness**. If either marker persists, boot remains denied. If both stores fail, the source explicitly guarantees only current-boot fail-closed behavior; reboot durability is not established. Do not claim crash-atomic financial state, independent anti-rollback, or production durability from this fallback.

Exact-head source-extracted dual-store lab [44242190343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190343) reports PASS for both boards and `EXPECTED_CURRENT_BOOT_ONLY` for both-store failure. Relay/output lab [44242190332](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190332) passes logical host scenarios. Full build [44242190324](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44242190324) fails the QA-owned legacy `Missing poll signature check` assertion; 14 target/platform builds pass, downstream simulations/signing/publishing are skipped. These are CI/source-extracted results, not real flash or physical acceptance.

Require independent QA reboot vectors for primary/secondary read/write failure, corrupt/partial records and both-store failure. Preserve poll/coin default-deny. Keep #323 draft-only; no COE #26 migration or production authority is granted. See [HARDWARE_POLL_FAULT_DUAL_STORE_AND_COE_STAGING_RECONCILIATION_20261118_UTC05.md](HARDWARE_POLL_FAULT_DUAL_STORE_AND_COE_STAGING_RECONCILIATION_20261118_UTC05.md). **PRODUCTION NO-GO.**

---

## 6.21 COE INTERCON Stage-3/Stage-4 candidates — provisional integration boundary (2026-11-18 UTC06)

COE INTERCON is not an adopted Phoenix financial authority. Three incompatible Stage-3 candidates remain open: #39 uses a 64-byte record, #40 a 76-byte record, and #42 a 92-byte record. Stage-4 #41 is a journal-only shadow-credit child of #39; Stage-4 #43 is a live timer/relay child of #42. Do not combine these formats or call either Stage-4 branch canonical without an explicit COE owner decision, independent QA and a reversible format migration plan.

The #43 source commits Master pending state before CRED and commits Slave paid time + receipt/sequence before live timer/output changes. That is useful candidate ordering, but it is a two-device prototype, not integration with the Phoenix CORE ledger: the PR explicitly leaves the BlazePwifi router adapter and multi-target accounting separate. Any future integration must map to the canonical receipt/event identity, idempotency, disposition and reconciliation contracts in §§1–2. A local 64-bit sequence and paid-event count are not by themselves proof of cross-system receipt parity.

The current #43 unresolved pulse count is RAM-only and absent from its journal record. A failed/unavailable Master journal can therefore leave an unresolved physical coin alarm without demonstrated reboot persistence. Such a state must remain deny/CS-off and must be durably reconciled before another paid event is admitted.

The inspected peer-auth source stores a raw 32-byte shared key in a LittleFS config record. No protected key store or independent signer is shown in the inspected files. HMAC transport and a checksum do not satisfy the independent protected P-256 signer / anti-rollback witness gate.

The #43 host end-to-end test models two journal slots in RAM and copies encoded bytes to simulate a rename boundary. It does not certify actual LittleFS metadata atomicity, flash brownouts, watchdog behavior or power-cut recovery. Its 650 ms burst grouping and 60-second timer checkpoint are prototype assumptions; the latter can restore up to approximately 60 seconds of consumed time after a sudden outage. Physical coin acceptance, CS inhibit/hold-up, relay behavior and real flash recovery remain NOT TESTED.

#41 remains shadow-only and must not be represented as live paid-time acceptance. #43 changes live timer/relay behavior but remains DRAFT / NO-GO. No COE INTERCON source route exists in OWNERSHIP_ROUTES.json; no PHX-PISONET or PHX-HARDWARE ownership is inferred for this subtree.

---

## 6.22 Current poll admission is intentionally hard-deny; legacy positive-signature fixture is incompatible — 2026-11-18 UTC07

At current PHX-HARDWARE PR #323 source/test SHA `a3aa967087680887e925791f83a8fbc48a1e62b9` (current PR/docs head `0d6f0c7f4f9d2d07bc43d24e5db63d8bddb11f43`), both ESP sketches keep `acceptPollResponse()` deny-only: ignore the response, force `insertMode=false`, clear `activeTarget`, and return false. Both `coinPostDispositionVerified()` functions also return false. This is the current safe contract, not an incomplete positive verifier.

The current Experiments `cgi-bin/vendo` poll branch (blob `2e3a1430d08cc6606429a042df3b5848f53c7267`) emits no `response_sig`. The inherited `tests/v05_firmware_hardening_test.sh` (blob `41211b2c110ab409f6d9d1812ef12fda73b13211`) still requires `response_sig` and literal `|poll|` in both sketches, so the Full workflow fails at `Missing poll signature check`. That fixture does not match the current deny-only contract or current producer. It must be replaced by negative tests proving unsigned/unknown responses cannot enable insertion, retain a target, clear a pending coin or authorize disposition. Do not add a synthetic signature string or enable unauthenticated poll admission to satisfy the old assertion.

A positive poll path remains blocked until PHX-CORE publishes a canonical producer/consumer schema and golden vectors, PHX-QA verifies both sides at pinned SHAs, and the independent signer/anti-rollback gates are satisfied. See [HARDWARE323_POLL_DENY_CONTRACT_AND_EXACT_HEAD_RECONCILIATION_20261118_UTC07.md](HARDWARE323_POLL_DENY_CONTRACT_AND_EXACT_HEAD_RECONCILIATION_20261118_UTC07.md). **PRODUCTION NO-GO.**


## 6.23 Exact poll response producer/consumer reconciliation — 2026-11-18 UTC08

**Decision:** the current Experiments source producer and the current #323 firmware consumer do not implement an authenticated positive poll response. Keep coin admission and coin POST disposition fail-closed. The COE #26 response-signature expression is a separate, unapproved candidate and is not permission to copy or enable it.

### Exact refs and source evidence

| Component | Exact ref / blob | Observed behavior |
|---|---|---|
| Experiments development `blazepwifi-v0.5.3-development` | branch HEAD `aad3aade72c1156eecba1fed30907c6d0283b2c5`; `vendo` blob `a1c19180385e618c412b4af21c0e91c1f47da1dd` | `register|ping`, `poll`, and `coin` response bodies contain no `response_sig` |
| Experiments development `common.sh` | blob `ca4920d3d9572382fb381a325183a18311be5954` | `bp_vendo_sig_expected()` / `bp_check_vendo_sig()` check a keyed SHA-256 concatenation (not standard HMAC); `bp_json()` only prints headers and the supplied JSON, with no response-signing wrapper |
| Experiments development `controller.sh` | blob `54bdc59949884bd3e734f8c07ddeb1d7c2cf9848` | `bp_controller_json()` emits configuration fields, not an authenticated configuration envelope |
| Current HARDWARE #323 ESP8266 | source/test SHA `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`; sketch blob `8e79b9eb8856e67d966f4c6385f89fccdc8be7fc` | `acceptPollResponse()` and `coinPostDispositionVerified()` return false; missing register `response_sig` leaves remote configuration disabled |
| Current HARDWARE #323 ESP32 | same source/test SHA; sketch blob `bd74b11c1496b0943404ff387ee72bb45d4743e5` | Same deny-only poll and coin disposition behavior |
| COE integration #26 | head `b382d233ff06c8791b1028bed3c617cc7b670d12`; `vendo` blob `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e` | Contains `vendo_poll_sig()` and emits a candidate `response_sig`; its construction is keyed SHA-256 concatenation, not standard HMAC |

The COE candidate's poll expression is ordered as secret, action, controller ID, request nonce, insert flag, target nonce, expiry, secret, then SHA-256. Structural field-order similarity is not cryptographic approval: there is no accepted canonical schema, key/version lifecycle, independently executed shared golden vector, or exact combined-tree QA evidence. Do not transplant this candidate into Experiments or infer that #323 consumes it.

### Exact #323 CI and stale QA fixture

- Current PR/docs head: `4850b16a31a1ccb67f265e5224a2799b25cf2e01`; source/test SHA: `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`; parent #322: `50d93e0de3d682550b6f02fb43484e76ad9c7e08`.
- Focused quarantine/readback run [44262258247](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258247): SUCCESS.
- Focused relay/output run [44262258937](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258937): SUCCESS.
- Full build [44262258842](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44262258842): FAILURE at validation job `134658178171`, which reports `Missing poll signature check` in ESP8266. All 14 firmware target jobs and Android completed SUCCESS; downstream import, update, simulations, candidate gate, signing and publishing jobs were SKIPPED.
- The exact merge-tree QA fixture `v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` requires literal `response_sig` and `|poll|` presence. It does not test the current intentional deny-only behavior. The `controllers.sh` entrypoint blob `f7896647713d6bf8034ff48ed19b6383e4dedea0` invokes this fixture.
- The focused CI runs are source-extracted simulations, not physical flash, GPIO, coin-acceptor or power-cut acceptance.

### Owner actions — no source takeover

1. **PHX-QA:** replace the positive `|poll|` string-presence assertion with source-linked negative behavior tests for both boards: arbitrary/missing/forged poll bodies must leave `insertMode=false`, clear `activeTarget`, and never enable intake; coin POST disposition must remain false. Keep the test bound to the exact #323 source/test SHA.
2. **PHX-CORE:** define the canonical versioned response schema, cryptographic construction (do not label concatenated SHA-256 as HMAC), key identity/version, nonce and target binding, freshness/expiry, canonical field order, and positive/negative golden vectors.
3. **PHX-HARDWARE:** retain deny-only behavior until the approved producer and consumer exist; keep source/test and handover refs synchronized.
4. **PHX-RELEASE:** keep downstream signing, candidate-gate and publishing jobs closed while validation fails.
5. **PHX-MASTER:** maintain this contract and migration matrix only; do not edit worker-owned firmware, CGI or QA fixture files.

### Integration and release boundary

COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, with five workflows QUEUED and zero jobs. Its staged poll producer differs from Experiments development; exact per-file source/destination blob, license/NOTICE, import-completeness, test-identity and exact-head CI review is still required. No file was copied, moved, overwritten or deleted. The ownership manifest remains `DRAFT_REVIEW_ONLY`, with PHX-MASTER destination null.

The private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed Library/Drive surface. The AGENTS-linked cloud artifact policy/storage handover could not be retrieved through the GitHub connector or web endpoint; COE root `AGENTS.md` returned 404. No older registry snapshot was substituted and no private registry contents were published.

**Status:** DEVELOPMENT / LAB ONLY; integrated acceptance UNKNOWN; physical acceptance NOT TESTED; **PRODUCTION NO-GO**. Independent protected signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

## 6.24 Current HARDWARE #323 to COE #26 provenance and test-identity hold — 2026-11-18 UTC09

**Decision:** keep #323 and COE #26 separate DRAFTs. The current source candidate is not byte-identical to the staged destination and its source dual-store lab is not imported or invoked there. No copy/move/overwrite or positive poll admission is authorized.

- Current Hardware branch/docs head: 1761bf38d01c44f3bfd87acc6c7f03d97d7e1d17; exact source/test SHA: d37d5da9bdd8e3be08f6344f4a2520c29c2d0abb; parent #322: 50d93e0de3d682550b6f02fb43484e76ad9c7e08.
- COE #26 head: b382d233ff06c8791b1028bed3c617cc7b670d12. ESP32 source/destination blobs bd74b11c1496b0943404ff387ee72bb45d4743e5 / 3cc7ec54b476943dc04a8d1af5e2df5fe054e422; ESP8266 source/destination blobs 8e79b9eb8856e67d966f4c6385f89fccdc8be7fc / c8be98f72596681e36a3ad1f8939bf8046c96887. Both pairs differ.
- Source dual-store lab blob 25f5e8bd1a344d69acc0505324156f66a1abffa4 has no COE #26 mapped counterpart. The source Hardware workflow blob 2358e4ab940b9879e961046180f01fc3d5356709 is not the COE Hardware workflow blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793; COE's workflow invokes a different generic test script.
- COE #26 test blob f921c56cecc19cab1989507b9b4ade1f45dac54e still greps for response_sig and |poll|; current source remains deny-only. COE Hardware README's keyed SHA-256 concatenation label is not standard HMAC.
- Source MIT license blob 1ee55b94183417be977ca287cd7391f9a6f7e721 equals sibling Pisowifi/LICENSE, but Hardware/root LICENSE/NOTICE applicability is unresolved; source root NOTICE is absent in the destination tree.
- #323 current-head focused CI [44278980129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980129) and [44278980263](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980263) PASS; Full [44278980291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44278980291) fails at Missing poll signature check. COE #26 has five queued workflows and zero jobs.

The source MIT license and sibling Pisowifi license match does not establish Hardware subtree licensing. The current QA fixture mismatch is not permission to add synthetic signatures or enable positive admission. See [HARDWARE323_CURRENT_HEAD_AND_COE26_MIGRATION_PROVENANCE_20261118_UTC09.md](HARDWARE323_CURRENT_HEAD_AND_COE26_MIGRATION_PROVENANCE_20261118_UTC09.md). **PRODUCTION NO-GO.**

## 6.25 UTC12 — poll-fault output-inhibit ordering (provisional, source-verified)

PHX-HARDWARE selected the #322 → #323 review-candidate stack in control-plane comment 6978026438. This is an owner-reported candidate selection, not a Master merge decision or hardware acceptance.

At #323 PR/docs head 0975fe4416daa72c097d3fee2b631950eb64908c, both board sketches contain the same latch ordering: set journalRecoveryRequired, disable insertMode, clear activeTarget, call applyOutputs(), then attempt the secondary NVS/EEPROM backup and LittleFS marker. If both stores fail, the source explicitly says the current boot remains fail-closed but reboot durability is NOT established. The two stores are not an independent protected witness.

Exact source/test commit 176ad50da2180ee085e2fb63ddb23d17b53dd63d corrected the source-extracted mutation so the deferred-output-inhibit mutation actually matches the source newline. Exact-head focused runs 44301775875 and 44301775918 pass; their logs show POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS and reject defer-fault-output-inhibit on ESP8266 and ESP32. This is host/source-extracted CI only.

Full build 44301775872 fails at the QA-owned Controller protocol parity assertion Missing poll signature check in the ESP8266 sketch. All 13 firmware-target jobs and Android completed successfully; downstream simulations, candidate gate, signing and publishing were skipped. Both acceptPollResponse() and coinPostDispositionVerified() remain deny-only. Do not add a synthetic signature or relax firmware to satisfy the stale positive fixture.

PHX-QA owns replacing the positive string-presence fixture with exact-source negative behavior tests. PHX-HARDWARE owns refreshing the stale #323 PR description (it still cites older docs/source SHAs) and reconciling sibling #324. PHX-CORE owns the canonical response envelope and replay contract. Physical relay, coin, flash, power-cut and soak acceptance remain NOT TESTED.

---

<!-- PHX-MASTER-20261118-UTC13-ESP8266-BOOT-POLARITY-AUDIT -->


## 2.1.2 Boot-time relay/LED polarity must be established before first OUTPUT transition (2026-11-18 UTC13)

The OFF-preload ordering above is safe only when the polarity variables already match the physical relay/LED wiring before the first call to `configureRuntimePins()`. The source-exact audit in [HARDWARE_ESP8266_BOOT_POLARITY_SOURCE_AUDIT_20261118_UTC13.md](HARDWARE_ESP8266_BOOT_POLARITY_SOURCE_AUDIT_20261118_UTC13.md) found a board-specific gap:

- At HARDWARE #323 source/test SHA `176ad50da2180ee085e2fb63ddb23d17b53dd63d` (docs-only PR head `0975fe4416daa72c097d3fee2b631950eb64908c`), ESP8266 initializes `runRelayActiveHigh=true` and `runLedActiveHigh=true` at line 46. The only later assignments to those runtime polarity values are inside `applyRemoteConfig()` (lines 587–605), which is explicitly marked intentionally dormant because the returned configuration is not authenticated. The ESP8266 `setup()` reaches `configureRuntimePins()` without a persisted/local polarity load.
- Therefore the source currently demonstrates the OFF-preload sequence only under the active-high default for ESP8266. It does **not** establish a safe active-low ESP8266 boot profile. If a deployed relay is active-low, the active-high default may drive the wrong physical level; the actual wiring is not inferred here.
- ESP32 is a separate path: `loadConfig()` reads relay/LED polarity from Preferences and `setup()` loads it before the first `configureRuntimePins()`. This source distinction is not physical acceptance and does not prove behavior for corrupted/missing NVS or every board.
- The #323 poll-fault host lab observes the relay/LED state at both the secondary backup-write and LittleFS marker-open boundaries. That proves the fault latch deasserts outputs before those persistence calls in the extracted control-flow harness; it does not prove the boot-time polarity source or electrical behavior.

**Required gate:** PHX-HARDWARE must either (a) define and document a verified active-high-only ESP8266 target profile with board/wiring evidence, or (b) implement a persistent, validated local polarity source loaded before the first output configuration. PHX-QA must independently test cold boot with default, missing, corrupt and each supported polarity value, including the first GPIO level before OUTPUT mode. Do not activate remote polarity configuration until the authenticated response-envelope contract and exact-SHA QA vectors are approved. Physical relay voltage and reset-state acceptance remain NOT TESTED; no firmware flash or production admission is authorized.



## 6.25 Current ESP8266 local boot-polarity implementation and test-wiring hold (2026-11-18 UTC14)

**Disposition: BLOCKED at the exact current HARDWARE #323 head; no boot-polarity implementation or CI verification is established.**

The Hardware owner acknowledged an implementation plan in control-plane comment [6980748685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-6980748685), but the current PR head is now 9cd889ec184c81d96569d3994602da3076efb537. At that exact head:

- ESP8266 sketch blob: 8e79b9eb8856e67d966f4c6385f89fccdc8be7fc. The file contains ConfigV1 and the current Config record with MAGIC 0x42505732; it has no ConfigV2/ConfigV3 structure, no outputPolarityConfigured/outputPolarityKnown state, no configChecksum, and no local relay_active_high / led_active_high setup fields. loadCfg() at line 498 accepts the current record or migrates V1; setup() at line 1379 loads that config and calls configureRuntimePins() without a validated local polarity source. applyRemoteConfig() contains remote polarity assignments, but that function is explicitly dormant and is not an authorized boot-time source.
- New boot-polarity lab blob: f08e1aadc40acf09e08ad055c92a38073c33f6c2. Its first prerequisite checks require the missing ConfigV2, outputPolarityConfigured, outputPolarityKnown, configChecksum and local setup fields. The lab is not source-compatible with the exact sketch blob and would fail if actually invoked at this head.
- Workflow blob: dd2692df58c5311ad5d365a5539279da2018d8f7. The new command is written as a folded YAML plain scalar: the second Python line is part of the first command, not a second command or step. The exact Actions log for run 44320124000 confirms the shell received one command containing both script names. Only the relay-output lab ran; the boot-polarity lab did not execute.

Therefore the focused relay/output result [44320124000](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320124000) is PASS only for the existing relay-output lab. It is NOT boot-polarity regression evidence. Quarantine/readback [44320123810](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320123810) passed independently. Full build [44320123851](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320123851) completed FAILURE. Validation job 134856529480 failed at Controller protocol parity with the exact message Missing poll signature check. All 13/13 firmware target jobs and Android job 134856530339 completed SUCCESS; downstream simulations, update bundle, candidate gate, signing and publishing jobs were SKIPPED. This is not Full CI acceptance.

**Required owner actions:** PHX-HARDWARE must first commit the actual versioned local polarity record, fail-closed V1/V2 migration, boot-time read/validation before any output configuration, and strict local setup AP 0/1 selection. Correct the workflow using a block scalar (run: |) with separate commands or a separate step, then verify the log shows the boot lab itself executing and its negative mutations being rejected. PHX-QA must independently test cold boot with default, missing, corrupt, active-high and active-low values, including the first GPIO level before OUTPUT mode, at the same exact source SHA. Do not read polarity from unauthenticated remote configuration. Physical relay voltage/reset-state acceptance remains NOT TESTED.

This section supersedes the earlier UTC13 statement that the local-polarity implementation was in progress as if the current source already contained it. The owner plan is real; the current source implementation is not yet present. Keep the candidate DRAFT, keep financial/coin admission NO-GO, and do not migrate this firmware into COE.

## 6.26 — ESP8266 ConfigV3 local polarity authority (provisional; 2026-11-18 UTC14)

The current Hardware review candidate #323 at 4dc5fd566da6ed3e523e3e15174837f5cfb8b183 introduces an ESP8266-only local ConfigV3 polarity profile. V1/V2 migration leaves polarity unconfigured; boot validates the record before runtime pin configuration; unknown polarity leaves relay/LED pins as INPUT and blocks poll/coin paths; only the WPA2 setup AP accepts explicit 0/1 local polarity values. EEPROM commit is followed by reopen/readback and full record comparison.

Focused exact-head CI 44329837932 and 44329837962 passed, including the boot-polarity lab and interrupt-attachment mutation rejection. Full build 44329837987 was pending at the snapshot. This is host-simulation evidence only. Physical relay, coin pulse and power-cut acceptance remain NOT TESTED. Do not generalize the ESP8266 profile to ESP32; the ESP32 configuration path requires separate review. Poll-response admission and coin-post disposition remain deny-only.



## 6.27 — Current ConfigV3 failure-latch result and ESP32 polarity parity (2026-11-18 UTC15)

At current Hardware #323 head `bc0447f013698a2e45c154b0ae69a098b0e75fe5`, ESP8266 ConfigV3 is present (firmware blob `283dbe329a5445931cc9fe7096561a68b9c8bf62`). Its default/missing-config and V1/V2 migration failure paths call `latchConfigPersistenceFailure()`, which clears output-polarity authority, keeps GPIO configuration unsafe, disables insertion and sets `journalRecoveryRequired=true`. The boot lab (blob `25fe2f6040f59c4fa74c9d88c821aed9804d3fe2`) now actually executes: workflow blob `1140daf71d5218c9c58cdf74ae4cc3ab3822c51a` uses separate block-scalar commands, and run [44330729195](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44330729195) shows the relay lab passing before the boot lab fails at the `journalRecoveryRequired` assertion after injected EEPROM commit failure. The visible firmware path and observed source-extracted result contradict one another; root cause is unresolved. Do not label the firmware or test harness correct until Hardware instruments the fake commit, extraction and latch path and reproduces the branch decision.

**Cross-board P0:** ESP32 blob `bd74b11c1496b0943404ff387ee72bb45d4743e5` is not at ConfigV3 parity. Its `Config` defaults relay/LED polarity to active-high; `loadConfig()` reads Preferences with `getBool(..., true)`; setup calls `configureRuntimePins()` before `setupPortal()`; and that routine writes logical OFF using the default polarity before enabling OUTPUT. It has no explicit unknown-polarity validity flag or INPUT hold. The local setup form appears later and cannot protect the initial output transition. For active-low relay wiring, the default LOW write is potentially active. No physical assertion is made, but the source ordering is insufficient for a safe active-low boot claim.

**Required contract:** both boards must boot with relay/LED pins as INPUT until a locally configured, validated, durably read-back polarity profile is known. Unknown, missing, corrupt, future-version or failed-commit state must remain fail-closed; no remote response may establish polarity. QA must independently verify both board paths at the same exact source SHA. Focused host tests are not physical acceptance; poll/coin admission remains deny-only. **PRODUCTION NO-GO.**


## 6.28 — UTC16 ConfigV3 two-board boot gate and COE poll-contract provenance (2026-11-18)

At current HARDWARE #323 head 988904e8bcd058b62a9fac4aa6319a9b7c5b2470 (latest source/test tree 359bd8f685a2a464f4a77b84501fcf4055944d5c; later commits are documentation-only), both ESP8266 and ESP32 now have source-extracted local polarity boot gates. ESP8266 ConfigV3 uses validated local persistence/readback; V1/V2 and unknown/future schemas remain unconfigured, and missing/corrupt/failed-commit state stays fail-closed. ESP32 holds unknown/legacy polarity as INPUT until the local marker/profile is validated and read back. Focused logs record ESP8266_COMMIT_FAILURE_TRACE=PASS, UNKNOWN_EEPROM_SCHEMA_PRESERVED=PASS, ESP8266_BOOT_POLARITY_CONFIG_V3=PASS and ESP32 boot-polarity gate PASS. Runs: [44347847077](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347847077) and [44347847191](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347847191).

This supersedes §6.27's prior unresolved failed-commit / ESP32 parity statement. It is Hardware-owner source/test + focused CI evidence only; both labs report SIMULATED_ONLY, physical relay/polarity and power-cut acceptance remain NOT TESTED. QA has not independently accepted the same exact source/test tree.

Full #323 [44347846832](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347846832) still fails at QA-owned Missing poll signature check; 13/13 firmware targets and Android completed, but downstream simulations/signing/publishing did not pass. The source fixture requires positive response_sig and |poll| strings. Current firmware poll-response admission and coin-POST disposition remain deny-only. Do not add synthetic signatures or relax firmware. QA must replace the stale positive-presence test with negative default-deny behavior tests; CORE owns the canonical producer/consumer contract.

COE #26 is not a safe migration destination at current head b382d233ff06c8791b1028bed3c617cc7b670d12: both board firmware blobs differ from current #323, all three new boot/dual-store labs are absent, the generic Hardware test still expects positive poll signatures, and its workflow does not invoke the new labs. Source main/development poll producers do not emit a signed poll response, while the COE destination producer adds vendo_poll_sig. Source MIT license matches Pisowifi/LICENSE, but Hardware-scoped LICENSE/NOTICE and COE root LICENSE/NOTICE are absent. No move/copy is proposed; manifest remains DRAFT_REVIEW_ONLY / target null. **PRODUCTION NO-GO.**


## Live exact-head contract reconciliation — 2026-11-18T17:39:33Z

HARDWARE #326 is now at PR/docs head `58c558fb6a237935214621adc3dee65a10fe1a51`, with source/test commit `28e13fc82a250821e815fd84b5fd61f1769e7106`. The current source-extracted lab compiles production `latchPollPulseFault()` and `sampleCoinPulseEdge()` for ESP32 and ESP8266; only persistence backends are fault-injected. The latch deasserts outputs before attempting both NVS/EEPROM and LittleFS markers. If both fail, the source explicitly says current-boot denial only and reboot durability is NOT established. This same-chip fallback is not an independent witness, durable ledger, receipt, or proof of coin recovery.

Focused PR runs [44358712365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712365) and [44358712238](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712238) pass on PR head `58c558fb...`; Full [44358712823](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44358712823) fails the inherited QA positive `Missing poll signature check`. Firmware poll/coin admission remains deny-only. QA must change the fixture to negative deny behavior; do not add synthetic signatures or relax firmware. These are host simulations/build CI only, not electrical acceptance.



## 6.29 — UTC18 Hardware #327 pre-poll edge and ambiguous backup-commit fence (provisional; 2026-11-18T18:52Z)

Current Hardware stack: PR #323 `988904e8bcd058b62a9fac4aa6319a9b7c5b2470` → child #326 `58c558fb6a237935214621adc3dee65a10fe1a51` → child #327 current docs HEAD `0a26468022d25746fdc38525c0c0979da098f6d4`; exact source/test SHA `e774420c3404141ffe4ec7b9c002c14d3c2286b8`. PR #327 is OPEN / DRAFT / UNMERGED. Firmware blobs at the current #327 tree are ESP8266 `dde063b1f578fa66a52221b74643d8862a38957c` and ESP32 `ada9723c5f07879775284eb128a986ac865394f7`.

### 6.29.1 Pre-poll ISR edge fence

Both sketches snapshot the ISR edge sequence before `beginPollWindow()`. After the quiet-drain helper returns successfully, but **before** synchronous `post("poll")`, the loop snapshots again. If the sequence advanced during the drain window, it calls the existing `latchPollPulseFault(delta)` while poll intake remains inhibited, does not dispatch the HTTP poll, reapplies outputs under the sticky recovery deny, updates the poll timestamp, and defers the next poll. This closes the source-level interval in which an ISR edge could otherwise remain volatile during the blocking HTTP wait.

The source-extracted `poll_loop_blocking_inhibit_lab.py` injects an edge after the final quiet sample and asserts that no poll dispatch occurs before the fault marker. Exact-source focused CI on #327 source/test SHA `e774420c...`: quarantine/readback [44373043845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043845) PASS; relay/output [44373043958](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043958) PASS. The later docs-only PR head `0a264680...` also has focused quarantine [44373742439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742439) PASS and relay/output [44373742382](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742382) PASS. These are source-extracted host/fake-I/O simulations, not physical ISR, acceptor or relay acceptance.

### 6.29.2 Ambiguous backup-commit retry fence

Both sketches now set current-boot `pollFaultBackupWriteFailed` when the secondary NVS/EEPROM set, commit, reopen or readback path is ambiguous. Further same-boot backup writes return false instead of treating dirty EEPROM/NVS cache state as proof of durable storage. A cold boot resets the RAM-only flag and checks the flash-backed marker again. The source-extracted dual-store lab exercises ordinary commit failure, ambiguous commit-after-write, no same-boot retry, and reboot marker detection; both board markers report `FAILED_COMMIT_RETRY_HELD_UNTIL_REBOOT_PASS` and `AMBIGUOUS_COMMIT_RETRY_DENY_REBOOT_MARKER_PASS`.

**Limit:** the flag itself is RAM-only. If both LittleFS and NVS/EEPROM fail and no marker reaches durable media, the source proves current-boot denial only; reboot durability remains NOT ESTABLISHED. Same-chip stores are not an independent anti-rollback/freshness witness, durable ledger or receipt authority. The lab explicitly reports `DUAL_STORE_FAILURE_LIMITATION=EXPECTED_CURRENT_BOOT_ONLY`. This is not a production durability pass.

### 6.29.3 Test-harness correction and Full validation

An intermediate #327 source/test commit `fcb5c1ab...` had a test-only symbol typo `pollFaultBackupBackupPresentOrCorrupt`; quarantine CI failed at C++ compilation before the dual-store and pre-poll labs. Hardware corrected the assertion in test-only commit `e774420c...` to `pollFaultBackupPresentOrCorrupt`. The exact-source focused runs above then passed. Do not carry the intermediate harness failure forward as a current source defect, and do not carry an earlier focused PASS to a different SHA without exact-head evidence.

Full build on the latest docs head [44373742348](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742348) **FAILED**: validation job `135047376378` still rejects the inherited QA-owned positive `response_sig` / `|poll|` assertion as `Missing poll signature check`; Android job `135047377045` separately failed resolving legacy Gradle dependencies (including protobuf-gradle-plugin 0.8.3 and Kotlin 1.2.0 artifacts). Other firmware/platform target jobs completed successfully, but downstream simulation, signing, candidate and publishing gates were skipped. The current firmware remains deliberately deny-only; do not add synthetic positive signatures or weaken it. QA must replace the stale positive fixture with negative default-deny tests and rerun the exact combined candidate.

**Owner routing:** HARDWARE owns #327 source and labs; QA owns the stale poll-signature fixture and independent same-SHA review; CORE owns unresolved-ingress/ledger reconciliation semantics; RELEASE/INFRA own Android dependency and runner/build-environment triage. MASTER records the contract and integration gate only. No source ownership or release authority transfers here. **PRODUCTION NO-GO.**


## 6.30 First-boot ULA generation must preserve site scope across appliances — 2026-11-19 UTC00 refresh

Section 6.9 remains normative: an RFC 4193 `fd00::/8` /48 is durable site identity, unique between independent sites and shared by devices on the same LAN/site. It must survive reboot, upgrade and restore; it is not a static hardware-profile property.

COE Release PR #44 is OPEN / DRAFT at `582fd5d5e83e36b36546ac28534740298ba94af4`, based on #35 at `1a5be48d2845781b0b07bad39a37f8440cea4d4f`. Its first-boot script creates a random 40-bit ULA global ID, validates the resulting /48, persists `network.globals.ula_prefix`, checks the named UCI section type, and scopes rollback to the ULA option/newly-created globals section.

**Exact-head evidence:**
- Shared Hardware/Contracts [run #44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309), job 135105225016: 109 packager tests ran, 2 sandbox-only skips; 10/10 appliance profiles passed. The ULA first-boot, commit-failure rollback and wrong-`network.globals`-type tests executed and passed.
- Case-collision [run #44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296): PASS.
- Mandatory ImageBuilder sandbox [run #44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327): FAILED CLOSED because `bwrap` is absent; 14/14 host-preflight tests passed before the availability gate. No unsandboxed fallback or packaging pass is claimed from this run.

**Remaining contract gap:** random generation per installation does not prove that two independently installed appliances at the same site receive the same /48. The current implementation contains no site-level assignment authority or shared site identity input. Two first boots can therefore produce different prefixes on one site.

**Acceptance before contract completion:** PHX-CORE/COE owners must define a site-scoped assignment authority or explicitly propose a one-installation-per-site constraint for owner review. QA must verify two appliances on one site share the same prefix, independent sites receive distinct prefixes, and reboot/upgrade/restore preserve identity. Missing, malformed, unavailable or conflicting authority must fail closed before network services consume the prefix. No static/global fallback is permitted.

PHX-RELEASE owns first-boot implementation; COE integration owns destination staging; PHX-CORE/COE define provisioning authority; PHX-QA independently verifies exact-source behavior; PHX-HARDWARE validates target behavior only after authorization. PHX-MASTER owns the contract and gate, not implementation. Keep #44/#26 draft. **PRODUCTION NO-GO.**

## 6.31 ESP8266 EEPROM full-image read failure is not an erased Config state — source correction verified, physical durability open — 2026-11-19 UTC00

**Prior source hazard: corrected in the current Hardware candidate; independent QA and physical acceptance remain open.**

Hardware PR #327 is OPEN / DRAFT at docs head `3046c74d19ee1040996860a66cbdcb850acdbe14`; exact source/test head is `6b52d63f889a9567303f9f2de464c743c1991f0c`. Source correction commit is `40cfc0799a6e65e4a724e8ccbe6baa0f5f51de54`.

The ESP8266 sketch now performs a status-bearing raw `ESP.flashRead` of the full 544-byte EEPROM image using the core 3.1.2 EEPROM sector mapping. It reconciles the EEPROM emulation RAM buffer from that verified image before `EEPROM.get()` can supply Config. `configImageReadVerified` gates subsequent configuration and poll-fault writes. If the full-image read or RAM restoration fails, `loadCfg()` latches the persistence failure and returns before defaults, schema migration or commit; output polarity remains unknown and coin admission stays denied.

The source-extracted `config_load_read_failure_lab.py` at blob `9da02102020e97360320cfa7bc1f39a184b20011` executes the production `loadCfg/saveCfg` functions against a fault-injected EEPROM model that reproduces ESP8266 core 3.1.2 `EEPROM.begin()` ignoring the `flashRead` return value. It verifies:
- transient initial `EEPROM.begin()` read failure followed by a successful full-image read preserves the pre-existing poll-fault marker;
- recovered image survives the modeled cold-boot deny check;
- a subsequent full-read failure with marker-only recovery does not commit an unverified Config image;
- persistent full-image read failure prevents save/marker writes and preserves the existing marker.

**Exact-head CI at PR/docs head `3046c74d...`:**
- Quarantine/readback [run #44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021), job 135225761344: PASS; logs include all four EEPROM recovery markers above, plus dual-store and pending-journal source-extracted cases.
- Relay/output [run #44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181): PASS; includes the same EEPROM recovery markers.
- Full [run #44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063): FAILED only at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. All 13 firmware/platform target jobs plus Android succeeded; downstream simulations, update bundle, candidate gate, signing and publishing were skipped.

This corrects the previous full-image-read hazard in source-extracted host tests; it is **not** physical flash or power-cut evidence. LittleFS and EEPROM remain on the same flash device and do not constitute an independent witness. Physical reboot/power-cut behavior, 150 real power cuts, 30-device/24-hour soak, independent anti-rollback witness and production durable-accounting proof remain open. HARDWARE owns #327 source; QA owns the positive-signature fixture correction and independent same-SHA review; RELEASE owns toolchain pinning. MASTER does not modify firmware. **PRODUCTION NO-GO.**

## 6.32 ISR edge reconciliation must cover both poll-window outcomes — 2026-11-18 UTC21

**Status:** P0 source-level race reproduced by the current Hardware-owned source-extracted regression. PHX-HARDWARE owns the firmware correction; PHX-QA owns independent exact-SHA review. This is simulated control-flow evidence, not a reported physical coin/customer event.

At current Hardware PR #327 head `b346eba3ebee228abcff03456deb7889f2d39144`, the ESP8266 sketch blob is `4d73c5dc451c29f2ffd64a5cb2d230cc84a78ed5`. `loop()` snapshots `coinEdgeSequence` before `beginPollWindow()`, but compares it again only inside `if(beginPollWindow())`. The helper returns false when `coinLineQuietAfterInhibit()` detects activity; on that path it currently clears `pollIntakeSuspended`, reapplies outputs, and returns before the caller reconciles the ISR sequence.

The new `injectDuringDrainAbort` source-extracted case injects an ISR edge during the drain read and returns an active level, forcing the false-return path. The next main-loop sample sees the line idle after the injected pulse has ended. The caller does not observe the sequence delta, and the expected sticky `/pollpulse.fault` marker is absent. Exact-head focused CI fails this case with exit 25 on ESP8266. The current run stops on ESP8266, so no ESP32 result for this new false-return case is claimed.

**Required invariant:** after the quiet-drain helper returns, reconcile the ISR sequence regardless of whether the poll window is ready or aborted. Keep poll intake/output inhibition asserted until that reconciliation is complete. If the sequence advanced, latch unresolved ingress and persist the deny marker before any release or HTTP poll; do not convert the edge into pending credit or silently drop it. Only dispatch `post("poll")` when the helper reports ready and the before/after sequence is unchanged. A non-edge abort may follow its separately defined safe release path.

**Acceptance on both ESP8266 and ESP32:** inject an ISR edge during the final drain/abort sample, let the pulse end before the next ordinary loop sample, and assert: no HTTP poll; sticky recovery deny; marker persistence attempted before inhibition release; relay/LED logically OFF; active target cleared; no pending credit; poll timestamp deferred; no hot retry. Include a mutation that removes false-return reconciliation and must fail. Do not weaken default-deny or add synthetic poll signatures.

Exact evidence: [current sketch](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/b346eba3ebee228abcff03456deb7889f2d39144/experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino), [source-extracted poll-loop lab](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/b346eba3ebee228abcff03456deb7889f2d39144/experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py), [quarantine run 44404536230](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44404536230), [relay/output run 44404536459](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44404536459). These are host/source-extracted tests only; physical ISR, coin acceptor, relay and power-cut acceptance remain NOT TESTED.

**Separate P0 retained:** §6.31's full-image `EEPROM.begin()` read-failure/default-`saveCfg()` hazard remains open. The marker-only raw flash read does not prove the whole 544-byte EEPROM image was read successfully. The current #327 false-return regression does not address that separate path.

### §6.32 — UTC22 exact-head evidence refresh (2026-11-18T22:51:38.802Z)

Live Hardware #327 API head is f9d1fa165ccc94b18aeac7e85ffd83c29899463f; source/test SHA is ed667e88f6844284834ebd3a337dfce07a817e8c; firmware correction commit is ddb386847e152e8ca4992e9f6b3370bfa3f20462. The PR description still cites c51271938c15e13998d1c99f1d311ca777bb1cc2 and is stale. #327 remains OPEN/DRAFT under #326 at 58c558fb6a237935214621adc3dee65a10fe1a51.

- ESP8266 sketch blob cd1acb1da298d4f9598e943dae05918b088e5363; ESP32 sketch blob ef498761e46d37134730dd41de1cc322d5d443e8; poll-loop lab blob 02dc80e547424817d00bfa23c70540a51a262273; full-image EEPROM read lab blob 07e44b5076db69c1d55e913790c44a5feac29ca3.
- Exact-head quarantine/readback 44414150601 and relay/output 44414150956 both pass the poll-drain abort scenario on ESP8266 and ESP32, including POLL_ABORT_DRAIN_INHIBIT_CONTINUITY_PASS, both abort-edge persistence modes, and POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS.
- Both focused jobs then fail in ESP8266 config_load_read_failure_lab.py: expected exit 0, got 31 in the first recovery scenario. The combined predicate is not split into individual failure messages. Source inspection shows loadCfg() still calls EEPROM.begin(544) then EEPROM.get(0,current); the status-bearing raw ESP.flashRead helper reads only the poll-fault marker, not the complete Config image. Full-image read-failure/recovery remains OPEN.
- Full run 44414150578 has validation job 135190015439 failing at the inherited QA-owned “Missing poll signature check”. All 13 firmware/platform targets and Android completed SUCCESS; simulations, bundle, candidate, signing and publishing were skipped.

Disposition: poll-drain abort is focused CI subtest PASS on both source models; overall focused jobs remain FAIL at the separate full-image EEPROM read lab; Full validation FAIL; independent QA and physical hardware acceptance pending. Same-flash stores are not an independent anti-rollback witness.

## 6.33 COE #45 receipt v1 — contract candidate, not Master adoption (2026-11-18 UTC23)

**Disposition:** CONTRACT CANDIDATE / SYNTHETIC CI VERIFIED / RUNTIME DENY / NOT IN COE #26.

Exact candidate: COE PR #45, OPEN/DRAFT, head 9d76a134c1f6512aa40c20ec4d247306a71a8cce, base d0830332 (a separate candidate base, not COE #26). The contract, golden vectors, verifier and focus runner are under Pisowifi/docs/contracts and Pisowifi/tests. Exact-head run [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) passed and logs include COIN_RECEIPT_V1_GOLDEN_PASS; case-collision run [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) passed. These are synthetic/host contract checks, not a deployed producer, firmware parser, financial ledger, key provisioner or hardware acceptance.

### Contract shape and incompatibility

COE v1 uses canonical ASCII name/value lines with LF, fixed field order and HMAC-SHA256. It binds receipt_id to the event hash and includes event_nonce, target_nonce, account_id_hash, ledger_epoch, ledger_sequence, issued_at, expires_at, disposition/reason, pulse_count, credit_delta_centavos, credit_total_centavos and key_version. It specifies stable retry bytes for an already committed event.

Master §1.2 currently documents a different v2-style receipt example: event_id, protocol_version, target, amount_centavos, seconds_granted, timestamp_utc, nonce, signature and replayed. There is no approved v1-to-v2 mapping, version negotiation, field-equivalence table or consumer migration. In particular, target vs target_nonce, seconds_granted vs credit_delta_centavos, event_id vs receipt_id, and signature vs HMAC are not one-to-one substitutions. The new ledger_epoch/ledger_sequence and account_id_hash fields have no approved Master-v2 mapping. **Do not adopt COE v1 as the Master canonical receipt or copy it into #26 until CORE and QA approve an explicit versioned bridge.**

### Test coverage and remaining proof

The exact verifier checks the known golden vectors, fixed field ordering, event-derived receipt ID, HMAC sensitivity to each field and byte-identical committed retry. Source inspection shows the verifier does not yet enforce uint32/uint64 upper bounds for key_version, ledger_sequence, timestamps and centavo values; it checks account_id_hash syntax but does not derive it from an approved canonical account identity; it has no approved clock-skew policy; and it does not implement or test a production parser/consumer. The three committed vectors do not exercise every allowed disposition/reason or malformed, duplicate, missing, unknown and reordered input. These are QA/CORE follow-ups, not a reason to weaken runtime default-deny.

**Adoption gate:** CORE must publish the versioned field mapping, numeric bounds, account-hash derivation, key-version authority, ledger-epoch authority and replay semantics. QA must add parser-level malformed/boundary/replay vectors. Hardware and Release must remain deny-only until the shared contract and durable authority are independently approved.

## 6.34 Hardware #327 — full-image EEPROM read recovery corrected in source tests (2026-11-18 UTC23)

**Current live PR head:** 3046c74d19ee1040996860a66cbdcb850acdbe14 (docs-only handover sync), child of #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. **Exact source/test head:** 6b52d63f889a9567303f9f2de464c743c1991f0c. **Firmware correction commit:** 40cfc0799a6e65e4a724e8ccbe6baa0f5f51de54.

The source correction adds a status-bearing read of the complete 544-byte ESP8266 EEPROM image, restores that verified image into the EEPROM RAM buffer, and tracks configImageReadVerified. loadCfg refuses to interpret an unreadable image as erased defaults; saveCfg and writePollFaultBackup require a verified image and revalidate after reopening. The reserved poll-fault bytes at offset 512 are preserved by the source-extracted recovery lab.

Exact source/test-head focused evidence:
- [Quarantine/readback #44423903845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903845) PASS. Logs show full-image first-read recovery with marker preservation, recovered-image cold-boot deny, marker-only recovery without commit, persistent full-read failure without commit, poll-drain abort continuity and pulse capture pass on both board-shaped harnesses.
- [Relay/output #44423903842](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903842) PASS. Both boards report 48/48 relay-polarity cases; output-off preload, poll-drain and pulse-capture checks pass.
- Source/test-head Full runs [PR #44423903891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903891) and [push #44423897080](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423897080) completed FAILURE at the inherited QA-owned Missing poll signature check. All 13 firmware/platform targets plus Android completed successfully; simulation, update bundle, candidate, signing and publishing jobs were skipped.

The live PR head advanced after those source/test runs: docs-head quarantine [#44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021) and relay [#44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181) were IN_PROGRESS at this audit; Full [#44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063) was QUEUED. Therefore the current PR head 3046c is not yet exact-head CI VERIFIED. PR description and the top handover pin still cite older c51271938; the live PR API and the appended UTC23 handover section are newer. HARDWARE must refresh its own PR description and top handover pin.

These are source-extracted host/fake-I/O simulations only. The same flash chip backs LittleFS and EEPROM/NVS; simultaneous store failure still yields current-boot denial only and is not an independent protected witness. No physical flash, GPIO/relay/acceptor test, power cut, native acceptance or 30-device soak is established.

## 6.35 Hardware #327 docs-head final CI readback — 2026-11-18 UTC23

The live #327 PR head remains 3046c74d19ee1040996860a66cbdcb850acdbe14; exact firmware/source-test head remains 6b52d63f889a9567303f9f2de464c743c1991f0c. The docs-head Actions runs have now completed:
- [Quarantine/readback #44424514021](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514021): PASS.
- [Relay/output #44424514181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514181): PASS.
- [Full build #44424514063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44424514063): FAILURE at QA-owned Controller protocol parity / Missing poll signature check. All 13 firmware/platform targets plus Android passed; simulation, update bundle, candidate, signing and publishing jobs were skipped.

This supersedes the in-progress/queued snapshot in §6.34 for the same docs-head. The EEPROM read-recovery correction remains source/test verified; the only Full validation failure is the inherited positive poll-signature fixture. The PR body/top handover still cite c51271938 and must be refreshed by HARDWARE. No physical hardware or power-cut acceptance is established.



## 6.36 Release ImageBuilder overlay-size accounting — descriptor-pinned no-follow contract (2026-11-19 UTC01)

**Disposition:** SOURCE/TEST FIX VERIFIED IN HOST CI / MANDATORY IMAGEBUILDER SANDBOX BLOCKED / INDEPENDENT QA REVIEW REQUIRED / NOT A RELEASE APPROVAL.

COE Release PR #35 current docs head is 3455e0ce56bed780a727a6297db14a8e1d345f99; exact packaging source/test head is 5e25e4ceab7c0615bcdad8309d50739e6b255f46. The source replaces path-based overlay walking with Linux/POSIX descriptor-pinned traversal: open entries with O_PATH|O_NOFOLLOW, fstat the opened object, compare its device/inode to a no-follow stat relative to the pinned parent directory, open child directories with O_DIRECTORY|O_NOFOLLOW, and fail closed on identity changes or missing platform primitives. Symlinks are excluded from the byte budget; regular staged files are counted from the opened object rather than a re-resolved path.

Test-first evidence:
- RED #44435063672 reproduced regular-file-to-symlink replacement at the open boundary.
- RED #44436345907 reproduced symlink-to-regular replacement and the old undercount.
- Exact source/test shared run #44436769990 passed; docs-head shared run #44438686744 passed 107 packaging tests with two intentional sandbox-only skips, all ten appliance profiles, shared-contract checks, and ESP32/ESP8266 compile/upload.
- Docs-head case-collision #44438686678 passed.
- Mandatory sandbox #44438687009 failed closed after 13/13 host-preflight tests because bubblewrap is absent (exit 125). No unsandboxed fallback or actual sandbox packaging acceptance is claimed.

**QA follow-up discovered by Master source/test inspection:** both race fixtures replace the directory entry inside the patched os.open wrapper before delegating to the real open. They cover both entry types at the open boundary, but do not exercise replacement after the O_PATH descriptor has been acquired and before the subsequent dir_fd no-follow stat. The implementation compares inode identity and raises ValueError on that later mismatch, but this branch lacks a deterministic regression. PHX-QA should add both post-open replacement directions and assert fail-closed behavior with unchanged external sentinel bytes. This is a test-coverage gap, not a confirmed source defect.

The CI artifacts are nonproduction build archives. PR and push artifact ZIP digests differ; no byte-reproducible firmware claim, signed release, real ImageBuilder sandbox run, target flash, or hardware acceptance follows from these checks.

## 6.37 COE Release #44 site ULA and #35 stack ancestry — no adoption (2026-11-19 UTC01)

COE #44 remains OPEN/DRAFT at 582fd5d5e83e36b36546ac28534740298ba94af4, based on the earlier #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4. Current #35 is at 3455e0ce56bed780a727a6297db14a8e1d345f99. GitHub compare reports #44 is 15 commits ahead and 13 commits behind current #35. These are divergent sibling stacks; #44 does not contain the current #35 overlay-accounting source/test and terminal handover commits. PHX-MASTER did not merge, rebase, cherry-pick, or alter either release branch. PHX-RELEASE must reconcile the stack without force-push before treating the candidates as one release lineage.

The #44 first-boot script generates a random 40-bit RFC 4193 ULA global ID per installation, commits the prefix to UCI, validates persisted readback, and scopes rollback to its own option/section. Its shared CI #44390136309 and case-collision #44390136296 pass; mandatory sandbox #44390136327 remains blocked by missing bubblewrap. A random prefix per installation does not establish the Master §6.9 same-site rule that multiple appliances at one site share a site identity. Site-level assignment authority and same-site/different-site, reboot, upgrade, and restore tests remain open. No ULA contract adoption or migration is approved.


## 6.38 Board toolchain versions are part of firmware and migration identity — 2026-11-19 UTC02

**Disposition:** exact-head CI exposes unpinned ESP32 core drift; COE destination compile is blocked; PHX-MASTER changed no firmware or workflow source.

Experiments #327 source sketch blob ef498761e46d37134730dd41de1cc322d5d443e8 (59,117 bytes) differs from COE #35 destination blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 (18,505 bytes). Both contain mbedtls/sha256.h; source also includes nvs.h and string.h, absent from destination.

Experiments #327 run #44439616677 installed esp32:esp32 3.3.13 and compiled. COE #35 run #44443780617 installed 4.0.0 and failed because mbedtls/sha256.h was not found; ESP32 artifact upload was skipped. Both workflows use unpinned arduino-cli core install esp32:esp32 commands. A green unpinned source run is not a reproducible destination-compatibility claim.

**Required contract:** pin Arduino CLI, exact ESP32/ESP8266 core versions, FQBN and build options. Source and destination must use the same pinned toolchain, or an independently verified upgrade matrix. Record resolved versions with job evidence; never use an unpinned latest package index as migration equivalence. RELEASE owns workflow pinning; HARDWARE owns firmware compatibility; QA owns independent same-SHA verification. Master edits neither subsystem firmware nor release workflows.

COE #35 mandatory sandbox remains blocked by missing bubblewrap after 14/14 host-preflight tests (exit 125). Site-scoped ULA, independent durability witness and production acceptance remain open. **PRODUCTION NO-GO.**

## 6.38.1 UTC03 correction — COE #35 toolchain pinning verified; #26 remains floating

**Disposition:** the earlier UTC02 ESP32 toolchain-drift finding is corrected for COE #35 only. It is not corrected for the integration candidate #26.

At COE #35 current PR head a270b547fb5ff570bd2bc49c2e96219043d7c9bd, source/test head 3b83a408583091f2b2e8a7cf4ef73833f2eb9e39, the release-owned hardware workflow pins Arduino CLI 1.6.0, ESP8266 core 3.1.2, and ESP32 core 3.3.13, with runtime version checks. The setup action is pinned to immutable commit b3cda96fddef6af6c56b4c5efb5c47e2357935db. The pin guard is tools/test_release_toolchain_pins.py. Current workflow blob: e16e6e0f97092bd63a5dec8b871f98be2149847f; guard blob: 983f12ead5e76e59f5d1dec0b42b3facda66fd32.

Exact-head evidence: shared/firmware run 44451317780 PASS, including both board compile/artifact-upload jobs; case-collision 44451317996 PASS; mandatory sandbox 44451317807 FAIL CLOSED because bwrap is absent (exit 125). No unsandboxed fallback was used. The current PR description still contains older head/status text; the current handover at a270 records the pinned toolchain evidence. PHX-RELEASE owns refreshing its PR description.

COE #26 remains different: its hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 uses arduino/setup-arduino-cli@v2 and unversioned core-install commands for both ESP targets. Its Hardware/README.md blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb documents ESP32 core 3.3.12 and ESP8266 core 3.1.2. The #35 pin fix is not present in #26, and #26's README/workflow do not agree on an exact ESP32 core. Do not infer toolchain parity across branches.

## 6.39 Hardware migration identity requires exact source, test, license, and toolchain parity

**Disposition:** COE #26 is not an import-complete or behavior-equivalent destination for current Experiments Hardware #327. No staging, copy, move, overwrite, or migration is approved.

Current Experiments #327 branch head is 11fae729df415cc26b9e1675b1758cd8e4d22648, child of #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. The PR description still says a3597125fef3964ab08f05b3300c8de3e47516ae; that description is stale. Commit 11fae729 adds an explicit Mbed TLS major guard: major 4 uses PSA Crypto, major 3 uses the legacy SHA-256 API, and every other major fails compilation. Exact current ESP32 source blob f54805b17cac45388dfacc5e65eff9b731234316 is 60,326 bytes. ESP8266 source blob 1b32cb90be11da79ba7ea1155f128aee9e495dd2 is 67,300 bytes.

The latest #327 exact-head CI is focused quarantine/readback 44453235563 PASS, relay/output 44453235544 PASS, and Full build 44453235564 FAILURE at the QA-owned Controller protocol parity / Missing poll signature check. The ESP32 job 135322011864 compiled successfully with esp32:esp32@4.0.0 and uploaded artifact 14496054232; all target and Android jobs completed successfully. Downstream update bundle, simulation, signing, candidate and publishing jobs were skipped. The 4.0.0 compile verifies the Mbed TLS 4 branch, not the Mbed TLS 3 branch or unsupported-major rejection at runtime. The latest source-extracted lab head remains 071a711d6598c67124e84ffd995fd48aa7d9f054; no dedicated unsupported-major test was added. PHX-HARDWARE owns the source; PHX-QA owns independent negative/default-deny and version-matrix review. Master did not edit the Hardware branch.

Exact current source/destination sketch comparison at #327 head 11fae729 and COE #26 head b382d233:

| Platform | Experiments #327 source blob / bytes | COE #26 destination blob / bytes |
|---|---|---|
| ESP8266 | 1b32cb90be11da79ba7ea1155f128aee9e495dd2 / 67,300 | c8be98f72596681e36a3ad1f8939bf8046c96887 / 18,394 |
| ESP32 | f54805b17cac45388dfacc5e65eff9b731234316 / 60,326 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 / 18,505 |

Neither platform is byte-identical. The current source acceptPollResponse() returns false on both boards and contains no positive |poll| token. COE #26's Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e (4,118 bytes) is one generic shell test that greps for response_sig, |register|, |poll| and quarantine routes, then performs brace balancing. It is not equivalent to the eight source-side Python lab files in #327 (coin pulse capture, config read failure, boot polarity, dual-store fault, poll-loop inhibit, fail-closed response, poll-window drain, request-digest failure). Importing the current source without replacing this positive-presence fixture would produce a test-identity conflict. The destination README also describes positive response-signature verification, while the current Master/HW contract intentionally remains default-deny pending the approved producer and QA vectors.

License evidence: source BlazePwifi/LICENSE and COE Pisowifi/LICENSE are byte-identical at blob 1ee55b94183417be977ca287cd7391f9a6f7e721. COE Hardware/LICENSE and Hardware/NOTICE.md are absent; source BlazePwifi/NOTICE.md and COE Pisowifi/NOTICE.md are also absent. The #26 PR description was updated at 2026-11-19T03:44:46Z to claim the licensing/privacy gate is resolved, but the Hardware subtree's explicit license/notice scope is not established by the exact files inspected. That claim is not independently accepted as migration evidence.

COE #26 remains OPEN/DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12. Its five current workflows (case-collision, Windows SoftTimer, Hardware/shared contracts, Rental, Pisowifi) are QUEUED with zero jobs. The PR description also claims 18/18 tests and 95% software readiness; those claims are not destination-CI evidence while all five workflows have no jobs.

**Required admission evidence:** per-file source/destination path, mode and blob SHA; complete import inventory; license and NOTICE scope; exact test identity and negative-path coverage; pinned CLI/core/FQBN/options; exact-head destination CI; reversible rollback evidence; owner approvals. Until all are independently reviewed, keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null.


## 6.40 Local EEPROM configuration migration is not financial-ledger migration evidence

**Classification rule:** ESP8266 local device-configuration migration from ConfigV1/ConfigV2 to ConfigV3 is a separate persistence domain from the financial ledger v1-to-v2 migration. Passing the former must never be reported as testing, proving, or authorizing the latter.

At current Hardware PR #327 branch head e799b0f042889b97ba7bae2ae2e06c1ec76392d6 (docs-only successor), the relevant firmware source commit is 11fae729df415cc26b9e1675b1758cd8e4d22648 and the exact source/test lab head recorded by Hardware is 071a711d6598c67124e84ffd995fd48aa7d9f054. The ESP8266 source blob 1b32cb90be11da79ba7ea1155f128aee9e495dd2 is 67,300 bytes; the COE #26 destination blob c8be98f72596681e36a3ad1f8939bf8046c96887 is 18,394 bytes. The ESP32 source blob f54805b17cac45388dfacc5e65eff9b731234316 is 60,326 bytes; the COE #26 destination blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 is 18,505 bytes. Neither platform is byte-identical.

The local configuration failure lab is present at source blob 40dfa46e48d8288bf94ad8c5579bf0d7436d4df6. It is invoked indirectly by coin_pulse_capture_lab.py blob cdc6d85aed5e5a0c85b154afa67c302023ec20b9 (lines 337-339); the PHX-HARDWARE quarantine workflow blob fe98e5e41dbf73e22fbd34479dbc971f008d18c9 invokes coin_pulse_capture_lab.py. This invocation chain is confirmed by exact-head quarantine/readback run 44453718564, job 135323579699. The job log reports full-image read failure/recovery cases, malformed v1/v2 and unknown-schema setup-save denial, valid local v1/v2 migration marker preservation, and failed local migration commit same-boot denial/cold-boot retry.

The lab explicitly emits LOCAL_CONFIG_MIGRATION_LAB_ONLY=1, FINANCIAL_MIGRATION_TESTED=0, PRODUCTION_MIGRATION_AUTHORIZED=0, SIMULATED_ONLY=1 and PHYSICAL_POWER_CUT_VERIFIED=0. This is source-extracted fake-I/O evidence only. It does not establish physical EEPROM durability, a financial ledger schema transition, receipt/replay consistency, an independent durability witness, or reversible financial migration.

Exact-head #327 focused quarantine run 44453718564 and relay/output run 44453718633 pass. Full run 44453718661 fails at the QA-owned Missing poll signature check (validation job 135323581119); all 13 firmware/platform target jobs and Android complete successfully, while downstream simulation, signing, candidate and publishing jobs are skipped. The Mbed TLS 4 / ESP32 core 4.0.0 path has compile evidence; an exact-head Mbed TLS 3 / ESP32 core 3.3.13 rebuild and an executable unsupported-major compile-rejection test remain NOT RUN.

**Contract:** PHX-HARDWARE owns local device configuration and firmware; PHX-CORE owns financial ledger and receipt semantics; PHX-QA independently verifies both domains at exact SHAs. Do not let a local EEPROM configuration test satisfy the financial migration gate. No financial interface or source code was changed by Master.


## 6.41 Hardware #327 Mbed TLS selector and COE #26 migration gate — exact current heads (2026-11-19 UTC06)

**Disposition: COE #26 Hardware migration remains BLOCKED. Keep the current firmware poll and coin-disposition consumers deny-only. No source or destination staging is authorized.**

Experiments Hardware PR #327 is OPEN / DRAFT at branch head ba4c0cb0c5eae4be5e014c0df6f5abe20a67b0bf, based on #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. Its source/test commit is 0e5514adb0088649eca8bec9df6215faa50b556c. Current ESP32 sketch blob c29483f0761ca6e2db0573bd12d6bfa502f12434 is 61,807 bytes; ESP8266 sketch blob 1b32cb90be11da79ba7ea1155f128aee9e495dd2 is 67,300 bytes.

The ESP32 sketch selects PSA Crypto for Mbed TLS major 4, the legacy SHA-256 API for major 3, and emits a compile-time error for every other major. Both current board sketches keep acceptPollResponse() and coinPostDispositionVerified() fail-closed: each returns false. The response_sig reference in source comments describes an unapproved derived candidate; it is not a positive poll authorization implementation.

Exact current-head Hardware CI:
- Focused quarantine/readback [#44468941707](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941707), job 135373435174: SUCCESS. Logs report Mbed TLS 3/4 selector and digest checks, rejection of unsupported majors 2/5, coin POST gate scenarios, poll-window/edge labs and local EEPROM configuration failure cases.
- Relay/output [#44468941718](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941718): SUCCESS.
- Full [#44468941728](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941728), validation job 135373435914: FAILURE at the inherited QA-owned v05_firmware_hardening_test.sh assertion “Missing poll signature check”. The 13 firmware/platform targets and Android completed successfully; downstream simulation, candidate, signing and publishing jobs were skipped.

The focused Mbed TLS lab emits MBEDTLS_MAJOR_3_SELECTOR_AND_DIGEST_PASS, MBEDTLS_MAJOR_4_SELECTOR_AND_DIGEST_PASS, MBEDTLS_UNSUPPORTED_MAJOR_2_REJECTED and MBEDTLS_UNSUPPORTED_MAJOR_5_REJECTED, but explicitly sets STUB_API_ONLY=1 and EXACT_ESP32_CORE_3_3_13_BUILD_REQUIRED=1. This is host stub/API evidence, not an actual ESP32 core 3.3.13 build. The Full run compiled ESP32 using resolved core 4.0.0 and ESP8266 using 3.1.2. The Experiments build workflow blob 2cd6ce83b01c65fd78df091e502b68bf4fd277dc still installs unversioned board cores.

The source-side v05_firmware_hardening_test.sh blob 41211b2c110ab409f6d9d1812ef12fda73b13211 still requires response_sig, |register| and |poll| strings. Its current failure is the positive |poll| assertion. Do not weaken the firmware or add a fake signature token to satisfy this legacy fixture. PHX-QA owns replacing the obsolete positive-presence assertion with source-exact negative/default-deny tests at the current source SHA.

COE integration PR #26 remains OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12; COE main is a6513ab4412b4c014eee2863e45cbe32d06cb243. Its ESP32 destination sketch blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 is 18,505 bytes, has no Mbed TLS major selector, retains the legacy mbedtls/sha256.h include and contains a positive response_sig/|poll| consumer. It is not the current deny-only source. The source/destination ESP32 Git blobs differ.

PR #327's changed-path inventory contains nine Python lab files (eight ESP8266-oriented labs and one ESP32 Mbed TLS compatibility guard). COE #26 has one generic Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e. That destination test positively requires response_sig, |register| and |poll|; it is not equivalent to the current source labs or contract. The five #26 workflows remain QUEUED with zero jobs, so no destination build or test has executed.

COE #26 hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 installs unversioned ESP32/ESP8266 cores. Hardware/README.md blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb documents ESP32 3.3.12 and ESP8266 3.1.2, which is not enforced by that workflow. COE Release #35 has a separate pinned toolchain at head 5047af8b5a8296e06294bbda6bf42a6baea2294d: Arduino CLI 1.6.0, ESP8266 3.1.2 and ESP32 3.3.13. Its shared/firmware run #44465377784 and case-collision run #44465377781 pass; mandatory sandbox run #44465377807 fails closed because bubblewrap is absent after 14/14 host-preflight tests. The #35 pin fix is not present in #26.

Release #35 is 108 commits ahead / 0 behind parent #31 at 59ed44d0b911e176f1a95b9cf5585ef811ffd31b. Release #44 is at 582fd5d5e83e36b36546ac28534740298ba94af4, based on older #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4; compare #35 → #44 is DIVERGED, 15 ahead / 25 behind, and PR #44 reports mergeable=false. PHX-RELEASE owns history-preserving reconciliation; Master did not modify either branch.

COE INTERCON candidates remain separate. Stage-3 #39 uses a 64-byte journal, #40 a 76-byte journal, and #42 a 92-byte journal; each has exact-head host/simulation and board compile CI success. Stage-4 #41 is shadow-credit only on #39; #43 is live timer/relay behavior on #42. Both have passing scoped CI, but they are not equivalent and do not establish physical flash durability, real power-cut recovery, protected key custody or a canonical router financial adapter. No candidate is selected.

License evidence remains incomplete: source BlazePwifi/LICENSE and COE Pisowifi/LICENSE are the same MIT blob 1ee55b94183417be977ca287cd7391f9a6f7e721, but COE Hardware/LICENSE and Hardware/NOTICE.md are absent at #26. The source BlazePwifi/NOTICE.md is also absent at the inspected source root. The Pisowifi license does not by itself establish Hardware subtree license/NOTICE scope.

**Migration admission remains closed** until exact per-file path/mode/blob provenance, all required source labs or reviewed equivalents, negative/default-deny tests, pinned CLI/core/FQBN/options, runnable exact-head destination CI, explicit Hardware license/NOTICE scope, reversible rollback evidence and owner acceptance are independently verified. Keep OWNERSHIP_ROUTES.json unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, with PHX-MASTER destination null. PRODUCTION NO-GO remains binding.

### UTC07 exact-head supersession — 2026-11-19

At current Hardware PR #327 head, branch phoenix/hardware-prepoll-edge-abort-20261119 is 31f5d727f0f61128694b9b0c4b92af8e4b6afa52, based on #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. Hardware identifies c37338439eec23c54a2e4a5f9c9c538d08f182cf as the source/test commit. Current sketch blobs are ESP8266 1b32cb90be11da79ba7ea1155f128aee9e495dd2 (67,300 bytes) and ESP32 c29483f0761ca6e2db0573bd12d6bfa502f12434 (61,807 bytes).

Exact-head CI:
- Focused quarantine/readback [#44478447580](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447580), job 135404563994: SUCCESS. The source-extracted poll-response lab reports 11/11 fail-closed cases per board, 13/13 strict-root-JSON cases per board, coin POST root-status 4/4 per board, and coin-disposition default-deny 4/4 per board. The same run reports simulated EEPROM/NVS, poll-window, pending-journal and request-digest labs; physical flags remain zero.
- Relay/output [#44478447647](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447647), jobs 135404564309 and 135404565326: SUCCESS. ESP32 boot-polarity logs show unknown/legacy profile stays INPUT, local polarity readback passes, active-high/active-low OFF preload passes, and remote polarity authority is denied.
- Full PR [#44478447410](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44478447410), validation job 135404563869: FAILURE. All 13 firmware/platform targets and Android completed successfully; downstream simulation, update-bundle, signing, candidate and publishing jobs were skipped.

The Full failure is the legacy QA fixture, not a reason to relax firmware. The exact test chain is:
- controllers.sh blob f7896647713d6bf8034ff48ed19b6383e4dedea0 invokes tests/v05_firmware_hardening_test.sh.
- That fixture blob 41211b2c110ab409f6d9d1812ef12fda73b13211 still requires positive response_sig, |register| and |poll| source strings; its |poll| assertion is the reported failure.
- Both current board sketches keep acceptPollResponse() and coinPostDispositionVerified() fail-closed (return false). The focused source-extracted poll_response_failclosed_lab.py blob 69dbddee4133588940f4c5b53817401db531a8a4 already exercises negative/positive-looking response denial.

**Master direction:** PHX-QA must replace only the obsolete positive-presence assertion with source-exact negative/default-deny tests and ensure the source-extracted lab remains in the Full validation path. Do not add a fake |poll| token, enable positive unauthenticated admission, or weaken the firmware to satisfy a string grep. PHX-HARDWARE retains sketch ownership. This remains SIMULATED/CI evidence only; physical relay, coin acceptor, flash and power-cut acceptance are NOT TESTED.


## 6.42 Release handover freshness is a build-provenance admission gate — 2026-11-19 UTC07

Release PR #291 is OPEN/DRAFT on branch phoenix/release-publisher-isolation-20261115. The live PR and branch ref both remain 3ef73265abd52bf44273584afc406382c2805b1d (base 734b89d9e7792247e8376335c3f3685500ab3f89). The PHX-RELEASE UTC07 progress comment reports b8f4e3619a8c84b4e81d8bb24ba3da02825fa9e6, but the branch did not move. That commit object changes only .github/PHX_RELEASE_HANDOVER.md; it is not the current PR head and does not prove the reported workflow/script scope is on the branch.

Exact current-head CI:
- Windows release [#44479756135](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756135), handover job 135408844761: FAILURE; build and publisher skipped.
- BlazePwifi build [#44479756093](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756093), validation job 135408938465: FAILURE at tests/handover_gate.sh. The log says source/workflow changes are newer than experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md, identifies .github/workflows/blazepwifi-build.yml, and reports last checkpoint c0b5f3731e1db81faf275bf8f32a757f7d52f3d2. Downstream release/simulation/signing/publishing jobs are skipped.
- ESP32 core compatibility [#44479756113](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44479756113): SUCCESS.

**Contract:** any release-owned build/workflow/toolchain/provenance change must be followed on the same candidate branch by an updated authoritative product handover, live state and change ledger that identify the exact source/workflow SHAs, pinned CLI/core/FQBN/options, artifact hashes, CI run/job IDs, and explicit unsigned/unreleased state. The handover freshness gate must pass before artifacts are admitted to downstream simulation, signing, publishing or promotion. Green compile jobs do not override a failed handover gate. Do not bypass or disable the gate. PHX-RELEASE owns its branch/workflow and must coordinate with the designated handover owner; PHX-MASTER owns this contract only and does not edit subsystem or release files.


## 6.43 Exact-head release provenance and current poll-deny validation — 2026-11-19 UTC08

**Disposition: release handover and COE migration remain blocked; current poll and coin-disposition consumers remain deny-only.** A BLAZE-COMMS checkpoint is a status statement, not a substitute for the live PR head. Reviewers must compare the named checkpoint SHA with the current PR head and record ancestry before treating its tests as exact-head evidence.

At live Experiments PR #291, the current head is d498afbf2aa0e60fc1b1d0471328f5e6eb8e597c. The UTC08 RELEASE checkpoint #7003579497 names b8f4e3619a8c84b4e81d8bb24ba3da02825fa9e6 as current head, but GitHub compare shows the current PR head is 12 commits ahead / 0 behind that SHA. The current d498af exact-head Windows and BlazePwifi workflows fail the mandatory handover freshness gate; board compilation and the separate ESP32 compatibility workflow passing do not override it. RELEASE must refresh canonical product handovers and re-run the exact live PR head. No bypass is permitted.

At Hardware PR #327 head c62af73ec5b45cd87f4c8f3295ede18f307fb359, quarantine/readback and relay/output focused workflows pass, while Full validation fails at the inherited positive “Missing poll signature check” assertion. The source-extracted poll-response lab deliberately denies current positive-looking responses. QA must replace the obsolete positive-presence fixture with negative/default-deny source-exact tests; Hardware retains firmware ownership. Do not add a fake signature token or enable unauthenticated admission.

COE #26 remains a separate draft staging candidate. Its ESP32/ESP8266 blobs differ from current #327 source, its Hardware test still requires positive signature/poll strings, its Hardware license/NOTICE scope is absent, and all five destination workflows remain queued with zero jobs. The source and destination LICENSE blobs match only for the Pisowifi/BlazePwifi scope; this does not establish Hardware subtree license scope. No migration is authorized.

Master CI was not run because the execution runtime could not resolve github.com; no Master test pass is claimed. This section records source/tree and exact-head Actions inspection only. PRODUCTION NO-GO remains binding.


## 6.44 Exact-head poll consumer remains deny-only — 2026-11-19 UTC10

**Disposition: retain firmware default-deny; repair the legacy positive fixture in QA-owned validation, not in firmware.**

At Experiments HARDWARE PR #327 head `47eceaf2ccd3cfdc3403df6b1964610bd32ed24f`, ESP8266 sketch blob `75f62c359bbb69f4f580b7ee0c3875396b12cc7f` has `acceptPollResponse()` explicitly clear `insertMode` and `activeTarget`, then return `false`; `coinPostDispositionVerified()` also returns `false`. The source says the current `response_sig` expression is only a derived candidate pending CORE's canonical producer and QA-approved vectors. The source-extracted poll lab is blob `69dbddee4133588940f4c5b53817401db531a8a4`.

Exact-head Full run [#44501072563](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072563) fails in validation job `135480829727` at legacy `Missing poll signature check`. All 13 firmware/platform targets and Android completed; downstream simulations, update bundle, candidate, signing and publishing were skipped. Focused quarantine [#44501072485](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072485) and relay/output [#44501072498](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072498) passed. Quarantine logs include both-board poll-fault and EEPROM/config labs, but explicitly report `SIMULATED_ONLY=1`, `FINANCIAL_MIGRATION_TESTED=0`, and `PHYSICAL_POWER_CUT_VERIFIED=0`.

Do not add fake `response_sig` or `|poll|` markers and do not enable poll admission to make the old assertion green. PHX-QA owns source-exact negative/default-deny cases at the same source/test SHA. PHX-CORE owns the future canonical response envelope and golden vectors; PHX-HARDWARE retains firmware ownership. This is not financial disposition or hardware acceptance.


## 6.45 Site-scoped RFC 4193 ULA provisioning contract — decision required (2026-11-19 UTC10)

COE Release #35 at `5047af8b5a8296e06294bbda6bf42a6baea2294d` emits `option ula_prefix 'fd00:db8:blaze::/48'` from packager blob `f1d9c8ef1da7e1d3df11f45dfe36f14f5f11a650`. Independent Python `ipaddress.IPv6Network(..., strict=False)` rejects it: `AddressValueError: Only hex digits permitted in 'blaze'`. The accompanying test blob `e3f625673bd90bb28e107a88aff9ed4d824a2bb7` checks bridge/VLAN output and formatting but contains no ULA/IPv6-prefix validity assertion.

**Normative interface constraints:**
1. A site ULA must be a valid RFC 4193 prefix in `fd00::/8`, with a 40-bit Global ID and `/48` length. Reject malformed/non-hex, non-`/48`, documentation placeholders, multicast, link-local, global-unicast and unspecified values.
2. It is site-scoped: all appliances at one site share the same prefix; distinct sites use independently provisioned/generated Global IDs with collision-aware handling. A random prefix per appliance is not a site identity.
3. Persist the prefix across reboot, upgrade, migration, backup and restore. Do not regenerate it during ordinary boot/restore or derive it from a device MAC/product name.
4. The provisioning authority is undecided. PHX-CORE and the COE integration owner must choose owner-provisioned site prefix or a first-boot site authority that creates/distributes one durable identity. PHX-MASTER does not invent a prefix, secret or site credential.
5. Until that decision exists, packagers fail closed when no approved site prefix is supplied. Never emit `fd00:db8:blaze::/48`, another hard-coded vendor literal, or a per-appliance fallback.
6. QA independently tests syntax, /48, same-site sharing, distinct-site separation, persistence/restore and authority-unavailable denial.

PHX-CORE/COE own the provisioning decision; PHX-RELEASE implements after approval; PHX-QA owns independent vectors. This contract does not change networking code or authorize hardware acceptance.



### UTC14 exact-head supersession — 2026-11-19T14:39:41Z — site ULA implementation evidence

The §6.45 decision remains **site-scoped**, not per-appliance: appliances at one site must share one durable RFC 4193 /48; independent sites must not share the same Global ID; the selected identity must survive reboot, upgrade, backup and restore. The current COE RELEASE #35 source/test head is `90ce4200b66ce0b55f40feaab42cc7b53fad1f2d`, with final documentation head `0e3662b9aef4b2a2248e3a064b07d07e9097be1b`. Its packager now sets `APPROVED_SITE_ULA_PREFIX = None` and strictly validates an explicitly supplied RFC 4193 /48 before writing UCI. The tests patch `fd12:3456:789a::/48` only as a **synthetic test fixture**; it is not a production allocation or approved site prefix.

Exact final-head PR run [44543625272](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625272) ran 116 packager/tool tests successfully (two intentional skips), then correctly failed `validate_all_profiles`: all 10 profiles reject the absent approved site prefix. Firmware compile jobs were skipped. This is a **fail-closed gate**, not a successful profile build or release. The mandatory sandbox [44543625389](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625389) passed 14/14 host preflight tests but failed because Bubblewrap is not installed (exit 125); sandbox packaging tests were skipped.

COE RELEASE #44 at `582fd5d5e83e36b36546ac28534740298ba94af4` generates a random 40-bit Global ID per appliance installation and persists it locally. That does not prove same-site appliances share one /48 and therefore does not satisfy §6.45. Exact compare from #35 head to #44 is 15 commits ahead / 29 behind; GitHub reports the candidate non-mergeable. Do not select, merge or reconcile #44 as the site authority. PHX-CORE and the COE integration owner must define the site-prefix authority and supply contract; PHX-RELEASE may consume only that approved input; PHX-QA must independently test same-site sharing, different-site separation and persistence/restore.


## 6.46 NVS/EEPROM commit-call evidence is not a durability witness — 2026-11-19 UTC15

Current Experiments HARDWARE PR #327 API head is c4954de95e319f7a2acf4bf4ee0bcae44b4b99b5; its current source/test head is 05ddd64f0d982c32d0297010596bfa9bd46bb472. The host lab blob 2562cdb84135b3e9dab6e531567c6b1619eeeed3 adds a one-commit call-count assertion for the ESP32 NVS backup and ESP8266 EEPROM backup. Its source mutation removes the ESP32 nvs_commit() call and must be rejected (exit 61); the premature-durability mutation remains rejected (exit 60). Focused quarantine run [44555100182](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555100182) and relay/output run [44555100184](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555100184) passed for that source/test checkpoint.

This is a control-flow/call-site regression, not proof that bytes survive power loss. The fake same-handle readback can observe pending data; a successful commit call does not independently establish media durability, atomicity across NVS/EEPROM and LittleFS, or a second anti-rollback witness. Those stores share the same physical flash. Local configuration migration V1/V2-to-V3 is not the financial-ledger v1-to-v2 migration.

Current #327 focused quarantine [44557974485](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974485) and relay/output [44557974378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974378) passed. Current Full run [44557974541](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974541) completed FAILURE at the inherited QA-owned “Missing poll signature check”; all 13 firmware/platform jobs and Android completed PASS, while downstream simulations, update bundle, signing and publishing were skipped. Both current source sketches keep acceptPollResponse() and coinPostDispositionVerified() returning false. Do not add fake signature/poll markers or enable admission to satisfy the old fixture. PHX-QA owns the fixture; PHX-HARDWARE owns firmware.

**Acceptance boundary:** a future durability claim requires an independently designed power-fail test that cuts power at each write/commit phase, cold-reboots, verifies canonical and sidecar state, journal/attempt-marker consistency and replay/rollback behavior, plus independent protected anti-rollback witness evidence. Until the required 150 real power cuts, 30-device/24-hour soak and owner-authorized independent QA are complete, keep physical and financial acceptance NOT TESTED and PRODUCTION NO-GO.

## 6.47 Build-artifact payload single-link admission — 2026-11-19 UTC16

Release provenance inventory must not admit a payload file that aliases an inode also named outside the artifact tree.

1. A payload must be a regular, non-symlink file reached through descriptor-relative parent traversal with no-follow semantics. If the platform cannot provide the required no-follow descriptor operations, admission fails closed.
2. Require st_nlink == 1 on the directory entry before open, the opened descriptor after open, and both descriptor/path identities after read or hash. Stable identity comparisons include device, inode, size, modification time, change time, and link count.
3. Reject a hard-linked payload before rewriting SHA256SUMS or creating BUILD-PROVENANCE.json. Do not mutate the external alias.
4. QA independently reviews the hard-link and path-race rejection on the exact source/test SHA; this host-side artifact rule does not establish signing, archive transfer, financial durability, or hardware acceptance.

Exact RELEASE evidence: source/test commit 90165b173179e9b36c73f98e06cfd5e0a06a3fe3; writer blob 7a85da2c6a46abed1c7585e78b72e854637fb93f; test blob 081c05b94377d4251f02e4fadeeb4d44e1fdb3d8. The test creates an external hard link and requires ProvenanceError while preserving SHA256SUMS, omitting BUILD-PROVENANCE.json, and leaving external bytes unchanged. Expected RED was recorded in run 44564359785. Exact PR docs-head run 44565010341, job 135704442410, reports 22/22 provenance tests PASS including the new hard-link test. This is CI-verified host behavior only; no release or production gate is waived.


## 6.48 Poll response remains deny-only until producer/consumer contract approval (2026-11-19 UTC17)

**Authority boundary:** The current ESP32 and ESP8266 source/test candidate #327 at `ad421e48b2908fab48dc85b40c169450d9c0239c` does not authorize coin intake from the current plain-HTTP poll response. Both sketches implement `acceptPollResponse(const String &response)` as fail-closed: ignore the unapproved response, set `insertMode=false`, clear `activeTarget`, and return `false`. Both implement `coinPostDispositionVerified(...)` as `false` until PHX-CORE publishes an approved event-bound receipt/disposition contract and PHX-QA approves its vectors. Pending journal and one-shot attempt evidence must remain; body text, root `ok:true`, or a derived `response_sig` expression is not authority to clear/credit.

**Test requirement:** QA must not require a positive literal `|poll|` marker or inject a fake signature string to make the legacy test green. Replace marker-presence assertions with source-linked negative tests that prove malformed/unsigned poll responses cannot enable insertion, assign a target, clear pending evidence, authorize coin-post disposition, credit time or energize relay output. The current inherited `v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` requires `|poll|` and causes the exact current shared build validation failure. QA owns `experiment/openwrt/BlazePwifi/tests/`; HARDWARE owns the board sketches. Any later signed poll contract must be coordinated across CORE producer, HARDWARE consumer, QA vectors and RELEASE only after exact pinned interoperability tests.

**Evidence class:** source inspection plus hosted host-lab CI only. Current #327 Quarantine run 44580223038 passed; Relay run 44580223257 was still in progress at the read; shared build run 44580223115 failed validation at the QA-owned positive poll marker assertion. This section does not claim physical hardware acceptance, a protected signer, financial durability or production authorization.


## 6.49 Destination intake evidence is scoped to its declared source root and commit — 2026-11-19 UTC18

A destination intake manifest proves only the exact source commit, tree, path root, and file classes that it declares. It must not be extrapolated to neighboring product trees.

1. COE integration PR #26 contains Pisowifi/SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f, schema version 8. It pins Experiments source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00, project root experiment/openwrt/BlazePwifi, and destination root Pisowifi/. Its recorded rootfs summary is 61/61 files recovered, 47 byte-identical, 14 locally derived, zero unrecovered rootfs files, and only two unchanged original tests. It does not declare Hardware/ as an intake root and does not establish firmware-tree or firmware-test import completeness.
2. At current Experiments main f4e8a891aed8af86d5fd315d28750a0ac3a7372b, the ESP32 sketch blob is 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0 (15,049 bytes) and ESP8266 is bfb94920eb0a189ca01d52e5443954fa133f5423 (14,583 bytes). COE #26 destination blobs are ESP32 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 (18,505 bytes) and ESP8266 c8be98f72596681e36a3ad1f8939bf8046c96887 (18,394 bytes). Neither current-main pair is byte-identical. At the manifest's historical source commit, the sketch blobs are also different from the COE destination: ESP32 29f1125d52ff474a0d028ad41f7af201be1f0f9d; ESP8266 12c4bb82b6fddafe813674a0b5f692c1d3634073. Treat Hardware files as derived candidates requiring owner/QA provenance, not exact copies.
3. The current-main experiment/openwrt/BlazePwifi/tests/ tree has 38 entries; COE #26 Pisowifi/tests/ has 19. Four basenames overlap (config.sh, integration.sh, portal.sh, security.sh); only portal.sh has the same Git blob 71b3c9622f51a80dc09a446389ba6faa001b7897. COE Hardware/tests/ contains one generic test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e. File counts or matching names are not test identity; maintain a source-SHA-to-destination-test mapping and execute it on the exact destination candidate.
4. experiment/openwrt/BlazePwifi/LICENSE and COE Pisowifi/LICENSE match at blob 1ee55b94183417be977ca287cd7391f9a6f7e721. Experiments root NOTICE.md exists at f6d92cd21465312be5993631fe26977219be0fb9; COE root NOTICE.md, Hardware/LICENSE, and Hardware/NOTICE.md are absent at the inspected #26 candidate. The Pisowifi license match does not establish Hardware licensing/notice scope; obtain owner and licensing review before any Hardware migration.
5. COE #26 exact head b382d233ff06c8791b1028bed3c617cc7b670d12 has five queued workflows and zero jobs. Until destination workflows execute on a reviewed exact candidate SHA, no destination CI or integrated acceptance is established.

No copy, move, overwrite, rebase, cherry-pick, merge, or migration staging is authorized by this contract. PHX-MASTER owns this evidence boundary; source implementations and destination files remain with their respective owners.


## 6.50 Poll-fault pulseEdges is a first-latch lower bound — 2026-11-19 UTC19

**Source-grounded interpretation; no persistence schema change.** Current Hardware #327 sketches at ESP8266 blob `284f4337bc9e2aa4d78c61f0d7e4c4163ffb0a82` and ESP32 blob `f89bc561b2093328286d7633da794667b2ab06de` define a V1 `PollFaultRecord` with `magic`, `version`, `size`, `pulseEdges`, `bootMillis`, and `checksum` (20 bytes). The first call to `latchPollPulseFault()` sets the sticky `journalRecoveryRequired` flag, inhibits outputs, and persists the supplied edge count to the secondary store and LittleFS.

In `sampleCoinPulseEdge()`, the count supplied on the first latch is `pendingPulses + unseenEdges`. Once `journalRecoveryRequired` is true, later ISR deltas are consumed by advancing `lastHandledCoinEdgeSequence` but do not call the latch again and are not added to the already-persisted V1 record. Therefore:

1. **V1 meaning:** `pulseEdges` is the first-fault snapshot, not a live cumulative counter.
2. **Reconciliation meaning:** it is a lower bound on observed edge activity over the full quarantine/recovery window; later edges may be absent. It is not an exact total.
3. **Financial boundary:** never use this field to credit time, settle/refund a coin, infer a precise denomination/count, or clear pending evidence. The sticky fault remains deny-only until separately authorized reconciliation.
4. **Completeness:** V1 has no explicit completeness flag. Consumers must treat every V1 count as potentially incomplete; absence of a flag is not evidence that no later edge occurred.
5. **Schema boundary:** do not add a field or change record layout in this task. Any future completeness flag requires a new version, dual-store migration/recovery tests, exact-head QA, and explicit HARDWARE/CORE/QA review.

**Regression gap / owner action:** the current dual-store lab `poll_fault_dual_store_lab.py` blob `7d211b5e8e47232d08d2a2c625d3212676aee7a9` does not extract/call `sampleCoinPulseEdge()`. The poll-loop lab blob `440efc0fc76e90d22283f62c6605628a6c79342e` covers a release-window edge and unobserved-edge persistence, but no explicit second-ISR-after-sticky-latch count assertion was found. PHX-HARDWARE should add a two-board host regression proving the persisted first-fault snapshot stays unchanged after later edges and admission/output remain denied; PHX-QA independently reviews it; PHX-CORE confirms the count is never treated as a financial quantity. This section resolves the interpretation for existing V1 records, not owner approval of a future schema.


**UTC05 first-fault/current-head status (2026-11-24T05:37:40Z):** Source/test head `1247a5c7b332677ae8dca83dc94cf586a015e7a0` retains `poll_loop_blocking_inhibit_lab.py` blob `aacba2e366a0b68ca47e04012ecaa0496cc3309a`, which extracts/calls the sample path, latches the first fault, injects later ISR edges, and checks the first LittleFS marker/backup observation remains unchanged, pending pulse/target/nonce identity is preserved, no save/POST/clear occurs, and outputs/admission remain denied. Source/test Quarantine [#45335896662](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335896662) and Relay [#45335896640](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335896640) PASS; Full [#45335896670](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335896670) FAILs at `Missing poll signature check` (13/13 target jobs and Android PASS; downstream skipped). The test-only pending-clear refactor adds fixture blob `5b10b47f4994bb053ebad5c7c1dd6c56900ea0a6` and runner blob `a18ada4da4809af93f9d18d4834a13f5c3cadd29`.

Current docs/PR head `8639deda8d341d61efddff77be4d06ea931d040d` adds handover blob `571a6d66de41620e26eab0457d620fddc2bb3a96`. Current docs-head Quarantine [#45336321346](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336321346) and Relay [#45336321352](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336321352) were IN_PROGRESS; Full [#45336321274](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336321274) remained in progress with validation already FAIL at the same assertion. The PR body still pins older e4ab80/8dd8b12; HARDWARE must refresh its own top-level pin. This is host/CI evidence only, not physical persistence, power-cut or hardware acceptance.

**Exact #327 source/test SHA:** `64ec57daf161a0b4517d350f4f08bee55c0cabec`. This pins the host-lab implementation/handover reviewed for the interpretation above; it does not establish physical acceptance.

Evidence is source inspection and hosted simulated labs only. No physical device, flash, financial state, record migration, or production action is authorized. **PRODUCTION NO-GO.**

 
## 6.51 Build-artifact identity, site ULA, and sandbox gates — 2026-11-19 UTC21

The build-output, site-identity, and sandbox checks are separate admission gates; passing one does not imply the others passed.

1. **Output inode identity:** a generated firmware candidate admitted to a checksum manifest must be a regular, non-symlink file with a single link. Reject candidates with link count greater than one before writing the manifest. A hard-linked cache file is not a fresh ImageBuilder output. The COE #35 release-owned regression `test_generated_wrapper_denies_hardlinked_firmware_output` is present and passed at docs-head shared run [44617782050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617782050); source/test fix is commit `6f007699a513e46d6d45bfca6693d91c02c03b5e`.
2. **Mandatory sandbox execution:** host-preflight unit tests do not prove that the generated wrapper ran inside the required Bubblewrap namespace. If Bubblewrap is absent or namespace setup fails, stop with a blocked/failing result; do not install privileged tools or run an unsandboxed fallback. COE #35 sandbox run [44617781877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617781877) stopped at missing Bubblewrap (exit 125); namespace and packaging steps were skipped.
3. **Site identity:** appliance profile admission remains closed until an approved, durable, site-scoped RFC 4193 ULA /48 authority is supplied. A synthetic test prefix is not a production allocation. A per-appliance first-boot random prefix does not prove same-site sharing, distinct-site separation, or identity persistence across backup/restore and upgrade.
4. **Manifest meaning:** a SHA-256 manifest is integrity metadata for the observed output bytes. It is not a digital signature, trusted source/build provenance, target compatibility proof, rollback witness, or hardware acceptance.
5. **Independent gates:** at COE #35 docs head `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`, the hard-link test and 118-test packaging/tool suite passed (2 intentional skips), but all 10 profiles failed closed without site ULA authority and board compiles were skipped. The mandatory sandbox also failed closed. The packager fix is bounded and valuable, but the overall candidate remains NO-GO.

No Master change to release scripts, profiles, firmware, ULA provisioning, sandbox runtime, credentials, or publication is authorized by this contract. PHX-RELEASE owns the packager; PHX-CORE/COE integration own the site authority decision; PHX-INFRA owns the runner; PHX-QA independently reviews the same source/test SHA.


## 6.52 COE #48 Stage 5 Remote CS adapter boundary — 2026-11-19 UTC22

**Exact candidate refs:** COE #48 head `b72ca86a141329b4b401f5d790cfb04a58423331`, based on COE #47 head `1c10f7421dfaa87fcb2ce89d4a8b2d22422d1597` (15 commits ahead, 0 behind). COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; the existing integration draft #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`. #48 is a separate Hardware candidate, not part of #26.

1. **Protocol boundary:** #48 introduces a new HMAC-SHA256 `BLZCS1` frame (`BLZCS1|KIND|SOURCE8|DEST8|COMMAND16|SESSION16|EVENT16|VALUE|HMAC64`) for Remote CS. Existing COE #26 `/cgi-bin/vendo` uses the distinct `action/id/nonce/pulses/target/sig` request and `insert/target_nonce/expires/controller/response_sig` poll response. These envelopes are not wire-compatible. Existing poll also forces `insert=0` unless both controller `enabled` and `coin_enabled` are true. A real adapter must map the backend's stable vendo/target/customer session and expiry to the device's 64-bit session without treating a pulse count as money or time.
2. **Credit/ACK ordering:** `POLL` is read-only. Device `EVNT` contains device event ID, session ID and physical pulse count only. The router must durably commit exactly-once credit keyed by `(device_id,event_id)`, tied to the correct customer, target nonce, denomination and expiry, before sending matching `ACKN`. `ACKN` only clears the device's pending receipt; it is not proof that the backend credited money. Unknown timeout/replay outcomes require readback/reconciliation, never a fresh credit.
3. **No backend implementation:** `REMOTE_CS_BLAZEPWIFI_BRIDGE_CONTRACT.md` is a design contract. The #48 diff changes Hardware/ESP8266 staging and tests; it does not implement the `Pisowifi/` backend bridge, customer mapping, durable credit transaction or reconciliation service. The reference to JuanFi is architectural only per the candidate document; no copied endpoint/protocol compatibility is claimed.
4. **Journal limits:** `RemoteCsJournal.h` stores identity/key tag, generation, command/event counters and pending session/event/pulses in two LittleFS slots with temporary write, readback, rename and readback. The record checksum is CRC32, which detects accidental corruption but is not a protected signing or anti-tamper witness. The runtime's `remoteHardLocked` and `remoteJournalWriteFailed` are RAM flags; every reboot still requires AP-only physical reconciliation through the arm guard, but this does not turn a pulse lost before its first durable write into a recoverable receipt.
5. **Known pulse-loss window:** the Stage 5 document explicitly states that physical coins may be lost between the electrical pulse and the first completed flash commit. No software-only claim can remove that physical window. A hardware inhibit/hold-up design and controlled pulse, brownout, reboot and real coin acceptance are required before any paid use.
6. **Test identity/limits:** `intercon_remote_cs_protocol_test.cpp` exercises BLZCS1 encode/decode, wrong key/identity, corruption and record codec round-trip. `test_intercon_remote_cs_source.py` is source-pattern validation. These do not exercise the actual LittleFS file-write/rename fault path, runtime state machine against a real controller, backend financial transaction, physical acceptor or power-cut behavior.
7. **Exact CI:** Stage 5 workflow [44629292767](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44629292767) passed all three jobs (static-contract, signed-wire, ESP8266 compile); case guard [44629291957](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44629291957) passed. Shared Hardware/Contracts run [44629291962](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44629291962) failed compiling the unchanged ESP32 Vendo sketch at `Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino:6` because `mbedtls/sha256.h` is absent under ESP32 core 4.0.0. This is a destination-tree blocker, not evidence that the Stage 5 ESP8266 compile failed.
8. **Disposition:** keep #48 draft/LAB/NO-GO, keep #26 migration staging frozen, and do not treat #48's passing scoped workflow as backend, accounting, ESP32 or hardware acceptance. PHX-HARDWARE owns firmware/electrical review; PHX-PISONET/COE integration owns the router adapter in its own paths; PHX-CORE owns the durable credit contract; PHX-QA independently validates both sides; PHX-RELEASE preserves the no-release gate.




### 6.53 Stage 5 Remote CS bridge boundary — 2026-11-20 UTC00

COE Stage 5 PR #48 defines a new BLZCS1 HMAC-SHA256 controller/ESP protocol; it is not wire-compatible with the existing COE #26 OpenWrt `/cgi-bin/vendo` contract. The Stage 5 PR changes only Hardware staging/workflow paths; it does not implement the OpenWrt backend adapter or financial credit path. Keep it separate from #26 and unassigned until PHX-HARDWARE and PHX-PISONET explicitly accept or decline their review scopes.

**Mandatory bridge invariants before any paid use:** durably map (ESP identity, session) to (Vendo ID, original target nonce, customer account, expiry); bind each physical event to one stable backend nonce; treat timeouts as unknown and retry the identical tuple; verify the backend's signed durable receipt before exact event/session/pulse ACKN; retain pending/unknown state across router and ESP reboot; block new coin acceptance until reconciliation. Never infer customer identity from IP alone or regenerate credit after expiry without operator reconciliation.

The Stage 5 two-slot CRC32 journal and HMAC transport are not an independent protected anti-rollback witness, and HMAC does not encrypt the LAN transport. Host/native/ESP8266 CI does not establish LittleFS crash atomicity, physical pulse losslessness, 150 power cuts, or device soak. The existing backend's paid-state-uncertain and default-deny gates remain authoritative. No positive admission, migration, or production release is authorized by Stage 5 CI.
### 6.54 Remote CS v1 target-kind and expiry authority — 2026-11-20 UTC01

**Contract:** a physical ESP coin event may be ACKed only after the correct backend customer/target has durably committed the exact event once and returned a signed receipt. Before any paid backend mutation, the backend must prove that the active target is authorized for the adapter's declared product kind. A client-side check performed after the backend response is not a pre-credit safety gate.

**Observed Stage 5.1 gap (COE #49 `aeb8ff11...`):**
- `RouterV1.poll()` verifies a signed v1 response over `insert`, `target_nonce` and `expires`, but the response contains no target `kind` and no signed server time.
- `RouterV1.coin()` calls the v1 `coin` endpoint before rejecting a response with `rental:true`.
- The #26 backend's `coin` branch reads the target `kind`; for rental it calls `bp_rental_apply_coin`, updates rental progress and returns `rental:true` only afterward. Therefore an unsupported rental target can cause a backend rental-time mutation before the sidecar refuses the response and withholds ESP ACK. The existing mock test does not exercise the backend mutation.
- The adapter's documented hotspot-only assumption is not cryptographically or server-side enforced by the current poll response. Require a signed target-kind claim and server-side rejection before any rental/paid write, or a separately enforced hotspot-only controller identity that the backend checks before the coin branch. Do not rely on UI/operator configuration alone.

**Expiry authority:** the sidecar uses local `time.time()` to calculate the remaining ESP lease from router expiry. Since the signed poll response has no server-time anchor, a slow/rolled-back sidecar clock can over-open the ESP relative to the router's actual expiry; a late backend rejection can strand a physical pulse. Require a signed time anchor and monotonic lease calculation, or an equivalent server-enforced expiry gate before actuation. The current adapter also returns ACTIVE for an already-bound ESP session before recalculating remaining router TTL; every poll must enforce the close-before-expiry floor before that existing-session fast path.

**Required independent tests:** real backend-path tests for hotspot and rental targets proving the rejected rental case causes no ledger/time/progress mutation; valid and invalid signed target-kind; same-event retry after response loss; lost ESP ACK; reboot reconciliation; expiry and clock skew; plus journal readback/fault tests. Existing #49 CI's 16 SQLite/mock tests and ESP8266 compile are LAB/CI evidence only, not native router, physical coin or power-cut acceptance.

**Standing boundaries:** local SQLite FULL sync is not a protected anti-rollback witness; ESP CRC32 journal is not a protected signing witness; the physical pulse-to-first-durable-write loss window remains. COE #49 is a sidecar, not an installable OpenWrt service. Keep default dry-run; never enable paid-lab mode on an occupied/customer machine. No migration to #26 is approved. **PRODUCTION NO-GO.**

See [PHX-MASTER UTC01 COE #49 audit](PHX_MASTER_UTC01_20261120_COE49_STAGE51_TARGET_KIND_AND_CLOCK_AUDIT.md).



## PHX-MASTER 2026-11-20 UTC04 — Remote-head, cleanup and integration reconciliation

**Candidate-only interface gate for COE #49; no route or source ownership change.** The exact current #49 head remains `aeb8ff11b2f5db9a5f86280ab62ab988245f3919`, stacked on #48 `8286548e395366f2332830025fed00ceebdfb24a`. Hardware's only explicit response is audit-only ACK / implementation ownership declined (COE #49 comment [7028198239](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/49#issuecomment-7028198239)); no explicit CORE or PISONET scope ACK was found in the #49 thread.

1. **Target kind is pre-mutation authority.** A hotspot-only adapter must receive a server-authenticated target-kind claim, or the backend must independently enforce an adapter/controller identity bound to hotspot-only targets before entering the coin mutation branch. A response such as `rental:true` returned *after* `bp_rental_apply_coin` is not a rejection gate; the adapter cannot undo a rental mutation by withholding ESP ACK.
2. **Time and expiry require an authenticated anchor.** A signed `expires` value without signed server time does not establish remaining lease duration for a sidecar using local wall clock. Bind the time anchor to the router/controller/session/target/sequence and calculate local remaining lease with a monotonic clock. Re-evaluate the close-before-expiry safety floor on every poll, including the existing-session ACTIVE path.
3. **ESP ACK follows durable authoritative receipt.** Do not emit ACKN until the exact paid receipt is authenticated, bound to the same event/nonce/target/customer, and durably committed by the existing router accounting authority. Local SQLite state or an ESP CRC journal is not an independent protected financial witness.
4. **Tests must exercise the real mutation path.** A mocked `rental:true` response is insufficient. QA must prove that a rental target causes no ledger, rental-progress or time mutation; cover valid/invalid signed kind, wrong identity/nonce, duplicate/replay, response loss, lost ESP ACK, reboot reconciliation, expiry-floor, and clock rollback/skew.
5. **Ownership remains unchanged.** CORE owns router accounting/receipt authority; PISONET owns the router-side adapter/API boundary; HARDWARE owns ESP intake/lease/ACK behavior; QA owns independent regressions. These are review boundaries, not assignments or owner acknowledgements. Obtain explicit scope ACK/DECLINE before any source edit or route proposal.

The current Experiments `main` Vendo producer is not the signed target-kind/server-time producer required above. COE #26's candidate signatures are on a separate draft base and are not a deployed or approved producer. COE #49 remains **UNASSIGNED / AUDIT-ONLY / NO ROUTE TO #26**. This section states a review gate, not an adopted wire schema or production authorization.



## 6.53 Exact-head QA poll-fixture and RELEASE handover-freshness gates — 2026-11-20 UTC12

### 6.53.1 Poll response admission remains deny-only

Current HARDWARE #327 source/test head is e759f70325523fe6429170e8b4396e335f574c8b. Its focused quarantine and relay/output runs pass, but Full run 44732030246 fails in Controller protocol parity with the legacy message Missing poll signature check. The merge-tree test identities are v05_firmware_hardening_test.sh blob 41211b2c110ab409f6d9d1812ef12fda73b13211 and controllers.sh blob f7896647713d6bf8034ff48ed19b6383e4dedea0.

The v0.5 fixture requires response_sig and literal |poll| presence. The current firmware explicitly documents that register/poll admission signatures do not authenticate the returned configuration object and keeps that positive path dormant. This matches the deny-only contract in §§6.23 and 6.24. PHX-QA owns replacing the positive marker test with source-linked negative assertions for both boards; PHX-HARDWARE owns firmware. Never add a synthetic signature marker or enable keyless/unauthenticated poll admission to satisfy the legacy fixture. Focused host labs are simulated CI only.

### 6.53.2 RELEASE handover freshness is an admission gate, not a compile failure

Current RELEASE #291 head is d497ee71f1d84d9fd0ca22dd1127a53d62515642. Compatibility run 44736348774 passes both pinned ESP32 core legs. Windows run 44736348781 and Full run 44736348760 fail at the shared handover freshness gate.

At the exact head, handover_gate.sh blob d175106a9c534ca17a35f9f49082b70ea27e77da reports that .github/workflows/blazepwifi-build.yml is newer than the PROJECT_HANDOVER.md checkpoint and names last checkpoint commit 0f2e67b3794b2469523b51ced2ba4ec4a334e84b. The gate checks PROJECT_HANDOVER.md, CURRENT_STATE.md and CHANGE_LEDGER.md against subsequent meaningful source/workflow changes. The correct response is an owner-reviewed live handover update after the latest change, followed by rerunning Windows and Full. Do not bypass the gate. PISONET owns the two SoftTimer test paths in the #291 diff; this contract does not transfer them to RELEASE or Master.

### 6.53.3 COE destination remains unaccepted

At current #327 source and COE #26 destination heads, the two board sketch blobs differ; 25 source board-local Python labs have no destination Hardware Python identities; three source PHX-HARDWARE workflows do not have exact destination equivalents; and root NOTICE / Hardware license-notice scope is incomplete. The sibling Pisowifi MIT license blob match is not a Hardware subtree license decision. COE #26 remains frozen with five queued workflows and zero jobs. No migration is approved.

This section records an exact-head review gate only. It is not physical acceptance, financial authorization, release approval or permission to migrate.
## 6.55 Poll admission fixture and migration-parity gate — 2026-11-20 UTC14

### 6.55.1 The inherited positive marker is not an approved wire contract

At current HARDWARE #327 source/test commit `dc9af45eaa33713713473cfa1ea8ab051769286f` and docs/PR head `a2388aedc611e831f339a87555450bd5554fa781`, the exact docs-head Full run [#44756633635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44756633635) fails at the inherited `Missing poll signature check` assertion in the ESP8266 sketch. The fixture blob `41211b2c110ab409f6d9d1812ef12fda73b13211` requires both `response_sig` and literal `|poll|` presence. Current firmware intentionally keeps positive poll admission dormant; those string markers are not a signed response-envelope contract and must not be added to satisfy a stale fixture.

**Owner split:** PHX-QA owns replacing the positive marker assertion with source-linked negative/default-deny tests for both boards. PHX-HARDWARE owns firmware and its source-extracted labs. Preserve default-deny; do not add a synthetic signature producer, relax admission, or authorize coin intake. Focused host CI is simulated evidence only; physical acceptance remains NOT TESTED.

### 6.55.2 COE destination acceptance is independent of sibling license presence

At source tree #327 `a2388aedc611e831f339a87555450bd5554fa781` and destination PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, both recursive trees are complete. The source has 25 board-local Python labs and three scoped Hardware workflows; the destination has zero Hardware Python labs and one generic workflow. Both ESP8266/ESP32 sketch blobs differ. The source BlazePwifi MIT license matches destination `Pisowifi/LICENSE`, but source root NOTICE and destination Hardware-specific LICENSE/NOTICE files are absent. These facts do not establish test equivalence, import completeness, or Hardware license/notice scope.

No migration, copy, move, overwrite, rebase, cherry-pick, staging, or route promotion is authorized by this review.

## 6.56 Exact-head poll fixture must encode the approved deny-only contract — 2026-11-20 UTC15

At HARDWARE #327 docs/PR head `a2f2d42b1e65ceb0e60ae79517a0edc1d38a0d5d` and source/test commit `53243577ca145e90efa40eeadb536f1737933f6f`, exact-head focused relay [#44765919343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44765919343) and quarantine [#44765919179](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44765919179) workflows pass. Full [#44765919275](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44765919275) fails in validation job `136390525481`, invoked through `experiment/openwrt/BlazePwifi/tests/controllers.sh`, with `Missing poll signature check` at the ESP8266 sketch. The exact inherited fixture `v05_firmware_hardening_test.sh` is blob `41211b2c110ab409f6d9d1812ef12fda73b13211` and requires `response_sig` plus literal `|poll|` markers in both sketches.

Those string markers are not a signed response-envelope contract. The current producer does not emit `response_sig` for the register/poll/coin response bodies, and the firmware remains deliberately deny-only for positive poll admission until CORE defines the versioned envelope and key binding, HARDWARE implements the approved consumer, and QA verifies same-SHA golden vectors. Do not add synthetic positive markers, loosen verification, clear pending evidence, or enable coin/relay admission to make this fixture green.

**Owner split:** PHX-QA owns replacing the inherited positive string-presence check with source-linked negative/default-deny tests for both ESP8266 and ESP32. The tests must demonstrate that missing/unverified responses cannot enable admission, clear pending ingress evidence, authorize coin disposition, or energize outputs. PHX-HARDWARE retains firmware and source-extracted lab ownership. Focused CI is simulated/hosted evidence only; no physical board acceptance is implied.



## 6.57 Current source deny-only poll contract is not equivalent to COE #26 Hardware — 2026-11-20 UTC18

At Experiments HARDWARE #327 docs head `9bef8c1e7dcbde9e8987f14a1a874de1d7d11514`, the current ESP8266/ESP32 source no longer carries the legacy positive response_sig / |poll| signature-marker implementation. The COE #26 destination sketches still contain that older response_sig extraction and positive poll-signature calculation. Their Git blobs differ on both boards, and the source/destination hardening fixtures also differ.

The inherited source fixture still greps for response_sig, |register| and |poll|. Its Full CI failure is a test-contract mismatch, not permission to re-enable positive admission. PHX-QA owns replacing those string-presence checks with source-linked negative/default-deny tests for both boards. PHX-HARDWARE retains firmware ownership. No synthetic positive marker, weaker verification, pending-evidence clear, coin disposition, or relay-enable path is authorized.

COE #26 remains frozen until a versioned authenticated response/receipt contract is approved by CORE, implemented by HARDWARE, independently verified by QA at the same source SHA, and mapped to exact destination blobs, tests, licenses/notices and CI. No interface compatibility is asserted by tree similarity or historical signature code.

## 6.58 COE Hardware candidate must preserve deny-only admission and durable evidence — 2026-11-20 UTC19

The exact current source candidate is Experiments HARDWARE #327 at 1a631567eb0c14c12a114f592685f44cc414466f; the exact COE destination candidate is PR #26 at b382d233ff06c8791b1028bed3c617cc7b670d12. These trees are not behavior- or blob-equivalent. The following are mandatory interface and migration invariants:

1. **Missing-key / missing-signature default deny.** A response consumer must not initialize signature authorization to true and then skip verification when the controller key is empty. Register/poll authentication does not implicitly authenticate returned configuration. A separately approved config envelope and CORE/QA golden vectors are required before remote config can mutate controller, coin, relay or LED state.
2. **No destructive mount recovery.** A failed LittleFS mount is ambiguous evidence, not an empty journal. Do not format persistent storage automatically. Preserve the existing journal, latch recovery-required state and keep coin intake disabled.
3. **Quarantine before pending clear.** A quarantine disposition requires a matching durable coin-attempt marker and a successful append/commit. If append, flush, readback or durability verification fails, retain pending coin evidence and inhibit retries/actuation; never clear pending state on a best-effort append.
4. **Quarantine deletion requires authenticated reconciliation.** Network clients may read/export evidence. Deletion remains denied until an authenticated operator-recovery contract and durable receipt/reconciliation proof exist; an unauthenticated HTTP 200 delete route is not acceptable.
5. **Poll remains deny-only until the complete producer/consumer contract is approved.** Current #327 source acceptPollResponse returns false on both boards, and applyRemoteConfig is definition-only in both source sketches. Do not add positive poll admission or config application to satisfy an inherited string-presence test.
6. **Test identity follows the source contract.** The inherited v05_firmware_hardening_test.sh and COE test_firmware_hardening.sh still assert positive response_sig / register / poll markers. QA must replace these with source-linked negative/default-deny tests for empty key, missing signature, malformed response, provider error, and unsupported algorithm/major cases at the exact source SHA.
7. **Migration acceptance is independent of adjacent subsystem CI.** A matching Pisowifi MIT license, a passing Windows or Android job, or a successful ESP32 build does not establish Hardware subtree provenance, test identity, NOTICE scope or destination acceptance.

Current COE #26 destination source inspection identifies keyless signature bypass, unauthenticated remote-config application, format-on-mount-failure, quarantine append without verified commit before pending clear, and unauthenticated quarantine deletion. These are static source findings, not an observed physical/customer incident. Destination remains FROZEN until exact blob provenance, complete lab import/equivalence, license/NOTICE scope, pinned toolchain, destination CI and independent Hardware/QA/Release owner acceptance are verified.

No source file was modified by this contract update; no firmware, payment, migration or release authority is granted.


## 6.59 Cross-role firmware baseline and exact-build provenance — 2026-11-20 UTC20

A consumer PR may inherit firmware or shared runtime files from its base without changing those paths. Integration review must therefore distinguish the consumer's changed-file scope from its inherited source baseline.

1. **Pin the actual artifact source.** A firmware compatibility result must record the exact source commit, firmware file Git blob, board target, toolchain/core version, workflow run and job. A branch label or a passing build on a different source commit is insufficient.
2. **Scope the claim to the tested blob.** If a workflow tests an unchanged sketch blob from an earlier commit, it proves that blob under the tested toolchain. It does not prove the later host-lab tree, workflow wiring, or other source changes at a newer commit.
3. **Do not repair inherited firmware in a consumer PR.** The firmware owner controls firmware changes; the consumer role owns only its declared changed paths. A stale inherited firmware baseline requires owner-coordinated base/source selection or an explicitly qualified compatibility result, not an unauthorized edit by the consumer.
4. **Keep handover authority separate.** Canonical PROJECT_HANDOVER.md, CURRENT_STATE.md and CHANGE_LEDGER.md remain CORE-owned. RELEASE owns toolchain and release-workflow qualification. Master records the dependency and routes the action; it does not edit those source paths.
5. **Exact #328 example.** RENTAL #328 at 0e0da62 inherits ESP32 sketch blob 29f1125d from #289, with an unconditional mbedtls/sha256.h include. Current HARDWARE #327 source blob ae0da8e2 selects PSA crypto for Mbed TLS 4 and mbedtls/sha256.h for Mbed TLS 3. The #328 core-4.0.0 compile fails because the inherited header is absent; its six changed files do not include the sketch. This is a cross-role baseline blocker, not a Rental-owned firmware defect.
6. **CI evidence remains layered.** Passing APK identity and API21/API23 emulator smoke do not override a failed shared firmware build. Passing one firmware blob on two ESP32 cores does not establish the complete source tree or production acceptance.

This contract grants no source ownership, firmware modification, release authority, migration permission, or production approval. Preserve default-deny and all financial/hardware release gates.


## 6.60 BLAZE-COMMS recipient exactness and checkpoint idempotency — 2026-11-20 UTC20

The communication protocol defines `to` as one exact registered ROLE-ID or literal `ALL`. This is a control-plane envelope contract, not a subsystem API.

1. A role-specific message uses exactly one registered role string (for example `PHX-QA`); a global Master checkpoint uses literal `ALL`.
2. Arrays, semicolon/comma multi-target strings, unknown roles, empty values, leading/trailing whitespace, and case variants such as `all` are invalid. Do not silently trim, split, or accept partial recipient matches.
3. The current Master verifier enforces exact membership in the seven registered PHX roles or `ALL`; its regression suite covers known recipients, unknown/ambiguous recipients, invalid recipient types, and empty values.
4. One role activation per scheduled UTC hour uses one stable message ID. A retry/revalidation updates the existing checkpoint in place; it does not create a second comment for the same role/hour.
5. QA #292 remains based on historical Master base `b1ca02e...`; its test blob is unchanged, but its branch has no current PR-triggered run. Rebase/replay against the current Master candidate and obtain exact-head evidence before treating the QA branch as integrated.

The current UTC20 checkpoint was corrected from a recipient array to `"to": "ALL"`. The bounded four-case local test used the exact QA test and example Git blobs with the current verifier's extracted `validate_envelope()` function; it is not the full Master suite or hosted CI.

This contract grants no worker ownership, migration permission, merge authority, signing authority, hardware acceptance, or production approval.


## 6.61 Release compatibility evidence must identify the compiled source, not only the PR tree — 2026-11-20 UTC23

A release PR can check out its own branch for release tooling and a separate pinned source ref for a firmware compatibility build. Those are distinct source identities and must never be conflated.

1. **Record both identities.** Every cross-branch qualification must record the PR event/docs head, the exact external source/test commit, the exact firmware file Git blob, the target board, compiler/core/toolchain version, workflow run and job IDs.
2. **Verify before compiling.** The workflow must compare `git rev-parse HEAD` and `git rev-parse HEAD:<path>` in the external source checkout against the declared source commit and expected blob before invoking the compiler.
3. **Scope the PASS.** A successful matrix qualifies only the pinned source/blob and explicit toolchain versions in the successful jobs. It does not certify a different inherited file in the consumer PR tree, the entire product tree, a release package, hardware acceptance, or production readiness.
4. **Expose inherited divergence.** If the consumer PR tree carries a different inherited sketch blob, report that blob alongside the external pinned source. Never describe the external-source compile as proof that the consumer's local inherited sketch was compiled.
5. **Separate terminal gates.** A successful compatibility matrix or provenance suite does not override a failed Full/Windows handover, skipped signing/publishing, missing independent QA, or physical acceptance. A scoped PASS must not be promoted to a terminal Full PASS.
6. **Preserve ownership.** HARDWARE owns firmware/source changes; RELEASE owns compatibility workflows and release tooling; QA owns independent source-linked negative tests; the canonical product handover remains with its designated source owner. PHX-MASTER records the dependency and does not edit worker source paths.

**Exact example — RELEASE #291 / HARDWARE #327:** PR #291 docs head `88d8e326e0b19bed8a157fb88aa0a3a9524d90a9` runs a compatibility workflow whose external checkout is HARDWARE #327 source/test `83c20c9d59bcdf6c24e2112f3396b90847b5bde0` and ESP32 sketch blob `ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7`. Run [#44835998901](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44835998901) completed 3/3: ESP32 core 3.3.13 and 4.0.0 reproducibility jobs plus the 32-test provenance suite. The Release branch's own inherited ESP32 sketch is a different blob, `29f1125d52ff474a0d028ad41f7af201be1f0f9d`; the compatibility workflow does not compile that local blob. Release #291 Full and Windows still fail at handover freshness, so this scoped qualification is not a release approval.

This contract grants no source ownership, route promotion, merge, signing, hardware flash, payment operation, or production approval.


## 6.62 Immutable pinned-source qualification vs current branch-tip claims — 2026-11-21 UTC00

A reproducible build against an immutable source SHA remains evidence for that exact source commit and exact compiled file blob. A later branch advance does not automatically invalidate the compiled artifact identity, but it does change what can truthfully be called the **current** source/test revision.

1. Record the qualified source commit, current source/test commit, compiled file path/blob, build dependencies, toolchain, workflow/job IDs, and consumer PR/docs head separately.
2. If the branch advances, compare the exact changed paths and compiled/dependency blobs. If the compiled file and all build inputs are byte-identical, preserve the earlier result as a qualification of the pinned snapshot; do not relabel it as a build of the new tip.
3. A host-lab/test-harness-only change does not invalidate a firmware compile for an unchanged firmware blob, but the earlier run does not test the new harness. Re-run focused lab tests at the new source/test SHA.
4. Re-run the compatibility build when a compiled source file, include, generated input, build script, compiler configuration, or other build dependency changes. Do not require an unrelated documentation-only rebuild.
5. PR descriptions and handovers must not use “current head” for a stale pin. Show both the immutable qualified pin and the live branch source/test SHA, with the exact blob comparison.
6. Attribute a failing wrapper accurately: when `tests/controllers.sh` invokes `tests/v05_firmware_hardening_test.sh`, report the nested test file as the failing assertion owner, not the wrapper itself.

**Exact example — #291 / #327:** Release compatibility run #44843256993 qualifies Hardware commit `0f365dada...` and ESP32 sketch blob `ae0da8e2...`. Current #327 source/test `177312434...` is two commits ahead with only the handover and host-lab fixture split; the same 71,103-byte sketch blob is verified at both commits. The earlier compile remains valid for that blob, but does not test the new lab fixture modules. Current #327 focused lab CI must be cited separately.

This contract grants no source ownership, route promotion, merge, signing, hardware flash, payment operation, or production approval.

## 6.63 Boot-time output-safe ordering before LittleFS mount — 2026-11-21 UTC02

**Scope:** source-observed ESP8266/ESP32 boot ordering in HARDWARE PR #327 only. This is a bounded integration invariant, not a claim of physical acceptance or a new positive controller/coin authorization contract.

1. Load local board configuration and initialize the secondary persistent fault backup first (EEPROM on ESP8266; NVS on ESP32).
2. After validated runtime pin/polarity selection, preload relay/LED outputs OFF and attach the coin ISR before `initPendingStore()` mounts LittleFS.
3. If an ingress fault is observed before LittleFS is available, persist through the already initialized secondary store; after LittleFS mounts, boot recovery must observe the marker and deny admission.
4. If both stores fail, the current boot remains denied, but durable post-reboot evidence is not guaranteed. Do not describe this as crash-atomic persistence.
5. This ordering does not prove the external relay's electrical state during reset, pulse capture on real hardware, or 150-power-cut/30-device acceptance. No register/poll/coin response signature, positive admission path, financial behavior or shared API was changed.

**Exact evidence:** HARDWARE source/test `2d10db5db8ad95f15abf335f25cbbbb2d02c7fae`, firmware behavior commit `ebadec9aaed3113c632a0776a2ac71238ecd0d13`, PR/docs head `1db9855aadb1aeeab797c9e298a850546b66037f`; Quarantine #44854558168 and Relay #44854558206 PASS. Full #44854558160 remains FAIL at QA-owned `Missing poll signature check`.

**Evidence tier:** SIMULATED / FOCUSED CI VERIFIED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO. PHX-HARDWARE owns implementation; PHX-QA owns the stale positive fixture; PHX-MASTER records the cross-role gate only.



## 6.64 Coin-authority board parity is a test-coverage guard, not admission authority — 2026-11-21 UTC04

HARDWARE #327's normalized ESP8266/ESP32 helper-parity lab now covers 17 shared helpers and injects six ESP32-only fail-open mutations. This is useful source/test coverage, but parity is not proof of authenticated controller authority or durable financial behavior.

1. A parity PASS is bound to the exact Hardware source/test commit and exact helper blobs. Record the source/test SHA, both sketch blobs, the parity-lab blob, focused workflow/job IDs, and any docs-only PR head separately.
2. A normalized source-parity comparison establishes only the declared helper equivalence and the injected mutation cases. It does not prove electrical pulse capture, relay behavior, LittleFS durability, power-cut recovery, replay safety, signer identity, anti-rollback freshness, or hardware acceptance.
3. The current helper set includes `acceptPollResponse`, `coinPostDispositionVerified`, `canAttemptCoinPost`, `markPendingPostAttempt`, `pendingAttemptMarkerMatches`, and `clearPending`. The six ESP32-only mutations must remain rejected. Do not turn a parity helper into a positive admission path.
4. Poll and coin admission remain default-deny until CORE publishes the approved authenticated register/poll response and event-bound receipt contract with golden vectors, and QA independently verifies source-linked negative/default-deny behavior. The inherited positive `Missing poll signature check` assertion is not permission to invent a signature or weaken firmware denial.
5. Release compatibility remains pinned-source evidence. At the UTC04 audit, RELEASE #291 compiles Hardware pin `268ca9b...`; current #327 source/test `c5cb17b...` is three commits ahead. ESP32 and ESP8266 sketch blobs remain identical, but the host poll-lab blob changed. Preserve the old compile qualification for the exact unchanged firmware blob; cite current-source focused CI separately and do not claim the old compile tested the new lab.
6. COE #26 remains frozen until source/destination blobs, complete test import, license/NOTICE scope, exact-head destination CI, and independent QA are accepted. A source parity PASS does not authorize migration.

**Exact evidence:** HARDWARE #327 source/test `c5cb17bfa35ea24615f53097b936c49ebe5f0104`; PR/docs head `efb10354a71c392de8c72b6e73ff7616158cd675`; focused runs #44863161774, #44863167396, #44863167432, #44863539280, #44863539382; Full #44863539439 fails QA's positive poll-signature assertion. RELEASE #291 compatibility #44862405800 passes 3/3 on pin `268ca9b...`.

This contract grants no source ownership, route promotion, merge, signing, hardware flash, payment operation, migration approval, or production release.


## 6.65 Zero-pulse RAM state with a durable POST-attempt marker is a financial disposition contradiction — 2026-11-21 UTC06

A pending coin event is not safely absent merely because the in-memory pulse counter is zero. If the durable one-shot POST-attempt marker still represents a nonzero event, the RAM and durable state disagree and must be treated as unresolved financial evidence.

1. On both ESP8266 and ESP32, if pendingPulses == 0 while a valid /pending.attempt marker remains, latch journalRecoveryRequired=true, emit an operator-reconciliation diagnostic, deny further admission, and return without appending a quarantine record or clearing pending/attempt evidence.
2. Do not use a zero-pulse fast path to infer “nothing to quarantine” when a durable attempt marker exists. The marker is evidence that a POST may already have been dispatched; silently clearing it could destroy replay/reconciliation evidence.
3. The test-first RED must demonstrate that the inconsistent state is detected and no clear/append occurs. The source fix must be tested on both board implementations and preserve the default-deny poll contract.
4. This invariant does not establish crash-atomic financial state, server receipt authority, electrical behavior, or physical power-cut durability. The current evidence is source-extracted simulation plus focused hosted CI only.
5. HARDWARE owns firmware and lab implementation; QA owns the inherited positive poll-signature fixture; CORE owns the authenticated poll/receipt contract. Master records the cross-role invariant and does not modify those source paths.

**Exact evidence:** HARDWARE #327 test-only RED 8b7311b28a4e35ddac1bd9208df40eb6f9721bb2, run #44872068887; source fix 3292d2a1e207da4241189952eec0e97255a48475; source/test focused Quarantine #44872148862 (36/36) and Relay #44872148854 PASS; current docs head a873042c2a59a2197e4b4457c18dc75da12a0d02, Quarantine #44873105133 PASS, Relay/output #44873105198 PASS. Full #44873105141 fails at QA-owned Missing poll signature check after 15/15 target/platform jobs pass; downstream jobs are skipped.

**Disposition:** SIMULATED / FOCUSED CI VERIFIED. PHYSICAL ACCEPTANCE: NOT TESTED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.

## 6.66 Release compatibility pins must follow the current firmware source identity — 2026-11-21 UTC06

A compatibility PASS is bound to the immutable source SHA and compiled file blob in the workflow. It cannot be promoted to current-branch qualification after the Hardware source changes.

1. Record the Release PR head, Hardware source/test SHA, exact board sketch blob, core/toolchain versions, workflow run/job IDs, and docs-only handover head separately.
2. Recompare the compiled sketch and build inputs whenever the Hardware source/test branch advances. A changed sketch blob requires a new exact-source compatibility run; do not reuse an earlier PASS as current-tip evidence.
3. Preserve the old run as valid evidence for its old immutable pin, but label it historical and scope-limited.
4. Do not edit RELEASE-owned workflow/test paths from Master. RELEASE owns its pin and compatibility workflow; HARDWARE owns the sketch; QA independently reviews the result.

**Exact example:** RELEASE #291 current head f06ac4df2f61b9c39a03a6ff6009b32948b94778 pins Hardware 268ca9bde6d3710b418134ffd328060250fad42f and ESP32 blob 09c02d589ae15b0c8a4f2a3bbcdee20c41d2cb79 (test blob e6d1308ad8be08405da74dbd8dd8a1e47b63842f, workflow blob 3597b451887e1b612ddea3d383093bba734bbc0d). Current HARDWARE #327 source/test 3292d2a1e207da4241189952eec0e97255a48475 is 11 commits ahead / 0 behind and modifies both board sketches. Current ESP32 sketch blob is 7ffb7b534c7163678726902946a17b04992950a0, not the pinned blob. Compatibility run #44862405800 remains a 3/3 PASS for the old pin only; it does not qualify the current #327 tip. RELEASE must refresh the pin and rerun ESP32 cores 3.3.13 and 4.0.0 plus reproducibility/image identity checks.

This contract grants no source ownership, route promotion, merge, signing, hardware flash, payment operation, migration approval, or production release.

## 6.67 Checksum-manifest publication durability and failure-injection boundary — 2026-11-21 UTC06

A generated appliance release manifest is not complete merely because a same-directory no-overwrite hard link was created. The final manifest bytes, published name, and temporary-name cleanup must have distinct durability boundaries.

1. After atomic no-overwrite publication, pin the containing directory with an O_DIRECTORY | O_NOFOLLOW descriptor and open the final manifest relative to it with O_NOFOLLOW. Verify the final file is regular, the published and sorted names identify the expected inode/link count, and the unsorted input is a separate regular file.
2. Fsync the final manifest file descriptor, then fsync the containing directory before removing either temporary name. Remove temporary names relative to the pinned directory descriptor, then fsync the directory again.
3. Any open, stat, fsync, or unlink failure must stop packaging with a nonzero RELEASE-BLOCKED result. Do not use a privileged install or unsandboxed fallback. A pre-cleanup file or directory sync failure must retain the temporary names as recovery evidence.
4. Independent regression coverage must inject failure at both pre-cleanup sync boundaries: the manifest-file fsync and the directory fsync that persists the final published name. Verify nonzero failure, final-name preservation, and temporary-name preservation. The successful call-order test alone is insufficient.
5. Hosted call-order and failure-injection CI is filesystem-API evidence only. It does not establish storage-controller power-loss durability, actual ImageBuilder sandbox execution, physical power-cut acceptance, or production release readiness.

Exact reviewed implementation: CoinOperatedEcosystem PR #35 source/test commit 3f4028aec38f922e197fa25bd54bf31cdd4c31cd, docs head 93bab4c97e2a487a3223dc209c5be8fbbc609b5c. Current exact-head packaging tests pass 124 tests with two intentional skips; the profile gate and mandatory sandbox remain fail-closed. Master does not own or modify the RELEASE packager or its tests.

This contract grants no merge, signer, publication, hardware flash, payment operation, migration, or production release authority.


### UTC08 exact-head evidence update — 2026-11-21T08:47Z

The previously requested second pre-cleanup directory-fsync failure injection is now present in COE RELEASE #35 source/test commit `d5a2d727727d7019cf3b4ad60503a4fb821d69d1` (`test_generated_wrapper_keeps_temporary_manifests_when_precleanup_directory_sync_fails`). Current docs head is `d28271a35776543bf558c90e3a117957829ee61c`. Exact-head validation run [#44879927378](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927378), job `136772755043`, reports **125 tests PASS / 2 intentional skips** and the second-directory-fsync failure test passes. This resolves the earlier Master test-coverage request at the hosted unit-test level.

The same run then correctly fails all 10 appliance profile admissions because no approved site-scoped RFC 4193 ULA /48 has been supplied. Case-collision [#44879927411](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927411) passes. Mandatory sandbox [#44879927380](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927380), job `136772754810`, passes host preflight but fails closed because Bubblewrap is absent (exit 125); namespace and packaging tests are skipped. This does not prove storage-controller power-loss durability, real power-cut behavior, or actual ImageBuilder namespace execution. RELEASE retains source/test ownership; PRODUCTION NO-GO remains.

## 6.68 Arduino staged-source provenance must bind the complete declared source tree — 2026-11-21 UTC10

A successful board compile or a checksum over staged output is not proof that staged build inputs correspond to the pinned Git source. Before writing or refreshing `BUILD-PROVENANCE.json` or `SHA256SUMS`, the release pipeline must establish a closed, descriptor-safe inventory of every declared input for the selected Arduino target and bind each path to the exact Git tree/blob identity at the pinned source commit. This includes the sketch tree, local library tree, required `library.properties`, included headers, and declared rebuild/build-control metadata such as `esp/REBUILD.md`.

The verifier must fail closed on missing source blobs, extra or missing staged paths, or any staged sketch/library byte drift. It must compare the staged copy against the exact pinned Git tree before manifest creation and revalidate after any later packaging/checksum rewrite. The provenance manifest and checksum file must not be allowed to bless a staged tree that diverges from the source pin.

Required independent regressions: (1) assert every required source path/blob is represented; (2) mutate a staged local-library file and require `ProvenanceError`; (3) mutate a staged sketch file and require `ProvenanceError`; (4) verify no manifest/checksum update occurs after a failed comparison. Exact #291 current-head CI [#44892584693](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44892584693) records three failures: omitted `esp/REBUILD.md` / `BlazePendingSequence` library blobs and missing rejection of staged library/sketch drift. This is a RELEASE-owned implementation defect/regression; PHX-MASTER owns only this cross-repository contract. Do not weaken the tests or claim release qualification until the owner fixes and reruns the exact head.


## 6.69 Post-clear ISR sequence recheck is required before output restoration — 2026-11-21 UTC11

When an approved event-bound coin POST disposition eventually allows the positive disposition path, the pre-clear ISR snapshot alone is insufficient. The coin ISR sequence must be reconciled both before and immediately after clearing pending journal state.

1. Before clearPending(), call reconcileUnobservedCoinEdges(). Attempt the pending clear only when the pre-clear snapshot reports no unhandled ISR edges.
2. Immediately after clearPending() returns, call reconcileUnobservedCoinEdges() again before output restoration. If an ISR edge arrived during the blocking filesystem clear, the second snapshot must update the observed sequence, latch the poll-pulse fault, and keep the output policy deny-only pending operator reconciliation. A pre-clear snapshot cannot authorize a post-clear output decision.
3. Retain explicit no-edge, pre-existing-edge, and edge-during-clear scenarios. The regression must reject removal or bypass of the post-clear check; the current source-extracted mutation test rejects that change with exit 32.
4. This contract is not admission authority. On both current boards coinPostDispositionVerified returns false and acceptPollResponse returns false until CORE publishes the approved authenticated register/poll and event-bound receipt contract and QA approves golden vectors. The positive disposition branch remains unreachable in current production firmware.
5. Exact evidence: HARDWARE #332 source/test commit 8b5b99e08297ba85bda1e665818161ee8d8859f6, PR/docs head 9f1d9ebf9c7256da2e8eace4bc0be510f6566daa, focused source-extracted C++17 run #44898340322 PASS; current Quarantine #44898547339 PASS; Full #44898547404 still fails the inherited QA positive poll-signature fixture. SIMULATED / FOCUSED CI VERIFIED only; not GPIO timing, LittleFS crash durability, relay acceptance, 150 power cuts, or physical hardware acceptance.
6. HARDWARE owns firmware and labs; QA owns independent fixture review; CORE owns the authenticated contract. Master records this cross-role invariant and does not modify subsystem source paths.

This contract grants no source ownership, route promotion, merge, signer, publication, hardware flash, payment operation, migration, or production release authority.


### UTC12 evidence update for §6.67 — 2026-11-21T12:38Z

COE RELEASE #35 now adds a stricter Bubblewrap executable trust check alongside the manifest durability contract. The host preflight and runtime runner reject a final-component symlink, setuid/setgid bits, and group/world-writable mode bits; ordinary executable mode 0755 remains accepted. This is path/mode validation only and does not pin Bubblewrap binary contents, prove directory ownership, or establish trusted-directory immutability.

Exact COE #35 source/test head `e1934fcb42f493ac0929490884045d54ad3a035e`, docs head `9d6fa64113243981efcc4b5c7af098a5c4bb94c8`. Shared validation [#44903155982](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903155982) reports 133 tests PASS / 2 intentional skips and the manifest durability marker, then correctly fails all ten profile admissions without an approved site ULA /48. Sandbox [#44903155993](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903155993) passes 18 host preflight tests but fails closed because Bubblewrap is absent (exit 125); case-collision [#44903155996](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903155996) passes.

This is hosted filesystem/path-mode test evidence only. No actual namespace or ImageBuilder execution, storage-controller power-loss proof, physical power-cut acceptance, or release authorization is established. RELEASE owns the implementation; PHX-MASTER records the cross-role gate only.

### UTC14 evidence update for §6.67 — 2026-11-21T14:36Z

Current COE RELEASE #35 PR head is `a533ec7b3f8080eb7f3780ba59d4bb411906f503`. Exact-head shared validation [#44913144724](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44913144724) ran 139 tests with two intentional skips and emitted `PHX-MANIFEST-DURABILITY-PASS`; the subsequent ten appliance-profile checks correctly fail closed because no approved site-scoped RFC 4193 ULA /48 is available. Sandbox [#44913145098](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44913145098) passed 23 host tests, then exited 125 because Bubblewrap is absent; case-collision [#44913145084](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44913145084) passes.

This is hosted unit/profile/path-gate evidence only. It does not prove actual user-namespace/ImageBuilder execution, storage-controller power-loss behavior, physical power-cut acceptance, or release readiness. RELEASE owns implementation; site authority and Infrastructure own the missing prerequisites. PRODUCTION remains NO-GO.

## Architecture heading-number audit — 2026-11-21 UTC15

Top-level level-two 6.x headings contain five legacy duplicate numbers: 6.9 (lines 278, 404), 6.10 (305, 413), 6.11 (317, 426), 6.25 (542, 572), and 6.38 (782, 794). Nested 6.x.y headings are excluded. Explicit non-heading references to §6.9 in this file point to the first ULA installation-identity contract at line 278. No body references to the other four duplicate numbers were found in this file. Cross-document references are not fully audited, so no renumbering was attempted.

A regression test now rejects additional top-level collisions outside the reviewed legacy set {6.9, 6.10, 6.11, 6.25, 6.38}. Existing collisions are not claimed fixed.


## 6.70 Host-lab module extraction is byte-preserving, not hardware acceptance — 2026-11-21 UTC19

PHX-HARDWARE PR #336 is a cleanup-only child of PR #335. Parent #335 documentation head is `d09b0c9dafad8dbbcda5723d8094f4975c14a274`; child #336 head is `741068c7804b83897f5deab5afc7739457532427`. The child changes only the ESP32 quarantine host-lab runner and its adjacent C++17 template module. It does not change either production firmware sketch.

A source-level exact-blob readback compared the raw C++ string embedded in the parent runner (`3723bc38e80bab5a458812162f48051356dc235b`) with the new module (`9e94b69adff78ac5b45076c1de362f93a8df568e`): both strings are 17,937 characters and compare exactly equal. The child runner (`f952b1ce98682e3c8618c3ce4216b90a034b378c`) imports `CPP` from `quarantine_readback_lab_cpp.py`. This proves the template bytes were relocated unchanged; it does not prove the entire runner is behaviorally identical or that hardware is accepted.

Exact-head Quarantine CI [#44943004243](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44943004243) completed SUCCESS. Its source-extracted host logs report 72/72 quarantine scenarios PASS, while explicitly recording `SIMULATED_ONLY=1`, `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`. Exact-head Full [#44943004250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44943004250) completed FAILURE at Controller protocol parity / `Missing poll signature check`; all 14 firmware/platform targets and Android completed SUCCESS, while downstream simulation, signing and publishing jobs were skipped.

**Classification:** human-debuggability cleanup and source-extracted CI only. HARDWARE ACCEPTED: NO. Physical coin, relay, flash, power-cut and 24-hour soak evidence remain NOT TESTED. Preserve the firmware default-deny contract; PHX-CORE owns the authenticated producer contract and PHX-QA owns the independent fixture. No migration, merge, release or hardware action is authorized.


## 6.71 Manifest baseline and owner-PR candidate trees are distinct migration authorities — 2026-11-21 UTC20

The source ref in OWNERSHIP_ROUTES.json is a pinned repository baseline, not a wildcard reference to whichever role branch happens to be newest. For every migration audit, record the manifest baseline and each current owner-PR candidate separately.

1. The current manifest pins Experiments main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b and COE #26 at b382d233ff06c8791b1028bed3c617cc7b670d12. The route matrix for those refs must not silently use files from a later owner branch.
2. A role-owned PR candidate such as HARDWARE #336 at 000d4e6804c451991e1cf81ec97d1b2d7ed6b526 is a separate candidate tree. Apply its counts only to the routes and exact paths that candidate actually contains; do not project its added lab/tests onto unrelated role routes or rewrite manifest source_ref without owner review.
3. Bind CI to the exact PR head and report source/test commits separately from docs-only heads. For #336, source/test is 741068c7804b83897f5deab5afc7739457532427 and final docs-only head is 000d4e6804c451991e1cf81ec97d1b2d7ed6b526. Current-head Quarantine #44943506271 passes source-extracted tests; current-head Full #44943506269 fails at the inherited Missing poll signature check. The old source/test run must not be relabeled as a current-head run.
4. Per-route admission requires exact source and destination paths, Git blob SHA and mode, relative-path/import completeness, test identity, license/NOTICE scope, and terminal CI at the proposed integration SHA. A filename match or one identical LICENSE is not sufficient.
5. The current #336 candidate contains 33 Python lab/helper files absent from COE Hardware; the ESP32 and ESP8266 sketch blobs diverge from COE #26, and the QA test trees are not equivalent. The manifest baseline and owner-candidate route counts are intentionally recorded separately in the UTC20 Master audit report.

This is a provenance and coordination contract only. It does not authorize route promotion, staging, copy, move, merge, release, signer provisioning, firmware flash, payment operation or production acceptance. COE #26 remains frozen and PRODUCTION NO-GO.
## Appendix — current CORE poll-auth versus coin-receipt boundary (2026-11-22 UTC11)

This appendix updates the source detail behind §2.2 without approving a positive response schema or changing any runtime contract. The current CORE #252 producer no longer needs to be described only as “no response signature”: register/ping and poll now carry a nested `config_auth` object under `blazepwifi-controller-response-v1`. The object is HMAC-authenticated but deliberately sets `admission_allowed:false`. The poll body retains legacy `insert` for compatibility only; CORE's source comment says new hardware must ignore it as authority.

The Hardware #327 consumer remains fail-closed: `acceptPollResponse()` clears the active target and returns false; `coinPostDispositionVerified()` also returns false. Hardware #340 ignores register/poll fields and reasserts `denyRemoteControl()`. Neither branch implements positive poll admission.

COE #26 still expects a top-level `response_sig` and derives legacy `|register|` / `|poll|` tuples. Its test enforces those legacy strings. This does not match CORE #252's nested `config_auth`; the destination remains frozen and has no completed CI jobs. Do not restore the legacy assertion by weakening firmware default-deny.

COE #45 defines a separate `blazepwifi-coin-receipt-v1` HMAC-SHA256 event-bound receipt contract. It is explicitly `CONTRACT CANDIDATE / TEST VECTORS ONLY / RUNTIME DENY`; its golden-vector test passed at exact head #45, but it is not the controller register/poll contract and does not prove firmware runtime acceptance. Do not reuse the member-operation `response_sig` or controller-response key/domain for the receipt MAC.

**Owner sequence:** CORE publishes the canonical versioned register/poll producer contract and separate coin-receipt semantics; HARDWARE implements only after that contract is approved; QA independently verifies exact producer/consumer golden vectors and replaces the inherited positive legacy fixture with negative/default-deny tests in the interim; COE integration owner reimplements destination consumer/tests under its own branch after per-file provenance and exact CI review. Until then, poll and coin disposition remain deny-only. This appendix is coordination evidence, not release authorization.\n

## Appendix — COE INTERCON Stage 5.1 router bridge boundary (2026-11-22 UTC13)

COE #49 Stage 5.1 is a separate experimental sidecar candidate, not a replacement for the canonical CORE controller-response contract or the frozen COE #26 destination. Its adapter documentation describes the existing router v1 request digest as SHA256(secret|action|id|nonce|pulses|target|secret), explicitly not HMAC; the ESP command channel uses a separate HMAC protocol. Do not collapse these into one cryptographic contract or describe the router v1 digest as HMAC. The Stage 5.1 bridge tests use FakeRouter/FakeEsp and SQLite and are explicitly not real OpenWrt/ESP hardware tests. Its stage-specific suite passes, but the shared COE workflow still fails ESP32 compilation because the staged sketch includes mbedtls/sha256.h, while current source #327 has an Mbed TLS 3/4 guard. No positive financial or hardware admission follows from the isolated bridge test. Keep the candidate review-only until CORE, HARDWARE, QA and COE owners approve the exact producer/consumer contract, build parity and migration provenance.


## 6.74 — Hardware #343 GPIO parser lab does not approve poll authentication (2026-11-22T17:40Z)

This appendix reconciles the current exact owner refs. It does not approve a positive poll response or change any runtime contract.

### Exact producer and consumer evidence

- CORE #252 `vendo` blob `16eb4105c15569dfd77b19a276ee05a25768083e` emits a nested `config_auth` object for register/poll. Its helper in `controller.sh` blob `1a820416051a7af5462841b191b02630aa87781f` uses the versioned domain `blazepwifi-controller-response-v1`, includes the requested policy/nonce/window and an explicit `DENY` bit, and serializes `admission_allowed:false`. The separate member-operation `response_sig` values are not the poll contract.
- HARDWARE #343 ESP8266 sketch blob `ac7712ef9e41c396d87b6a336e82a8335c7e9b2f` and HARDWARE #327 ESP32 sketch blob `7ffb7b534c7163678726902946a17b04992950a0` both keep `acceptPollResponse()` deny-only: clear `insertMode` and `activeTarget`, then return false.
- COE #26 `vendo` blob `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e` still uses `vendo_poll_sig()` and a top-level poll `response_sig`. It is a separate derived candidate and is not byte- or interface-equivalent to the current CORE producer.

### Ownership and acceptance boundary

HARDWARE #343 tests the actual production `jsonInt()` parser with a non-default GPIO tuple (3/12/13) plus unknown-polarity and invalid-pin deny cases. Its focused Quarantine and Relay CI passes, but its Full workflow still fails the inherited QA assertion `Missing poll signature check`. That parser/GPIO work does not establish authenticated poll admission, coin-post disposition, physical relay acceptance or production readiness.

Do not add a positive `response_sig` to either firmware sketch merely to satisfy the legacy test. PHX-CORE owns the canonical producer contract and golden vectors; PHX-HARDWARE owns the consumer; PHX-QA owns the stale fixture and independent negative/default-deny tests. COE #26 remains frozen until its own integration owner reconciles the derived producer, test identity, source pins, imports, licenses/NOTICE and exact CI.

**Disposition:** current poll/coin admission remains deny-only. No schema approval, route promotion, migration, merge, release, signer provisioning, hardware flash or physical acceptance is granted by this appendix.


## 6.75 Cross-repository migration evidence is snapshot-scoped, not current integration approval

A migration manifest proves only the identities it explicitly pins. Before any destination staging proposal, compare each mapped source blob against (1) its pinned historical source tree, (2) the current source default/development refs and active owner candidate, and (3) the destination candidate tree. Separately reconcile test identities, imported lab/helpers, Git modes, LICENSE/NOTICE scope and terminal CI at the exact destination SHA. A destination that matches an old snapshot is not necessarily current-source complete. Summary counters must be recomputed from the actual table, not copied from the manifest summary. Any source drift, absent path, divergent test, missing notice, incomplete import or nonterminal/failed CI keeps the destination FROZEN. A `DRAFT_REVIEW_ONLY` route cannot authorize copy/move; PHX-MASTER remains coordination-only with `target: null`.


## 6.76 — Relay-disabled coin edge is non-crediting (provisional; Hardware #345 test-first RED, 2026-11-22T23:26Z)

**Status: PROVISIONAL / OWNER REVIEW REQUIRED.** At the exact Hardware #343/#345 source, both ESP8266 and ESP32 sketches use relayEnabled in applyOutputs() to force the relay output OFF, but sampleCoinPulseEdge() does not include relayEnabled in its sampled-edge eligibility conditions. With insertMode and activeTarget still set, a sampled active GPIO edge can enter the normal pending-pulse path even though the acceptor relay is disabled. This is a source-level gap reproduced by the Hardware #345 test-first RED; it is not evidence of a customer incident.

**Required invariant:** When relayEnabled is false, a sampled GPIO transition must not increment pendingPulses, create or refresh a normal pending record, or become coin-POST eligible. Fail closed: keep relay and LED OFF, clear insertion mode and active target, latch a boot-visible sticky ingress fault using the established dual-store/fault-marker semantics, and require operator reconciliation. No credit, receipt, lease, or customer balance is created. Apply consistently to both board sketches; do not bypass canAttemptCoinPost or weaken poll authentication.

**Exact evidence:**
- ESP8266 sketch blob: 01fe33404d51653515e64833038d23d080ff80b2.
- ESP32 sketch blob: 9011029ea05bb6160bc326598e6d25cbe953c4c2.
- Hardware #345 is a test-only child of #343, pinned parent dfeff7d5f63e699de7bc296c7641f2493f1e0e13; test head 834738d2e82b6857779935b988c4046cbcb6c89f. Its only changed path is poll_loop_blocking_inhibit_lab_scenario_fixtures.py.
- Exact-source Quarantine run 45083252631 fails at ESP8266 with expected exit 0, got 60 (RED). Full run 45083252628 fails at the inherited QA-owned Missing poll signature check; target firmware builds and Android pass, downstream simulation/signing/publication are skipped.

**Ownership and acceptance:** PHX-HARDWARE owns both sketch changes; PHX-QA owns independent source-linked negative/default-deny verification; PHX-MASTER owns this provisional cross-role invariant only. Keep #345 draft until the exact-source RED is followed by a source fix and exact-head Quarantine/Relay/Full evidence on both boards. Physical acceptance remains NOT TESTED. This appendix grants no release authority.

## 6.77 Configured coin-ingress gate parity — Hardware #345 current exact head (2026-11-23 UTC00)

Hardware #345 has advanced from the UTC23 test-only RED to a source correction on both board sketches. At exact PR head `01916c89ae6718d3991c778b676d06718155d6a2`, both `sampleCoinPulseEdge()` paths now require `controllerEnabled && coinEnabled && relayEnabled` before a sampled edge can become pending/credit eligible. A sampled active edge while any configured gate is OFF enters the existing sticky poll-fault path, clears insertion mode/target, deasserts relay/LED before persistence, preserves any pre-existing pending identity, and creates no new pending credit. Temporary poll-time suspension remains distinct because `relayEnabled` stays true while `pollIntakeSuspended` temporarily deasserts the output.

**Exact source:** ESP8266 blob `203db2f8394a5466517845d964195f8d6f25752f`; ESP32 blob `2a5bad5904a1f6afabdcac95e762482975ebd886`; shared disabled-ingress fixture blob `103357a14381fbc26240a3910373332f75c2ec83`. The Hardware Quarantine job compiles both exact board sources and exercises controller/coin/relay OFF with and without an ISR edge (six cases per board). Exact-head Quarantine [#45085291729](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45085291729) and Relay [#45085291635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45085291635) pass. Full [#45085291816](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45085291816) still fails at the inherited QA-owned `Controller protocol parity` / `Missing poll signature check`; downstream simulations/signing/publication are skipped.

**Durability boundary:** `latchPollPulseFault()` attempts secondary NVS/EEPROM and LittleFS markers. The new six-case fixture checks the LittleFS marker and no-credit/no-save/output-off state, but does not independently assert both stores in every disabled-gate case. If both stores fail, the source explicitly says current-boot fail-closed but reboot durability is NOT established. QA must independently verify both stores, partial/dual-store failure, and preservation of an already-pending identity before any durability claim.

**Ownership:** PHX-HARDWARE owns both sketches and the Hardware fixture/handover; PHX-QA owns the stale parity assertion and independent verification; PHX-MASTER owns only this cross-role invariant and integration record. Do not add a positive legacy poll signature to firmware. PR #345 remains OPEN / DRAFT / UNMERGED; physical acceptance NOT TESTED; this contract grants no release authority.


## 6.78 Existing pending identity preservation under disabled coin ingress — Hardware #345 follow-up (2026-11-23 UTC00)

The latest Hardware #345 source/test SHA is `6eb3e9ba82fdbdcfe4fb6dc8ab1c38c9ffdc3043` on current PR/docs HEAD `01916c89ae6718d3991c778b676d06718155d6a2`. The follow-up adds six cases per board source that seed a two-pulse pending batch with target/nonce, then observe an edge while controller, coin feature or relay is OFF, with and without an ISR sequence. Each case requires the existing count/target/nonce to remain unchanged, `pendingReady` to be raised for reconciliation, no POST/save, sticky fault `pulses=3`, and relay/LED/insertion outputs OFF. Two mutation controls reject removal of the preservation assignment and clearing pending target/nonce.

Exact-source Quarantine [#45090899038](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899038) and Relay [#45090899225](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899225) pass at `6eb3e9ba...`; Full [#45090899167](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899167) fails the inherited QA-owned `Missing poll signature check`, while all 14 target/platform jobs pass and downstream stages are skipped. At the later PR HEAD `01916c89...`, Quarantine [#45091417124](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417124) and Relay [#45091417060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417060) pass; Full [#45091417147](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417147) was still IN_PROGRESS at the last read. Do not infer a terminal result.

These are host-lab/CI results only. They do not prove physical reboot durability or hardware acceptance. The fault helper attempts secondary NVS/EEPROM and LittleFS persistence; both-store failure leaves only current-boot fail-closed behavior, not established reboot durability. PHX-HARDWARE owns the source/fixtures; PHX-QA owns independent review and the stale parity assertion; PHX-MASTER owns this contract only. No release authority is granted.


## 6.79 Current Hardware #345 Full terminal result — 2026-11-23 UTC00

The final documentation-head Full run [#45091417147](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417147) at PR head `01916c89ae6718d3991c778b676d06718155d6a2` is terminal FAILURE. Validation job `137421604329` fails step 8 `Controller protocol parity` at the inherited QA-owned `Missing poll signature check`. All 14 target/platform jobs (13 firmware targets plus Android) pass; downstream simulations, update bundle, candidate, signing and publication are skipped. Current-head Quarantine [#45091417124](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417124) and Relay [#45091417060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417060) pass. This remains CI-only, not physical acceptance. QA owns the assertion correction; do not weaken firmware default-deny or add a positive legacy signature. No release authority is granted.


### UTC06 evidence update for §6.69 — 2026-11-23T06:50:43.021Z

HARDWARE #345 adds a source-extracted regression for an ISR edge arriving while `clearPending()` is in progress after a simulated authenticated success response. At source/test commit `edff098446247d3b2851af643d31673921cae03f`, the test-only clear hook injects `coinEdgeISR()`; the scenario requires the post-clear `reconcileUnobservedCoinEdges()` call to observe the new edge, latch `journalRecoveryRequired`, write the fake `/pollpulse.fault` record with `pulses=1`, and leave relay/ready outputs OFF. A mutation removing the second reconciliation call is rejected with expected exit 54 on both extracted board sources.

Exact final docs-head CI at PR #345 head `e385a26fecd36e2696b5be1dcfcce601609614ff`: Quarantine [#45125188884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188884) PASS; Relay [#45125188887](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188887) PASS; Full [#45125188863](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188863) FAIL at the inherited QA-owned `Missing poll signature check` in ESP8266. All 14 target/platform jobs pass; downstream validation-dependent stages are skipped.

This is host-lab / source-extracted CI evidence only. The positive disposition is a test-only stub override; production `coinPostDispositionVerified()` remains default-deny. It does not establish physical ISR timing, LittleFS crash durability, relay electrical acceptance, 150 power cuts, 30-device/24-hour soak, or hardware acceptance. PHX-HARDWARE owns firmware/lab implementation; PHX-QA owns independent fixture review and the inherited assertion; PHX-CORE owns the authenticated producer contract. PHX-MASTER owns this cross-role invariant only. No release authority is granted.


## 6.80 Orphan pending-attempt marker after partial clear remains a reboot recovery deny — Hardware #345 (2026-11-23 UTC07)

A successful-looking removal of the durable attempt marker is not sufficient evidence that the marker is gone. The current Hardware #345 source-extracted regression models removal of /pending.dat succeeding while /pending.attempt remains present after remove("/pending.attempt") reports success. The extracted production clearPending() must verify post-remove existence; if the marker remains, it must fail closed, preserve the pending identity and marker bytes, and latch journalRecoveryRequired. After simulated reboot, loadPending() must detect the orphan marker and remain in recovery-deny rather than infer that a zero-pulse RAM state means no financial event exists.

The test-first mutation removes only the post-remove exists() check and is rejected on both ESP8266 and ESP32 with expected exit 103. The source/test SHA is 78bfd193a90ab04630ac0c064c72b9b66a6d29f6; the logging-only evidence SHA is 7dee461649e6554389e4f80481086b43a4ddd85a; current Hardware #345 PR/docs head is deed0f49c04d8cd69dc4fda78d2a4d914aa4dd4d.

**Exact source/test CI:** Quarantine [#45133190059](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133190059) and Relay [#45133190127](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133190127) PASS. Full [#45133190056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133190056) fails at the inherited QA-owned Controller protocol parity / Missing poll signature check; 13 firmware targets pass, Android is cancelled, and downstream stages are skipped. The later logging-only Full [#45133582073](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133582073) fails at the same assertion; logging-only Quarantine [#45133582142](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133582142) and Relay [#45133582168](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133582168) pass. On the current docs head, Relay [#45134012012](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012012) passes; Quarantine [#45134012104](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012104) and BlazePwifi build [#45134012436](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012436) were IN_PROGRESS at the last read. No current-docs-head Full result is claimed.

**Evidence boundary:** FakeLittleFS/host simulation only. This does not establish actual LittleFS serialization, flash durability, physical reboot behavior, electrical relay acceptance, 150 real power cuts, or a 30-device/24-hour soak. PHX-HARDWARE owns sketches and fixtures; PHX-QA owns the inherited poll-signature assertion and independent review; PHX-MASTER owns this cross-role invariant only. Do not add a positive legacy response_sig marker to firmware. Admission remains default-deny. This contract grants no release authority.
## 6.81 — Disabled-ingress attempted-pending evidence remains opaque and non-crediting (Hardware #345 host-lab follow-up; scheduled UTC07)

At Hardware source/test commit `b1a5a36627075581973b451934eed000e43b4038`, the test runner isolates an `ATTEMPTED_EVIDENCE_MAIN` so the new mutation checks execute against their own baseline instead of being intercepted by an earlier legacy pending-identity assertion. On both extracted board sources, six cases cover controller OFF, coin feature OFF, and acceptor relay OFF, each with and without a simulated ISR edge. Each case seeds an existing attempted pending batch (two pulses, target, nonce, `pendingReady`, `pendingPostAttempted`) plus opaque sentinel bytes for `/pending.dat`, `/pending.new`, `/pending.bak`, and `/pending.attempt`; it requires identity/attempt state and all four byte sequences to remain unchanged, no save or POST, a sticky unresolved fault recording `pulses=3`, and relay/LED/insertion outputs OFF. Mutations deleting each evidence path or clearing `pendingPostAttempted` are rejected with expected exit 82 on both board sources.

**Exact source/test and docs heads:** source/test `b1a5a36627075581973b451934eed000e43b4038`; current PR #345 head `deed0f49c04d8cd69dc4fda78d2a4d914aa4dd4d`, parent #343 `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`. Source/test Quarantine [#45114100708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45114100708) and Relay [#45114100704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45114100704) pass. At the actual current PR head, Quarantine [#45134012104](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012104) and Relay [#45134012012](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012012) pass; BlazePwifi build [#45134012436](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012436) fails at validation step `Controller protocol parity / Missing poll signature check`. All 14 target/platform jobs pass; validation-dependent simulation, bundle, candidate, signing and publication stages are skipped.

**Scope and limit:** commit `b1a5a366` changes only the Hardware-owned host lab runner and scenario fixture; it does not change either production `.ino` in this follow-up. The opaque sentinels are FakeLittleFS/host-test data, not production `PendingRecord` serialization. This is not actual LittleFS durability, physical reboot, relay/coin acceptance, power-cut or soak evidence. Firmware admission remains default-deny; do not invent a positive `response_sig`. PHX-HARDWARE owns the source/fixture, PHX-QA the inherited poll-signature assertion and independent review, PHX-CORE the producer contract, and PHX-MASTER this cross-role record only.

**Pin hygiene:** GitHub PR metadata reports current #345 head `deed0f49...`, while the PR description still says `4c4653e5...`; Hardware must refresh its own PR description/handover pin. Master uses the live PR head and exact current-head Actions runs, not the stale body pin.

## 6.82 Each configured coin-ingress gate term must remain independently necessary — Hardware #345 mutation coverage (2026-11-23 UTC10)

Hardware #345's current source/test commit `ad0c6993e3cfdde4f1b11723c277488044b58abd` adds three independent fail-open mutation checks for the existing sample-path admission predicate `controllerEnabled && coinEnabled && relayEnabled`. The Hardware-owned host runner removes one term at a time and requires the corresponding disabled-ingress regression to fail on both extracted board sources. Expected mutation exits are 64 (controller), 62 (coin feature), and 60 (acceptor relay) for ESP8266 and ESP32. This distinguishes sample-path coin admission from the separate physical relay-output interlock.

**Exact-source CI:** Quarantine [#45150630588](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45150630588) and Relay [#45150630809](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45150630809) pass; Full [#45150630590](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45150630590) fails at the inherited QA-owned `Missing poll signature check`. Final PR/docs-head revalidation: Quarantine [#45151311625](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45151311625) PASS, Relay [#45151311962](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45151311962) PASS, Full [#45151311738](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45151311738) FAIL at the same assertion. All 14 target/platform jobs pass; validation-dependent simulations, candidate, signing and publication stages are skipped.

**Scope and limits:** source/test commit `ad0c6993` changes only `poll_loop_blocking_inhibit_lab.py`; final documentation commit `797dece76c18d464a7c0580658b5db9351cb8e15` adds the Hardware handover. No production `.ino` changed in this mutation-coverage increment. This is source-extracted host-lab/CI evidence, not physical ISR timing, coin-acceptor, relay-electrical, flash durability, reboot, 150-power-cut or 30-device-soak acceptance.

**Ownership:** PHX-HARDWARE owns the firmware and lab runner; PHX-QA owns the inherited positive poll-signature assertion and independent verification; PHX-CORE owns the authenticated producer contract; PHX-MASTER owns this cross-role invariant only. Do not synthesize `response_sig` or weaken default-deny. No route promotion, merge, release or production authority is granted.


## 6.83 Shared configured coin-ingress predicate and stacked child verification — 2026-11-23 UTC11

HARDWARE child PR #346 at bd3fd6e85717395f768aae26a310b647cdd72a7e centralizes the existing configured admission expression in both ESP sketches as coinIngressConfigurationAllows() returning controllerEnabled && coinEnabled && relayEnabled, reused by both sampleCoinPulseEdge() and applyOutputs(). Poll-time suspension remains a separate runtime condition. This is a source-level contract observation, not accepted integration or hardware evidence.

The child has no Quarantine/Relay run at its final head. Its base is 797dece76c18d464a7c0580658b5db9351cb8e15; parent #345 is now ca72497ed386c9ac4e50d3f811827bef51e296ad (four commits ahead). Parent changed the same poll-loop lab and added pending_clear_failure_lab.py, which child #346 does not include. Keep the stack blocked until PHX-HARDWARE reconciles it and runs focused CI at the final exact head.

Parent #345 current-head Quarantine #45165015610 and Relay #45165015665 pass; Full #45165015859 fails at QA's inherited Missing poll signature check. No positive response_sig is synthesized. Hardware owns firmware and labs; QA owns the inherited assertion and independent review; CORE owns producer authority; Master records the cross-role boundary only. Physical coin/relay, flash durability, power-cut and soak acceptance remain NOT TESTED.


## 6.84 Stacked owner PR freshness and exact-head acceptance contract — 2026-11-23 UTC12

A stacked child PR is not a current cumulative candidate merely because its base branch name still points at its parent. Before any cross-role review or migration:

1. Resolve the child's live `base.sha` and the parent's live `head.sha`. If they differ, classify the child as **STALE / OWNER-RECONCILIATION-REQUIRED**; do not infer it contains the parent's latest changes.
2. Compare the parent commits since the child's base and compare changed path/blob identities. Shared paths require explicit owner reconciliation; parent-only safety tests, fixtures and handovers must be preserved in the child before cumulative review.
3. CI is commit-scoped. Parent CI, child CI from an earlier child commit, and runs from the child's old base do not validate the child's current head. Require focused and full workflows on the final exact child SHA.
4. Only the owning role may rebase, retarget, resolve conflicts or update its source branch. PHX-MASTER records the gate and requests owner action; it does not rewrite subsystem branches.
5. A failing inherited QA assertion is not permission to weaken default-deny, invent a positive `response_sig`, bypass missing validation, or skip parent-only failure-injection coverage.

**Current evidence:** HARDWARE #346 is at `bd3fd6e85717395f768aae26a310b647cdd72a7e`, based on `797dece76c18d464a7c0580658b5db9351cb8e15`; current parent #345 is `ca72497ed386c9ac4e50d3f811827bef51e296ad`, four commits ahead and zero behind. Four changed paths overlap between the PRs; parent #345 adds `pending_clear_failure_lab.py`, which is absent from child #346, and both branches change the poll-loop lab. No Quarantine/Relay/Full workflow run exists at the current #346 head. Parent #345 exact-head Quarantine `45165015610` and Relay `45165015665` pass; Full `45165015859` fails at QA-owned `Missing poll signature check`, while all 14 target/platform jobs pass and 12 downstream jobs are skipped.

**Ownership and limit:** PHX-HARDWARE owns #345/#346 firmware and labs; PHX-QA owns the inherited assertion and independent verification; PHX-CORE owns authenticated producer authority; PHX-MASTER owns only this cross-role acceptance rule. Hardware acceptance remains NOT TESTED. No merge or release authority is granted.


## 6.85 Exact test-source anchor freshness after a PR-head test change — Hardware #347 (2026-11-23 UTC13)

A PR's `source_test_sha` must identify the latest commit that changes any test/lab source included in the claimed focused CI. A later docs-only commit may preserve the source/test anchor; a later test-file commit may not. Verify the PR API head, commit file list, and each workflow run's `head_sha` before reusing earlier test evidence.

Hardware #347 illustrates the rule. Its PR body still identifies `724d892e980f878903425837226c45b321638793` as the test-harness correction and says no firmware/test source changed afterward, while the actual current PR head is `275057aa28375223a32da099420f52696d9b667c`. That final commit changes `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/pending_clear_failure_lab.py`; therefore the test-source anchor in the PR body is stale even though the final commit does not change firmware runtime code. Current Quarantine `45186057750` and Relay `45186057806` runs both record head SHA `275057aa...` and pass. Full `45186057891` also records `275057aa...` and fails the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`; target jobs do not convert the Full workflow to PASS.

**Ownership:** PHX-HARDWARE updates its own PR body/handover and preserves test lineage; PHX-QA resolves the obsolete poll-signature assertion only against an approved producer contract; PHX-CORE owns that authenticated producer contract. PHX-MASTER owns only this cross-role evidence-freshness invariant. This section grants no source ownership, merge or release authority. Physical acceptance remains NOT TESTED; PRODUCTION NO-GO.

### UTC14 correction — current Hardware #347 source/test and docs heads (2026-11-23T14:40:25Z)

The UTC13 stale-body observation is historical and is superseded by the live Hardware handover refresh. Current #347 is OPEN / DRAFT at PR/docs HEAD `c256098dc84574d87321b81bdfd602e6f71b7c78`, based on parent #345 HEAD `ca72497ed386c9ac4e50d3f811827bef51e296ad`. Its PR body now correctly distinguishes latest test/lab source SHA `275057aa28375223a32da099420f52696d9b667c` from the later handover-only docs HEAD `c256098dc84574d87321b81bdfd602e6f71b7c78`. The c256 commit changes only `experiment/openwrt/BlazePwifi/docs/handover/2026-11-23-hw-configured-ingress-stack-reconciliation-utc13.md`; it does not change firmware or test source. Compare from source/test reconciliation `59de2e122f57559804ecb2929b56903b6486c694` to test-only correction `275057aa28375223a32da099420f52696d9b667c` is seven commits ahead / zero behind and includes the board sketches plus lab-source corrections. The latest test-source anchor is therefore 2750, while c256 is a docs-only successor.

**Current exact #347 docs-head CI:** Quarantine [#45189705741](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45189705741) PASS; Relay [#45189705900](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45189705900) PASS; Full [#45189706099](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45189706099) FAIL at `tests/controllers.sh` / `Missing poll signature check`. ESP32, ESP8266 and firmware target build jobs pass; validation-dependent simulation, update-bundle, signing and publication stages remain skipped. The inherited assertion is QA-owned and must be reconciled only against the approved authenticated producer contract; no positive legacy signature may be fabricated and default-deny must not be weakened.

This correction supersedes the UTC13 statement that the live #347 PR body still had a stale test-source anchor. Preserve that earlier statement as a historical snapshot; do not repeat it as current status.

## 6.86 Release compatibility evidence is exact-source-pin scoped — PHX-RELEASE #291 versus HARDWARE #347 (2026-11-23 UTC14)

A successful release compatibility matrix qualifies only the exact Hardware source commit and sketch blob checked out by that matrix. A green parent-source compile cannot be inherited by a later child whose source/test lineage changes the sketch, helper, compile flags or board contract.

At current PHX-RELEASE #291 docs HEAD `886cc1530119b280574c60ceb68fdf4705b7c362` (source/test HEAD `1efd329c5b43d12c22a077577e532381aecaff34`), compatibility run [#45193305396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45193305396) passed the release provenance suite and ESP32 core 3.3.13 / 4.0.0 compile legs. The job logs identify the checked-out Hardware source as `6eb3e9ba82fdbdcfe4fb6dc8ab1c38c9ffdc3043`. Current reconciled Hardware #347 has source/test head `275057aa28375223a32da099420f52696d9b667c` and docs head `c256098dc84574d87321b81bdfd602e6f71b7c78`. GitHub compare from the release pin to #347 source/test is 64 commits ahead / zero behind, with merge base exactly `6eb3e9...`; the intervening tree changes include both ESP32 and ESP8266 sketches and multiple Hardware labs. Therefore #45193305396 is valid evidence for the pinned 6eb3e9 source only, not current #347 dual-core qualification.

**Required owner sequence:** HARDWARE nominates the immutable current candidate source SHA and ESP32 sketch blob; RELEASE updates its own compatibility workflow and negative/source-pin contract, then runs both cores against that exact source/blob. PHX-MASTER records the cross-role dependency only and does not edit Hardware or Release source paths. Current #347's own build compiles both boards, but that is not a substitute for the release-owned two-core source-pinned matrix.

At the same #291 docs head, BlazePwifi build [#45193305375](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45193305375) and Windows [#45193305362](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45193305362) fail the mandatory CORE-owned handover freshness gate: `PROJECT_HANDOVER.md` is older than source/workflow changes (last recorded checkpoint `adcae8141e673dc2147fcad50521ef3a23084d71`). CORE must refresh its own live handover/current-state/change-ledger; RELEASE then reruns its own exact-head jobs. No bypass or cross-owner handover edit is permitted.

**Acceptance limit:** dual-core hosted compilation is not a signed release, physical board acceptance, financial migration proof or production authorization. PR #291 remains OPEN / DRAFT / UNMERGED; PRODUCTION NO-GO.


## 6.87 Hardware firmware, lab/test, and documentation pins are separate evidence axes — #347 UTC15 (2026-11-23)

A stacked Hardware PR can carry distinct firmware-source, test/lab-source, and PR/docs heads. Do not compress these into one ambiguous `source/test SHA` when a later test-only commit follows a firmware-source commit.

For current HARDWARE #347:
- **Parent/base:** #345 exact head `ca72497ed386c9ac4e50d3f811827bef51e296ad`.
- **Firmware-source anchor:** `275057aa28375223a32da099420f52696d9b667c`.
- **ESP32 sketch Git blob:** `717336b84d434d51eb24beac1ed8efce8e719f69`.
- **Latest test/lab-source commit and current PR/docs head:** `fa7115f7bc15c6c885de8cf0af1469cf5d71bf84`. The latest commit changes the ESP8266 `coin_pulse_capture_lab.py` helper map plus the Hardware handover; it does not change production `.ino` runtime in that commit.
- The lab now derives mutation indexes from one `FUNCTION_SPECS` table, checks duplicate helper names/signatures, validates extracted declarations, and rejects unknown mutation targets. This is a host-lab integrity correction, not firmware behavior change.

**Exact #347 head CI at `fa7115f7...`:** Quarantine [#45202818871](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45202818871) PASS; Relay [#45202818915](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45202818915) PASS; Full [#45202801601](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45202801601) and duplicate trigger [#45202819813](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45202819813) FAIL at QA-owned `tests/controllers.sh` / `Missing poll signature check`. The Full run completed 14/14 target/platform jobs; validation failed and downstream stages were skipped.

**Release compatibility is scoped to firmware source, not the latest lab source.** RELEASE #291's exact-source matrix [#45209288305](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288305) checked out firmware source `275057aa...`, verified ESP32 sketch blob `717336b8...`, and passed provenance plus ESP32 core 3.3.13 and 4.0.0 jobs (3/3). It does not execute or qualify the later Hardware lab-source change at `fa7115f7...`, and it does not establish physical acceptance.

**Required pin schema for future handovers:** record `firmware_source_sha`, `test_lab_source_sha`, `pr_docs_head`, `parent_base_sha`, and each CI run's `head_sha` independently. A test/lab commit invalidates prior lab-source evidence even when firmware sketches are unchanged; a docs-only commit does not invalidate source tests, but any new exact-head workflow still needs its own terminal result. The release matrix may pin the firmware source and sketch blob separately, provided it explicitly states that it does not qualify the latest test/lab commit.

**Ownership:** HARDWARE owns firmware and its labs/handover; RELEASE owns the compatibility workflow; QA owns the inherited poll-signature assertion; CORE owns authenticated producer and shared handover. PHX-MASTER owns this evidence-identity contract only. No source edit, rebase, merge or release authority is granted. Physical coin/relay, LittleFS power-loss, 150 real cuts, 30-device/24-hour soak and native acceptance remain NOT TESTED.

## 6.88 RELEASE #291 now qualifies the current #347 firmware pin; integrated Full/Windows remain blocked — UTC15 (2026-11-23)

This supersedes the historical stale Hardware-pin finding in §6.86. The exact-source matrix now follows the current #347 **firmware-source** SHA and sketch blob; the integrated release workflows remain fail-closed at a separate CORE-owned handover gate.

**Current RELEASE branch state:** PR #291 OPEN / DRAFT / UNMERGED; branch `phoenix/release-publisher-isolation-20261115`; base #242 `734b89d9e7792247e8376335c3f3685500ab3f89`; code/workflow head `98ba3af1fe76128b331f93a4cf3543087cc0919b`; final docs/handover head `c5a566fd04a59a3c4a4bbbaa9524f8a9b97e6b7d`.

- Exact-source compatibility [#45209288305](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288305): **3/3 SUCCESS**. Provenance job `137813399239`, ESP32 core 3.3.13 job `137813398561`, and ESP32 core 4.0.0 job `137813399194` all PASS. Both core jobs verify exact Hardware source `275057aa...` and sketch blob `717336b84d434d51eb24beac1ed8efce8e719f69`, pinned Arduino CLI/core inputs, image inspection, and two-build reproducibility. CI-generated application images are not production-approved binaries.
- Integrated Full [#45209288533](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288533): **OVERALL FAILURE**. CI-0701 and all 14 target/platform jobs PASS; validation job `137813526598` fails at mandatory freshness check for CORE-owned `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` (last recorded checkpoint `adcae8141e673dc2147fcad50521ef3a23084d71`). Thirteen downstream update/simulation/signing/publishing jobs are SKIPPED.
- Windows [#45209288746](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288746): **FAILURE** at the same CORE-owned handover freshness gate; `build-windows` and `publish-release` are SKIPPED.

**Owner sequence:** CORE refreshes its own shared handover/state records; RELEASE reruns Full and Windows at the resulting exact head; QA independently reviews the compatibility pin contract. PHX-MASTER records the dependency only and must not edit CORE or RELEASE source paths. No bypass or synthetic freshness claim is permitted.

The compatibility PASS is firmware-source-scoped hosted CI only. It does not imply a successful integrated Full build, signed release, production binary, financial migration, hardware acceptance, real power-cut evidence or customer readiness. PR #291 remains DRAFT / UNMERGED. **PRODUCTION NO-GO.**



## 6.89 Role/hour checkpoint idempotency and delayed activations

- The deduplication key is **role ID + scheduled UTC hour**, not the time at which a delayed automation actually starts or finishes.
- Put the scheduled slot in the stable BLAZE-COMMS `message_id`; put the actual write time in `updated_utc`. These fields must not be conflated.
- Before posting, inspect the live control-plane comments and current PR checkpoint. If the same role already has a checkpoint for that scheduled UTC hour, update that comment in place; do not create a second lock or a second checkpoint.
- A delayed/retried activation resumes the original scheduled slot. It must not claim a later UTC hour merely because the wall clock crossed the boundary while the task was queued.
- A PR conversation comment is supporting evidence, not a substitute for the one canonical control-plane issue checkpoint. Keep exactly one BLAZE-COMMS/1 issue checkpoint per role and scheduled UTC hour.
- If no source/document delta exists, perform a read-only reconciliation and update the existing same-hour checkpoint; do not create a no-op commit. If a delta exists, preserve history and make one fast-forward commit on the existing role branch.
- A checkpoint is VERIFIED only after remote readback of its comment ID/body, exact branch/commit, and linked evidence. Never claim a future activation or background work that has not actually run.

## 6.90 Cross-repository migration evidence tuple and fail-closed staging

For every proposed mapped file, record and compare the complete evidence tuple:

`(source repository, source commit, source path, source blob, source mode; destination repository, destination commit, destination path, destination blob, destination mode)`.

1. Resolve every recorded source and destination blob against the exact source and destination trees. Compare file modes as well as blob IDs; missing paths or unresolved blobs are blockers.
2. Distinguish the historical source commit recorded by an intake manifest from current source main. A historical blob that has drifted from current main is not silently “current” and must not be overwritten by a broad recursive copy.
3. Recompute aggregate identical/derived counts from the row-level tuples. A recorded summary that disagrees with computed rows is a migration blocker until corrected in the owning destination branch.
4. Verify original test identities, derived-test inventories, exact CI at the candidate SHA, import completeness, license files, NOTICE files, and owner-approved path mapping independently. Missing derived-test rows or stale test blob IDs block integration even if runtime files resolve.
5. A green workflow on another branch, parent, historical source pin, or docs-only successor does not qualify the candidate. Record the exact source/test SHA separately from a later handover/docs HEAD.
6. `DRAFT_REVIEW_ONLY` and `manual-file-mapping-required` are hard holds, not copy permission. Review the staged destination tree before proposing a move; do not stage/copy/move/overwrite/rebase/cherry-pick until per-file provenance, licenses, tests, exact-head CI and owner authorization all agree.
7. PHX-MASTER's route target remains `null`; Master coordinates provenance and integration but does not own subsystem source or destination files.

These controls preserve a human-auditable chain from original source blob through destination import and exact test evidence. Missing or contradictory evidence remains UNKNOWN/BLOCKED, never PASS by inference.


## 6.91 Firmware-source vs test/lab-source qualification

A release compile pin, a Hardware test/lab source head, and a later PR/handover head are different evidence identities. Record them separately and qualify only the object actually tested.

1. Record at least: PR/docs HEAD, production firmware source commit and per-board sketch blob(s), test/lab source HEAD, and each workflow's exact **head_sha**.
2. A compatibility compile result is **source-file scoped**. If the candidate's exact sketch blob equals the blob compiled by the compatibility run, that result remains source-exact for that sketch even when later commits change only host-test/lab code or handover documents.
3. That narrow result does not qualify changed test/lab code, the other board's sketch, the full integration workflow, or any later source blob. Every test/lab change requires its own exact-head Quarantine/Relay/Full evidence.
4. A failing test-harness refactor remains a failure until the owning role corrects it and the corrected test/lab SHA has terminal exact-head runs. Preserve the failed intermediate SHA and correction lineage; never relabel the failed run as PASS.
5. A docs-only successor may carry forward a test result only when its test/lab source SHA is unchanged and the workflow explicitly proves that identity. Record the docs HEAD and source/test HEAD separately.
6. Do not require a production-source repin merely because a test-only commit advanced; first compare the exact board sketch blob. Conversely, a matching ESP32 sketch does not qualify ESP8266 or full-stack behavior.
7. PHX-MASTER owns this evidence contract and integration matrix only. HARDWARE/RELEASE/CORE/QA owners retain their source branches and must correct their own files.

This contract prevents both false stale-source claims and the opposite error of promoting a narrow compile pass into full-stack acceptance.


## 6.92 Release overlay traversal errors must abort staging — COE #35 (2026-11-23 UTC20)

COE RELEASE #35 source/test SHA `daf08616ec001dae7013a8f029894153f597e1ae` fixes a real staging-integrity defect: the final permission-normalization pass used `os.walk(staging_dir)` without an `onerror` callback, so a subtree scan failure could be silently skipped while the staging operation appeared successful. The correction re-raises the original traversal error.

1. Every recursive filesystem walk that contributes to a release manifest, permission normalization, or packaging-complete decision must surface traversal errors. A silently skipped subtree is not a complete package.
2. If traversal or normalization fails, abort the packaging operation before publishing a manifest, execute-mode claim, or completion marker. Preserve the original exception for diagnosis.
3. A partially created staging directory after a failed walk is **tainted**. The current correction does not guarantee automatic rollback; do not reuse that directory for a retry. Cleanup and verify it, or create a new isolated staging directory with a fresh identity before another attempt.
4. Regression evidence must inject a nested subtree scan failure and verify both that the original error propagates and that no package-complete/publishable result is emitted. A host preflight PASS is not a Bubblewrap/ImageBuilder execution.
5. Keep ULA authority, sandbox availability, and package traversal correctness as separate gates. COE #35's 204 packaging/tool tests passing does not override 10/10 profile admission denials for missing approved ULA /48 or the unavailable Bubblewrap runner.
6. PHX-MASTER owns this cross-role contract only. PHX-RELEASE owns its packager implementation; PHX-QA owns independent regression review; PHX-INFRA/COE owns the compliant runner. No firmware, financial schema, migration, or release authority changes.

This contract is source/test/host-CI scoped. It does not establish an appliance binary, sandbox execution, signing, or production readiness.


## 6.93 C++ fixture timeout overrides must be finite and positive — HARDWARE #347 (2026-11-23 UTC21)

HARDWARE #347 added a bounded-input contract to the shared ESP8266 C++ fixture runner. Source/test commit [00fcd6a9](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/00fcd6a9ed80a4ccccd429d3912e183ee2d4b3bd) changes only `cpp_fixture_runner.py` and `cpp_fixture_runner_contract_lab.py`; the later PR/docs head is [b33e654](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b33e654af8aecc1a8477e63121ba03bc7c72cf2c).

1. Compile and execution timeout defaults remain finite (30 seconds and 10 seconds respectively). An explicit override is permitted only when it is a finite, strictly positive real number of seconds.
2. Reject `None`, zero, negative values, positive/negative infinity, NaN, booleans, and strings. Python booleans must be rejected explicitly even though `bool` subclasses `int`.
3. Validate both timeout parameters before temporary-directory creation and before any compiler or fixture process launch. Invalid overrides raise a parameter-specific `ValueError`; the regression asserts `subprocess.run` was not called.
4. The contract lab covers 16 invalid combinations (eight values across compile and execution parameters). Exact PR merge-ref Quarantine run [#45272162126](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45272162126), job `138034494698`, passed six tests and emitted `CPP_FIXTURE_RUNNER_CONTRACT_PASS 6/6`; both board coin-pulse labs emitted 17/17. Relay [#45272162193](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45272162193) passed both jobs.
5. Full [#45272162174](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45272162174) remains FAILED at the inherited `Missing poll signature check` in the ESP8266 controller parity step. Fourteen target/platform jobs passed; twelve downstream simulation/update/signing/publication jobs were skipped. The PR workflow checked out merge ref `539f76ba` (b33e654 over parent #345 ca72497), not a physical board.
6. This is a test-harness reliability contract, not financial or hardware acceptance. HARDWARE owns the runner; CORE owns the authenticated poll producer contract; QA owns the independent assertion review; MASTER owns this cross-role evidence rule. Do not synthesize a signature or weaken default-deny.

The result is **CI VERIFIED for the bounded runner contract only**. Physical compiler/relay/coin behavior, LittleFS durability, power cuts, native acceptance and soak remain NOT TESTED.


## 6.94 Hardware firmware and migration-test identity are separate gates — 2026-11-23 UTC22

The current source owner candidate is Experiments HARDWARE PR #347 at `e69a3d715aca6724dd0390e925e48a7510009ab1`, based on parent #345 `ca72497ed386c9ac4e50d3f811827bef51e296ad`. The frozen destination candidate is COE PR #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`. These are different source identities, not a byte-identical migration.

| Artifact | Experiments #347 source blob | COE #26 destination blob | Result |
|---|---|---|---|
| ESP8266 sketch | `fa8ed828026396db89aab2889bf6a61d6cf6bbac` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different |
| ESP32 sketch | `717336b84d434d51eb24beac1ed8efce8e719f69` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different |
| Source hardening test | `v05_firmware_hardening_test.sh`, blob `41211b2c110ab409f6d9d1812ef12fda73b13211` | `Hardware/tests/test_firmware_hardening.sh`, blob `f921c56cecc19cab1989507b9b4ade1f45dac54e` | Different |

All four firmware entries are mode `100644`. The COE candidate has one generic executable shell test (mode `100755`), but it is not the same blob as the source test. Both test scripts contain positive `response_sig` and literal `|poll|` expectations. The current source CI still fails the QA-owned `Missing poll signature check`; do not fabricate a poll signature or weaken default-deny firmware to make the assertion green.

The exact source tree at #347 contains 38 Python files beneath the ESP32/ESP8266 board directories; the COE #26 destination contains zero board-local Python files beneath `Hardware/esp32/` and `Hardware/esp8266/`. A directory-prefix route is not proof that its test helpers were imported. Each omitted, derived, or reimplemented test must be mapped explicitly and independently validated.

The source ESP32 sketch selects the PSA API for Mbed TLS 4 and the checked legacy API for Mbed TLS 3. The COE #26 destination sketch still includes `mbedtls/sha256.h`; separate COE INTERCON #49 exact-head Shared CI [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) fails at that missing header under ESP32 core 4.0.0. This #49 result is a separate candidate's CI, not #26 integration CI.

Before any destination move, the integration owner must reconcile every source/destination blob, file mode, test identity/import, dependency, license/NOTICE, and exact-head CI result. The ownership manifest remains `DRAFT_REVIEW_ONLY`; PHX-MASTER destination remains null. This contract authorizes no copy, migration, firmware edit, or release.

HARDWARE owns firmware and board-local labs; QA owns the positive/negative assertion; CORE owns the authenticated poll producer contract; COE integration owns destination mapping. PHX-MASTER owns only this cross-role qualification rule.

### 6.95 Non-empty authenticated policy and canonical-message spans — PHX-HARDWARE #348 (2026-11-23 UTC23)

A cryptographic match over an empty byte span is not a valid controller-policy or controller-response authorization:

1. A raw policy span MUST have a non-null pointer and an explicit length greater than zero before SHA-256 comparison. The digest of the empty string MUST NOT admit an empty policy.
2. A canonical controller-response span MUST have a non-null pointer and an explicit length greater than zero before HMAC verification. A mathematically valid HMAC over an empty string MUST NOT admit an empty response.
3. Verification MUST preserve the caller-supplied byte span and explicit length. Do not infer length by normalizing or silently substituting a different serialization.
4. Keep the rejection before cryptographic comparison and preserve default-deny admission. This host-lab contract does not authorize coin/relay intake, change the wire format, transfer parser ownership to HARDWARE, or establish a protected production signer or freshness witness.

Evidence / scope: HARDWARE PR #348 is an OPEN/DRAFT child of #254, final head c18826892160b1777f107e2ca0ca49aaed66ba6a; source correction 21d075e366e1a6fab54985a14996e2d30a7cc862; exact-head focused header run #45207909335, job 137808529744, passed 5/5 synthetic header checks, including correct SHA-256(empty) and HMAC(key, empty) rejection. The initial test-only head was not observed in Actions, so no RED result is claimed. The separate build run #45207909463 failed at ESP32 compile and mandatory handover freshness; no Full acceptance or hardware acceptance is implied.

Independent review: PHX-QA must verify both zero-length negative cases and the non-empty controls against the exact source/test SHA. CORE remains authority for the production response envelope and authenticated register/poll contract.


## 6.96 Preserve the primary failure when owned-descriptor cleanup is interrupted — COE RELEASE #35 (2026-11-24 UTC00)

A cleanup interruption must not replace an already-active primary scan/validation failure:

1. Attempt every owned descriptor close, even when an earlier close raises a process-level interruption.
2. If a primary exception is already active, retain cleanup interruption details as secondary diagnostics and allow the original primary exception to continue propagating. Use exception notes where available; retain the documented stderr fallback for runtimes without `BaseException.add_note`.
3. If no primary exception is active, preserve the existing fail-closed behavior: propagate the first cleanup interruption after attempting all closes. Do not convert an unrelated interruption into success.
4. Keep ordinary close errors diagnostic and preserve the existing primary-error policy. Do not silently discard the cleanup record or alter resource ownership.

Source evidence: COE #35 test-only RED `1c95c62b00deb571628704f8486a06abad79c5df` added `test_calculate_overlay_size_preserves_primary_scan_error_when_descriptor_close_is_interrupted` for both `KeyboardInterrupt` and `SystemExit`. Exact push [#45295374991](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45295374991), job `138114297356`, reproduced the primary `PermissionError: primary overlay scan failure` being replaced by `KeyboardInterrupt: injected parent descriptor close interruption` (exit 130). Source fix `1abe0164ce0540bf7b787b78e43777429512ff5d` changes only `tools/package_appliance_firmware.py`; exact-source push [#45295447823](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45295447823), job `138114548297`, passed the new regression and the full packaging/tool suite (211 passed, 2 intentional skips). The overall workflow still failed closed at all 10 appliance profiles because approved site-scoped RFC 4193 ULA /48 authority is missing; ESP builds were skipped. Final docs-only PR head `0019593cae93887bb5f195179b703688f1c57c7d` repeated 211/2 with the same ULA gate; sandbox host preflight was 40/40 but Bubblewrap was unavailable (exit 125), and case-collision passed.

This is hosted Python/packager evidence only. It does not establish ImageBuilder execution, an appliance binary, hardware acceptance, a shared wire/API change, or COE #26 migration approval. PHX-RELEASE owns the source; PHX-QA owns independent review.

## 6.97 Nested JSON grammar is structural validation, not poll authorization — HARDWARE #349 (2026-11-24 UTC02)

HARDWARE PR #349 is a child of #347, not a replacement for its parent. Its bounded parser correction and source-extracted tests establish JSON structure only; they do not authenticate the producer, bind the poll tuple, or authorize coin/relay admission.

Exact identities and evidence:
- Parent #347 head and #349 base: `960184670379f01e20f0e7e8bc23b3e5eedacd3f`.
- Parser implementation commit: `e3aa052a973edd78a2db00e7278f44adf6226cec`.
- #349 source/test SHA: `7c14c2600fbf4c10e591286a2eca786d5cf5e548`; final PR/docs HEAD: `c7d7d3c5e6dc8696a2bd108ae34570e667ea0cf9` (handover-only successor).
- #349 ESP8266 sketch blob: `2f87a9de84ac53dbb0d2718b5c79a4662b63de8f`; ESP32 sketch blob: `a9a1c2fecb001d71f8f22b43952edbd160aacaf8`.
- #347 parent sketch blobs remain ESP8266 `fa8ed828026396db89aab2889bf6a61d6cf6bbac` and ESP32 `717336b84d434d51eb24beac1ed8efce8e719f69`.
- Source/test-head Quarantine [#45310725411](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45310725411) and Relay [#45310725456](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45310725456) PASS; Full [#45310725430](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45310725430) FAIL.
- Final docs-head Quarantine [#45311315194](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45311315194) and Relay [#45311315250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45311315250) PASS; Full [#45311315267](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45311315267) FAIL.
- The source-extracted lab reports 6/6 valid cases accepted, 12/12 malformed composite/string cases rejected, and six parser fail-open mutations rejected per board. This is SIMULATED / CI VERIFIED only.

1. The parser must enforce bounded nested JSON structure: matching array/object delimiters, comma/colon placement, string termination/escape handling, primitive token boundaries, and a maximum nesting depth of 16. Malformed trailing delimiters and fail-open mutations must be rejected.
2. Structural parsing is not authentication. A successful parse MUST NOT set a trust, signature, freshness, or coin-admission flag.
3. Current Experiments main CGI blob `2e3a1430d08cc6606429a042df3b5848f53c7267` emits `response_sig` for member snapshot/auth/mutation endpoints but not register/ping/poll. PHX-CORE owns the authenticated producer envelope and golden vectors; PHX-QA owns the legacy positive poll-signature assertion. Do not invent a signature or weaken default-deny.
4. #349 Full validation still fails at QA-owned `Missing poll signature check`; focused Quarantine/Relay passes do not override that integration failure. The 13 firmware target jobs and Android job pass, while validation-dependent simulation/update/signing/candidate/publication jobs are skipped.
5. The #347 parent still has the older parser blobs and its own failing array-primitive labs. #349 child results MUST NOT be attributed to #347 or inherited by a different source SHA. Record PR/docs HEAD, source/test SHA, parent base, and each workflow `head_sha` separately.
6. The #349 PR body still has a stale top-level pin to docs HEAD `e4ab80dc012f2e2c4551213f85c844edc75c4149` and source/test `8dd8b12c3c32da76c7a087c44f3cbb32d5ac6a64`, while live PR/docs head is `8639deda8d341d61efddff77be4d06ea931d040d` and source/test head is `1247a5c7b332677ae8dca83dc94cf586a015e7a0`. Earlier UTC01/UTC02 pins remain historical. PHX-HARDWARE must refresh its own top-level PR body/handover; Master does not edit Hardware-owned text.
7. The test lab and parser are source-extracted/host-simulated. No native board, electrical, coin/relay, power-cut, or soak acceptance is established.

COE #26 remains FROZEN: its ESP8266/ESP32 blobs differ from #349, and the new board-local parser lab has no destination counterpart. See the current integration matrix; no copy or migration is authorized by this contract.


### UTC05 #349 exact-head update (2026-11-24T05:37:40Z)

Current docs/PR head `8639deda8d341d61efddff77be4d06ea931d040d`; source/test head `1247a5c7b332677ae8dca83dc94cf586a015e7a0`; parent #347 base `960184670379f01e20f0e7e8bc23b3e5eedacd3f`. The UTC05 handover is `571a6d66de41620e26eab0457d620fddc2bb3a96`. Source/test adds pending-clear fixture `5b10b47f4994bb053ebad5c7c1dd6c56900ea0a6` and refactors runner to `a18ada4da4809af93f9d18d4834a13f5c3cadd29`; parser lab `ac4b164e...`, first-fault lab `aacba2e...`, and production sketch blobs remain unchanged. Source/test Q/R PASS and Full FAIL; current docs-head Q/R are in progress and Full validation already fails at the inherited poll-signature assertion. No current docs-head pass, physical acceptance or production authority is established. CORE owns signed register/poll producer contract and golden vectors; QA owns assertion reconciliation. Hardware must not invent a signature or weaken default-deny.

### UTC05 final owner/CI refresh — supersedes earlier body/CI snapshots

HARDWARE owner checkpoint [#7123382454](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7123382454) and live PR #349 body now pin source/test `1247a5c7b332677ae8dca83dc94cf586a015e7a0` and final handover/docs `8639deda8d341d61efddff77be4d06ea931d040d`; the previous e4ab80/8dd8b12 top-level pin is superseded. Current docs-head Quarantine #45336321346 and Relay #45336321352 PASS; Full #45336321274 FAILs at validation job 138249136286 / `Missing poll signature check`, with 13/13 firmware targets and Android PASS and downstream jobs skipped. The failure is the existing CORE/QA authenticated poll-signature contract mismatch; do not weaken default-deny or invent a Hardware-side signature. #266 remains OPEN / 0-of-7.

## 6.98 Cross-owner PR path overlap is a pre-integration review gate — PHX-RELEASE #291 (2026-11-24 UTC03)

Exact tree comparison found that RELEASE PR #291 at `5222443b3747f47d440d804c4ff853eaa04686a5` changes three handover paths also changed by CORE #252, PISONET #255 and QA #290. These are the same paths but **not the same blobs** across the four candidate heads:

| Shared path | CORE #252 | PISONET #255 | QA #290 | RELEASE #291 |
|---|---|---|---|---|
| `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` | `72e8e487d333a9488f77c2c3e68652d1a650ff85` | `d3e66608280644af8c42635168a7e27c8fba8f31` | `83db03cf387f280ba2d595ff6e9d58ffa23417c5` | `e07027ca323f6b7f8004f23caad716141bad5036` |
| `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md` | `df50981c1596838b1abf544e94f68e89ad556b7d` | `02963d32018ea09ad2a6a5a95b487de1f65ff4f2` | `3180e1a93c852e5c983f947e8ca45a897df0479f` | `7501142206f563c1f31085622cb0fd096345565b` |
| `experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md` | `72c38aeb93377f3aedb758c91d670ff1150e87bd` | `47e07b7c0e06766d0d4ebb18bc13bfb274adfe22` | `73b9d1d6acbd8b58c13f2d1b9d17512c392f444a` | `94b9447fd8e22c427ebefae9c906959e72285573` |

RELEASE #291 also changes two files inside the PHX-PISONET-owned `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/` subtree: `negative-selftest.ps1` (blob `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`) and `PublisherMockCli.ps1` (blob `7d56522b4fd678a26a2d7ea39e9b51dc8e52612d`). Those paths are not in PISONET #255's 11-file diff, but the ownership manifest assigns the whole SoftTimer subtree to PHX-PISONET. Current RELEASE Windows run [#45319386947](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45319386947) fails in the PISONET-owned negative self-test at the missing-tag acceptance assertion.

**Required before integration:** RELEASE must enumerate and explain every overlapping path; CORE, PISONET and QA must review the intended final handover blobs; PISONET must review the two ReleaseSigning test changes; and all required checks must run on the exact final integration head. A pass on one branch does not qualify another branch's blob. Do not silently overwrite, cherry-pick, rebase or merge these paths. This is a review gate, not a merge authorization.

## 6.99 Hermetic release lookup negative controls must stub both GitHub endpoints — PHX-RELEASE #291 (2026-11-24 UTC04)

The future SoftTimer publisher has two independent read-only existence checks before artifact verification and publication:

1. The release-object lookup at /releases/tags/$releaseTag.
2. The Git-ref lookup at /git/ref/tags/$releaseTag.

A confirmed 404 for the release object does not prove that the Git tag itself is absent. Both checks must independently require exactly one unambiguous HTTP 404 with the expected nonzero CLI exit. Any 200, 401, 403, 5xx, transport error, duplicate status, multiple status lines, or other ambiguous result must fail closed.

**Test-harness contract:** a negative test that claims synthetic/no-network behavior must stub every external command invocation in the extracted decision block. The fixture must control stdout and exit code independently for both GitHub lookups, assert call order, arguments and call count, and keep gh release create mocked. There must be no real gh api invocation, network access, credential use or publication from the test. The test must distinguish a missing release object from an existing tag and from a missing tag; do not weaken the production fail-closed checks to make a fixture pass.

**Exact current evidence:**

- RELEASE PR #291 remains OPEN / DRAFT / UNMERGED at final branch head f1fda47b1ebd5c4eafe8d8c450ab1eafcb037528.
- The current release workflow blob is 61031c13aad934fb52aef3038598f8b4d6a89334. Its first release lookup is at workflow line 479; the second Git-ref lookup is at line 494, with its independent exit capture at line 495.
- PISONET-owned negative-selftest.ps1 blob is 8b69174bf519154e43f7e12e4a9fa2c0e75d350f. Its extracted decision block starts at line 302 and ends before final artifact verification; line 308 replaces only the first $lookupExit = $LASTEXITCODE. The extracted block still contains the second gh api invocation and $tagLookupExit capture, which are not replaced by the fixture in this script. The comment at line 300 says synthetic API output must not exercise the real GitHub CLI.
- The separate PublisherMockCli.ps1 blob is 7d56522b4fd678a26a2d7ea39e9b51dc8e52612d and defines a fake gh command, but its workflow step was skipped after the preceding negative-selftest failure.
- Exact final-head Windows run #45326528399, job 138217448588, passed handover freshness and package parity, then failed step "RELEASE-SIGN test fail-closed negative controls" at negative-selftest.ps1 line 326: "RELEASE-PUBLISHER executable lookup regression: missing tag accepted=False". The later PublisherMockCli step and all publishing steps were skipped. ESP32 compatibility #45326528385 passed; BlazePwifi build #45326528447 passed.
- The workflow log does not expose the second lookup's HTTP response. Therefore the static unmocked-command gap is confirmed, but the precise runtime response that caused accepted=False is not established. Do not attribute the failure to a specific GitHub status until the fixture isolates both calls.

**Ownership and review:** PHX-PISONET owns the SoftTimer test files under experiment/windows/BlazePisonet-SoftTimer/; PHX-RELEASE owns the release workflow and publisher behavior. PISONET must make both lookup fixtures hermetic; RELEASE must confirm the expected two-endpoint semantics; PHX-QA independently reviews the corrected test and exact final head. This contract changes no subsystem source, test file or workflow and transfers no ownership. No signing, publication, merge or release is authorized.

### UTC05 #291 exact-head update (2026-11-24T05:37:40Z)

Current PR/docs head `3f92801aadf47be594fdef5a278b6aa125eaea1a` changes only `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md`; release workflow blob `61031c13aad934fb52aef3038598f8b4d6a89334`, PISONET negative test blob `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`, and PublisherMockCli blob `7d56522b4fd678a26a2d7ea39e9b51dc8e52612d` are unchanged. The extracted negative test replaces only `$lookupExit = $LASTEXITCODE`; the workflow also performs a Git-ref `gh api -i` lookup and captures `$tagLookupExit`, which is not fixture-substituted. Prior head `157ec440...`: Windows [#45335209826](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335209826) FAIL at `negative-selftest.ps1:326`, `missing tag accepted=False`; ESP32 [#45335209966](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335209966) PASS 3/3; build [#45335209899](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335209899) SUCCESS with signing/publishing skipped. Fresh current-head ESP32 [#45336455127](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336455127) PENDING, Windows [#45336455064](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336455064) IN_PROGRESS, build [#45336455073](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336455073) QUEUED. Exact runtime HTTP response is not exposed. PR body still pins older f1fda47; RELEASE should refresh its own handover/body. PISONET owns test, RELEASE workflow, QA independent review. No publication or signing occurred.

### UTC05 post-run CI refresh — supersedes earlier in-progress snapshot
HARDWARE #349 docs/PR head `8639deda8d341d61efddff77be4d06ea931d040d`: Quarantine [#45336321346](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336321346) PASS; Relay [#45336321352](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336321352) PASS; Full [#45336321274](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336321274) completed FAIL at validation job `138249136286`, `Controller protocol parity / Missing poll signature check`. All 13 firmware targets and Android passed; downstream jobs were skipped. This is the final status at the exact docs head; it does not authorize weakening default-deny or imply physical acceptance.


### UTC05 post-run CI refresh — supersedes earlier pending/queued snapshot
RELEASE #291 current head `3f92801aadf47be594fdef5a278b6aa125eaea1a`: Windows [#45336455064](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336455064) completed FAIL at PISONET `negative-selftest.ps1:326`, `missing tag accepted=False`; ESP32 compatibility [#45336455127](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336455127) completed PASS 3/3. Build [#45336455073](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45336455073) remains IN_PROGRESS only because `v04_android_emulator` is still running; CI-0701, validate, firmware targets, update bundle and the other v0.4 simulations passed. Production sign handoff and publish jobs are SKIPPED. No release was signed or published.


### UTC05 final RELEASE CI refresh — supersedes earlier in-progress snapshot

RELEASE #291 current head remains `3f92801aadf47be594fdef5a278b6aa125eaea1a`. Windows #45336455064 FAILs at PISONET `negative-selftest.ps1:326`, `missing tag accepted=False`; ESP32 compatibility #45336455127 PASSes 3/3; build #45336455073 completed SUCCESS with CI-0701, validation, all firmware targets, Android, update bundle and all v0.4 simulations PASS. Production sign handoff, release publishing and prerelease publishing are SKIPPED. The negative-test two-lookup fixture gap remains; the PR body still pins older f1fda47 and must be refreshed by PHX-RELEASE. No release was signed or published.

## 7.0 Canonical product branch/version authority must be explicit before integration

Do not infer the active product branch or production version from a branch name, default-branch README, stale handover paragraph or VERSION file alone. Record the exact branch HEAD, VERSION blob/value, top handover status, control-plane designation and release/tag identity. If they disagree, classify the authority as UNKNOWN/BLOCKED and require the product owner to reconcile it before branch promotion, cross-branch migration or release decisions.

**Current source-of-truth conflict, re-read 2026-11-24T04:37:40Z:**

| Reference | Exact ref / file evidence | Current statement |
|---|---|---|
| Control plane #172 | Designates blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5 | Issue-designated development branch |
| v0.5.3 development | VERSION blob 62d8e87b40a05fb7a39b60d72369d10a4fccca21 = 0.5.3-dev.1; PROJECT_HANDOVER blob 0430f421f705451b2c94cf9a97d2cf02398e9657 | Handover calls v0.5.3-dev.1 active and v0.5.2 the frozen production baseline |
| blazepwifi-v0.6.0-audit-foundation | Branch HEAD 2fbd2475e9f54878c316fa7cea2f228386b0e859; VERSION blob be14282b7fffb9ba95d51c6546ed9816dc8f3ff8 = 0.5.3; README blob 62333e9c12ef3ba0d43c8efa7ef256e4dfeb840d; HANDOVER_POLICY blob c3a51e5185fb29de546d12e3b2ca25dc9aba77c6 | README and policy call v0.6.0 audit/UX/security foundation active while source VERSION remains 0.5.3; no signed installable v0.6.0 is claimed |
| Experiments main | HEAD f4e8a891aed8af86d5fd315d28750a0ac3a7372b; VERSION blob 43c05666668b2a6d1eef2c5dca9032d8c6b77869 = 0.5.3-dev.5; README blob 7990e2ecbab06cafa5f8227050929e16fff1f4a1; PROJECT_HANDOVER blob f86c0ae9b14853963b8a9b835e1100eb5178d1a6 | README says current production release 0.3.0; default-branch handover labels itself historical and directs maintainers to v0.6.0; lower handover sections also retain v0.5.3-dev.5 |

These statements are not mutually authoritative. The issue-designated v0.5.3 line is internally aligned at VERSION 0.5.3-dev.1, while the v0.6 branch is separately labeled active despite VERSION 0.5.3, and main's README production label conflicts with the v0.5.2 production baseline in the v0.5.3 handover. PHX-CORE must publish one owner-approved canonical development ref, version policy and production baseline, and reconcile the control-plane and handover pointers. PHX-MASTER records the conflict only; it does not select a product branch, edit product handovers or move source.
## 7.1 UTC06 exact-head review: release lookup fixture, cross-owner blobs and COE #26 (2026-11-24T06:04:45Z)

This section is a read-only integration contract refresh. It changes no subsystem implementation, ownership route, release authority, or migration permission.

### Current refs and owner evidence

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; issue-designated development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`; comparison-only v0.6 audit branch `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Master #288: `phoenix/master-coordination@1c8b3ca82c9b0212f925e65145bc8bf196c5ef80`, OPEN / DRAFT / UNMERGED, 192 changed paths, all under `coordination/phoenix/`; Master PR Actions and combined statuses returned zero.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT / FROZEN, 205 changed files, five workflows QUEUED / zero jobs.
- Routing manifest `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. Cleanup #266 remains OPEN, 0/7.

| Owner | Exact candidate head | Exact-head evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build #42698139210 SUCCESS (scoped); CORE implementation remains separately owned |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity #44782114384 and API21/API23 smoke #44782114393 SUCCESS; build #44782114390 FAIL at mandatory handover freshness and ESP32 compile |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows #42462978704 SUCCESS (synthetic CI only) |
| HARDWARE #349 | docs `8639deda8d341d61efddff77be4d06ea931d040d`; source/test `1247a5c7b332677ae8dca83dc94cf586a015e7a0` | Quarantine #45336321346 and Relay #45336321352 PASS; Full #45336321274 FAIL at Controller protocol parity / `Missing poll signature check`; 13 firmware targets + Android PASS, downstream validation-dependent jobs skipped |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows #43633486963 SUCCESS; QA #292 head `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` has no PR-triggered runs |
| RELEASE #291 | docs `3f92801aadf47be594fdef5a278b6aa125eaea1a`; source/workflow `1843a31236c07efa3f261ff69c278f77a1f1bfe5` | Windows #45336455064 FAIL; ESP32 compatibility #45336455127 PASS 3/3; BlazePwifi build #45336455073 SUCCESS; signing and publishing jobs SKIPPED |

### Release admission fixture and owner overlap

At RELEASE #291 source/workflow SHA `1843a312` and current docs head `3f92801`, the release workflow blob is `61031c13aad934fb52aef3038598f8b4d6a89334`. It performs independent read-only lookups at workflow lines 479 (`/releases/tags/$releaseTag`) and 494 (`/git/ref/tags/$releaseTag`), capturing `$lookupExit` and `$tagLookupExit` separately. The PISONET-owned `negative-selftest.ps1` blob remains `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`; it replaces only the first `$lookupExit = $LASTEXITCODE` in its extracted decision block. It does not fixture-substitute the second Git-ref lookup or its exit capture. The current Windows job log fails at line 326 with `missing tag accepted=False`; the later PublisherMockCli and publisher steps are skipped. The separate `PublisherMockCli.ps1` blob is `7d56522b4fd678a26a2d7ea39e9b51dc8e52612d`. The workflow and both test blobs were re-read at the source/workflow SHA and current docs head; identities match. No precise second-call HTTP response is exposed by the log, so do not infer it.

The three handover paths below are changed by CORE #252, PISONET #255, QA #290 and RELEASE #291. All twelve exact branch blobs differ:

| Shared path | CORE #252 | PISONET #255 | QA #290 | RELEASE #291 |
|---|---|---|---|---|
| `PROJECT_HANDOVER.md` | `72e8e487d333a9488f77c2c3e68652d1a650ff85` | `d3e66608280644af8c42635168a7e27c8fba8f31` | `83db03cf387f280ba2d595ff6e9d58ffa23417c5` | `92b28dbf4a5b5ec3c6b8f1552225ea359a05a941` |
| `CHANGE_LEDGER.md` | `df50981c1596838b1abf544e94f68e89ad556b7d` | `02963d32018ea09ad2a6a5a95b487de1f65ff4f2` | `3180e1a93c852e5c983f947e8ca45a897df0479f` | `ef6d52acbd053b2722eb018486b6c5a996ff1205` |
| `CURRENT_STATE.md` | `72c38aeb93377f3aedb758c91d670ff1150e87bd` | `47e07b7c0e06766d0d4ebb18bc13bfb274adfe22` | `73b9d1d6acbd8b58c13f2d1b9d17512c392f444a` | `29fb4b85d5ef8fa885f6b26982628fa5cf5abc6a` |

RELEASE #291 also changes `negative-selftest.ps1` and `PublisherMockCli.ps1` inside the PHX-PISONET-owned SoftTimer subtree. Those files are absent from PISONET #255's current diff/head, but the ownership manifest assigns the whole subtree to PISONET. PISONET must review the test files; RELEASE must review the two-endpoint production semantics; QA must independently review the corrected fixture and exact final head. Do not overwrite, cherry-pick, rebase, or merge shared paths to resolve this collision.

### Destination comparison and production boundary

At exact source #349 / destination COE #26 heads, ESP8266 sketch blobs differ (`2f87a9de84ac53dbb0d2718b5c79a4662b63de8f` vs `c8be98f72596681e36a3ad1f8939bf8046c96887`); ESP32 blobs differ (`a9a1c2fecb001d71f8f22b43952edbd160aacaf8` vs `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`). The source parser lab `ac4b164e79da90039b0f99a22efdb6a136046442` has no destination identity; destination `Hardware/tests/test_firmware_hardening.sh` is a different blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`. The product LICENSE and destination `Pisowifi/LICENSE` match exactly at `1ee55b94183417be977ca287cd7391f9a6f7e721`; destination root `NOTICE` is absent. COE #26 remains FROZEN; no staging, copy, move, overwrite, or promotion occurred.

PRODUCTION NO-GO remains mandatory pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates.


## PHX-MASTER UTC06 post-checkpoint exact-head refresh — fixture-source and exact-head freshness contract

A test-source refactor includes moving embedded C/C++ fixture strings into a separate fixture module and changing workflow path filters. The test-source anchor and PR handover must point to the final commit containing both runner and fixture module. A workflow result is usable only when its checked-out SHA equals that final commit; IN_PROGRESS, QUEUED, or a run from a previous source head is not a pass. If a workflow path filter omits a newly imported fixture, the refactor is not covered until the filter is corrected and rerun.

Applied to HARDWARE #349: commit `da046d5ea80a8daac7258d302ecc310cd5634b24` moves JSON grammar fixtures into `poll_json_array_primitive_lab_fixtures.py` and updates Quarantine/Relay path filters. Quarantine #45342525513, Relay #45342525472, and build #45342525544 were in progress; no exact-head Full result returned. The PR body remains pinned to e4ab80/8dd8b12 and must be refreshed by PHX-HARDWARE. The prior `Missing poll signature check` remains a separate CORE-producer / QA-assertion dependency; do not invent a poll signature or weaken default-deny.

Applied to RELEASE #291: current Windows run #45340630145 fails at PISONET-owned `negative-selftest.ps1:326` after package parity and release policy checks pass. PHX-PISONET owns the fixture correction; PHX-RELEASE owns workflow semantics. Publisher is skipped.

No financial, authentication, relay-admission, firmware, or production behavior changed in this Master update.


## 7.2 Board-local test-import completeness is independent of firmware presence — COE #26 exact-tree gate (2026-11-24T07:37:39Z)

A destination firmware sketch does not establish that its source-linked labs, fixture modules, mutation tests, licenses, or CI triggers were imported. Before any cross-repository promotion, the owner must map each source test/lab and fixture by exact blob or document an explicitly reviewed reimplementation; preserve executable modes and license/NOTICE obligations; then run destination CI at the exact destination SHA. Missing or identity-divergent tests remain NOT IMPORTED / UNKNOWN, not equivalent by filename or intent.

Current exact example: Experiments HARDWARE #349 tree dff053bb8fe276d3f0ba9764e845d61ebe640539 contains 56 board entries including 42 Python labs/helpers. COE #26 tree b382d233ff06c8791b1028bed3c617cc7b670d12 contains four board entries (two sketches) and zero Python labs/helpers. The ESP8266 and ESP32 sketch blobs differ; source poll_json_array_primitive_lab.py (15c0d31ef9c07c549a0ddd5cf4d26c687cac8fd3) and its fixture module (b55ec6ef0ec4184c7b18b4e55bd65aeb96951812) have no destination counterpart. Product, QRCode and TailAdmin license artifacts match, but root NOTICE, Tabler LICENSE and BlazeRentalLauncher LICENSE are missing at the destination. COE #26 has zero check-runs/statuses at its exact head.

This contract is a fail-closed review gate, not a migration instruction. PHX-MASTER did not stage, copy, move, overwrite, rebase, cherry-pick, or change COE #26. The destination remains FROZEN until owners complete file-level provenance, license review, test identity mapping and exact-head destination CI.


## 7.3 Synthetic release lookup tests must be network-isolated (2026-11-24T08:05:17Z)

Any test that extracts and executes a production release/publisher decision block must replace the process boundary for **every** external lookup and inject both response body and exit status. It is not hermetic to replace only one captured exit-code assignment while leaving a real CLI command in the extracted block.

For the SoftTimer release admission path, the Release-object lookup (`/releases/tags/$releaseTag`) and Git-tag lookup (`/git/ref/tags/$releaseTag`) are independent decisions. Synthetic tests must fixture both calls and assert that no real `gh api` process/network call occurs. Required vectors include: both lookups 404 → absent-tag path may proceed to final artifact verification; either lookup 200 → deny; 401/403/5xx, transport error, ambiguous/multiple status lines, or successful CLI exit paired with a 404 body → deny. The production publisher remains fail-closed and must still verify final shipped bytes before publication.

Evidence: RELEASE #291 current head `dabfd75cdccea6ab2f5adfe5251fbc3b506e38aa`; workflow blob `61031c13aad934fb52aef3038598f8b4d6a89334`; negative test blob `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`; Windows run [#45352021031](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352021031) fails at line 326 with the missing-tag vector rejected. The test substitutes `$lookupExit = $LASTEXITCODE` only; both `gh api` commands and tag-lookup output/exit remain live. PHX-PISONET owns the test harness, PHX-RELEASE owns publisher semantics, and PHX-QA owns independent review. This contract does not authorize Master edits to those files.


## 7.4 Upstream source/test, docs-head and PR-head anchors must advance as one release provenance tuple (2026-11-24T08:37:40Z)

A downstream release/compatibility consumer that validates another role's implementation must distinguish three refs whenever they differ: (1) the exact upstream source/test commit exercised, (2) the final upstream docs/workflow commit, and (3) the upstream PR head. Pin the relevant firmware/artifact Git blob separately. The downstream handover and its machine-checked test must contain the same exact tuple with the canonical labels; a test-only expected-SHA update is not a handover refresh.

When the upstream PR advances, the downstream owner must update the expected source SHA, docs/PR head, checked-out ref, and downstream handover in the same owner-controlled increment. Then rerun the exact-head compatibility workflow and the complete downstream build. A separate compatibility matrix PASS does not override a failed handover-freshness gate; downstream compile, signing, publisher, and release stages remain blocked until the tuple is consistent.

Current evidence:
- HARDWARE #349 source/test SHA: `6ce423783b306411bdb7e7217081c050cb4cbec4`.
- HARDWARE #349 final docs/workflow/PR head: `a994f7048673677651449eeb0a04d2bf9e91737c`.
- ESP32 sketch blob: `a9a1c2fecb001d71f8f22b43952edbd160aacaf8`.
- RELEASE #291 head `bffc4ffd86794a2df3408a099369e3d48f8b3f0b` updates the compatibility test to expect that tuple, but `.github/PHX_RELEASE_HANDOVER.md` remains blob `500cc0be69efdb7320320595f07d5d1f37c5df63` and still records the older docs head `dff053bb8fe276d3f0ba9764e845d61ebe640539` and PR head `6ce423783b306411bdb7e7217081c050cb4cbec4`.
- RELEASE build workflow [#45357167281](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45357167281) fails its CI-0701 freshness check with `PHX-RELEASE-HANDOVER-ANCHOR-RED`; separate ESP32 compatibility [#45357167298](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45357167298) passes 3/3. The failure is a stale handover anchor, not an ESP32 compile result.

Owner action: PHX-RELEASE updates its own handover to the current #349 tuple and reruns exact-head CI; PHX-HARDWARE owns its source and handover. PHX-MASTER records the contract only and does not edit either owner's files.


## 7.5 PHX-MASTER UTC09 — OpenWrt source-tree provenance and target-set parity (2026-11-24T09:37:39Z)

The current RELEASE #291 source/test increment cfd34e2b178455313210962f48ae4560d83be096 records Git tree identities for the OpenWrt rootfs overlay and Orange Pi Linux agent, in addition to target-specific helper blobs. The exact source commit tree 0be529f79674137dbdec4437abd622946595e983 contains experiment/openwrt/BlazePwifi/openwrt/rootfs at tree f4a923aaacf1374e90c7bab5f335efe6c6ec55cf and experiment/openwrt/BlazePwifi/linux-agent at tree da87d556b16bd7650c440083c9f0f929d57d1274; both objects were independently read back from GitHub.

Independent static comparison found the 11 supported target names identical across .github/scripts/write_build_provenance.py, build/build-openwrt-image.sh, and both OpenWrt workflow matrices: ruijie, x86_64, and nine Orange Pi targets. This is a source-set assertion, not a Python-suite execution. The existing Python tests exercise representative ruijie, x86_64, and orangepi_zero3 classes rather than iterating every target; RELEASE should consider a table-driven all-target mapping test.

At final PR head 9d45ee19b2d8e3ef6623b3b0f0db3da56b1616e8, the exact-head build run [#45366411182](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45366411182) completed with 26 successful jobs and four skipped jobs; its provenance suite passed 50 tests, Arduino CLI archive verifier passed 10 tests, and action-pin guards passed for 52 + 4 + 6 invocations. ESP32 compatibility [#45366411198](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45366411198) passed. Windows [#45366410925](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45366410925) still fails in PISONET-owned negative-selftest.ps1:326; publisher is skipped. Tree identities prove Git object provenance only, not artifact readback, licensing completeness, detached signatures, or hardware acceptance.

## 7.6 PHX-MASTER UTC09 — stacked PRs retain owner-specific handover history

RELEASE #291 remains OPEN / DRAFT / UNMERGED at 9d45ee19b2d8e3ef6623b3b0f0db3da56b1616e8 and its 27-file accumulated diff still includes three CORE-owned handover paths plus two PISONET-owned tests/ReleaseSigning files. At exact owner heads, PROJECT_HANDOVER.md, CHANGE_LEDGER.md, and CURRENT_STATE.md have distinct blobs across CORE #252, PISONET #255, QA #290, and RELEASE #291. The two PISONET test paths in #291 return 404 at PISONET #255's exact head. This is a review/ownership collision, not authorization to copy, overwrite, or transfer ownership. Require CORE and PISONET review and preserve all four histories before any integration decision. The 11-route manifest remains DRAFT_REVIEW_ONLY with PHX-MASTER target null.


## 7.7 Test-import identity is blob+mode, not filename or count — COE #26 exact-head gate (2026-11-24T10:05:28Z)

A source test and destination test are equivalent only when the mapped relative path, Git blob SHA, and Git mode all match at the exact reviewed source and destination refs. Same-name files with different blobs are divergent implementations; source-only and destination-only files remain separate populations. File counts, names, or a passing destination suite do not prove that source tests were imported. Before proposing staging, require per-file source provenance, license/notice coverage, import-completeness classification, test identity, and exact-destination-head CI. No recursive copy or automatic overwrite follows from a missing counterpart.

At source HARDWARE #349 final docs head `861e80de8eec289ef04a84bd80484eec032a3b73` versus COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, the source tree has 2,504 entries and the destination 286 (both non-truncated). Board subtrees are 58 versus 4 entries; 44 source board-local Python labs/helpers have no destination counterpart. Test mapping is 47 source / 19 destination: 1 exact blob+mode, 3 divergent same-path files (`config.sh`, `integration.sh`, `security.sh`), 43 source-only, and 15 destination-only. Both ESP8266 and ESP32 sketch blobs differ. This is a provenance gate, not a claim that every destination-only test is invalid or that every missing file should be copied.

Product LICENSE, QRCode LICENSE, and TailAdmin LICENSE/NOTICE match exact blobs at their mapped paths. Experiments root NOTICE, Tabler LICENSE, and BlazeRentalLauncher LICENSE have no mapped COE #26 counterpart. Matching licenses do not establish complete third-party licensing or migration provenance. COE #26 remains FROZEN with five queued workflows and zero jobs/statuses.

## 7.8 Exact source/test and final docs-head CI are separate release-provenance anchors — 2026-11-24 UTC11

Every role checkpoint that separates implementation from handover/documentation MUST record a provenance tuple:
1. exact source/test SHA;
2. exact final PR/docs HEAD;
3. workflow run IDs and conclusions for the exact SHA each run checked out;
4. the final handover checkpoint that covers every changed source/workflow path.

A focused source/test PASS does not imply that the final PR/docs head passes. If a later handover or workflow commit changes the tree, the relevant CI must be inspected or rerun at that final head. A final-head failure supersedes an earlier source/test PASS for integration readiness. Skipped downstream jobs are NOT PASS evidence.

Shared handover gates must identify their canonical documents and every source/workflow path they monitor. When a role changes a workflow that is covered by another role's shared handover, the two owners coordinate the handover update after the code change; neither may bypass the gate or silently overwrite the other owner's record. Master routes and records the dependency but does not take ownership of the source or shared handover.

For the current RELEASE #291 stack, the Windows workflow invokes the shared BlazePwifi gate while monitoring both BlazePwifi and SoftTimer paths. The current final docs head fails because `.github/workflows/blazepisonet-softtimer-release.yml` is newer than the canonical BlazePwifi `CURRENT_STATE.md` checkpoint. PHX-RELEASE and PHX-CORE must coordinate that update and rerun exact-head CI. This is a handover-freshness blocker, not permission to weaken the gate.

For HARDWARE #349, focused Quarantine/Relay passes at both source/test and docs heads do not clear the Full validation failure at QA-owned `Missing poll signature check`. Keep firmware deny-only until the producer/consumer contract and independent QA assertion are reconciled.


### 7.8.1 A ledger entry does not substitute for the gate's canonical live-state checkpoint — 2026-11-24 UTC11

When a shared handover gate computes the last committed revision of multiple canonical files independently, updating only the change ledger does not refresh an unchanged `CURRENT_STATE.md`. Verify the exact blob and last path commit for each required handover file at the final PR head. If the gate still names the previous checkpoint, the handover remains stale even if a new ledger entry exists. Coordinate the file owner and workflow owner; do not bypass the gate or infer that the entire handover is current from one updated document.

### 7.9 Exact-source migration manifests must reconcile rows, summary counters and source pin

A migration manifest is internally consistent only when (1) every row's exact source and destination blob SHA and Git mode match the named commits, (2) summary counters equal the row classifications, (3) destination-only files are explicitly dispositioned, and (4) the declared source commit is distinguished from current source HEAD. A historical pinned snapshot is not a live mirror. Never infer migration completeness from a summary count or copy a destination-only file into the source map without owner review.

For COE #26 at destination b382d233 and pinned source 6d4c9b48, all 61 SOURCE_INTAKE runtime rows match actual source/destination blobs and modes. The actual row split is 46 exact and 15 derived, while the summary says 47 exact and 14 derived. One destination-only file, blaze-appliance-diag, is outside the intake rows. The pinned original test tree has 143 top-level files versus 19 destination tests; only two are exact and two are same-name divergent. The current #349 source tree is a different snapshot (53 rootfs files, 33 same / 20 changed / eight pinned-only). The candidate remains FROZEN pending owner correction and complete test/licence disposition.

### 7.9.1 Shared handover files are path-shared but not branch-interchangeable

Compare the exact PROJECT_HANDOVER, CHANGE_LEDGER and CURRENT_STATE blob identities at each final owner PR head. A successful commit to one of these files on a role branch does not update the other branches or establish the canonical shared handover. CORE owns canonical reconciliation; each workflow/source owner records its change and reruns the relevant exact-head gate. Never bypass freshness checks or select a branch snapshot by recency alone. See the [UTC12 Master audit](coordination/phoenix/PHX_MASTER_UTC12_20261124_RELEASE291_HANDOVER_COE26_SOURCE_INTAKE_AND_HW349_RECONCILIATION.md).

### 7.9.2 Revalidate concurrent owner heads after a Master checkpoint

A Master checkpoint is a read-time snapshot, not a lock on owner branches. Before finalizing the same activation, re-read owner PR heads and exact-head CI. If an owner advances, append a read-time correction to the existing report and update the single role/hour checkpoint in place; do not post a duplicate message or claim the earlier run set is still current.

At the post-checkpoint refresh, RELEASE #291 advanced to b154e845: PROJECT_HANDOVER and CHANGE_LEDGER changed, but CURRENT_STATE remained blob 85dd3c1e / checkpoint d85eb6a2. The new Windows/build runs still fail the CURRENT_STATE freshness gate. HARDWARE #349 advanced to dce158b3 with a lab-only poll-response fixture change; focused jobs pass, while build validation still fails at Missing poll signature check. Keep source/test SHA, docs SHA and CI head distinct, and route the shared handover to CORE and the contract assertion to CORE/QA.

### 7.9.3 Source-intake and migration-map reconciliation is a hard staging gate

A destination candidate is not migration-ready until all of the following are independently checked at exact source and destination commits:

1. The manifest's source commit and original subtree tree IDs resolve to the stated recursive source trees.
2. Every SOURCE_INTAKE row resolves to the exact source and destination blob SHA and Git mode.
3. Summary counters are recomputed from the rows and equal the actual identical/derived/missing counts.
4. MIGRATION_MAP rows reconcile one-to-one with the manifest's derived-test list; no omitted path or stale blob SHA is allowed.
5. Test identity is established by path, blob and mode, not filename similarity. Firmware sketches and test fixtures require the same exact-blob discipline.
6. Every applicable LICENSE/NOTICE and third-party asset has an explicit destination or exclusion disposition.
7. A historical source pin is compared separately with current source authority; a historical snapshot must never be silently represented as current main.

Any counter mismatch, stale map entry, missing source path, unaccounted license, incomplete test import or current-source drift keeps the candidate FROZEN. Do not stage, copy, rebase, cherry-pick, overwrite or promote until the owning integration role corrects the manifest/map and reviewers re-run exact-head CI. QUEUED workflows are not test evidence; CI at one SHA does not validate a different final docs/source head.


### 7.9.4 Release artifact provenance separates pinned commit, firmware blob and current test head

A reproducible firmware compatibility run must record the immutable source commit, the exact firmware sketch blob, and the test/lab head separately. A successful compile against an older source commit may still verify the same firmware blob at a newer test head, but it does **not** prove that the newer lab/test files were checked out or executed.

At current RELEASE #291 head `b97a360c107d1d28ab99e7376d5ba0a79fb276f0`, workflow blob `a127d06cd0a5784e026716c1feb18554f328329d` pins HARDWARE source commit `6ce423783b306411bdb7e7217081c050cb4cbec4` and ESP32 sketch blob `a9a1c2fecb001d71f8f22b43952edbd160aacaf8`. Current HARDWARE #349 source/test head `839c72ac68bb1f0a8fd9a2fc74a166cec15b624e` resolves the same sketch blob. Therefore compatibility run [#45415537967](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45415537967) is valid for that exact firmware sketch identity and pinned source timestamp; it is not evidence that the latest #349 lab/test commit was checked out. If the sketch blob changes, update the release pin and rerun both exact-core legs.

At the same RELEASE #291 head, Windows [#45415537929](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45415537929) and build [#45415537818](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45415537818) fail at the shared handover freshness gate. The gate names `.github/workflows/blazepisonet-softtimer-release.yml`, `.github/workflows/blazepwifi-v053-release.yml`, and `.github/workflows/blazerental-v053-lineage2-sign.yml` as newer than the canonical `CURRENT_STATE.md` checkpoint. The file remains blob `85dd3c1e9254d947c4e75daaeaf3351ef3e105e3`, last checkpoint `d85eb6a2766781b6cac1807cef461993d8216b84`. CORE owns canonical reconciliation; RELEASE owns workflow changes and exact-head reruns. Do not bypass the gate.

HARDWARE #349 Full validation still fails QA-owned `Missing poll signature check`; focused tests and target compiles do not authorize positive poll admission or hardware acceptance. Keep deny-only behavior until CORE's producer contract and QA's independent assertion are reconciled.



## 7.10 Exact-head evidence freshness and checkpoint identity (2026-11-24 UTC16)

A role PR may have three different identities: (1) source/test commit, (2) final documentation/workflow/PR head, and (3) the commit actually tested by a workflow run. Record all three separately. A CI result proves only the commit shown by that run; do not promote a focused source-head result to a later docs/PR head unless a workflow was executed at that exact head.

Before integration, require the PR description and owner handover to identify the live PR head and source/test head. If the PR head advances but the description still names an older source/test/docs pair, mark the handover **STALE / BLOCKED** and request an owner refresh; do not infer that the latest source or docs were tested.

Shared handover freshness is an admission gate, not a documentation preference. The canonical owner must update the authoritative `CURRENT_STATE.md` after the workflow/source changes, then the affected owner must rerun exact-head CI. Do not bypass the gate or select a last-writer handover copy. CORE owns the canonical BlazePwifi state; RELEASE owns release workflow changes; PISONET owns its SoftTimer tests; QA independently reviews.





### 7.11 Register/poll response authentication remains an unapproved interface

At Experiments main f4e8a891, the exact CGI producer blob is 2e3a1430d08cc6606429a042df3b5848f53c7267. Its register|ping and poll response branches do not emit response_sig; the same file emits response_sig on member snapshot/authentication/mutation responses. The current ESP8266 sketch blob bfb94920eb0a189ca01d52e5443954fa133f5423 and ESP32 sketch blob 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0 call register and poll and parse their ordinary fields, but do not contain a response_sig consumer check. This is source inspection, not approval of a future protocol.

HARDWARE #349 current head aa9ac766 has focused Relay/Quarantine PASS, but Full run #45452999881 fails Controller protocol parity at the inherited “Missing poll signature check”. The test fixture's signature-looking placeholder is not an authenticated protocol value. Do not fabricate a response signature, reuse a member endpoint signature for poll, create positive poll admission, or weaken default-deny.

PHX-CORE owns the authenticated register/poll producer contract, versioned envelope and canonical golden vectors. PHX-QA independently reconciles the legacy positive assertion against that approved contract. PHX-HARDWARE retains fail-closed consumer behavior until the contract is approved and independently tested. Hosted source-extracted CI is not native hardware acceptance; physical coin/relay tests, 150 real power cuts and the 30-device/24-hour soak remain NOT TESTED.


### 7.12 Exact source/test, handover and PR-head identity — UTC18

A role handover must distinguish (1) source/test commit, (2) final handover/docs commit, and (3) current PR head. These are not interchangeable.

- HARDWARE #349: source/test 32c026538e737870ea8bb1e22143e438f9d61f7a; handover/docs/PR head 66f6d101f21d8193466105da7677e3afe0ad92c3. The current PR body still names aa9ac766/d9adf204 and must be refreshed by HARDWARE. Exact-head Relay/Quarantine pass; exact-head build fails at Missing poll signature check. The latest source commit is a lab-runner consolidation; aggregate PR #349 still contains earlier ESP32/ESP8266 sketch changes. No approved authenticated register/poll producer contract exists yet.
- RELEASE #291: source/test anchor a004c647e67f90269a9149f918887622bb8cc5e8; current workflow/PR head 32487a5720040b8fb8374a7ab6efd224aeac7207. Latest commit changes only the BlazePwifi release workflow expression wiring. Windows and build validation fail the mandatory PROJECT_HANDOVER freshness gate at checkpoint 0406ce0b; compatibility is pending. Current PROJECT_HANDOVER blob ce00cabad64364c2255dc5a5a2fc29f4af0bcb17 and CURRENT_STATE blob 85dd3c1e9254d947c4e75daaeaf3351ef3e105e3 remain unrefreshed for this workflow change.
- A successful older compatibility run is not current-head proof. RELEASE compatibility #45453527038 was pinned to source 6ce423783b30, not current source/test a004c647.
- Freshness gates are admission controls. Do not bypass them, synthesize response_sig, reuse member signatures for poll, or weaken deny-default. CORE owns producer contract/canonical handover; QA owns independent assertion review; HARDWARE owns consumer labs; RELEASE owns release workflow and handover update.


## 7.13 Migration source refs, intake counters and test identities must reconcile before staging — 2026-11-24 UTC19

A cross-repository route manifest, a historical source-intake pin, a current source branch, a role PR source/test head, and a destination PR head are distinct provenance anchors. They must be recorded separately and tied to each mapped file. A high-level manifest source_ref does not silently replace a historical per-file source pin; a current role PR does not silently replace either.

For COE #26, OWNERSHIP_ROUTES.json records Experiments main@f4e8a891 while Pisowifi/SOURCE_INTAKE.json records historical source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00. The current HARDWARE #349 head d2565d9 is a separate role/test reference. The integration owner must state which source ref governs each path and document source drift before any staging proposal.

Recompute summary counters from rows, not from a copied summary. The 61 runtime rows yield 46 byte-identical and 15 derived, while the JSON summary says 47/14. All 61 recorded historical source blobs/modes and all 61 destination blobs/modes match; current main nevertheless has 20 changed and 8 missing paths relative to the historical runtime pin.

Test counts are meaningful only with an exact source ref and path scope: historical 6d4c9b has 149 entries under the project tests subtree; current main f4e8 has 38; current HARDWARE #349 d2565d9 has 47; COE #26 has 19. For the current #349-to-COE comparison, one test is exact, three same-path tests diverge, 43 are source-only and 15 destination-only. Do not collapse these inventories into one source count.

SOURCE_INTAKE derived_tests has 15 entries and all 15 recorded destination blobs match the exact destination tree. MIGRATION_MAP records only 14 derived rows, omits voucher_txn_journal.sh, and has stale run_focus.sh and member_txn_journal.sh hashes. These are owner-correctable manifest defects, not permission for Master to edit the destination.

The board route also remains incomplete: current #349 source ESP32/ESP8266 subtrees have 16/48 entries, while COE #26 has one sketch in each. Both destination sketches differ from the exact source blobs. Product, QRCode and TailAdmin LICENSE/NOTICE counterparts match; root NOTICE.md and Tabler LICENSE lack destination counterparts. BlazeRentalLauncher LICENSE remains a separate RENTAL route.

No staging, copy, move, overwrite, rebase, cherry-pick or destination write is permitted while these provenance, test, import and licensing dispositions remain unresolved. COE #26 stays FROZEN and DRAFT_REVIEW_ONLY.


### 7.13.1 Concurrent owner advances must supersede only the exact evidence tuple — UTC19 post-checkpoint

After the initial UTC19 audit, HARDWARE #349 advanced to PR/workflow head 4c99e1c while retaining source/test d2565d9 and prior handover/docs anchor 58c5418. The latest change is workflow path-filter-only; it does not alter the firmware source blobs or COE #26 tree comparison. Current exact-head focused Relay and Quarantine runs pass, while Full validation fails at the inherited poll-signature assertion. Record the three refs separately and require HARDWARE to refresh the handover/PR description.

RELEASE #291 advanced to docs/PR head d90e382 after source/workflow change 343e25b8. Current Windows and build runs fail the CORE-owned PROJECT_HANDOVER freshness gate; ESP32 compatibility passes. CORE owns the canonical handover; RELEASE owns the workflow and exact-head reruns. A later docs commit does not clear the gate unless the canonical owner checkpoint and exact CI are refreshed.


## 7.14 Exact-head handover and migration source-pin reconciliation — PHX-MASTER UTC20

A migration or release evidence tuple is incomplete unless it names the exact **historical source pin**, **current owner source/test head**, **destination candidate head**, and **final handover/docs head** separately. A branch name, PR number, latest handover file, or green run on a prior SHA is not a substitute for these immutable identities.

1. For each migration row, compare the recorded source blob and file mode against the historical source tree and destination tree. Reconcile the intake summary from the actual rows; a summary count that differs from its rows blocks staging.
2. Separately compare the historical source pin against the current owner source/test head. Changed or missing current paths are drift requiring owner disposition; do not silently move the historical pin to a newer branch head.
3. Test identity must include path, blob SHA and mode. The migration map, intake JSON, actual destination tree and CI test inventory must have the same row set. Missing rows, stale hashes or extra/missing tests keep the destination frozen.
4. License and notice checks are path-and-blob checks. A source LICENSE/NOTICE without a destination counterpart is a blocker until the correct owner provides a documented route or approved resolution.
5. Hosted CI evidence is valid only for the exact commit it ran against. Record source/test, docs/handover and PR head separately. A later docs commit cannot make an earlier test run exact-head evidence; a stale handover cannot authorize promotion.
6. Owner routing remains authoritative: CORE owns canonical `CURRENT_STATE.md` and authenticated financial/poll contracts; RELEASE owns release workflow logic and exact-head reruns; PISONET owns Windows tests; HARDWARE owns firmware/lab source; QA owns independent assertion review; MASTER owns coordination and integration matrices only.
7. Any missing registry access, branch protection evidence, required owner review, exact CI, physical acceptance or migration proof is a hard hold. This section adds no product protocol, accounting, firmware or release authority.



## 7.15 Migration intake row-set and source-pin invariant — PHX-MASTER UTC21

A migration candidate must keep four identities separate: (1) the historical source pin used by the intake record, (2) the current owner source/test head, (3) the destination candidate head, and (4) the final handover/docs head. A repository default branch or newer worker branch must never silently replace the historical source pin.

Before staging, the COE integration owner must prove all of the following from exact recursive trees:

1. Every SOURCE_INTAKE.runtime row resolves to its recorded source blob, destination blob, and Git mode.
2. Summary counts are recomputed from the actual row statuses; declared counts must equal the rows.
3. The derived-test list and MIGRATION_MAP.md test rows have identical path sets and exact destination blob hashes; no stale hash or omitted row is tolerated.
4. Current owner source/test drift from the historical pin is separately enumerated as changed, missing, or unchanged; it is not silently promoted into the intake pin.
5. Every in-scope LICENSE/NOTICE has a correctly routed destination counterpart or a documented owner-approved exclusion. A path outside the manifest is not implicitly copy-safe.
6. Board helper imports, sketch identities, tests, and exact-head CI are reviewed before any migration proposal.

Any count mismatch, stale test hash, missing test mapping, unowned UI/Rental license path, incomplete board import, or unreviewed source drift keeps the destination frozen. This contract is review-only; it does not authorize a copy, move, overwrite, financial migration, or production release.


## 7.16 PR descriptions and owner handovers are independent freshness controls — PHX-MASTER UTC00

A current owner handover does not make a stale PR description current. Reviewers must reconcile four distinct identities before integration: (1) source/test commit, (2) final handover/docs commit, (3) current PR head, and (4) the exact commit checked out by each workflow run. The PR description and handover must both state the current tuple and link the corresponding exact-head runs.

Current COE RELEASE #35 demonstrates the distinction: source/test a514e57d789d821cea0f0a29e3e864dad0570046; final handover/PR HEAD ecc1d3d4ad0c4564743a17e8155d524d805738de; handover blob 663b968ae8eea9b757338f3d5bc9fd72e452c470 contains the UTC00 evidence, but the PR description remains at UTC15. Treat the PR summary as STALE until RELEASE refreshes it, even though the handover is current. PHX-MASTER records and routes this discrepancy; it does not edit RELEASE-owned PR text or source.

HARDWARE #349 is the contrasting current tuple: source/test 353231c60fe09e4694fa73e3a3a1e64c5d21353d; final docs/PR HEAD 2fd939ef90db4f68b12f33732733697606c36f9b. Its current PR body records the exact-source and docs-head runs. Both Full runs fail at the inherited Missing poll signature check; focused Quarantine/Relay passes and target compilation do not override that failure.

If any one of the four identities is missing, stale or mismatched, classify the integration gate STALE / BLOCKED. Never infer that a passing source-head run validates a later docs/PR head; never treat a current handover as a substitute for an updated PR body; never bypass the CORE-owned canonical freshness gate. The owner of each source/PR updates its own handover and PR description; QA independently reviews critical money, crypto, hardware and migration claims.


## 7.17 Exact-head evidence freshness and migration provenance gates — 2026-11-25 UTC01

Keep three identities distinct for every worker PR: (1) source/test SHA, (2) final handover/docs/PR SHA, and (3) the exact SHA checked out by each workflow run. A docs-only commit does not inherit a prior source/test result unless the tree comparison proves that the tested paths are unchanged; a workflow name or green child run does not establish parent acceptance.

Current examples:
- HARDWARE #349 source/test `d5b5cd10ae7ab655639b011c442b6968b32c2398`, docs/PR `18d4ff4ff86c6ea6d04419e2117833faa58e5e88`. The source/test tree has 2,532 entries and docs tree 2,533; the only changed file paths are PROJECT_HANDOVER.md and the new UTC01 handover. Focused Quarantine/Relay pass; Full still fails at Missing poll signature check. Preserve the deny-only poll/coin contract until CORE producer schema/golden vectors and independent QA are accepted.
- COE RELEASE #35 source/test `eda86d1f2c6f6bef8e6ff1111329d3f1775e043b`, final handover/PR `02561ba1ed60e0eb827946f76d8749a26943eaaf`. Exact docs-head shared/sandbox/case CI is current; 220 host tests (218 pass / 2 skips) and 40 host preflight tests do not clear the 10-profile ULA authority gate or missing Bubblewrap namespace runner.
- COE #26 route-manifest source_ref main@`f4e8` and SOURCE_INTAKE historical pin `6d4c9b` are different source authorities. Preserve both; never silently rebase historical provenance onto current main.

Before any integration staging proposal, require complete non-truncated source/destination trees; per-file path, blob and mode comparison at the exact source pin; separate current-source drift disposition; license/NOTICE mapping; test identity and map reconciliation; owner-reviewed import completeness; exact-head destination CI; and an explicit owner-authorized staging decision. The current COE #26 candidate fails these prerequisites and remains FROZEN. This contract grants no copy, move, merge, release or production authority.

## 7.18 Shared canonical handover single-writer boundary — PROPOSED / owner acknowledgement required (2026-11-25 UTC04)

Current role PRs #252, #255, #348, #290, #291 and #349 change the same source `PROJECT_HANDOVER.md` at divergent exact blob identities. PRs #252, #255, #348, #290 and #291 also change `docs/handover/CHANGE_LEDGER.md` and `docs/handover/CURRENT_STATE.md` at divergent blob identities. The exact path intersection is recorded in `PHX_MASTER_UTC04_20261125_CROSS_ROLE_HANDOVER_OVERLAP_AND_COE26_PROVENANCE_AUDIT.md`.

To reduce merge conflicts and stale cross-role evidence, propose the following coordination invariant:

1. PHX-CORE is the sole canonical writer for source `PROJECT_HANDOVER.md` and `CURRENT_STATE.md`; other roles do not independently replace these whole files in their PR branches.
2. PHX-CORE is the proposed canonical writer for `CHANGE_LEDGER.md` pending explicit owner acknowledgement. If the team rejects that owner, use separate role-scoped append-only ledgers rather than concurrent rewrites.
3. Each non-CORE role records its own work in a dated role-scoped handover under `docs/handover/`, preserving source/test SHA, final docs SHA, exact workflow checkout SHA, run URLs, failures and next action.
4. A non-CORE role that needs a canonical correction submits the exact evidence/text to CORE for incorporation. The affected role reviews the resulting canonical blob before relying on it.
5. PRs already carrying inherited shared paths retain their history; do not rewrite, rebase, force-push, cherry-pick or merge them merely to apply this proposal. Obtain CORE/PISONET/HARDWARE/QA/RELEASE acknowledgement before merge sequencing.

This section is a coordination proposal, not an automatic source ownership transfer, code behavior change, merge permission or release gate waiver. Until affected owners acknowledge it, classify shared-file integration as `REVIEW_REQUIRED / STALE_RISK` and preserve each exact branch blob as evidence.

## 7.19 COE Hardware candidate admission fence — PROPOSED / owner acknowledgement required (2026-11-25 UTC05)

The exact COE #26 Hardware candidate is not an acceptable migration destination for the current #349 source. The two destination sketches are divergent and retain unsafe behavior not present in current deny-only source: format-on-mount, pending-record clearing after an unverified quarantine append, remote quarantine deletion, and a keyless signature-gate bypass followed by remote configuration application.

Before any Hardware destination staging can be proposed, require all of the following at exact pinned SHAs:

1. A Hardware-specific per-file source/destination map recording source commit, source path/blob/mode, destination path/blob/mode, license/NOTICE counterpart, test identity and owner disposition. The current Pisowifi SOURCE_INTAKE does not cover the Hardware subtree.
2. Both board sketches reviewed against current owner source. Filesystem mount failure must preserve the journal and latch deny; it must never format a possibly recoverable financial journal automatically.
3. Pending coin state may only be cleared after a durable quarantine append has been opened, fully written, flushed/closed, read back and validated. Any uncertainty preserves pending and quarantine evidence.
4. Network-visible quarantine clearing remains denied unless a separate authenticated operator recovery contract and durable receipt exist.
5. Missing/empty controller keys, missing signatures, malformed responses, stale revisions and unapproved response envelopes must deny poll/config admission. Do not call remote configuration application from an unsigned or unversioned register/poll response.
6. Source-exact negative tests cover mount failure, append/flush/readback failure, keyless response, malformed/missing signature, quarantine-delete attempt and reboot recovery. Destination test identity must be pinned and independently reviewed; a differently named or smaller grep script is not equivalent evidence.
7. Required CI must complete at the exact final destination SHA. Queued workflows with zero jobs are not a pass. CORE producer contract, HARDWARE consumer implementation, QA independent vectors and integration-owner provenance review must be recorded before staging review.

This is a coordination admission proposal, not a source change, ownership transfer, copy authorization, merge permission or production approval. COE #26 remains FROZEN / NO-GO.


## 7.20 Active v0.6 register/poll response is unauthenticated and cannot be treated as deny-only — P0 BLOCKER (2026-11-25 UTC20)

**Exact active development source:** \`blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859\`. This is the live development branch, not Experiments main \`6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5\`.

| Source | Exact Git blob |
|---|---|
| ESP32 sketch | \`29f1125d52ff474a0d028ad41f7af201be1f0f9d\` |
| ESP8266 sketch | \`12c4bb82b6fddafe813674a0b5f692c1d3634073\` |
| CGI \`vendo\` | \`db58041c0575ad0a1101d99cb85403e03c8dcb22\` |

### Source facts — inspection only, no runtime attack or hardware test

1. CGI \`register|ping\` returns \`ok\`, \`server_time\`, and a nested \`controller\` object. The response has no \`response_sig\`.
2. CGI \`poll\` returns \`ok\`, \`insert\`, \`target_nonce\`, \`expires\`, and a nested \`controller\` object. The response has no \`response_sig\`.
3. The same CGI emits \`response_sig\` for member snapshot/authentication/mutation endpoints. Those endpoint-specific signatures are not a poll-response contract and must not be reused as one.
4. Both sketches contain zero \`response_sig\` tokens. \`signedBody()\` authenticates the outbound request; \`post()\` returns the HTTP response body without authenticating it.
5. Both poll loops assign \`insertMode\` from \`jsonTrue(r,"insert")\`, assign \`activeTarget\` from \`jsonString(r,"target_nonce")\`, and then call \`applyRemoteConfig(r)\`.
6. Both \`applyRemoteConfig()\` implementations read top-level \`enabled\`, \`coin_enabled\`, \`relay_enabled\`, and \`led_enabled\` fields with permissive default value \`1\`. The CGI poll response places controller state inside a nested \`controller\` object rather than those top-level fields. A missing \`config_revision\` falls back to the initial \`remoteRevision == 0\`; the early-return guard only applies when the revision is already nonzero. Therefore the initial missing-field case does not prevent the permissive defaults from being applied.
7. Both \`applyOutputs()\` implementations define acceptance as \`controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady\`; when \`relayEnabled\` is true, that result controls the relay output. The unauthenticated poll body therefore influences the device's insert/target/configuration and output decision path.

**Disposition:** the current active v0.6 source is **not verified deny-only**. This source inspection establishes an unauthenticated response-to-actuation/admission influence path; it does **not** claim that an unauthorized financial credit was achieved, and no dynamic exploit test was run. The server-side coin-request validation was not audited in this check.

### Required owner resolution

- **PHX-CORE:** publish and approve the versioned register/poll response envelope, authentication/freshness rules, and exact golden vectors. Request signing does not authenticate the response.
- **PHX-HARDWARE:** consume only an approved response contract; fail closed before changing \`insertMode\`, \`activeTarget\`, remote configuration, or relay/coin output state. Do not call remote configuration application on an unauthenticated response.
- **PHX-QA:** independently verify both boards with source-linked negative tests for missing, malformed, stale, replayed, wrong-controller, wrong-target, and invalid-authentication responses.
- **PHX-MASTER:** retain the interface blocker and release gate. Do not invent a signature, reuse a member endpoint signature, or remove/relax the inherited \`Missing poll signature check\`.

The current HARDWARE #353 Full failure at \`Missing poll signature check\` is a valid blocking signal, not a test to bypass. This section supersedes any earlier coordination wording that treated the current v0.6 implementation as verified deny-only. No source owner or branch was changed by this audit. **PRODUCTION NO-GO.**

## 7.21 COE #26 Hardware response-auth candidate is keyless-bypassable and not HMAC-bound — P0 BLOCKER (2026-11-25 UTC21)

**Scope distinction:** this section describes the COE #26 draft candidate only. It does not claim that the active Experiments v0.6 source has acquired response authentication. The active v0.6 register/ping and poll response blocks remain unsigned as recorded in §7.20.

Exact candidate pins:
- COE #26 branch `integration/ecosystem-nonproprietary-candidate-20261111`, head `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- ESP32 blob `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`; ESP8266 blob `c8be98f72596681e36a3ad1f8939bf8046c96887`; CGI `vendo` blob `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e`.
- Hardware test blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`; Hardware README blob `99af3e5b46cd8b6f35c6479b204683f60c55ebcb`.

### Source facts — static inspection, no exploit or hardware test

1. ESP32 `loadConfig()` loads `cfg.key` with an empty default (`prefs.getString("key", "")`). ESP8266 `defaults()` zero-initializes the complete config, including the key. Both setup portals render a controller-key password field without `required`; both save handlers update the key only when the submitted field is nonempty. A fresh or blank-key controller can therefore retain an empty key.
2. Both sketches initialize `sigOk=true` and enter response-signature verification only inside `if(cfg.key.length())` / `if(strlen(cfg.key))`. With an empty key, the verification block is skipped and `sigOk` remains true. The success branch then accepts an HTTP body containing `"ok":true`; the poll loop reads `insert` and `target_nonce` and invokes `applyRemoteConfig()`.
3. The normal router first-boot UCI-defaults script generates an 18-byte random `vendo_key`, while `common.sh` reads that UCI value. This server-side bootstrap does not provision the corresponding key into the ESP setup portal and does not make the ESP field mandatory. `bp_check_vendo_sig()` also has no explicit nonempty-secret guard if the UCI defaults hook is bypassed or fails.
4. The setup transport is HTTP. This audit does not demonstrate a live interception or actuation; it establishes a source-level unauthenticated response path when the device key is empty. A forged `ok:true` response can reach the success branch without response authentication. No unauthorized financial credit is claimed.
5. Hardware README describes the response construction as `HMAC/SHA256(key | action | id | nonce | ... | key)`. The implementation uses raw SHA-256 over a concatenated secret/message/secret string (`mbedtls_sha256` on the boards; `sha256sum` through CGI `bp_sha256`), not a standard HMAC primitive. This is a documentation/contract mismatch, not a claim that a particular cryptographic attack was demonstrated.
6. CGI `vendo_ping_sig()` binds action, ID, nonce and server time; `vendo_poll_sig()` binds insert, target nonce and expiry. The response JSON also contains a nested `controller` object, but that object is not included in either response digest. Firmware `applyRemoteConfig()` reads top-level enable/config fields, not the nested controller object. The response schema and signed-field set are therefore not a complete, canonical interface contract.
7. `Hardware/tests/test_firmware_hardening.sh` checks token presence with grep and computes a separate Python SHA-256 example using a fixed nonempty test key. It does not execute the firmware verifier or CGI helper, and it does not test empty/missing keys, invalid signatures, stale/replayed responses, wrong controller/target, or controller-object binding.

### Required owner resolution

- **PHX-CORE:** publish the versioned register/poll response schema, approved standard MAC/HMAC construction, canonical serialization, controller/target binding, nonce/freshness rules, and explicit key-provisioning contract with independent golden vectors. Reject an absent server key at the CGI boundary.
- **PHX-HARDWARE:** require a provisioned nonempty controller key before Wi-Fi registration/polling; keep outputs disabled and reject every response when the key is absent; verify the complete approved envelope before mutating insert, target, remote configuration or outputs. Make the setup flow enforce and clearly report key provisioning.
- **PHX-QA:** add source-exact tests for both boards and CGI covering empty/missing key, missing/malformed/invalid signature, stale/replayed nonce, wrong controller/target, altered nested config, and exact positive vectors. A grep-only token check and a separately reimplemented digest are not equivalent to exercising the production verifier.
- **COE integration owner:** correct the HMAC claim only after CORE approves the algorithm; pin per-file source/destination blobs, modes, licences and tests; refresh intake/migration provenance for the actual #26 branch; run all destination workflows at the exact final SHA.
- **PHX-MASTER:** retain this as a P0 integration blocker. Do not modify Hardware or CGI source, provision a key, stage a copy, or waive the inherited poll-signature gate.

**Disposition:** COE #26 remains FROZEN / DRAFT_REVIEW_ONLY. No destination staging or writes. **PRODUCTION NO-GO.**

## 7.22 HARDWARE #340 is a separate deny-only poll candidate, not the active v0.6 response-auth fix — P0 boundary (2026-11-26 UTC01)

**Exact Hardware candidate:** PR #340 final docs/PR head a85eec4aa2ca1ad834f50031658f52aec51856e3; source/test merge commit a32c02311e4837669124c5b4b54fb1dfceed94fc. Its second parent is the current #283 head 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30; the final PR head is 45 commits ahead / 0 behind that parent. The final docs commit adds only the UTC01 ancestry handover.

### What this candidate does

Static source inspection of the #340 candidate shows both board sketches now:
1. De-energize/deny remote control before the synchronous poll HTTP wait.
2. Discard the register/poll response fields rather than accepting insert/target/configuration from an unauthenticated response.
3. Keep applyRemoteConfig as a compatibility sentinel that ignores the response and calls denyRemoteControl.
4. Select the Mbed TLS 4 PSA one-shot SHA-256 provider path and retain the Mbed TLS 3 legacy API path with explicit status/digest checks.

This is a **deny-only safety candidate**. It does not implement positive response authentication, an approved HMAC, or the CORE-owned authenticated register/poll envelope. The outbound request digest is not a substitute for response authentication.

### Exact final-head CI

- Quarantine append/readback [#45737856305](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856305): PASS.
- Poll preflight inhibit [#45737856314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856314): PASS.
- Mbed TLS compatibility guard [#45737856364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856364): PASS, but log explicitly says SIMULATED_ONLY=1, TARGET_BUILD_REQUIRED=1, COIN_ADMISSION_ENABLED=0.
- ESP8266 Arduino core 3.1.2 compile [#45737856422](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856422): PASS.
- ESP32 Arduino core 3.3.13 compile [#45737856339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856339): PASS.
- Full BlazePwifi build [#45737856635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856635): PASS, 26 successful jobs / 4 skipped. Skips are production signed APK import, prerelease publication, release publication and production-sign handoff.

The Mbed TLS guard is a source-extracted simulation, not an Arduino core 4.0.0 application compile. The Full build's ESP32 target compile is on core 3.3.13. HARDWARE #348 remains a separate branch and its Full run #45731176586 still fails because core 4.0.0 cannot find mbedtls/sha256.h. Do not transfer #340's guard result to #348.

### Separation from active v0.6

The active development branch remains blazepwifi-v0.6.0-audit-foundation at 2fbd2475e9f54878c316fa7cea2f228386b0e859. Its exact ESP32/ESP8266 sketches still contain no response_sig token, consume unsigned poll insert/target_nonce, and call applyRemoteConfig; the active CGI register/ping and poll bodies do not include response_sig (member endpoint signatures are not a poll contract). Therefore the active v0.6 source remains **not verified deny-only** and the P0 response-auth/actuation-influence finding remains open. PR #340 is not integrated into that branch.

### Required owner actions

- PHX-CORE publishes the versioned authenticated register/poll response envelope, canonical serialization, standard MAC/HMAC construction, controller/target binding, freshness/replay rules and mandatory nonempty key-provisioning contract.
- PHX-HARDWARE keeps the deny-only candidate separate until the approved contract exists, then implements the consumer on both boards.
- PHX-QA independently verifies missing, malformed, invalid, stale, replayed, wrong-controller, wrong-target, altered-config and positive vectors on both boards.
- PHX-MASTER records exact source/test and docs heads separately; no candidate promotion, source merge or contract invention.

CI/simulation is not physical acceptance. No coin pulse, relay/electrical recovery, LittleFS power-loss, 150 real power cuts or 30-device/24-hour soak is established by these runs. **PRODUCTION NO-GO.**
## UTC03 evidence note — #340 core-4 compile is real but not yet reproducible; #353 remains blocked — 2026-11-26T03:57:22Z

HARDWARE #340 now has an actual ESP32 Vendo sketch compile against ESP32 Arduino core 4.0.0: [run #45747192648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747192648), exact source/test SHA d1380acf80c0b631c5814d746dca36b2fad7a986. The final PR/docs head is f70f6af78c64ef86ba0f631faeb02b6cb6eb2725; the source/test SHA to final docs head comparison adds only PROJECT_HANDOVER.md and the UTC03 handover note. The ESP32 sketch blob is fc883d20ef76ec5521a5872a175ec73a16cf8cbe at both prior source/test SHA d3168ccb4959fe1eab718912fd04510ef7603253 and current source/test SHA d1380acf80c0b631c5814d746dca36b2fad7a986.

However, the two exact core-4 compile runs report the same Arduino CLI 1.6.0 and ESP32 core 4.0.0, yet their application binary SHA-256 values differ: prior run #45742944327 produced f9489e1df0d075cbfce549120c37af2778c53cb055f165c14a1d790623293c31; current run #45747192648 produced ea6bfb5fbf31f4fca3ed7942e92cede58b75c1d087cd74ac15414d9d568f0a2e. The dedicated core-4 workflow blob is 0598839f92831698a60bc8715df14db1c56b6fac. It uses arduino/setup-arduino-cli@v2, updates the live package index, installs core 4.0.0, and does not retain the resulting core-4 binary as a workflow artifact. No root cause is established. This is a reproducibility evidence gap, not proof of compromise or a failed compile.

The later final docs-head Full build [#45747758154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747758154) PASSes with 26 successful jobs / 4 intentional skips. The earlier source/test Full #45747199081 was cancelled. Full-build success does not replace the missing dedicated core-4 artifacts or establish bit-for-bit reproducibility.

HARDWARE #353 current source/test SHA is ed2f77d5924172881f27222cc26649f8f85abe6c and final docs head is 832692020a428ff4fe03a197a1bfce65b3f9316c, 27 ahead / 0 behind parent #352 2fa3b7db1161ddb531ed94bcf60617947fa1a7bd. The final docs commit adds only PROJECT_HANDOVER.md and the UTC03 handover note. Quarantine #45751177827 and Relay #45751177670 PASS. Full #45751177730 fails in validation job 139679141206 at Missing poll signature check; the 14 target/platform jobs and Android pass, while downstream simulation, update, signing, publication and candidate gates are skipped. The current source/test change adds source-extracted runtime-pin/ISR ordering mutations; no production .ino was changed in this PR.

Active v0.6 remains unauthenticated at register/poll. Both board sketches consume unsigned insert/target_nonce and call applyRemoteConfig; the CGI poll response has no response_sig. COE #26 still has a keyless sigOk=true bypass. No authenticated response contract is approved.

---

## 7.23 Firmware build provenance and reproducibility gate — P1 release evidence / production blocker (2026-11-26 UTC03)

A successful compile proves only that one exact source/toolchain tuple compiled. It does not prove that a second build from the same inputs yields the same firmware bytes, and it does not establish signing, physical acceptance or release readiness.

### Observed #340 evidence

- Source/test SHA d1380acf80c0b631c5814d746dca36b2fad7a986 and prior source/test SHA d3168ccb4959fe1eab718912fd04510ef7603253 contain the same ESP32 sketch blob fc883d20ef76ec5521a5872a175ec73a16cf8cbe.
- Both exact-source runs report Arduino CLI 1.6.0 and ESP32 core 4.0.0, but the binary hashes differ: f9489e1df0d075cbfce549120c37af2778c53cb055f165c14a1d790623293c31 versus ea6bfb5fbf31f4fca3ed7942e92cede58b75c1d087cd74ac15414d9d568f0a2e.
- The dedicated workflow file blob is 0598839f92831698a60bc8715df14db1c56b6fac. It installs a pinned ESP32 core version but updates the live package index and does not upload/retain the core-4 binary. The two core-4 workflow runs returned no retained artifacts.
- The final docs/PR head f70f6af78c64ef86ba0f631faeb02b6cb6eb2725 is two documentation-only commits beyond source/test SHA d1380acf80c0b631c5814d746dca36b2fad7a986. Full #45747758154 PASS is a separate matrix result; do not substitute its regular ESP32 artifact for the dedicated core-4 compile output.

### Required build provenance tuple

Before a firmware binary can be described as reproducible or promoted to a release candidate, retain the following for every build:

1. Exact source/test commit SHA, source tree SHA, each compiled source blob SHA and file mode; separately record final PR/docs SHA and every docs-only delta.
2. Exact workflow file blob SHA and run/job IDs.
3. Arduino CLI version and binary checksum; package-index URL and SHA-256; exact platform/core version; compiler, linker, bundled tool and transitive package versions plus checksums or a lock manifest.
4. Runner OS/architecture and immutable image/container digest; board FQBN, menu options, build properties, compiler flags, library versions and clean-build state.
5. Firmware binary, byte size, SHA-256, SHA256SUMS, machine-readable manifest, full compile log and artifact ID/retention location. Do not store secrets in the manifest.
6. Two independent clean builds from the same pinned inputs. Their output firmware bytes and SHA-256 must be identical. Preserve both artifacts and manifests until the comparison is independently reviewed.

### Failure classification and owner boundary

If any supposedly identical clean builds differ, classify the result as NONDETERMINISTIC / REPRODUCIBILITY UNVERIFIED, preserve both run IDs and hashes, and block artifact promotion until PHX-RELEASE identifies and pins the missing input or explains the deterministic build transformation. Candidate CI may remain green, but no release, signing or production acceptance may be inferred.

PHX-RELEASE owns workflow/toolchain pinning, artifact retention and reproducibility investigation. PHX-HARDWARE owns source/build intent and exact sketch identity. PHX-QA independently reviews the evidence. PHX-MASTER owns this cross-role contract only; it does not edit the owner workflow, re-run owner jobs, sign, publish or approve a release.

This contract does not close the separate authenticated register/poll response P0, durable financial state, migration, QA, native acceptance, 150 real power cuts or 30-device/24-hour soak. **PRODUCTION NO-GO.**



## 7.24 Active v0.6 coin-pulse sampling is ordered after a blocking poll — P0 loss risk remains open (2026-11-27 UTC01)

This is a source-level revalidation of issue #177, not a firmware fix or physical acceptance. Active branch `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` was fetched directly:

| Board | Sketch blob | Synchronous poll | First coin-pin sample |
|---|---|---:|---:|
| ESP8266 | `12c4bb82b6fddafe813674a0b5f692c1d3634073` | line 354 | line 357 |
| ESP32 | `29f1125d52ff474a0d028ad41f7af201be1f0f9d` | line 314 | line 318 |

Both `loop()` implementations call synchronous `post("poll")` before `digitalRead(runCoinPin)`. The issue #177 host C++ extraction reports a 3.5-second wait that misses an 80 ms active-low pulse while the relay remains energized; that is **SIMULATED** evidence, not a real coin-slot, relay-electrical or power-loss test.

**Required cross-role invariant:** a coin acceptor must not remain energized during a blocking network wait that prevents pulse capture. HARDWARE owns a reversible local intake-inhibit or nonblocking capture implementation and the electrical polarity review; CORE owns the authenticated, fresh, device/target/sequence-bound poll, receipt and durable disposition contract; QA independently verifies the same exact source SHA and negative/reboot/failure paths. Do not re-enable from unsigned `insert` / `target_nonce` fields, do not treat RAM-only ISR counts as durable credit, and do not invent `response_sig`. The existing deny-only #355 candidate is not integrated into active v0.6 and does not close this issue.

## 7.25 STORCHK-0674 physical-parent/holder guard is synthetic-only — issue #34 remains NOT TESTED (2026-11-27 UTC01)

HARDWARE-owned draft PR #356 current docs/PR head is `5c0f58db6a2df74390ca00d946c594ec417942ab`; source/test correction `9fad1abd1eab8bcb2caadff6901999df4be30944`. The helper resolves sysfs parent relationships and rejects candidate/parent block nodes with active `slaves` or `holders`; tests use synthetic mountinfo and fake sysfs only.

- Expected RED for active-holder topology: #45923702833, job 140260078848.
- Exact-source focused push #45923785751, job 140260350436 — PASS.
- Exact-source focused PR #45923791729 — PASS.
- Final docs-head focused PR #45923906079 — PASS.
- Final docs-head Full #45923906088 — FAILURE. ESP32 build job 140260850690 fails because `mbedtls/sha256.h` is unavailable; validation job 140260850694 also fails. 12/13 firmware/platform jobs and Android pass; downstream simulation, update, candidate, signing and publication jobs are skipped.

This establishes only a synthetic topology guard. It does not prove separate enclosure/controller, physical media independence, disposability, actual mount safety, flash durability or power-cut behavior. Physical issue #34 remains NOT TESTED; no mount, block write, power cut, flash or customer install was performed.

---

## UTC09 interface-boundary refresh — 2026-11-27

P0 #177 remains OPEN. The active v0.6 audit foundation is 2fbd2475e9f54878c316fa7cea2f228386b0e859; its synchronous poll-before-first-coin-sample behavior remains unresolved. Hardware owns local edge capture, strap-safe GPIO validation and deny/inhibit behavior. CORE owns the authenticated register/poll response, receipt identity and pending disposition contract. QA owns independent semantic and controller-parity assertions. MASTER owns only the cross-role interface contract and evidence matrix.

Hardware #358 adds an ESP8266 boot-strap GPIO guard and a corrected test fixture. It does not implement the CORE poll-response signature, receipt/disposition semantics, or resolve P0 #177. Its Full CI still fails at the missing poll-signature contract. Related #357 Full validation and Native synthetic journal gates remain failed at QA/CORE-owned parity assertions. Do not invent config_revision or response_sig fields, and do not add an unsafe clearPending callsite merely to satisfy a literal assertion. Keep coin and relay admission deny-only until CORE and QA publish and independently verify the semantic contract.

No physical GPIO/relay/coin test, power-cut test, 30-device/24-hour soak, protected signer/anti-rollback witness, or production financial migration was executed or approved in this refresh.