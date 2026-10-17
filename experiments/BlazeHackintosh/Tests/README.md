# Tests

Run `python -m unittest discover -s Tests -v` from the project directory.
Tests cover minimum taxonomy count, explicit Intel/AMD SKU mappings, unknown CPU fallback,
unverified boot classification, malformed catalog rejection, device-ID redaction and scanner privacy fields.

This is software-unit-level evidence only, not verification of actual Hackintosh booting or image integrity.
Windows CLI packaging is separately handled by GitHub Actions.
