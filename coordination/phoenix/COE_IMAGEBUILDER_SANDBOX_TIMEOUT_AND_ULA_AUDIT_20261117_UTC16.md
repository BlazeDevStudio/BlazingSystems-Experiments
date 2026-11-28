# PHX-MASTER UTC16 — COE ImageBuilder sandbox timeout, ULA hold, and current hardware fixture audit

**Date:** 2026-11-17 UTC16  
**Role:** PHX-MASTER  
**Scope:** `coordination/phoenix/` only  
**Disposition:** P0 integration blockers remain; PRODUCTION NO-GO  
**No Codex:** No Codex app, CLI, API, agent, workflow, or delegated Codex execution was used.

## 1. Exact refs re-read

| Ref | Exact SHA |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| PHX-MASTER `phoenix/master-coordination` before this audit | `5e11daf8d9a65659e92030df94b212eb9e28d21f` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| COE RELEASE PR #31 | `9c2bebf50030c03bc4dd1e827e050863ba482eab` |
| Experiments HARDWARE PR #317 | `839c21877c27c893e2efc73b3afe7c48e1fcfa4e` |

Experiments main and development refs were read from live branch endpoints. The v0.6 audit-foundation ref remains comparison-only and is not promoted by this audit. COE main remains the structure/scaffold baseline; #26 is still a separate draft integration candidate.

## 2. Correction to the prior operator-boundary finding

The prior UTC14/UTC15 Master audits correctly found that the generated operator wrapper did not invoke the sandbox runner at those exact source heads. **That source-state finding is superseded by the current COE #31 head.**

Current source identities:

| File | Exact blob |
|---|---|
| `tools/package_appliance_firmware.py` | `f819ef1cd5265ff026e8a98ad9541c36ed087617` |
| `tools/run_imagebuilder_sandbox.py` | `ce098e44e847c265604e3dbb5d8df505025dd0ad` |
| `tools/test_package_appliance_firmware.py` | `a5310f90d0405afeeedb2a5981700945f4270aad` |
| `.github/workflows/release-imagebuilder-sandbox.yml` | `151c052f36664c1cb70138e7f135a5570909e09e` |

The current generated wrapper validates the runner file and its expected digest, requires the sandbox-active marker plus a regular ownership-probe file for an already-contained invocation, and otherwise re-enters through:

```sh
exec sudo -- python3 "$RUNNER_PATH" --cwd "$SANDBOX_ROOT" --builder "$BUILD_DIR" --wrapper "$SCRIPT_PATH"
```

The runner uses bubblewrap with a read-only host-root bind, a writable bind for the ImageBuilder workspace, a temporary `/tmp`, and a cleared child environment. It explicitly uses `--share-net`: **network isolation is not provided or claimed**. The filesystem write-boundary claim is not a confidentiality guarantee.

The test file now includes both an operator-entrypoint routing regression and an external-sentinel symlink-write regression. This is a source-level correction; it does not yet establish successful end-to-end runtime verification.

## 3. Exact-head sandbox CI is incomplete

COE #31 exact-head sandbox run [44125258197](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44125258197), job `134197585782`, concluded **CANCELLED**. The workflow sets `timeout-minutes: 20`. The log starts the packaging suite, records 15 tests as `ok`, then records `The operation was canceled` at the 20-minute boundary. No test failure assertion was emitted and no final runtime-pass result exists.

The last visible completed test was `test_generated_build_script_passes_posix_shell_syntax_check`. The next test in unittest's sorted method order is `test_generated_wrapper_contains_make_created_symlink_write_to_host`; it is the first unreported test, **not a proven root cause**. Logs do not contain a stack trace or test-specific timeout proving which operation stalled.

A source-level observability gap is confirmed:
- The test helper calls `subprocess.run(command, ...)` without a per-invocation timeout.
- The sandbox runner calls `process.communicate()` without a post-start timeout.
- The workflow has a 20-minute whole-job timeout, so a stuck child can consume the full job budget without identifying the test or subprocess phase.

**PHX-RELEASE action:** add bounded per-invocation and runner-process timeouts, terminate the complete child process group on timeout, preserve diagnostic stdout/stderr, and rerun the complete exact-head suite. Do not increase the whole-job timeout as a substitute for bounded child execution. PHX-QA independently reviews the exact final head.

Other COE #31 exact-head runs:
- [Shared/hardware contracts 44125258235](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44125258235): SUCCESS, scoped.
- [Case-collision guard 44125258102](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44125258102): SUCCESS, scoped.

These scoped successes do not turn the cancelled sandbox suite into a pass.

## 4. Independent P0 ULA defect remains

The current packager still emits the literal:

```text
option ula_prefix 'fd00:db8:blaze::/48'
```

The `blaze` component is not a hexadecimal IPv6 hextet. The current packaging tests contain no `ipaddress` / IPv6-network parser coverage. The source blob and exact line were inspected at COE #31 head `9c2bebf5...`; no ULA fix is present.

Preserve the existing architecture contract: the ULA /48 is installation/site identity, not a shared hardware-profile constant. It must be valid RFC 4193 ULA space, generated or accepted per site, persisted durably across reboot/upgrade/restore, and shared by devices on the same LAN. Do not replace the invalid literal with one globally shared example prefix.

