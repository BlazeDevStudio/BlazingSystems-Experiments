# Public preview signing

`preview-signing.p12.base64` is a deliberately public, debug-only preview identity (password `android`, alias `blazing-preview`). It lets future CI previews update preview 2 while preserving the app's library and settings. It must never sign a production release.

Preview 1 used an ephemeral CI debug identity. Its private key was not retained, so preview 2 cannot be installed as an in-place upgrade of preview 1. Export any wanted BlazeViz presets before uninstalling preview 1; install preview 2 once, then subsequent previews can retain this identity. The release workflow records actual certificate fingerprints.
