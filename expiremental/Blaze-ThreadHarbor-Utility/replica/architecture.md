# ThreadHarbor v0.1.0 architecture

- Engine A: Chromium-based Android System WebView for general browsing, cookie and DOM storage managed by WebView.
- Engine B: separate app-owned test WebView served through WebViewAssetLoader. WebViewCompat origin-filtered WebMessageListener normalizes visible fixture DOM into ObservedMessage.
- Native rendering: Jetpack Compose independently renders snapshot state and pending action status.
- Reverse path: user Send -> unique id -> evaluateJavascript only against pinned controlled fixture -> MutationObserver -> bridge -> observed id/text equality. No duplicate retry.
- File access: SAF grants; no broad storage permission.
- Download foundation: Android DownloadManager queue. Full resumable downloader remains milestone E.
- Offline inspection metadata: local Android preferences and user-controlled JSON export.
- Trust: arbitrary browser pages get no injected HarborBridge; Meta-specific adapter disabled.

## Exit criteria
A. Functional initial browser navigation and debug APK build — compile evidence complete, emulator pending.
B. Fixture Web->Native->Web->Observed confirmation — model implemented, synthetic regressions pending.
C. Permission for real Facebook observation — not established.
D-G. Advanced downloads, gallery, file moves, calls — incomplete.
H. Debug preview APK — compiled; no physical device acceptance.

No backend SQL schema: app is local-first and does not host messages or financial data.
