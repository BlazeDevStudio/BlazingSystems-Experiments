# BlazeFusion × EasyMode R281 (staged preview only)

**Status:** Development preview, no installed system changed. Historical deployed EasyMode R281 v4.2.3 release source is kept **unchanged**, as are the separate EasyMode 5.0.0-alpha.1 installer and stable 4.1.4 baseline.

This adapter lets the existing EasyMode operator page use BlazeFusion's three visual modes without replacing native EasyMode `/ubus` authentication, WAN/repeater/bridge/SMS settings, or its server-owned light/dark/accent controls. No React, Redux, Alpine, remote assets, customer balances or new RPC actions are included. It is not a PisoWiFi billing-engine merger.

## Safe preview workflow (developer computer only)

From this folder:

```sh
python3 build-preview.py --output /tmp/easymode-fusion-preview
```

The builder requires a **new nonexistent output directory**. It copies only the audited `releases/v4.2.3-r281-experiment/root/www` static snapshot into that staging directory, then injects local `/easy/blazefusion/blazefusion.css` and `blazefusion.js` links plus an appearance selector in the existing operator header. It refuses unknown old style/logout anchors, unexpected version text, previously modified release markup, and any existing destination. No OpenWrt login, SSH, password, UCI, system partition, deployed web root or physical router is accessed.

Do **not** upload the generated directory directly to production. A separate review must verify the on-device EasyMode version, customizations, prior backup, correct filesystem path, static integrity, owner authorization, recovery and rollback before adding an installer.

## Trust and appearance behavior

- `blazepwifi.console.appearance.v1` holds **only** Fusion, Compact or Comfort preference in the browser. An unknown value safely normalizes to Fusion. This is independent of EasyMode `html[data-theme]` (light/dark) and the user's server-owned `--accent`.
- No network requests, `/ubus` RPC, stored authentication tokens or coin/payment data from the adapter. Existing `app.js`, `core.js`, admin links and network configuration functions are copied without changes.
- Local CSS is applied to cards, navigation, spacing and accessibility. It must not conceal submit/save/logout controls or mask true mobile overflow with global `overflow-x:hidden`.
- CoreUI React template 5.7.0 and Metis template 3.6.0 were MIT-licensed **design references**, not deployed library binaries. Preserve upstream notices if any actual upstream source code is imported in a later candidate.

## Evidence and limitation

- Required static test: `experiment/openwrt/BlazePwifi/tests/v060_easymode_fusion.sh`. It stages the preview, verifies all expected assets, original login and EasyMode JS references, rejects output overwrite, ensures frozen input hash is unchanged, checks no network authority in the new adapter.
- Required Chromium test: `experiment/openwrt/BlazePwifi/simulation/easymode_fusion_browser.py`. It serves the **staged output locally on a developer loopback**, never connects to a router, temporarily reveals the existing operator shell *for visual tests only*, verifies theme switching, reload persistence, mobile 360/390px width and logout visibility. **It does not prove OpenWrt authentication, remote network changes or payment safety.**
- The published R281 firmware/installer is unchanged; this preview is **not a new EasyMode 4.2.4 release** or production firmware upgrade.

## Follow-up after validation

After full BlazePwifi CI and manual security review, design an explicitly approved, idempotent, backed-up and rollback-capable on-device installer for supported EasyMode versions. Never use this staging script itself as a production installer. Subsequent adaptations for the other five EasyMode editions, ESP, Android, and Windows are separate source/release validation tasks.
