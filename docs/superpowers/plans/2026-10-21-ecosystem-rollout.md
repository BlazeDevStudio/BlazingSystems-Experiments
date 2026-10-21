# BlazeSystem ecosystem rollout implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Advance the existing ecosystem through verified integrations, installable packages and compatible owner-approved deployments, prioritizing coin-operated business systems and easier demonstrated defects.

**Architecture:** Retain the existing Full router authority, native Android rental, Windows timer/stations, ESP/SBC controllers and independent product groups. The R281 manual standalone server remains a separate test surface; it is not the Full Vendo backend. Each independent project keeps its own release/device gates.

**Tech Stack:** Existing OpenWrt shell/native tools, Python build validation, Arduino CLI, Android and .NET workflows.

**Spec:** Owner continuation/rollout instructions; existing experiment/openwrt/BlazePwifi/docs/ARCHITECTURE.md, HANDOVER_POLICY.md, migration/signing/physical acceptance contracts and current three canonical handovers.

## Global constraints

- Preserve owner ZIP branding, existing network/configuration, native and legacy identities and private rollback evidence.
- Keep production money, independent witness, permanent signer/custody, migration and physical acceptance gates. A build or checksum is not production authorization.
- Preserve current0.5.3 source identity; do not relabel it0.6. The standalone preview remains0.1.3-preview.1.
- Firmware protocol/sketch/shared-header bytes remain unchanged in package-closure work.
- Additional Windows/ESP/server targets require actual host/access inventory; continue independent source work while waiting. Do not rerun the completed R281 replacement.

## Review focus

1. Missing local Arduino includes must fail source-package validation.
2. Each target must compile its shipped sketch/library tree, not a checkout-only dependency.
3. Artifact hashes must cover nested source as well as build outputs.
4. Missing or mismatched installed VERSION must fail before package output is created.
5. Real compiler/archive checks must remain distinct from stubbed local fixtures and hardware acceptance.

## Task1: Integrate existing verified work

- [x] Verify exact126/129 source checks and merge into their intended development/standalone branches.
- [x] Reconcile107 canonical records against new development without authored application changes; exact Full/standalone checks, then guarded integration.
- [ ] Classify post-merge development checks and retain exact source/run evidence.

## Task2: Ship complete ESP source

**Files:** tools/package-vendo-source.py, esp/REBUILD.md, tests/test_vendo_source_bundle.py and .github/workflows/blazepwifi-build.yml under the existing Full project/repository.
**Interface:** package-vendo-source.py TARGET OUTPUT stages source/SKETCH, source/libraries and README; existing firmware artifact names remain compatible.

- [x] Reproduce actual old artifact/workflow missing-header RED.
- [x] Stage unchanged source/library bytes; compile the shipped layout and recursively hash output.
- [x] Execute real packaging blocks with only the compiler stubbed; verify both targets, byte identity, compile inputs and complete manifest.
- [ ] Require actual ESP8266/ESP32 compile at the final combined SHA; inspect downloaded artifacts before completion.

## Task3: Correct update version identity

**Files:** openwrt/rootfs/usr/share/blazepwifi/VERSION, tools/build-update-bundle.sh and tests/test_update_version_identity.py in Full, plus its existing workflow step.
**Interface:** existing builder ROOT OUT either refuses invalid runtime identity before temporary/output creation or produces the existing overlay-v1 archive format.

- [x] Prove mismatch using a real successful CI artifact and verify its checksum/manifest.
- [x] Align embedded identity with existing declared0.5.3; add missing/nonregular/mismatch refusal.
- [x] Verify local source/negative cases; explicitly skip actual archive construction on Windows without required metadata tools.
- [ ] In Linux CI, build actual archive and verify root/release/runtime identity and version manifest hash; inspect generated artifact.

## Task4: Deliver and continue rollout

- [x] Create a self-contained manual-R281 test download from verified standalone source; verify all payloads and exclude credentials/state.
- [x] Save the whole-ecosystem status board with concrete next actions for13 groups.
- [ ] Merge current development into the package branch, update canonical checkpoint, independently review final diff and verify exact CI before integration.
- [ ] Deploy only compatible verified components to actual owner-approved hosts with private backup and observed acceptance. Device checks blocked by approval review remain pending; never substitute simulated proof.
- [ ] Continue remaining financial/hardware/signing dependencies and independent product groups through their existing checklists; keep the five-hour follow-up synchronized.
