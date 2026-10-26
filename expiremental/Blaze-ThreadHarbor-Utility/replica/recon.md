# Independent compatibility reconnaissance (2026-10-26)

This is not a Facebook clone. Target is a user-authorized, independent Chromium browser with an optional, explicitly permitted semantic adapter. Third-party website markup and proprietary source are not redistributed.

| Screen | Entry | Evidence |
|---|---|---|
| S01 Native Chats | Main navigation | App-owned fixture only; no third-party authorization |
| S02 Browser | Browser tab | Android System WebView / supported Web APIs |
| S03 Downloads | Downloads tab | System DownloadManager |
| S04 Files | Files tab | Storage Access Framework |
| S05 Gallery | Gallery tab | Android picker and ImageView |
| S06 Inspection | Inspection tab | Locally stored manual metadata / JSON |
| S07 Settings | Settings tab | External browser fallback |
| S08 Calls | Calls tab | Explicit UNSUPPORTED state |

Flow F01 controlled page mutation to native model, native action back to fixture. Flow F02 browser navigation / tabs / external fallback. Flow F03 basic native HTTP transfer and status. Flow F04 SAF folder browse. Flow F05 offline inspection metadata export.

**Observation boundary:** only publicly documented Android/Web APIs and an app-authored fixture are observed. Facebook DOM structure, real messages and platform permission grants are unknown, not inferred. Meta integration remains blocked until formally reviewed.
