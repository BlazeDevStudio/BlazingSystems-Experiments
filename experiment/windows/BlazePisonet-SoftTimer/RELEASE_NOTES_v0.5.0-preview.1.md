# BlazePisonet SoftTimer v0.5.0-preview.1

Development candidate only. No production release or customer deployment is authorized.

This candidate adds a FOG management page for Windows host and image inventory and explicitly confirmed deployment scheduling. It prefers FOG 1.6 Bearer authentication, supports a FOG 1.5 global/user token pair, requires HTTPS outside localhost, and never saves API tokens to configuration. It does not provision PXE, iSCSI targets or live diskless Windows boot.

FOG integration has only fake-server contract tests and Windows build/installer CI until a self-hosted FOG server and approved noncustomer Windows clients are validated. Diskless boot additionally needs iSCSI and PXE hardware acceptance.
