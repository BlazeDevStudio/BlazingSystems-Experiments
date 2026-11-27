# Handover Log — 2026-10-05 — BlazePwifi v0.5.0 Prerelease Published

## Release result

GitHub Release:

`v0.5.0`

Title:

`BlazePwifi v0.5.0 — Management Console & BlazeRental`

Release ID:

`403831689`

Release URL:

`https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.0`

Published:

`2026-10-05T14:50:27Z`

State:

**PUBLISHED PRERELEASE**

The release is intentionally marked prerelease because the locked BlazeRental production signer is not currently available to GitHub Actions.

## Exact validated application candidate

Branch:

`blazepwifi-v0.5.0-rc9`

Commit:

`66e159b65b6d8fb5f74dd981dc73d46db7229adc`

Validated build run:

`37326542666` — **PASS**

Candidate-gate artifact:

`11351899683`

Android build artifact:

`11352033229`

Android Device Owner evidence:

`11352761808`

Browser evidence:

`11351948709`

Final candidate gate:

**PASS**

## Exact validation that passed

- full static/security/config/integration validation;
- BlazeRental Android build;
- Device Owner emulator audit;
- unpaid BlazeRental cold-start fail-closed gate;
- unpaid All Apps containment;
- unpaid horizontal escape containment;
- secret native-admin timer hold;
- local administrator password setup;
- Use device as is / daily-driver setup without BlazePwifi enrollment;
- normal Launcher3 Home in unrestricted mode;
- normal All Apps in unrestricted mode;
- Notifications adjacent to Blaze area;
- Clear All notifications;
- far-left BlazeRental page;
- Device Owner persistence and uninstall defense;
- browser Management Console/portal audit;
- ESP8266 build/simulation;
- ESP32 build/simulation;
- Ruijie firmware build/simulation;
- x86_64 build/QEMU simulation;
- required Orange Pi build/simulations;
- retained v0.4 compatibility contracts;
- v0.5 launcher/console source contracts.

## Locked signing result

Workflow:

`BlazeRental v0.5 locked production sign`

Run:

`37327439782` — **FAILED SAFELY**

Reason:

`Locked v0.4 signer recovery requires BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM.`

`Refusing to rotate the production certificate.`

No alternative certificate was generated.

Locked production fingerprint remains:

`C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`

## Release workflow

Workflow:

`BlazePwifi v0.5 release`

Run:

`37327843195` — **PASS**

Release-stage artifact:

`11352224246`

Stage digest:

`sha256:210862a04d87e1d37ec818027e0907e04b99dce1be4421562137a5ed07e0b4f8`

## Verified RELEASE-MANIFEST.json

```json
{
  "release": "0.5.0",
  "commit": "66e159b65b6d8fb5f74dd981dc73d46db7229adc",
  "build_run_id": "37326542666",
  "signing_run_id": "0",
  "candidate_gate": "passed",
  "production_signed": false,
  "android_package": "com.blazesystems.blazerental"
}
```

## Verified CANDIDATE-GATE.json

```json
{
  "release": "0.5.0",
  "commit": "66e159b65b6d8fb5f74dd981dc73d46db7229adc",
  "status": "passed",
  "required_targets": ["android","esp8266","esp32","ruijie","x86_64","orangepi_zero3","orangepi_one","orangepi_pc"],
  "simulation": "passed"
}
```

## Android release assets

Present:

- `BlazeRental-v0.5.0-TEST.apk`
- `BlazeRental-v0.5.0-release-unsigned.apk`

Verified SHA256:

- TEST APK: `8ca246de82c675c23acf47047dc36ffe2d1e07ef7fe9ef22e5129b62040a30d6`
- unsigned APK: `6fe66c1bf99357fad4fdd00629514a2b7059b8089d7efd155d3f231ebc8c74ad`

Not present:

- `BlazeRental.apk`

This absence is intentional. No TEST or unsigned APK is being misrepresented as production-signed.

## Other release assets

The release includes deployable assets for:

- Ruijie RG-EW1200G Pro v1.1;
- x86_64 BIOS/UEFI OpenWrt images;
- Orange Pi Zero3 / One / PC and optional family images;
- ESP8266 Vendo firmware + INO;
- ESP32 Vendo firmware + INO;
- candidate/evidence images;
- `README.md`;
- `RELEASE-MANIFEST.json`;
- `CANDIDATE-GATE.json`;
- `SHA256SUMS`.

## Release features

v0.5 includes the first full implementation pass for:

- BlazeRental branding and LCM icon;
- Launcher3 custom-left BlazeRental + Notifications architecture;
- unpaid fail-closed containment;
- paid/unrestricted normal Launcher3;
- Use device as is;
- Clear All notifications;
- native admin/QR improvements;
- escalating local admin lockout hardening;
- expanded framework-light Management Console;
- WAN/LAN/VLAN/device/storage visibility;
- safe diagnostic Tools/Terminal controls;
- WireGuard/ZeroTier worldwide remote-access configuration/status model;
- portal Movies and Games surfaces;
- Multimedia/BlazeGames manager foundations;
- richer safe portal status.

## Known release limitation

The v0.5.0 Android production APK is **not yet signed with the locked v0.4 production certificate** because the private recovery material is unavailable to GitHub Actions.

To produce an upgrade-compatible production `BlazeRental.apk`, the owner must restore the existing locked signer via repository secrets/offline recovery. Do not upload or paste the private transfer key into chat.

The validated TEST APK is suitable for testing/fresh test deployments. The unsigned release APK is intended for the locked signing workflow, not normal end-user installation.

## Next action

If production Android signing is required:

1. restore the locked v0.4 signer securely;
2. rerun the locked v0.5 signer against build run `37326542666` and candidate SHA `66e159b...`;
3. verify the certificate fingerprint;
4. refresh the v0.5.0 release with `BlazeRental.apk`;
5. clear prerelease status only after production signing and release verification.

Otherwise, v0.5.0 prerelease is complete and available for firmware/TEST evaluation.

## Audit & Reconcile prompt

```text
@GitHub Audit and reconcile BlazePwifi from the published v0.5.0 state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read experiment/openwrt/BlazePwifi/docs/handover/2026-10-05-v050-release-published.md.
3. Verify GitHub release v0.5.0, release ID 403831689, and tag target 66e159b65b6d8fb5f74dd981dc73d46db7229adc.
4. Verify build run 37326542666 and exact candidate gate are successful.
5. Verify release workflow 37327843195 and release-stage artifact 11352224246.
6. Confirm RELEASE-MANIFEST.json has production_signed=false and signing_run_id="0".
7. Confirm BlazeRental-v0.5.0-TEST.apk and BlazeRental-v0.5.0-release-unsigned.apk are present and BlazeRental.apk is absent.
8. Preserve locked signing fingerprint C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24; never silently rotate it.
9. If the owner restores the locked signer, sign the exact validated candidate or a newly validated successor, verify fingerprint/checksums, refresh v0.5.0, then clear prerelease only after verification.
10. For any future development, preserve all approved v0.5 architecture and continue updating PROJECT_HANDOVER.md plus dated logs after every meaningful success/failure/change, always leaving a fresh Audit & Reconcile prompt.
```
