# PHX-MASTER UTC18 — hosted ImageBuilder user-namespace blocker and COE hardware staging provenance audit

**Disposition:** BLOCKED / REVIEW-ONLY / PRODUCTION NO-GO  
**Owner scope:** `coordination/phoenix/` only  
**No subsystem source, destination staging, signing, hardware, or financial state was changed.**

## 1. Exact repository and candidate identities

| Reference | Exact identity | State |
|---|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | Current default HEAD |
| Experiments development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` | 293 commits behind main; not promoted |
| PHX-MASTER #288 before this audit | `phoenix/master-coordination@0b5adc046d6da13e3dd1913e8658e96e712f2bea` | Open/draft |
| COE main | `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` | Structure-only baseline |
| COE integration #26 | `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12` | Open/draft; five workflows queued |
| COE RELEASE #31 | `phoenix/release-imagebuilder-failclosed-20261115@d0491517388479aa44c6c0ede8fc876f0be5950c` | Open/draft, child of #26 |
| HARDWARE parent #317 | `phoenix/hardware-clear-pending-marker-match-20261117@d3acdd8f60fb42bbcc6e8dbd7bdb3634fc496c78` | Open/draft; source/test SHA `1f263114fe003a930028b7fa9610655b03336614` |
| HARDWARE child #318 | `phoenix/hardware-poll-inhibit-settle-20261117@be371b03a36306a7691b411bf1b29da60b916646` | Open/draft; divergent, mergeable=false |

The machine-readable route manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`, with PHX-MASTER destination `null`.

## 2. COE #31 — least-privilege namespace trial is source-present but host-blocked

The UTC17 Master decision is now implemented as a RELEASE-owned trial. Exact current blobs:

| File | Blob |
|---|---|
| `tools/run_imagebuilder_sandbox.py` | `7bf7ec5b2512704aca52bedd8ccc7067786533af` |
| `tools/package_appliance_firmware.py` | `062fd2638f22daa9656bfdafd8003b640ca1c579` |
| `tools/test_package_appliance_firmware.py` | `b40e6be6c8646b315ed97bc6c8646b315ed97bc6` |
| `.github/workflows/release-imagebuilder-sandbox.yml` | `2a865da751e00175bfd18687323899730659799b` |

The runner now requires the invoking non-root identity, uses bubblewrap `--unshare-user --uid 0 --gid 0`, and no longer depends on sudo, SUDO identity variables, or newuidmap/newgidmap. The generated operator wrapper dispatches through this runner. The workflow forces `PHX_REQUIRE_BWRAP=1` on `ubuntu-24.04`.

**Exact-head runtime result:** [run 44147379837](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379837), job `134266101493`, FAILED. The runner reached bubblewrap but the host denied UID-map setup:

```text
bwrap: setting up uid map: Permission denied
RELEASE-BLOCKED: sandbox did not create its ownership probe
```

The job ran 53 tests and reported 20 failures because the real namespace could not be established. The symlink-confinement and delayed-write timeout integration paths were not reached. This is a host capability blocker, not sandbox acceptance and not a reason to weaken the runner.

Scoped exact-head results:
- [Shared/hardware run 44147379880](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379880): SUCCESS — validation, 10/10 profiles, shared contracts and both board compile/artifact jobs; scoped only.
- [Case-collision run 44147379865](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44147379865): SUCCESS; scoped only.

**Master disposition:** stop further runner-code experimentation on this hosted runner until the infrastructure owner supplies an approved disposable no-secret runner with the required unprivileged user-namespace capability. Do not reintroduce sudo, mapping helpers, broad subordinate-ID ranges, or an unsandboxed Make fallback. Any new runner must prove host ownership, nested-symlink sentinel confinement, real timeout/process-group cleanup, and fail-closed behavior on the exact same candidate SHA. Because the runner uses a read-only host-root bind and `--share-net`, the host remains readable and the network remains shared; this is write confinement only, not confidentiality or network isolation. Do not expose secrets/customer data to untrusted build inputs.

## 3. COE #26 Hardware staging is not source-equivalent

The manifest routes the Experiments firmware into `Hardware/esp32/` and `Hardware/esp8266/` as selective-review candidates. Exact current #317 source blobs do not match the staged #26 destination blobs:

| Firmware | Experiments #317 source blob | COE #26 destination blob | Result |
|---|---|---|---|
| ESP32 | `6399b471460effe7817ec849b2f6a9ca271fbc57` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | Different |
| ESP8266 | `b0aba5fb9d18a6c3a51f04eed3a52c1e85074d7b` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | Different |

This is a behavioral divergence, not merely a formatting difference:

