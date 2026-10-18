# Production evidence URL validation

The production-gate ledger accepts only syntactically valid public HTTPS evidence URLs. The `release_gates.py` validator rejects empty or malformed URLs, embedded credentials, fragments, control characters, non-ASCII characters, invalid/nonstandard ports, literal IP addresses, and local/internal-only hostnames. It performs no DNS resolution, network request, download, or executable invocation.

**Scope limitation:** URL syntax does not authenticate evidence, identify an upstream publisher, prove licenses or hashes, establish Windows CI correctness, or demonstrate physical boot and rollback. An attacker can host misleading content at a syntactically valid public HTTPS URL. Reviewers must independently validate every claim against actual signed artifacts, authoritative upstream identities, workflow commit SHAs, and hardware test records.

Regression tests live in `Tests/test_release_evidence_url.py`. They check valid links, malformed/local links, invalid URLs embedded in a release-gate manifest, the exact required gate inventory, and preservation of the blocked state. Test results must be verified from a GitHub Actions run for the exact source commit before being recorded as CI evidence.

Do not replace `Production/RELEASE-GATES.json` with any synthetic fixture. The validator does not promote production gates, authorize physical disk writes, or redistribute macOS.
