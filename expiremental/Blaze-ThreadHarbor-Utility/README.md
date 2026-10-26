# Blaze ThreadHarbor Utility — v0.1.0 Preview (development)

Independent Android application by Blaze Systems. Not affiliated with or endorsed by Meta/Facebook.

## Scope of this branch
- Android System WebView full-browser navigation with tabs and persistent website-managed storage.
- Origin-locked semantic observation of **app-owned fixture content only**.
- Independently rendered Jetpack Compose chat interface reading normalized fixture messages.
- Native reply dispatched to the controlled fixture, with confirmation **only when the mutated fixture DOM is observed**.
- Files via Android Storage Access Framework; basic image picker/gallery.
- Browser-initiated system DownloadManager queue and status display.
- External Facebook Messages browser fallback.

**No live Facebook messages are read.** Facebook site adapter, authenticated media, voicemail, call recording, download pause/resume, file move/copy/ZIP, true multiple browser profiles, and hardware-device acceptance are **not verified or implemented**.

## Build
Run from this project folder using JDK 17, Android SDK Platform 36 and Gradle 8.13:
`gradle :app:assembleDebug`
The CI job uploads the built debug APK and its SHA-256 if compilation succeeds.

## Security design
The one privileged WebMessageListener is installed only on the controlled `https://appassets.androidplatform.net` fixture WebView. The general browser runs in separate WebViews without a native JavaScript bridge. Messages larger than 128 KiB are discarded, only the main frame is trusted, and credentials, cookies and encryption PINs are never extracted. Unsupported site functions remain unavailable.

## Known limitations
Android WebView does not universally support embedded login for identity providers. Open Facebook externally when login or browser support fails. The preview is not an official messaging client. A DOM observation in the fixture is not evidence of remote message delivery.
