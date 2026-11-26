# PHX-HARDWARE UTC02 — #349/#352/#353 ancestry reconciliation

Observed: 2026-11-26T02:38Z
Role: PHX-HARDWARE
Repository: BlazeDevStudio/BlazingSystems-Experiments
PRs: #349, #352, #353 (all remain DRAFT / UNMERGED)

## Revalidated starting refs

- #349 parent branch: `phoenix/hw-json-array-primitive-guard-20261124-utc00` at `1a2ecf5fa8c8c20a0095ac898c1bff254280ad27`.
- #352 child branch: `phoenix/hw-exact-arduino-core-matrix-20261125-utc11` at `0e984e267b3a8fb10c314800d1a7f120806354b7`.
- #353 grandchild branch: `phoenix/hw-board-conditional-isr-selector-20261125-utc17` at `4e2185b150ba6d1a614fe86d875a9d2bfc7db9a4`.
- #349 → #352 compare: 43 ahead / 3 behind, merge base `2a5c997add4f49fcd74f753101d3a9daac0040bf`.
- #352 → #353 compare before this task: 21 ahead / 0 behind.

## #349 changes imported into #352

The three parent-only commits changed four paths. The normalizer and its contract lab were not changed by #352, so these were applied directly from the exact #349 head:

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_token_normalizer.py` — adds CRLF-aware C++ phase-2 line-splice recognition in `//` comments.
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_token_normalizer_contract_lab.py` — adds the CRLF regression (15 total contract cases).
- `experiment/openwrt/BlazePwifi/docs/handover/2026-11-25-hw-cpp-crlf-line-splice-guard-utc23.md` — carries the source/test RED/GREEN evidence.
- `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` — combined additively; no prior #352 history was removed.

## Merge safety

- The #352 merge commit uses the prior #352 head as first parent and #349 head as second parent.
- The branch ref update uses the exact previous #352 SHA as an expected-SHA lease and `force=false`.
- The next #353 merge will use the prior #353 head as first parent and the resulting #352 merge commit as second parent, retaining the ISR-specific child work.
- No rebase, force-push, PR retarget, merge-to-main, or release action is performed.

## Verification

- Existing #349 exact-source RED/GREEN evidence is preserved in its narrow handover and CI links.
- New exact-head Quarantine, Relay, Arduino core and Full workflow runs must be read after the branch update; this file does not claim those future runs passed.
- Physical coin pulses, relay polarity/contact, electrical recovery, LittleFS power-cut durability, 150 controlled power cuts and 30-device/24-hour soak remain NOT TESTED.
- Protected anti-rollback signer/witness, v1→v2 migration, durable accounting/replay and independent QA/Release acceptance remain NOT ACCEPTED.

## Status

SIMULATED / CI VERIFIED evidence only for inherited host tests. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.

## Exact-head CI results after UTC02 ancestry reconciliation

All run heads below were read from GitHub Actions and match the source/test merge commits, not a physical device:

### PR #352 — source/test SHA `a1720e1724a15b5254d9dd1ee57e6212259a4896`

- Quarantine Byte Readback [run #45744575878](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45744575878), job `139657404426`: PASS. ESP8266 and ESP32 coin pulse capture 18/18 each; C++ token normalizer 15/15 including CRLF line-splice regression; bounded HTTP token normalizer 8/8; JSON/UTF-8, boot-polarity, EEPROM-read failure and fail-closed mutation checks passed.
- Relay Output Polarity [run #45744575789](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45744575789), jobs `139657404082` and `139657404444`: PASS / PASS.
- ESP8266 core 3.1.2 [run #45744575794](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45744575794), job `139657404588`: PASS.
- ESP32 core 3.3.13 and 4.0.0 [run #45744575866](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45744575866), jobs `139657405152` and `139657404946`: PASS / PASS. The actual ESP32 Vendo sketch compiled under both pinned cores; core-4 output was 1,099,857 bytes (83% of 1,310,720 bytes).
- Full BlazePwifi [run #45744575781](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45744575781): FAIL at validation job `139657404573`, inherited `Missing poll signature check` in the active ESP8266 sketch. All 14 firmware/platform jobs and Android passed; production APK import, signing, simulations, candidate gate and publication were skipped.

### PR #353 — source/test SHA `c42ceae028e21e4061c9d424f28c4bcfdbff7c63`

- Quarantine Byte Readback [run #45744810594](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45744810594), job `139658174292`: PASS. ESP8266 and ESP32 coin pulse capture 18/18 each; C++ token normalizer 15/15; bounded HTTP token normalizer 8/8; JSON/UTF-8, boot-polarity, EEPROM-read failure and fail-closed mutation checks passed.
- Relay Output Polarity [run #45744810597](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45744810597), jobs `139658174191` and `139658174518`: PASS / PASS.
- Full BlazePwifi [run #45744810573](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45744810573): FAIL at validation job `139658174516`, same inherited `Missing poll signature check`. All 14 firmware/platform jobs and Android passed; production import/signing, simulation, candidate and publication jobs were skipped.

These are SIMULATED / CI VERIFIED results. The failure is not fixed by ancestry reconciliation and must not be bypassed by weakening the signature check. No physical coin pulse, relay contact, power cut, or device soak was performed.
