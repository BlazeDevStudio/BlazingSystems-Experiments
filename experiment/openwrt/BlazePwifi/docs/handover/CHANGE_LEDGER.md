## 2026-11-26 UTC05 — PHX-HARDWARE active-v0.6 poll intake deny

**State:** committed / focused CI VERIFIED / Full integration BLOCKED / physical NOT TESTED.

- **Task:** #177 P0 synchronous poll can miss coin pulse while acceptor relay remains energized.
- **PR/branch:** #354 DRAFT, `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`, based on active v0.6 `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- **Source commit:** `dc619870a096f01d0d1cba24f0bf3c0c981a08d2`; corrected test matcher `f381f6d38699e953b32e1d0c603524bc6da86541`.
- **Files:** both ESP sketches; `firmware_source_extract.py`; `poll_preflight_inhibit_lab.py`; `remote_config_deny_lab.py`; focused workflow; narrow handover.
- **Behavior:** deny controller/coin/relay/LED, apply logical OFF, discard register/poll responses, disable remote JSON parsing, and remove automatic coin POST/retry/clear. Preserve pending pulse/nonce/target and journal state. No shared protocol or finance code changed.
- **RED:** #45764293566 job 139721362633 failed on test-only head 95a32 because active loop still contained pending disposition.
- **GREEN focused:** #45765161847 job 139724228280 PASS on docs head 2bd7a25c2a00e74079b83a3953b190bdd929a11e. Board source-extracted tests, polarity harness, pending-evidence preservation and deny-only remote-config checks passed.
- **Full validation failure:** #45765161859 job 139724399274 stopped at handover_gate.sh because PROJECT_HANDOVER/CURRENT_STATE/CHANGE_LEDGER were older than source/workflow changes. This entry and canonical current-state refresh address that omission; a new exact-head Full run is still required.
- **QA-owned test blocker:** #45765161848 job 139724228753 failed at `tests/v060_vendo_sequence_contract.py:20` requiring `clearPending(true)` and `clearPending(false)` callsites. This candidate intentionally has no automatic pending disposition until CORE's authenticated event receipt contract is approved. QA must revise its owned assertion; Hardware did not edit it.
- **Physical status:** relay electrical polarity, coin-slot cutoff, electrical pulse/recovery, LittleFS power loss, 150 power cuts, 30-device/24-hour soak all NOT TESTED. HARDWARE ACCEPTED NO; PRODUCTION READY NO.
- **Next:** PHX-QA reviews/updates the sequence contract; PHX-CORE publishes authenticated register/poll and receipt/disposition contract; PHX-HARDWARE reruns Full exact-head. No flash, live money, signing, migration, merge or deployment.

