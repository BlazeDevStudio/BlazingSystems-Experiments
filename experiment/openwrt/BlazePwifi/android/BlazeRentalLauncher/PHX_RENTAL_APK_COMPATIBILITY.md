# PHX-RENTAL — APK compatibility and signing contract (draft audit)

**Scope:** source-preserving BlazeRental Android launcher; static artifact gate only.
**Source snapshot:** `BlazeDevStudio/BlazingSystems-Experiments` PR #289, starting head `68928774d0d7cf65adb26bc6b54199a3159d066c`. Parent PR #240 remains draft. No source relocation or signing in this change.

## Reconciled implementation identities

| Line | Source at audited head | Declared identity | Relevance |
| --- | --- | --- | --- |
| Launcher3-derived active candidate | `experiment/openwrt/BlazePwifi/android/BlazeRentalLauncher/` | Gradle `com.blazesystems.blazerental`, `minSdk 21`, `targetSdk 27`, versionCode `50300` (`.debug` suffix for debug) | Existing PHX-RENTAL native tests, managed launcher, Android 5.0 install eligibility **subject to APK signing and device tests** |
| Separate newer Android client | `experiment/openwrt/BlazePwifi/android/BlazeRental/` | Gradle `com.blazesystems.blazerental`, `minSdk 26`, `compileSdk 36`, versionCode `30002` | **Cannot** be substituted as an API21 app or as an in-place upgrade to `50300` |
| Token launcher | `android/token-launcher/` | Separately scoped token launcher | Do not confuse with the Launcher3-based managed rental client |
| Dedicated repository | `BlazeDevStudio/BlazeRental-Android` | Empty on 2026-11-21 inspection | Intended destination, **no transfer authorized by the draft ownership route** |
| `BlazeDevStudio/AndroidDevel` | `main` README only | Not established as current implementation | Not a migration baseline |
| `BlazeDevStudio/CoinOperatedEcosystem` | `main` intake scaffold; staged draft PR #26 | Not verified equivalent to native Launcher3 tree | Do not substitute unreviewed staging or overwrite server ledger |

Source blob anchors at the inspected PR head:

- Launcher3 `build.gradle`: Git blob `aeb2ca7e57a969d99b6cabd984ea484cb37397e2`.
- Launcher3 `AndroidManifest.xml`: Git blob `43b01bead3583eead0e542d8584c033cf831b3b7`.
- New client `app/build.gradle`: Git blob `7e3aeedf8c6608f1db2ec20ecac2f9090908ad74`.
- New client `AndroidManifest.xml`: Git blob `b1463e397949115682fd1cdfbe304d9f9d2d06e5`.
- Launcher3 `ManagedPolicyController.java`: Git blob `cd049432c37ea3859b6e9bc3c42a088ef34c4311`.
- Release signing recovery guide: Git blob `80d6693f5d567a24ab7536b7d99a065af0e76297`.
- Previous legacy v0.3.0 `apksigner` report: Git blob `70b251aee9f79c78a44e5e57de45dbe931940f17` (v1 **false**, v2/v3 true, signer different from Lineage 2).

These are **Git object SHA-1 IDs**, not source-file SHA-256 transfer checksums. No files have been migrated or deleted. Obtain byte-level SHA-256 for each file at actual transfer/readback time.

## Production identity and rollback guard

- Frozen production identity after v0.5.2: `BlazeRental-production-lineage2`, certificate SHA-256 `1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25`.
- v0.5.2 production versionCode `50200`; v0.5.3 production versionCode `50300`; v0.5.3 rescue versionCode `50301`.
- A new upgrade required to install over the rescue variant must reserve **at least `50302`** rather than simply reusing `50300`. The version reservation must be reconciled with current release ownership before allocation.
- Older v0.4 signers and v0.3.0 signed assets are **not** compatible with the Lineage-2 production in-place upgrade without Android-supported signing proof. Do not relabel a debug or independently signed APK as an upgrade.
- Never fetch, create, or publish keystores in this audit. Production signing is a separate closed gate.

## APK contract verification

Requires `python3`, `aapt` and `apksigner` from the Android SDK Build Tools. The verifier is **read-only**: no `adb`, device provisioning, APK modification or signing.

```bash
# Pure host tests; no emulator, Docker or APK required.
python3 -m unittest discover \
  -s experiment/openwrt/BlazePwifi/android/BlazeRentalLauncher/tests/validation \
  -p 'test_*.py' -v

# Against a real signed Lineage-2 production APK, once authorized and available:
python3 experiment/openwrt/BlazePwifi/android/BlazeRentalLauncher/tools/verify_apk_contract.py \
  path/to/BlazeRental.apk --mode production --min-api 21 \
  --minimum-version-code 50300

# For a new installer supporting upgrades from rescue code 50301:
# ... add --minimum-version-code 50302

# Debug APKs have a different install package and signing identity.
python3 experiment/openwrt/BlazePwifi/android/BlazeRentalLauncher/tools/verify_apk_contract.py \
  path/to/BlazeRental-debug.apk --mode debug --min-api 21
```

Validation failures are nonzero exit status. The tool checks package, manifest min SDK, minimum version code, v1-signing result for API levels prior to 24, exactly one signer, production certificate matching Lineage 2, APK SHA-256, and native-library ABI declarations. It passes `--min-sdk-version` to Android's **actual** `apksigner verify`, not merely a manually parsed report. Optional `--required-abi arm64-v8a` checks embedded libraries when they exist. If none exist, it explicitly records that observation instead of falsely asserting physical ABI compatibility.

**Why v1 matters:** Android 5.0/6.0 require JAR/v1 signature compatibility. The older v0.3.0 report records v1 disabled, and its separate app min SDK is 26. The v0.5.3 signing workflow explicitly enables v1/v2/v3, but the actual signed APK still requires verification. See [Android `apksigner` documentation](https://developer.android.com/tools/apksigner).

## Evidence boundaries and next gates

- Host pure-Python tests establish only local source-validator behavior. Real signed-APK scanning **NOT EXECUTED** until an APK is retrieved and Android SDK Build Tools are available.
- Emulator startup, actual installation, runtime API21/API23 compatibility, Device Owner provisioning, Work Profile, unlock/reversal, physical ARM/ARM64 and OEM restrictions: **NOT EXECUTED** in this audit.
- Existing PR #289 has separate historical API27 instrumentation and CI evidence, **not** proof about these new tests or API21 support.
- `HQarroum/docker-android` and `google/android-emulator-container-scripts` may be used only with verified KVM/container capability and pinned images; the current local environment has no Docker/ADB/Android SDK and outbound Git clone DNS is unavailable. `ReactiveCircus/android-emulator-runner` is already wired in the existing isolated API27 workflow. Dockerized Device Owner testing must use disposable fresh images and confirm both policy application and recovery.
- Keep all related PRs draft and the full Phoenix production NO-GO until independent QA, signed physical install/upgrade, controller-ledger security, migration route, and operator recovery approval.
