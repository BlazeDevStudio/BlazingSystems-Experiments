# EasyMode baseline

Canonical stable baseline recovered: **4.1.4**.

- Known-good R281 backend registered `ubus` object `blaze` and `blaze.status`.
- R281 ucode constraints: avoid `args={}`, router-side `??`, and the previously failing 3-variable `for ... in`.
- Validate executable ucode/rpcd code with the target router's `/usr/bin/ucode` where practical.
- 4.1.4 introduced transactional preflight/rollback behavior.
- Hardware-only verification remains for Wi-Fi scan, modem AT/bands, WAN failover/balance, watchdog, SMS and USSD.

The six-edition shared-core work begins at **5.0.0-alpha.1** and does not replace 4.1.4 as the known hardware baseline until physical verification is completed.
