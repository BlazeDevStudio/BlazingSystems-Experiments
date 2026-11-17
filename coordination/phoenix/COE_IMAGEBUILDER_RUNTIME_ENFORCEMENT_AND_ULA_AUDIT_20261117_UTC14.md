# PHX-MASTER — COE ImageBuilder test-harness vs runtime sandbox, ULA and integration revalidation

**Role lock:** PHX-MASTER/2026-11-17T14Z (one run per role and scheduled UTC hour).  
**Disposition:** P0 integration/release blocker; COE #26 and #31 remain draft; **PRODUCTION NO-GO**.  
**Scope:** PHX-MASTER coordination, architecture/interface contracts, exact-head provenance and release-gate routing only. No RELEASE, QA, HARDWARE, PISONET, CORE, RENTAL or COE runtime source was changed.

## 1. Exact live refs re-read

| Ref | Exact SHA | State |
|---|---|---|
| Experiments default main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b | Default branch |
| Experiments development blazepwifi-v0.5.3-development | aad3aade72c1156eecba1fed30907c6d0283b2c5 | Development branch |
| Experiments v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 | Comparison-only; not promoted |
| PHX-MASTER #288 | e9e54ca4ac48dd7da72e8093bd252a94b6d31a5c | Open / draft; base main |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | Structure-only baseline |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Open / draft |
| COE RELEASE #31 | d45b84c67dc587fca6226662cb1d8bc59bdb11ae | Open / draft; based on #26 |
| COE #31 source/test head | da93eafde167f6ada9c6c0ea19d1e3e2f285001b | Earlier head before handover-only commit |

The live branch refs were read directly. The current #288 branch and PR both resolved to e9e54ca4ac48dd7da72e8093bd252a94b6d31a5c before this commit.

## 2. What changed in RELEASE #31 since the UTC13 audit

Current exact COE #31 source identities:

| File | Blob SHA | Current observation |
|---|---|---|
| tools/package_appliance_firmware.py | fd558928b2869ce1f4b2cb2776b405b4b723b310 | Packager unchanged; still emits invalid ULA literal |
| tools/test_package_appliance_firmware.py | b2cdbcebf111a4f04c0504edf983072323fa2718 | Test helper delegates generated-wrapper calls to sandbox runner when required |
| tools/run_imagebuilder_sandbox.py | f20267d26185238bc82bcaccebf857fee67d929a | New UID/GID-mapped bubblewrap runner |
| .github/workflows/release-imagebuilder-sandbox.yml | 151c052f36664c1cb70138e7f135a5570909e09e | Sets PHX_REQUIRE_BWRAP=1; checkout uses persist-credentials=false; workflow permission is contents read |
| tools/RELEASE_PACKAGER_HANDOVER.md | 835d2dcb5406b9792fffe0c46dcb5d376ff1c166 | Records current owner evidence and limitations |

The test helper invokes run_imagebuilder_sandbox.py only when PHX_REQUIRE_BWRAP=1; the dedicated workflow sets that variable. The runner uses a read-only host-root bind, a writable disposable ImageBuilder directory, tmpfs for /tmp, a cleared child environment, UID/GID mapping back to the invoking runner, and a host-side ownership probe.

This is a meaningful improvement to the CI test harness. It is not yet proof that a production build is forced through the same boundary.

## 3. New P0: test-harness containment is not runtime build enforcement

The exact current packager blob fd558928... contains neither bwrap nor run_imagebuilder_sandbox.py. Its generate_build_script() emits the normal shell wrapper and invokes the ImageBuilder Make command; the generated artifact does not invoke the new sandbox runner or otherwise require a sandbox.

By contrast, the test file invokes the runner around the generated wrapper when the CI-only environment variable is set. The workflow therefore tests a synthetic Makefile under the runner, but it does not make the generated build script self-enforcing. An operator can still run the emitted script directly unless a separate external build-host policy is followed.