- Current #317 source keeps poll admission default-deny: `acceptPollResponse()` returns false and clears positive insert/target state. The `applyRemoteConfig` routine is dormant (one definition, no call site in each current sketch).
- COE #26 destination retains `bool sigOk=true` defaults and active `applyRemoteConfig(r)` call sites (three occurrences per sketch).
- Current #317 source makes POST `/quarantine/clear` return 403 and preserves `/quarantine.log`. COE #26 destination deletes the log and returns HTTP 200.
- COE #26 `Hardware/README.md` still tells operators that quarantine records can be cleared through the setup AP, contradicting the current source safety contract.

The destination must not be treated as a current firmware import or a compatible fallback. Do not merge the old behavior back into the current source.

## 4. Test identity and license/notice provenance are incomplete

The current source QA entrypoint `experiment/openwrt/BlazePwifi/tests/controllers.sh` exists at blob `f7896647713d6bf8034ff48ed19b6383e4dedea0`. The corresponding routed target `Pisowifi/tests/controllers.sh` is absent at COE #26 (404).

COE #26 instead contains `Hardware/tests/test_firmware_hardening.sh` at blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`. It is a different file/path and still asserts a positive `|poll|` signature formula and the `/quarantine/clear` route. It is not an import-equivalent replacement for the source test tree or the current default-deny contract. Current source #317 Full run [44147243144](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44147243144) fails in the QA-owned legacy poll-signature assertion; focused [44147243190](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44147243190) and [44147243095](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44147243095) pass. The child #318 exact current head has no workflow run returned.

License/notice provenance:
- Source subproject `experiment/openwrt/BlazePwifi/LICENSE` is MIT at blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- COE #26 `Pisowifi/LICENSE` has the same blob, but it is in a sibling subtree.
- No `Hardware/LICENSE`, `Hardware/NOTICE.md`, COE root `LICENSE`, or COE root `NOTICE.md` was found at #26. The source root `NOTICE.md` is blob `f6d92cd21465312be5993631fe26977219be0fb9` and is not present at the destination root.

This is an unresolved license/notice applicability question, not a legal conclusion. Do not assume a sibling `Pisowifi/LICENSE` automatically covers `Hardware/`; the destination owner must explicitly map and preserve the applicable notice/license provenance before any move or integration.

## 5. HARDWARE #318 is a divergent child stack and remains held

Current compare of child #318 `be371b03...` against parent #317 `d3acdd8f...` is **DIVERGED: 49 commits ahead / 40 behind**, merge base `3ed38225d02c4d8dde9df5b5f483bfbeb7deccc3`, GitHub `mergeable=false`.

Both PRs change the same ESP32 and ESP8266 sketch paths, but their exact sketch blobs differ. #318 also adds child-only poll-loop/timeline labs and its own workflow. No current-head workflow run was returned for #318. This is not safe to resolve by automatic rebase, cherry-pick, force-push, or merge. PHX-HARDWARE must propose a stack direction; PHX-QA must review the exact selected source/test SHA; PHX-MASTER will reconcile the stack and role index after owner evidence. Until then, keep #317 and #318 separate and draft.

## 6. Remaining independent blockers

- The COE packager still emits invalid IPv6 ULA `fd00:db8:blaze::/48`; the ULA P0 remains separate from the sandbox and migration findings.
- COE #26 still has five queued workflows and zero completed integration evidence.
- QA #292 has no PR-triggered run returned.
- The canonical private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain inaccessible through the exposed connector; older Library snapshots were not substituted. No private registry contents or identifiers were published.
- Cleanup issue #266 remains open and is a checklist, not proof that cleanup or QA gates are complete.
- No real OpenWrt ImageBuilder artifact, UCI/netifd acceptance, physical hardware acceptance, signer/freshness witness, durable financial migration, 150 power cuts, or 30-device/24-hour soak is established.

## 7. Next exact human/owner actions

1. **Infrastructure owner:** authorize/provision a disposable, ephemeral, no-secret runner with unprivileged user namespaces enabled and an explicitly reviewed egress policy. No shared runner broad subuid/subgid grants.
2. **PHX-RELEASE:** keep #31 blocked on the current hosted runner; after infrastructure approval, rerun the exact-head real-bubblewrap symlink and timeout tests without fallback.
3. **PHX-QA:** independently verify #31's one-ID mapping, host ownership, sentinel confinement, timeout cleanup and fail-closed path; repair the legacy #317 poll-signature fixture without weakening default-deny.
4. **PHX-HARDWARE:** submit an explicit #317/#318 stack proposal; do not rebase or merge until the exact source/test candidate is agreed.
5. **COE integration owner:** reconcile each #26 Hardware source/target blob, restore current test identities, resolve license/NOTICE applicability and update the stale Hardware README before any selective migration.
6. **PHX-CORE / PHX-RELEASE:** resolve durable site-specific RFC 4193 ULA provisioning and validate the generated UCI.
7. **Registry custodian:** restore authorized access to private Drive v11 and newer corrections.

**No source/destination file was moved or copied. No role-owned source branch was modified. No merge, release, signing, secret provisioning, firmware flash, physical test, real payment, or financial migration occurred. PRODUCTION NO-GO.**
