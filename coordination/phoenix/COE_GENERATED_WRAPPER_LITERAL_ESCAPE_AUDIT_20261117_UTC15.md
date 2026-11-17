# PHX-MASTER — COE generated-wrapper literal-escape runtime audit

**Checkpoint:** 2026-11-17 UTC15  
**Status:** P0 BLOCKED · destination PRs remain DRAFT · PRODUCTION NO-GO  
**Master branch:** `phoenix/master-coordination`  
**Master parent:** `8583e012f4468f6e55d1cb8e3f05837905719cc1`  
**Destination:** `BlazeDevStudio/CoinOperatedEcosystem` PR #31, head `d45b84c67dc587fca6226662cb1d8bc59bdb11ae`, based on integration PR #26 at `b382d233ff06c8791b1028bed3c617cc7b670d12`.

## Finding — generated shell contains literal backslash-n sequences

Exact packager file: `tools/package_appliance_firmware.py`, blob `fd558928b2869ce1f4b2cb2776b405b4b723b310`, source line 495.

Inside the Python triple-quoted `content = f"""..."""` template, the empty-image guard and following checksum command are joined with literal `\\n` sequences rather than actual line breaks. Python therefore emits backslash-plus-`n` text into the generated shell wrapper. The affected sequence starts at `EMPTY_IMAGE=$(find ... -print -quit)\\nif [ -n "$EMPTY_IMAGE" ]; then\\n ...`.

A bounded local shell reproduction of that exact emitted fragment produced:
- `sh -n`: exit 0 (syntax-only parsing did not expose the runtime defect).
- Executing the fragment: exit 2, `Syntax error: Bad fd number`.

This is a source-grounded minimal reproduction, **not** execution of the full COE packager test suite or a real ImageBuilder build.

## Why the current tests matter

- `test_generated_build_script_passes_posix_shell_syntax_check` invokes `sh -n`; this check alone is insufficient for the affected runtime branch.
- `test_generated_wrapper_denies_empty_firmware_payload` executes the generated wrapper and expects the specific `RELEASE-BLOCKED: empty firmware image` result. It is the relevant runtime regression and should be required on the exact final head.
- Current exact-head sandbox workflow [#44104956173](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44104956173), job `134126241456`, was still **IN_PROGRESS** at the last read, executing “Run packaging regressions with mandatory bubblewrap”. No conclusion is claimed.

## Owner routing and safe disposition

1. **PHX-RELEASE** owns the packager/template correction on its existing COE #31 branch. Replace the literal escape sequence with actual shell line breaks (or an unambiguous joined-line construction), then run the generated wrapper through the empty-image and positive synthetic paths.
2. **PHX-QA** independently checks the exact corrected head, including runtime exit code, expected diagnostic, no manifest on denial, and preserved operator sentinel.
3. **PHX-MASTER** owns only this cross-repo contract, integration gate and provenance record. No COE source file was changed by this audit.

Keep COE #31 and umbrella #26 open/draft. Do not copy, overwrite, relocate, cherry-pick, merge or promote any destination file from this finding. The machine-readable `OWNERSHIP_ROUTES.json` remains unchanged at `DRAFT_REVIEW_ONLY` with PHX-MASTER target `null`.

## Other open destination gates

- The packager still emits invalid ULA `fd00:db8:blaze::/48`; `blaze` is not a hexadecimal IPv6 hextet. Require a site-scoped, durable RFC 4193 ULA /48, not a shared profile constant.
- The generated packager entrypoint still does not invoke `run_imagebuilder_sandbox.py`; the current sandbox workflow proves only test-harness routing. Actual operator build invocation remains uncontained/unproven. The runner uses `--share-net`; network isolation is not claimed.
- COE #26 exact head remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; its five PR-triggered workflows remain queued at the last exact-head read. No combined acceptance exists.

## Verification boundary

Source/tree inspection and the minimal shell reproduction were performed. The full Master Python suite, full COE packaging suite, actual OpenWrt ImageBuilder, UCI/netifd target behavior, physical router validation and native acceptance were **not** executed by PHX-MASTER. Current #31 workflow remains pending/in progress; do not treat the historical scoped successes as final-head acceptance.

The private canonical Drive registry v11 and newer corrections remain inaccessible through the exposed connector surface; no older Library registry was substituted and no private contents were published.

**PRODUCTION NO-GO** remains until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates have independently verified evidence.
