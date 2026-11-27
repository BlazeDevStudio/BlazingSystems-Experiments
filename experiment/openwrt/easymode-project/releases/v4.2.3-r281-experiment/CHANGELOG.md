# Change history

## 4.2.3 — 2026-10-04

Added actual CP signal-LED control: native restore, metric thresholds, timed/permanent asynchronous blinking. Browser save, metric levels, timed expiry and restored modem service passed. CP helper transfer is bounded, hash-checked and RAM-only. Health LED work uses the existing radio cache and a 12-second deadline. Private immutable-root candidate rebuilt and verified for 2,286 paths. Native recovery kit can retrieve both current CP records and validate the key before one unlock attempt; already-unlocked live path and simulated branch guards passed. No flash/reset test is claimed.

## 4.2.2 — 2026-10-04

Added independent repeater AP name, custom/inherited/open security, radio and enable controls. Added explicit shared-login compatibility for a captive upstream that rejected relayed client addresses. Verified portal redirect, final page, DNS and eight page assets from a DHCP relay client. Preserved newer user AP settings. Added bounded raw probe history. Private reset-default candidate passed structural and filesystem checks; no flash/reset test is claimed. USSD remains carrier/modem-unresponsive.

## 4.2.1 — 2026-10-04

Reconciled against the user's live 4.1.4 installation, preserving its newer UI. Added dedicated repeater scope, upstream DHCP isolation, captive portal compatibility and independent recovery-probe routing. Fixed scan deadlock, security classification, navigation races, band validation and diagnostic worker completion. Verified a live speed/CA trial reverted a slower result and restored connectivity. See the audit for remaining gaps.

## 4.2.0 — development checkpoints, 2026-10-03/04

Intermediate on-device scan/repeater and button-audit revisions. Superseded by 4.2.1; no standalone firmware image was released.