**PHX-RELEASE** owns packager/profile/tests. **PHX-CORE and the COE integration owner** define durable site-prefix provisioning. **PHX-QA** independently verifies generated UCI and persistence semantics. **PHX-HARDWARE** validates target behavior only after correction and separate authorization. PHX-MASTER owns the contract and integration gate only.

## 5. HARDWARE #317 exact-head QA fixture remains stale

Current HARDWARE PR #317 head is `839c21877c27c893e2efc73b3afe7c48e1fcfa4e`, based on #315 head `84fe6b790139d147f330f13a40b3ae3e89a7042d`. Its Full workflow [44130911522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44130911522) checks out merge commit `7ca593a51d336cc81649baf50a7d61876f07781a`. The validation job fails at `tests/controllers.sh` with `Missing poll signature check` for the ESP8266 source. The exact fixture still greps for both `poll` and `sig`.

The current firmware intentionally keeps poll admission default-deny. Focused quarantine-byte-readback [44130911539](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44130911539) and relay-output-polarity [44130911583](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44130911583) succeed. ESP32/ESP8266 compilation jobs in Full succeed, but the validation failure skips later suites.

**PHX-QA** owns the stale fixture correction. Replace the positive-signature expectation with source-linked default-deny regression coverage. Do not restore an unapproved positive signature path to satisfy the old grep.

## 6. Role CI snapshot at this activation

| Role / candidate | Exact current head | Exact-head evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped; separate CORE automation retains source ownership |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS, scoped |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped |
| HARDWARE #317 | `839c21877c27c893e2efc73b3afe7c48e1fcfa4e` | [44130911539](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44130911539) and [44130911583](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44130911583) SUCCESS; [44130911522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44130911522) FAILURE at legacy controller poll-signature fixture |
| QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, scoped; #292 no runs returned (UNKNOWN) |
| RELEASE #291 | `2c4edff231d9b2819415086825530d80b8801307` | [43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) SUCCESS, scoped |
| COE RELEASE #31 | `9c2bebf50030c03bc4dd1e827e050863ba482eab` | Sandbox [44125258197](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44125258197) CANCELLED; shared/hardware and case-collision scoped SUCCESS |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows remain QUEUED: 43096752609, 43096752632, 43096752800, 43096752563, 43096752557 |
| PHX-MASTER #288 before this audit | `5e11daf8d9a65659e92030df94b212eb9e28d21f` | No PR-triggered runs returned |

The #31 release branch remains a child of #26, not integrated into #26. #28/#30 remain separate PISONET candidates. No file move or copy is authorized by this audit.

## 7. Bounded source assertions executed by PHX-MASTER

**14/14 bounded assertions passed** against exact current Git blobs. They checked:
1. Operator wrapper invokes the release sandbox runner.
2. Active-sandbox and owner-probe checks are present.
3. Host root is read-only in bubblewrap.
4. Only the builder workspace receives the writable bind.
5. Runner explicitly shares the host network.
6. Operator-entrypoint regression exists.
7. External-sentinel symlink regression exists.
8. Test helper lacks a per-invocation timeout.
9. Runner process wait lacks a timeout.
10. Workflow whole-job timeout is 20 minutes.
11. Invalid ULA literal remains.
12. Packaging tests lack ULA parser coverage.
13. Legacy controller fixture still greps for poll and signature.
14. Current ESP8266 firmware retains unconditional poll denial.

These are bounded source assertions, **not** execution of the COE Python suite, Master Python suite, OpenWrt UCI/netifd, physical hardware, or financial tests. The COE sandbox workflow was cancelled; the full Master Python suite was not executed; no PR-triggered Master CI runs were returned.

## 8. Ownership, registry, and safety

All PHX-MASTER changes remain under `coordination/phoenix/`. `OWNERSHIP_ROUTES.json` remains unchanged, `DRAFT_REVIEW_ONLY`, and PHX-MASTER target remains null. No source/destination copy, move, overwrite, cherry-pick, merge, or migration was performed.

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections are not accessible through the exposed Files/Drive connector surface in this activation. Older Library snapshots are not authoritative and were not substituted. No private Drive identifiers or contents were published.

No subsystem source branch was modified. No Codex, merge, release, signing, secret provisioning, firmware flash, physical test, real-payment operation, or financial migration occurred.

**PRODUCTION NO-GO remains mandatory** pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates.

## 9. Next owner actions

1. PHX-RELEASE: bound the sandbox helper and child process with timeouts and process-group cleanup; rerun the full exact-head suite without cancellation.
2. PHX-RELEASE / CORE: replace the invalid ULA literal with durable site-scoped RFC 4193 /48 provisioning and negative/positive parser tests.
3. PHX-QA: independently verify the corrected sandbox path and ULA behavior at the exact final #31 head.
4. PHX-QA: replace the stale positive poll-signature grep in HARDWARE validation with default-deny regression coverage; rerun Full at exact #317 head.
5. COE integration owner: keep #26 draft until queued workflows, per-file provenance, licensing, test identity, and combined acceptance are resolved.
6. Registry custodian: restore authorized read access to canonical private Drive v11 and newer corrections.

**Master decision:** the prior operator-build sandbox-bypass finding is closed at current source level, but sandbox runtime acceptance is still BLOCKED; ULA remains P0; HARDWARE Full remains blocked by stale QA fixture. Keep #26/#31/#288 draft. **PRODUCTION NO-GO.**
