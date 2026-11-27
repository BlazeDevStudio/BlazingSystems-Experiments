# Validation scope

This profile is based on the same shared rental libraries exercised by `tests/rental.sh`.

The main BlazePwifi source includes regression coverage for HMAC enrollment, signed status policy, app inventory, allowed-package policy, managed-phone admin password, preferred vendo, coin replay/idempotency, expired-device synchronization, rename, additive lease grants, expiry, and rental event history.

R281 deployment validation checks board/release, the existing uHTTPd document root and CGI prefix, HTTPS availability, payload SHA-256 before activation, shell syntax, and safe rollback of the additive controller listener.

The installer does not write network/firewall/wireless/blaze configuration.

A physical Android Device Owner enrollment and physical ESP controller remain hardware validation steps.
