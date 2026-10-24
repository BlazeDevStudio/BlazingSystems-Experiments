# BlazePwifi handover and change-control policy (mandatory, v0.6.0 onward)

**Owner decision:** 2026-10-08, Asia/Manila. **Status:** active on the v0.6.0 development branch. **Purpose:** any new maintainer or ChatGPT conversation must be able to resume safely without guessing, repeating finished work, assuming pending CI passed, or overlooking a data/security hazard.

## Canonical source of truth — read this order, every time

1. `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` — the **top CURRENT STATUS** block supersedes older archived sections inside the same file.
2. `experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md` — authoritative current work tree, unresolved issues, exact tests, branch/PR, approved decisions and **NEXT EXACT ACTION**.
3. `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md` — a chronological append-only audit of meaningful changes including failures, abandoned attempts, fixes and retests.
4. This `HANDOVER_POLICY.md` and `experiment/openwrt/BlazePwifi/AUDIT.md` — constraints, threat model and release gates.
5. Latest dated `docs/handover/YYYY-MM-DD-*.md` checkpoint — **historical evidence**. Dates alone are not a freshness signal; cross-check the active branch and live state.
6. Original source, commit history, PR diffs, latest **exact-sha** GitHub Actions run and release assets — all claims must be reverified.

**Conflict resolution:** source/Actions/release API evidence overrides stale prose. The newest user-approved instruction overrides older requirements only on dimensions that are explicitly changed. Preserve untouched constraints and add a reconciliation entry explaining any conflict. Do not silently treat a different branch's green run as approval.

## Mandatory continuous transaction log — no unrecorded work

Every meaningful code/config/UI/security change, test correction, discovery, design decision, failure, canceled run, blocker, migration, version change, artifact, and publishing attempt **must** be written into the handover *in the same working session*. Do not leave a new-chat maintainer to infer the state from assistant replies. "Meaningful" includes changes to a command, PR state, test contract, security control, balance calculation, Android signer, or release gate; not each read-only search.

**Write order:**
1. Before writing code, enter `CURRENT_STATE.md` **IN PROGRESS** with work item ID, intent, affected surfaces, hazards, success/failure proof, and rollback path.
2. Apply a bounded source change on an isolated branch. For each logical change, append a dated `CHANGE_LEDGER.md` entry with issue ID, exact files, returned commit SHA(s), state `in_progress / committed_untested / failed / validated / released / blocked`, objective evidence link and next exact action. Never call untested work done.
3. Update `CURRENT_STATE.md` and the top of `PROJECT_HANDOVER.md` **at each meaningful transition**: after source write, test result, error, fix, canceled run, branch merge, artifact verification or release. Record uncertainty honestly. Prefer the source-code commit before the documentation-sync commit; link it. A documentation synchronization commit becomes the checkpoint.
4. Only after handover synchronization may an additional code change be considered ready for a branch PR gate. CI detects implementation commits newer than the latest handover checkpoint.
5. Do not leave an unfinished multi-step operation with a false completed label. An interrupted attempt remains `in_progress` or `blocked`, with the safest resume/retry. Keep failed/outdated evidence and explain supersession, do not erase it.
6. End any completed session with a copyable, **task-specific new-chat prompt**, containing exact repository, branch, PR, current live-state path, what's proven, what's not and one next action.
7. When new workflows/projects become relevant (Windows SoftTimer, Standalone Rental, EasyMode, ESP, Android), log their exact repository path and which version/branch owns them. Do not cross-edit standalone profiles or previously shipped releases without authorization.

## Minimum change-ledger record

Each entry MUST contain:
- `ID` + local date/time (Asia/Manila) and `scope`.
- `status` (not silently promoted to success) and `priority` (P0 money/security/data loss, P1 service/lock-bypass, P2 UX/compatibility, P3 documentation).
- why, precise paths and branch, exact code commit SHA or explicit `not committed`.
- test/reproduction and exact workflow run ID **with conclusion and HEAD SHA**, not just "CI green"; include failing job/step if failed.
- reversible deployment/rollback/migration concerns, blockers, dependency owners and data-integrity impact.
- one unambiguous `NEXT ACTION` (file/function, command/test, expected outcome). A link to a PR alone is not an actionable next step.
- new-chat Audit & Reconcile prompt at checkpoint milestones.

## Required continuity for the current business systems

