# Production acceptance gates

`RELEASE-GATES.json` is the machine-readable definition of **all** required
BlazeHackintosh production capabilities. No `alpha`, `preview`, CI-green build,
automatically generated config, QEMU smoke test or source commit satisfies
hardware acceptance on its own.

Run:

```powershell
BlazeHackintosh-Toolkit.exe release-readiness
```

It prints a JSON report with `production_ready: false` and a complete blocker
list and exits with code 2 while any required gate remains unverified.
Every gate remains required; the tracker does not permit excluding items from
the list to obtain a green verdict. Use independent review for evidence links;
a URL being present is not proof that it substantiates the claim.

When genuine verifiable evidence exists, update the precise gate entry and
include its source URL. Production publication must additionally require
physical UEFI/boot/usable macOS acceptance on explicitly identified compatible
hardware, signed deliverables, safe image readback/rollback and all other gates.

Use this tracker together with `../DEVELOPMENT-HANDOVER.md`, `../docs/KNOWN-ISSUES.md`
and GitHub Actions. The hourly development automation must not skip blockers
or declare finished solely based on this parser's result.