**Disposition:** classify current evidence as TEST-HARNESS FILESYSTEM WRITE-BOUNDARY ONLY. Do not mark the production build invocation sandbox-enforced. PHX-RELEASE must either:
1. make the generated build entrypoint invoke a verified runner with a trusted helper path and explicit disposable-workspace boundaries; or
2. document a separate isolated build-host requirement and provide exact, independently verified evidence that all supported build invocations use it.

PHX-QA must independently review the final source/test/runner/workflow heads. PHX-MASTER owns this acceptance contract and routing, not the release implementation.

### Boundary limitations that must remain explicit

- The runner passes --share-net; the network namespace is deliberately shared. Network isolation is not present or claimed.
- A read-only bind of host root constrains writes but is not a confidentiality boundary: the process may still read files accessible to the mapped runner identity. Do not run untrusted build inputs on a secret-bearing host and do not claim that read-only mounts hide host data.
- The CI workflow uses contents-read permission and checkout with persisted credentials disabled. That reduces this workflow's credential exposure; it does not turn the runner into a general-purpose secret-isolation boundary.
- The final-head sandbox run is still pending with no jobs returned. No caller-ownership or sentinel-preservation PASS is claimed.

## 4. Exact-head CI reconciliation

| Candidate / run | Exact result | Meaning |
|---|---|---|
| COE #31 final head d45b84c67dc587fca6226662cb1d8bc59bdb11ae, sandbox #44104956173 | PENDING; no jobs returned | No sandbox pass |
| COE #31 final head, Shared/Hardware #44104956321 | SUCCESS | Scoped shared-contract/firmware CI only |
| COE #31 final head, case collision #44104956464 | SUCCESS | Case-collision check only |
| COE #31 source/test head da93eafde167f6ada9c6c0ea19d1e3e2f285001b, sandbox #44104503489 | CANCELLED | No test result |
| Earlier pre-runner regression #44098400955 | FAILURE | Synthetic Makefile changed external sentinel to BUILDER-OVERWRITE; earlier-head RED evidence, not current-head CI |

COE #26 remains at b382d233ff06c8791b1028bed3c617cc7b670d12 with five workflows still QUEUED: 43096752609, 43096752632, 43096752800, 43096752563 and 43096752557. No combined integration acceptance is established.

## 5. ULA blocker remains unchanged

The exact current packager blob still emits the invalid value fd00:db8:blaze::/48. The blaze hextet is not hexadecimal. The current packager tests still have no IPv6/ULA assertion, and the shared EW1200G Pro profile still has no ULA property. The existing architecture decision remains: ULA is installation/site identity, not reusable router-profile metadata. Require a target-supported first-boot generation plus durable persistence, or a validated deployment-specific input; never use one globally hard-coded prefix or regenerate it per boot.

**Executed Python standard-library parser checks (2 cases):**
- Current emitted literal: rejected with AddressValueError at the non-hexadecimal blaze hextet.
- Control fd12:3456:789a::/48: parsed and confirmed inside fc00::/7 with prefix length 48.

This is parser evidence only, not OpenWrt UCI/netifd, ImageBuilder, router or hardware validation.

## 6. Current role PR / CI snapshot

Exact PR heads were fetched during this activation. Scoped CI success is not integrated acceptance.

