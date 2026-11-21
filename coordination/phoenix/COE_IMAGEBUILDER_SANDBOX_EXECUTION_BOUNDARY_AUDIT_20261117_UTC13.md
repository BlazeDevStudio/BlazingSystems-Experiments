# PHX-MASTER — COE ImageBuilder sandbox execution-boundary and ULA revalidation

**Role lock:** PHX-MASTER/2026-11-17T13Z (single scheduled-hour checkpoint).
**Disposition:** P0 release/integration blocker; all destination drafts remain open; **PRODUCTION NO-GO**.
**Scope:** PHX-MASTER coordination, architecture, exact-head provenance and gate routing only. No RELEASE, QA, HARDWARE or destination runtime source was changed.

## Exact live refs

- Experiments default main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Experiments development blazepwifi-v0.5.3-development: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Experiments PHX-MASTER branch / draft PR #288 before this update: d179a82592994256c83cdcea2183d3a79b1518f7; base main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- COE default main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration draft #26: b382d233ff06c8791b1028bed3c617cc7b670d12.
- COE RELEASE child #31: 19fc87988e55f47e8c6a512e51b470a91abbf816, based on #26.
- Experiments HARDWARE draft #317: 4496124580a11f8bdd88c2e5adcdfb86e824b978.

## ULA remains unresolved at current COE #31 head

| Artifact | Exact current #31 blob | Result |
|---|---|---|
| tools/package_appliance_firmware.py | fd558928b2869ce1f4b2cb2776b405b4b723b310 | Line 112 still emits fd00:db8:blaze::/48 |
| tools/test_package_appliance_firmware.py | 322b4a4b6df35ca91da68c71751ebb7879b6c69a | No ULA/IPv6 validation assertions |
| EW1200G Pro profile | 6e797cf9c9922209efe4c0da49c49fa1da16c11a | No networking.ula_prefix property |
| release-imagebuilder-sandbox.yml | b0ca74cb60670a4baafacd14c1645a0c115d037e | Sandbox workflow does not wrap the test invocation |

The current packager still contains the non-hexadecimal hextet blaze. The shared router profile remains model/topology metadata and must not receive one static site ULA. The prior §6.9 decision stands: installation/first-boot authority must create or accept a validated site-specific RFC 4193 ULA /48, persist it durably before network services consume it, and reuse it across reboot/upgrade/restore. No global placeholder or per-boot regeneration.

Python standard-library ipaddress checks were executed against the exact emitted literal and controls: fd00:db8:blaze::/48 was rejected; fd12:3456:789a::/48 parsed and met the ULA /48 contract; fd12:3456:789a::/64 parsed but failed the required /48 length; 2001:db8::/48 parsed but was not ULA. This is parser evidence only, not OpenWrt UCI/netifd, ImageBuilder or router validation.

## New P0 — ImageBuilder sandbox is probed but not applied to the build/test process

The current workflow installs bubblewrap and performs a standalone namespace capability probe. It then runs a separate privileged UID/GID probe. The current exact-head run [44098939249](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44098939249), job 134093412365, failed at that UID/GID probe with: bwrap could not find the runner temp probe path due to Permission denied. The subsequent packaging regression step was **SKIPPED**.

Even if that probe succeeds, the current workflow's packaging step is a direct python3 tools/test_package_appliance_firmware.py -v invocation, not a bubblewrap-wrapped invocation. The test method test_generated_wrapper_contains_make_created_symlink_write_to_host checks that bwrap exists, then launches subprocess.run(["sh", wrapper], ...) directly. Presence of bwrap and a separate 'bwrap ... true' probe do not sandbox the Makefile process.

At the prior #31 head edf4a37fef58fa92ed7fe7dc0815f479cb743084, run [44098400955](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44098400955), job 134091567142, reached the test and failed because the external sentinel contained BUILDER-OVERWRITE instead of KEEP-OPERATOR-OWNED-SENTINEL. That is an earlier exact head, not the current #31 result; it demonstrates the direct test process did not contain the synthetic Makefile write. At the current 19fc879 head, the same packaging test did not run because the UID/GID probe failed first.

**Required PHX-RELEASE action:** repair the UID/GID probe's source-path/bind permissions, then ensure the actual untrusted Make/ImageBuilder subprocess is executed inside the namespace. Bind only a disposable build workspace writable; keep the external sentinel outside that writable bind set or read-only; preserve the runner UID/GID; fail closed if the sandbox cannot be established. The malicious synthetic Makefile test must run under the same boundary and prove the host sentinel remains byte-identical. Do not claim network isolation unless separately configured and verified.

## Exact-head CI and independent Hardware hold

- COE #31 head 19fc879...: sandbox run 44098939249 FAILURE at UID/GID probe; packaging tests SKIPPED. Hardware/Shared Contracts run 44098939596 SUCCESS and case-collision run 44098939148 SUCCESS; these do not close sandbox or ULA.
- COE #26 head b382d233...: five workflows remain QUEUED (43096752609, 43096752632, 43096752800, 43096752563, 43096752557). No combined integration acceptance.
- HARDWARE #317 head 4496124...: focused quarantine run 44097183197 SUCCESS and relay polarity run 44097182916 SUCCESS; Full run 44097182945 FAILURE at validation job 134088551798 with 'Missing poll signature check' for ESP8266. Preserve firmware default-deny; PHX-QA owns the stale positive-poll fixture and extractor correction.
- Master #288 head d179a825... had no PR-triggered workflow runs returned.

## Source assertions and limits

Eight bounded source/CI assertions passed against the exact current #31 packager, test, profile, workflow and run results: invalid literal present; no deployment ULA input; no ULA/IPv6 test assertions; no profile ULA property; bubblewrap capability probe is separate from test invocation; test launches wrapper directly; current packaging step skipped; prior exact-head log records external sentinel overwrite. These are static evidence assertions, not the COE Python suite.

Role PR/CI heads were refreshed in ROLE_ASSIGNMENTS.md. OWNERSHIP_ROUTES.json remains unchanged at status DRAFT_REVIEW_ONLY with PHX-MASTER target null. No file move/copy/overwrite or migration proposal is authorized.

## Registry, policy and production gates

The exact private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections remain unavailable: no Google Drive file connector is exposed, and Library search returned older registry snapshots only (latest visible v7). No older registry was substituted and no private IDs or contents were published. AGENTS.md's canonical Cloud Artifact Policy and Cloud Storage Handover links could not be fetched through the available GitHub connector; the older Library storage policy/development handover were read only as historical guidance, not treated as current authority.

No subsystem source, destination runtime, financial state, secret, hardware, release or production workflow was changed. No merge, release, signing, flashing, physical test or payment operation occurred. Full Master Python suite was not executed.

**PRODUCTION NO-GO** remains mandatory pending independent protected signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.