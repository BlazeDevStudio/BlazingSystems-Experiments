# PHX-QA independent coordination recipient regression

**Status:** IN_PROGRESS / EXPECTED RED (not a release gate or completed native test).  
**Owner:** PHX-QA · **Task:** BLAZE-COMMS/1 recipient validation · **Priority:** P2 coordination/protocol integrity.  
**Source owner:** PHX-MASTER [PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288), pinned base `add087f84a2fda6f6aedf9938e38394f2b2c27be`.  
**Real verifier source blob:** `a8a989964c45ab9aef5719e8d17ba3f6fc66e773` (`coordination/phoenix/verify_coordination.py`).  
**This branch:** `qa/phoenix-comms-recipient-regression-20261115` (draft, unmerged).

## Exact audit finding

The uploaded QA instructions define BLAZE-COMMS/1 `to` as a **role ID or ALL**. At the checked source blob, `validate_envelope` only tests that `to` is a nonempty string. A message addressed to an unknown role (e.g. `PHX-UNKNOWN`) or a list containing an unknown role can therefore pass recipient validation. This is an *audit finding based on actual GitHub source inspection*, not a demonstrated production financial exploit.

## QA-owned, narrow test

`test_recipient_contract.py` imports the **actual** PHX-MASTER module from the checkout and mutates its JSON example. It checks a valid `ALL` and a valid PHX-QA recipient, then asserts malformed/unknown recipients cannot pass. No copy of production validation logic is embedded in the test. Master owns the validator; QA does **not** modify `coordination/phoenix/`.

Run from repository root:

```sh
python3 -m unittest discover -s tests/phoenix_coordination -p 'test_*.py' -v
```

**Expected before Master fix:** the unknown-recipient negative cases are RED. **Test execution:** NOT RUN until evidence is recorded on the exact QA head. If the test fails for import/checkout reasons, classify INCONCLUSIVE rather than as a reproduced security RED.

## Handover / rollback / safety

This work is stacked on the current Master **coordination-only** draft branch. That branch lacks the active BlazePwifi development `docs/handover/CURRENT_STATE.md` and `CHANGE_LEDGER.md` paths; do **not** create counterfeit snapshots or rewrite a different branch's history. This README and PR comments are the branch-local record, as allowed by the QA prompt when the authoritative handover cannot be synchronized. The live [#172 control plane](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) remains the cross-role inbox.

Rollback: close this draft without merge or discard the isolated QA branch. No financial/core/device/firmware source, account, hardware, cryptographic signer, production deployment or installer touched. All P0 money, protected anti-rollback witness, 150 physical power cuts, 30-device 24-hour soak, migration and final release gates remain **NO-GO**.

**Next exact action:** Write the fixture, execute on a source-exact checkout, document actual PASS/FAIL/UNKNOWN, ask PHX-MASTER to tighten recipient validation and rerun the same tests at the fix commit.