- **Accounting is server-authoritative and durable:** no duplicate/lost coin credit, transaction replay, time drift, invalid resets, silent balance conversion, or unlogged migrations. Prevent P0 changes from shipping on simulation alone; real coin/power-cut tests are mandatory.
- **BlazePisonet Windows SoftTimer:** one-slot-many-PC and one-to-one both remain supported, any COM/device binding, correct paid seconds and deterministic offline/reconnect authority, installer EXE not PS1 substitute; code lives in `experiment/windows/BlazePisonet-SoftTimer`.
- **BlazeRental:** distinguish **Device Owner factory-reset provisioning** from **lower-security already-installed binding**. A QR is not evidence of enrollment success. Enforce package, SHA, permanent signing certificate and TLS pin; normal APK install is not a substitute for Device Owner. Maintain an admin recovery procedure that cannot be triggered by a renter.
- **Full versus Standalone:** active Full tree is `experiment/openwrt/BlazePwifi`; `profiles/standalone-rental` and its separately published releases must not be modified inadvertently. Same license and release names do not imply binary equivalence.
- **Network/installer:** OpenWrt/Ruijie/Orange Pi/PC BIOS+UEFI builds, VLAN/bridges and remote VPN admin survive upgrade/rollback; default remote listener not exposed on WAN.
- **Security:** private signing keys, passwords, shared secrets, recovery files, personally identifiable/confidential business data must not appear in public Git, PR comments, CI logs or screenshots. Secrets live only in protected secret storage; disclose public certificate fingerprint if necessary, not secret material.
- **UX:** no hidden failure behind decorative success states; no false live data. Offline-first, responsive and usable with a keyboard; avoid a stale HTML wrapper masquerading as a native Android launcher.
- **Release:** never tag a `0.5.3` build as `0.6.0`. A versioned production release requires versionCode/migrations, exact green full CI, matching signed APK/rescue, checksums, installers, verified physical acceptance and provenance. Any skipped critical gate blocks release.

## Mandatory >=200 MB artifact storage — owner-directed Google Drive destination

**Owner-approved 2026-10-24:** all Blaze coin-operated ecosystem files **200,000,000 bytes or larger** (200 MB, inclusive) are to be placed in the designated Google Drive folder as part of build/release/archive handoff: https://drive.google.com/drive/folders/15jHh7-ZFcsdIkRY3YOk2XxRxzkDEcd-g

Read and follow [LARGE_ARTIFACT_DRIVE_POLICY.md](LARGE_ARTIFACT_DRIVE_POLICY.md) **before** creating, publishing, archiving, deleting or reporting a qualifying large file. Record actual byte size, original source/build provenance, SHA-256, verified Drive file ID/link and security/release impact. Treat upload and full-byte verification as distinct gates; a Drive policy entry is not evidence of an upload. Do not delete originals or publish secrets, customer financial records, or improperly licensed material. Provisioning the authorized uploader and transferring the backlog are separate pending operations; current CI, signing, financial durability and real-device release gates remain unchanged.

## Test and CI handover freshness gate

`tests/handover_gate.sh` is the repository consistency check. In CI, checkout must fetch full history. It requires all three canonical files and checks that the most recent meaningful source/workflow modification is **included in or precedes** the last canonical handover update. A code edit made *after* the latest documentation checkpoint fails. This is a safeguard, not proof that a document is factually complete; reviewers still verify the ledger against file diffs and exact run IDs.

Tests and changes **must not be falsified to pass the gate**. Document expected new checks, fix actual behavioral problems, and run the corresponding regression.

## New-chat protocol (copy/paste)

```text
@GitHub Continue the sensitive BlazePwifi v0.6.0 work in BlazingSystems/BlazingSystems-Experiments.
READ FIRST: experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md (top CURRENT STATUS);
docs/handover/CURRENT_STATE.md; docs/handover/CHANGE_LEDGER.md;
docs/handover/HANDOVER_POLICY.md; AUDIT.md. Use the current PR/branch/CI evidence,
not historical dates or claims alone. Compare actual commit SHAs and recent Actions.
Follow CURRENT_STATE.md NEXT EXACT ACTION; do not change shipped tags, signer,
standalone source, accounting balances, or accepted security policy without proof.
Before EACH meaningful source change write an IN PROGRESS handover entry, then update
the canonical state and append the ledger after the change and every test result.
Do not call v0.6.0 released until exact-SHA, signed artifacts, migrations, recovery
and hardware acceptance all pass. If interrupted, leave a precise safe resume point.
```
