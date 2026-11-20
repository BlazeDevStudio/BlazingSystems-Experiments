# PHX-MASTER UTC17 — ImageBuilder user-namespace least-privilege decision

**Decision state:** APPROVED FOR RELEASE IMPLEMENTATION TRIAL + INDEPENDENT QA REVIEW ONLY  
**Production state:** **NO-GO**  
**Owner scope:** `coordination/phoenix/` only

## Exact repository and source identity

- Experiments default branch: `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments development branch: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- PHX-MASTER branch before this commit: `phoenix/master-coordination@f8f5169b0f06f52f19f6889fd66ae84bb9461a93`; PR #288 remains open/draft against main.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, open/draft, five PR workflows queued with no jobs.
- COE RELEASE PR #31: `phoenix/release-imagebuilder-failclosed-20261115@411eeb103cfeebc589f6dc9c48b1789ebb047913`, open/draft, based on #26.

Exact COE #31 blobs read from its current branch:

| File | Blob |
|---|---|
| `tools/run_imagebuilder_sandbox.py` | `605146f635571baabab4534950ecb0e591f2db54` |
| `tools/package_appliance_firmware.py` | `f819ef1cd5265ff026e8a98ad9541c36ed087617` |
| `tools/test_package_appliance_firmware.py` | `92d8b4c14ce72503cea673b9e4aad116cbff7b11` |
| `.github/workflows/release-imagebuilder-sandbox.yml` | `e350b17a0cc2abac4d04a5fd98e5fabeab762934` |

## 1. Master decision

Approve the **unprivileged single-ID user-namespace model** as the only preferred implementation trial for this hosted-runner boundary:

1. Start the sandbox runner as the invoking non-root build user. Do not elevate the runner with `sudo`.
2. Inside the user namespace, namespace UID 0 and GID 0 may map only to that same invoking host UID and GID, one ID each. The host-side build output must remain owned by the invoking user.
3. Do not require `SUDO_UID`/`SUDO_GID`, `newuidmap`/`newgidmap`, subordinate UID/GID ranges, setuid helpers, root host execution, or broader host identity grants for this model.
4. Keep the owner probe and path checks. If the kernel/host cannot create the required unprivileged namespace, fail closed with a clear diagnostic. Do not fall back to a direct unsandboxed Make invocation.
5. If the hosted runner cannot support this model, the permitted alternative is a disposable, isolated, no-secret runner whose user-namespace policy is explicitly provisioned and independently reviewed. Do not edit shared runner `/etc/subuid` or `/etc/subgid` with broad ranges.

This is an architecture decision to **try and verify** the least-privilege model. It is not evidence that bubblewrap accepts this mapping on the current Ubuntu image, not sandbox acceptance, and not permission to weaken any check. PHX-QA must independently review the design and exact resulting source SHA before the implementation is considered accepted.

## 2. Why the current implementation is blocked

The current runner requires `os.geteuid() == 0`, reads `SUDO_UID` and `SUDO_GID`, requires `newuidmap` and `newgidmap`, blocks bubblewrap on `--userns-block-fd`, then invokes each helper to map namespace ID 0 to one host ID. The mapping request is a single ID, but the helper still requires a permitted subordinate mapping on this hosted runner.

The exact-head sandbox job failed before ImageBuilder execution:

- [COE #31 sandbox run 44137935105](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137935105), job `134232499311`.
- Exact diagnostic: `newuidmap: uid range [0-1) -> [1001-1002) not allowed`.
- The job ran 52 tests and ended with 20 failures because the namespace mapping gate prevented the real-bubblewrap integration paths from starting.
- The 1-second delayed-write timeout regression did not reach its timeout assertion. The timeout unit tests are not a substitute for the blocked real-bubblewrap test.

Scoped exact-head evidence:
- [Shared/hardware run 44137935148](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137935148): SUCCESS; scoped only.
- [Case-collision run 44137935308](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44137935308): SUCCESS; scoped only.

## 3. Boundary claims that remain limited

The current source uses a read-only host-root bind and a writable bind for the disposable ImageBuilder directory. It also uses `--share-net`. Therefore:

- This is, at most, a filesystem write-confinement boundary.
- The host root remains readable; this is not a confidentiality boundary.
- The host network remains shared; network isolation is not present or claimed.
- Do not run untrusted build inputs on a runner containing secrets, credentials, customer data, or other sensitive readable files. Use a disposable no-secret environment.
- Do not describe the result as a complete security sandbox or production-grade build isolation.

The generated operator wrapper already dispatches through the runner at the current #31 source head. That source-level correction is distinct from the failed runtime acceptance.

## 4. Independent QA acceptance required

PHX-QA must review and verify the same exact candidate SHA and prove all of the following:

- The runner starts non-root and does not use `sudo`, `SUDO_UID`/`SUDO_GID`, `newuidmap`/`newgidmap`, or subordinate-ID grants.
- The namespace mapping is exactly one UID and one GID, each mapped to the invoking build user's host identity; no additional host IDs are exposed.
- The host-side ownership probe is a regular file owned by the invoking UID/GID, and is removed safely.
- A malicious synthetic Makefile, including nested symlink writes, cannot alter a sentinel outside the disposable writable ImageBuilder bind.
- The timeout regression reaches its real-bubblewrap path and proves TERM/KILL cleanup prevents delayed descendant writes after the runner returns.
- Missing bubblewrap, disabled user namespaces, mapping failure, malformed namespace information, path escape, or owner mismatch all fail closed; there is no unsandboxed fallback.
- The generated operator entrypoint and the dedicated CI test use the same runner path.
- The test host contains no secrets or sensitive files. Network sharing remains explicitly documented.

Until QA returns independent evidence, runtime sandbox acceptance remains BLOCKED.

## 5. Separate P0: ULA remains invalid

The current packager still emits `fd00:db8:blaze::/48`, which is not a valid IPv6 prefix because `blaze` is not a hexadecimal hextet. This is separate from the namespace decision. Preserve Architecture Contract §6.9: a valid RFC 4193 site-specific /48 must be generated or accepted and durably persisted as installation identity, shared by devices on the same site, and stable across reboot/upgrade/restore. Do not substitute one globally hardcoded prefix. PHX-RELEASE owns implementation; PHX-CORE/COE own provisioning design; PHX-QA independently verifies; PHX-HARDWARE validates target behavior only after authorization.

## 6. Master checks and limits

- Bounded exact-blob source assertions: **14/14 PASS**. These assert the current root requirement, SUDO identity requirement, helper requirement, single-ID helper arguments, read-only host bind, writable builder bind, shared network, timeout/process-group code, generated-wrapper runner dispatch, invalid ULA literal, workflow runner image/helper installation, and presence of the real-bwrap timeout/symlink regressions.
- Full Master Python suite: **NOT RUN**. A local Git checkout was attempted and failed because the execution container could not resolve `github.com`; no test suite result is claimed.
- Master PR-triggered CI: no run returned for the current Master head before this commit.
- Cleanup issue #266 remains the cleanup-first checklist; its last edit is historical and its checkboxes are not evidence of current completion.
- The private registry and newer private corrections are not accessible through the exposed connector. No older Library snapshot was substituted and no private Drive IDs or contents were copied into GitHub.
- `OWNERSHIP_ROUTES.json` remains unchanged, `DRAFT_REVIEW_ONLY`, with PHX-MASTER target `null`. No source/destination file was moved or copied.

## 7. Next exact action

PHX-QA: review the single-ID unprivileged namespace decision and publish an independent accept/reject with the exact security tests above. PHX-RELEASE: implement only the approved trial on existing COE #31, preserve fail-closed behavior, and rerun the dedicated exact-head bubblewrap suite on the actual Ubuntu runner. If user namespaces are not available, stop and propose the isolated ephemeral-runner alternative; do not add broad subordinate-ID ranges or bypass the sandbox.

**No Codex, merge, release, signing, secret provisioning, firmware flashing, physical testing, payment operation, migration, or production approval occurred. PRODUCTION NO-GO.**
