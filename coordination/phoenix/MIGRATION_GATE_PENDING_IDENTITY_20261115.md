# PHX-MASTER migration hold — pending identity persistence parity

Date: 2026-11-15 UTC14  
Scope: PHX-MASTER coordination only; no product source or destination edits.  
Status: **DRAFT REVIEW ONLY — PRODUCTION NO-GO**.

## Exact inspected candidates

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Named development branch: `blazepwifi-v0.5.3-development` (branch existence checked; SHA not independently resolved in this review).
- Master draft #288 pre-change: `555019a8f13962606d474066c3a66d0869606939`.
- HARDWARE stacked #305: `8029c583f185736e770e3412308416d5ac87c976`, based on #304 `d5af6f7b18fcc8043f0dcbbb05482bb630d438aa`.
- HARDWARE stacked #306: `94b5247a9d457baf8c2eecc5a0b4ced5c2783812`, based on #305.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- Existing COE integration draft #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`. **Do not replace its staged implementation blindly.**

## Source-inspected trust-boundary mismatch

#305 checks the `strlcpy` returned source length for 17-byte nonce and 33-byte target persistent fields, rejecting values over 16 and 32 characters before LittleFS open. #306 additionally rejects nonce or target shorter than eight characters before any LittleFS operation, aligning `savePending()` with its reboot parser. Both ESP32 and ESP8266 sketches are modified; the owner-supplied fake-LittleFS regression suite grows from 13 to 15 to 17 cases per board. These are source/diff observations, **not independent execution**.

This sequence is stacked, not independently mergeable without its parents. A destination accepting an older `savePending()` could acknowledge a record that later reboots as corrupt, or persist an identity truncated relative to the pre-reboot in-memory identity. The exact destination firmware blobs, file modes, licenses, imports, test identities and whether stronger guards already exist have **not** been established; migration remains blocked.

## Required independent acceptance matrix

1. PHX-HARDWARE and independent PHX-QA record the exact source and proposed destination **Git blob SHA and mode** for each ESP32/ESP8266 sketch, its journal parser, build imports, licensing, and corresponding regression files; compare all against COE #26 and any newer stacked destination candidate.
2. Inject nonce/target lengths **0, 7, 8, 16, 17, 32, 33** separately. Assert the documented per-field capacity, no file open/create/remove/rename for rejected values, no coin/relay/ACK admission, and exact identity equality across reboot for accepted values.
3. Inject short writes, failed readback, failed temporary removal, rename/rollback failure, and conflicting `pending.new` / primary records. Verify recovery-required state, no silent journal loss and no fabricated ledger ACK. Separate simulated fake-filesystem checks from physical brownout evidence.
4. PHX-CORE owns any shared protocol or target-length contract changes. PHX-MASTER does **not** change shared schema; PHX-QA must independently review source-linked tests. The broad Rental destination-prefix overlap remains explicitly non-copyable.
5. Run Master 18-test suite at the new exact SHA, plus destination exact-head CI. An observed HARDWARE #306 run `43725320271` was completed/success while `43725320234` was in progress at inspection; these do not certify hardware or COE integration. COE #26 associated workflow records were queued. No Master exact-head workflow was returned at the preceding head.

Private Drive registry filename search did not locate the v11 registry; use authorized private folder traversal without publishing identifiers. Keep all original Git history and existing staging. Protected signing, independent anti-rollback witness, crash-atomic durable finance, reversible migration tests, native acceptance, 150 real power cuts, 30-device/24-hour soak, independent QA and owner authorization remain mandatory. **No merge, release, flash, payment action, secret provisioning or production approval.**
