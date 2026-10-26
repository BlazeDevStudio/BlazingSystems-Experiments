# Blaze ThreadHarbor — real-product gap audit (2026-10-26)

Status: **EXPERIMENTAL / NOT ACCEPTED / NOT RELEASE-READY**.
Source branch: feature/threadharbor-v0.1.0-preview, draft PR #209.
The previous Android 35 emulator "PASS" proved only an app-owned fixture round trip, not live messaging, full browser acceptance, or physical-device quality. The initial v0.1.0 debug APK must NOT be promoted as the requested utility.

## Required original product
- Real Chromium/System WebView browser with persistent session, usable tabs, history, bookmarks, downloads, uploads, permissions and external fallback.
- A **separate semantic interpretation engine** translating actual *authorized, compatible* site features into independently rendered Compose Chats/Calls/Gallery/Downloads/Files/Browser/Settings without exposing passwords/PINs.
- Native-to-website actions must be confirmed by the website's observed outcome, never by successful JavaScript invocation alone.
- Reliable downloads and local storage, redirect-safe authorization, explicit Save As, validated resume, file management and media gallery.
- Observable unsupported/failure modes. No mocked conversation, fake live delivery, bypass of authentication, Meta impersonation or silent third-party adapter.

## Source-level findings before corrections
1. Default landing screen was a two-message **static fixture**, with "Send" implemented only against app-owned fixture DOM. **Critical misrepresentation risk**.
2. Browser WebViews lived exclusively under a conditional Composable; switching to another native screen disposed them and their in-memory session/back stack. **P0 browser usability bug**.
3. Browser had no saved tab URLs, bookmarks or history; initial page example.org, basic URL field.
4. DownloadManager items were unlabeled numeric IDs with no open/retry/cancel controls; no Save As, authenticated transfer policy, Range/If-Range validators, crash resume.
5. SAF Files only listed a single selected folder, no nesting/import/create/rename/delete.
6. Gallery displayed one picked image; no indexing, albums, video or file management.
7. Calls merely declared unsupported.
8. CI tested controlled fixture and startup, **not** actual site semantics or physical Android. The previous claims cannot satisfy the release contract.

## Implemented on this development branch after audit (source changes, not production acceptance)
- Startup opens **Browser** instead of demo Chats. The fixture is explicitly labeled **Chats (Lab)** and remains isolated from third-party browsing.
- Browser remains composed (zero-size, noninteractive offscreen) when switching native tools. WebViews are not intentionally destroyed by a tab switch.
- Basic persistent open-tab URLs, selected tab, URL history and bookmarks using app-private Android preferences; tabs limited to 12, and user-gesture-created website popup support is attempted. **Does not preserve POST states, WebView history stacks after process death or independent cookie profiles**.
- Basic download entries show names/status/bytes and support opening completed items, retrying failed HTTP(S) transfers and cancelling queued/running ones. **No claimed true pause/resume, Save As, authenticated transfer or validated resume**.
- SAF folder navigation with durable permission attempts, importing a picked document, creating folders, selecting and renaming entries, and deleting only after confirmation. **No claimed bulk operations, ZIP, copy/move or Trash**.
- Normal browser still deliberately has no injected JavaScript bridge; isolated fixture bridge remains restricted to appassets origin and main frame.
- Session cookies are **not** forwarded to Android DownloadManager because redirect hops are not enforced by current code. Avoid accidental bearer-cookie forwarding to other origins.

## Acceptance gates before distributing a replacement APK
- [ ] Exact development head builds with Kotlin/Gradle errors = 0.
- [ ] Android 35 emulator launches with Browser first and verifies control availability.
- [ ] Android emulator creates a second browser tab, moves to Chats (Lab), executes isolated bridge regression, returns to Browser with two tabs retained.
- [ ] Process recreation retains saved URLs/bookmarks without leaking tokens; invalid saved JSON is rejected safely.
- [ ] Real public HTTPS navigation, page error and file upload validated. Embedded SSO/login differences reported rather than bypassed.
- [ ] Normal HTTP and failure/cancel/retry system downloads exercised on an actual emulator, with accurate status and file open behavior.
- [ ] SAF document-provider create/import/rename/delete/revocation/nested navigation exercised and test evidence attached.
- [ ] Dedicated redirect-safe range downloader developed with ETag/Last-Modified+Content-Range validation, durable checkpointing, pause/resume and Save As.
- [ ] Site-adapter compatibility and user consent review; test an authorized **real site** separately from fixture, with no credentials intercepted.
- [ ] Calls/voicemail, complete gallery, profiles and other nonimplemented features must stay disabled or explicitly unsupported.
- [ ] Physical Android device tests, crash/low-storage/slow-network tests, privacy/security review and independent signoff.

Keep PR #209 **draft**. Do not merge or release as production from mere compile/fixture test success.
