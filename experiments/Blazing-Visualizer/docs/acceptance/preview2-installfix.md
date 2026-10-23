# Side-by-side Preview 2 installation fix

This branch starts from the exact validated standard Preview 2 source commit `48c229e607e7fdcab2f71c915c7f75102a1e9304` and changes **only** Android packaging, full qualification of app components and a new release/test workflow. The canonical Preview 2 package and its published release are unmodified.

Build command: `./gradlew :app:assembleDebug -PblazeSidecar=true`.

Output application ID: `com.blazingsystems.visualizer.preview2`. The source namespace stays `com.blazingsystems.visualizer`, including the fully qualified Activity and services in AndroidManifest.

Version name: `1.0.0-preview.2-side-by-side`. Signing uses the retained Preview 2 *public debug-only* identity; not a production key.

The release workflow verifies APK integrity, package ID, cert hash and both ABIs. It then installs **both original Preview 1 and this independent APK** on API26 and API36 Android emulators before publishing a direct GitHub Releases APK with SHA256SUMS. Never publish if either install test fails.

Caution: This app has separate settings, custom presets and data; it does not migrate Preview 1's state. Existing Preview 1 stays installed, but future regular-package updates will not update this side-by-side app. This is intentionally a temporary install compatibility build.

If a user still sees "App not installed" with the side-by-side package, obtain their Android version and the actual Android package manager failure reason via `adb install` (e.g. `INSTALL_FAILED_NO_MATCHING_ABIS` or storage shortage); do not assume signing conflict is the only cause.