| Role / PR | Exact head | Exact-head CI observation |
|---|---|---|
| PHX-MASTER #288 | e9e54ca4ac48dd7da72e8093bd252a94b6d31a5c | No PR-triggered runs returned |
| PHX-CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | 42698139210 SUCCESS, scoped |
| PHX-RENTAL #240 / #287 / #289 | a7d113fb8ae3f0c5e838e64d31cae7a154e37b56 / a4fffd01c8fb1818c32a53522e0590c1dc8a77cd / 68928774d0d7cf65adb26bc6b54199a3159d066c | #240 40910311141 + 40910311159 SUCCESS; #287 43754089203 SUCCESS; #289 43653329235 + 43653329229 SUCCESS |
| PHX-PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | 42462978704 SUCCESS, scoped; physical COM acceptance unverified |
| PHX-HARDWARE #314 / #315 / #316 / #317 | 556adc20ef0cfd355089aff3b979c0169af79bdd / 84fe6b790139d147f330f13a40b3ae3e89a7042d / 888e6941e3a7a81641682c23d937f97d8117d2ea / 4496124580a11f8bdd88c2e5adcdfb86e824b978 | #314 43782088731 + 43782088748 SUCCESS; #315 44054778537 SUCCESS / 44054778555 FAILURE; #316 43972511337 SUCCESS / 43972511250 FAILURE; #317 44097183197 + 44097182916 SUCCESS / 44097182945 FAILURE |
| PHX-QA #267 / #279 / #290 / #292 | ff5367990c2d27b8ebbb822ee208251af0c890e2 / 8f476ef05893193325ef3d1f65a35e144ae7a568 / 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #267 41452247439 SUCCESS; #279 no runs; #290 43633486963 SUCCESS; #292 no runs |
| PHX-RELEASE #242 / #291 | 734b89d9e7792247e8376335c3f3685500ab3f89 / 2c4edff231d9b2819415086825530d80b8801307 | #242 40882814472 SUCCESS; #291 43744993487 SUCCESS; signing/publishing remain closed |
| COE #26 / #28 / #29 / #30 / #31 / #32 | b382d233... / b21b0461... / d0830332... / 4897348d... / d45b84c6... / 29b6fe08... | #26 five QUEUED; #28 43632393888 SUCCESS; #29 43653906676 + 43653906675 SUCCESS; #30 43653415598 SUCCESS with NSIS warning 6000 still requiring owner correction; #31 44104956173 PENDING / 44104956321 SUCCESS / 44104956464 SUCCESS; #32 43653540607 SUCCESS |

HARDWARE #317 Full validation remains failed on the inherited positive poll-signature fixture; preserve firmware default-deny and keep fixture/extractor repair with PHX-QA. No owner source branch was modified by PHX-MASTER. The separate CORE automation retains CORE implementation ownership.

## 7. Migration, registry and execution limits

- COE #31 is based on COE #26 and changes release packager/test/runner/workflow/handover paths only. No new source-repository migration is established by this release child.
- coordination/phoenix/OWNERSHIP_ROUTES.json remains unchanged, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. It is a review map, not a copy/move command.
- The public Cloud Artifact Policy and Cloud Storage Handover were fetched and read. They require the private registry and sync ledger before archive/mirror work.
- The exact private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in the accessible Library search. No Google Drive file connector is exposed in this run. The newest visible Library registry snapshot is v7; it was not substituted. No private Drive identifiers or contents were copied to GitHub.
- Ten bounded source assertions passed against exact fetched packager/test/runner/workflow blobs. Two Python ipaddress parser cases executed as above. The full Master Python suite was not run: a local Git checkout was unavailable because git ls-remote failed DNS resolution for github.com. No COE sandbox test is claimed while run #44104956173 remains pending.

## 8. Owner actions and safety

1. **PHX-RELEASE:** make the actual generated build entrypoint enforce the approved filesystem boundary, or document and prove the required external isolated build-host boundary; keep network-isolation claims separate. Correct ULA provisioning/validation and tests on the release-owned branch.
2. **PHX-QA:** independently review the runner and final exact-head sentinel/ownership evidence; test the actual supported build invocation, not only the synthetic test harness.
3. **COE integration owner:** keep #26 draft; reconcile exact source blobs, test identities, licenses and CI before any per-file migration proposal.
4. **Registry custodian:** restore authorized access to the canonical private v11 registry and newer corrections.

No merge, release, signing, secret provisioning, hardware flashing, physical test, real-payment operation, source migration, or financial state change occurred.

**PRODUCTION NO-GO** remains mandatory pending independent protected signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates.
