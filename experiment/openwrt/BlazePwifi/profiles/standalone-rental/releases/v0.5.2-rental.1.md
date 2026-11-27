# BlazePwifi Standalone Rental Server v0.5.2-rental.1

Stable hotfix over v0.5.2-rental.

## Fixed: CSRF validation / QR enrollment

On some R281/uHTTPd paths, an authenticated Rental session could work for read-only calls while mutating admin calls such as `rental_device_qr` failed with `csrf validation failed`.

The Rental UI now:

- sends CSRF in both `X-Blaze-CSRF` and the form-urlencoded `csrf` field;
- uses explicit same-origin credentials;
- disables request caching;
- refreshes the current authenticated session and retries once on a CSRF mismatch;
- reports QR renderer exceptions visibly instead of leaving a blank QR area.

No server API compatibility break is introduced.

## Credentials

Fresh install and the Windows reset utility remain:

```text
Username: admin
Password: admin
```

All R281 BusyBox compatibility fixes from v0.5.2-rental remain included.
