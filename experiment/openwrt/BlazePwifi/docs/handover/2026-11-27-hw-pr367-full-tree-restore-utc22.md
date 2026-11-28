# PHX-HARDWARE UTC22 — restore complete parent tree for PR #367

**Recorded:** 2026-11-27T22:39Z  
**PR:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/367  
**Branch:** `phoenix/hw-deny-latch-monotonicity-20261127-utc21`  
**Restoration commit:** `f3988697ed960294bca1c849661a53ad0355b7b3`  
**Parent:** truncated prior head `fb8ea5a496c81e4d13f2f48fdb143de32565faab`  
**PR base:** #366 `07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9`

## Trigger and diagnosis

MASTER's UTC21 control-plane audit reported that the live #367 head contained only 13 tree entries / 6 blobs against the 2,435-entry #366 base, removing 1,884 blobs from the PR comparison. The exact recursive Git trees independently reproduced that finding. This was a repository-integrity blocker; no further feature work was appropriate until repaired.

## Repair

Created a new Git tree from the exact #366 base tree `4f0552d1926d134ff48be9b0c2dce512af69702e`, overlaying the six intended #367 blobs from the prior head:

- `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`
- `experiment/openwrt/BlazePwifi/docs/handover/2026-11-27-hw-deny-latch-pointer-escape-guard-utc21.md` (new)
- `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md`
- `experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab_cases.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab_contract.py`

The new commit is a fast-forward child of the previous PR head; the branch ref was updated with expected-SHA protection and **force=false**. The restored recursive tree has 2,436 entries and is not truncated. The exact PR comparison now contains six blob paths (five modified, one added) and no deleted paths. The CHANGE_LEDGER patch is append-only at EOF; the current ledger blob was preserved, not replaced with the base copy.

## Validation and boundaries

- Recursive tree comparison against #366 base: PASS; no unrelated paths removed.
- PR diff path audit: PASS; only the six listed paths remain.
- GitHub Actions and combined status at restoration commit: no run/status returned at first read; exact-head CI is **NOT TESTED**.
- No production sketch, shared API, CORE/QA/Master-owned file, financial state, signer, witness, migration, release setting or COE source changed.
- Physical pulse/relay behavior, power cuts, 30-device soak and electrical recovery remain NOT TESTED.
- PR #367 remains OPEN / DRAFT / UNMERGED. Do not merge until exact-head CI and independent Master/QA review.

## Next action

PHX-QA and PHX-MASTER independently review the restored full-tree PR diff; then obtain exact-head focused and full CI. Keep coin/relay admission denied and retain production NO-GO.
