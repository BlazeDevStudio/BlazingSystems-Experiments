# Security policy for preview

- WebViewAssetLoader serves the local controlled fixture at https://appassets.androidplatform.net/assets/fixture.html.
- WebViewCompat.addWebMessageListener is restricted to that exact origin; only main-frame messages are accepted.
- Parser accepts snapshot + fixture-v1 adapter, limits payload length (131072 chars), message count (200), and displayed fields.
- Native send has a random action ID. Uncertain attempts remain UNVERIFIED and are never auto-retried.
- Browser WebViews never install HarborBridge and never receive filesystem bridge methods.
- Browsing cookies remain site/WebView-managed. The application does not read 2FA codes, passwords, encrypted chat PINs or key material.
- Native downloads use system DownloadManager without duplicating authentication cookies; protected/expired downloads may fail.
- No external calls or audio capture are implemented.
- Future isolation work: multiple browser profiles require a different process/data-directory suffix, not only a tab label.
- Production requires test evidence for WebView origin spoof attempts, redirects, lifecycle, storage revocation and device-specific behavior.
