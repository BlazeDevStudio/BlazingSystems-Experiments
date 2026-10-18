# Experimental staged-file audit

Run `python stage_audit.py --folder BlazeEFI-Example` from the BlazeHackintosh project directory against an existing research output.

This standalone, read-only audit checks the local unsigned SHA-256 ledger, directory inventory, and research-only safety marker. Exit code 0 means the local bytes match the recorded hashes; exit code 2 means a mismatch or unsafe input. It never verifies boot, component publishers, or recovery.

This feature does not write to a physical disk. Do not treat a matching unsigned manifest as proof of trusted binaries or physical boot readiness. Independent hardware and rollback acceptance remain required.
