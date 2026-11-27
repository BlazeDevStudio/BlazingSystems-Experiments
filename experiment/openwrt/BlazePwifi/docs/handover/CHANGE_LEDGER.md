

## PHX-HW-20261127T19Z-OUTPUT-SEQUENCE-LAB-MODULE-SPLIT

- Role: PHX-HARDWARE; tracking: cleanup-first #266 / Hardware #177 (no ownership transfer).
- Branch: phoenix/hw-output-enable-lab-modules-20261128-utc19; parent DRAFT #365 at e65b0b895af9c3fc9f21ebe9a68b6ee044080ee.
- Source/test commit: ff73702adf6fb958c9f21ebe9a68c908ee829ea4.
- Change: split output-enable sequence lab into source-contract/mutation helpers and a C++ host harness; retain the original entry-point command and all existing cases.
- Workflow: .github/workflows/phx-hw-active-v06-poll-intake-deny.yml now watches both new modules and this role branch.
- Test status at commit: NOT RUN on the new exact SHA; PR-triggered CI required. Parent #365 evidence is not transferred.
- Physical GPIO/relay/polarity, coin pulse, power-cut and soak acceptance: NOT TESTED. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.
- No production sketch, API, finance, QA-owned test, COE destination, secret, migration, signer, flash, reset, merge or deployment changed.
- Updated UTC: 2026-11-27T19:31:19Z.