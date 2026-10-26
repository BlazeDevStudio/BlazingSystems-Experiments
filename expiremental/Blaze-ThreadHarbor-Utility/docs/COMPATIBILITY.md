# Compatibility and evidence gate — 2026-10-26

| Component | Implementation | Verification |
|---|---|---|
| Chromium WebView tabs, navigation, file upload | Initial code | Android launch not yet proven |
| JavaScript semantic observer | App-owned fixture only | Requires Android build/device run |
| Native UI from normalized messages | Compose code | Requires Android device run |
| Native send and fixture DOM confirmation | Action IDs, no retry, observed-state check | Controlled fixture only |
| Facebook native messaging | Disabled | No authorized integration evidence |
| Facebook login in embedded browser | Best effort website mode | Provider may deny WebView |
| Meta calls/voicemail/recording | Disabled | No supported media path shown |
| Browser system downloads | Android DownloadManager | Not advanced reliable downloader |
| Save As / HTTP Range restart validator | Unimplemented | Not tested |
| Files | SAF selected-folder listing and open | Device run pending |
| Gallery | SAF image selection/preview | Device run pending |
| Inspection | Local text fields + JSON export | Device run pending |

Never claim fixture observation means a message reached Facebook. No webpage scripting or credentials are harvested from Facebook. This independent product is not official or endorsed.
