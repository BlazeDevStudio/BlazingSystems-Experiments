#!/usr/bin/env python3
"""Guard release-capable workflows against unsafe concurrency and token scope."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/blazepwifi-build.yml"
WINDOWS_WORKFLOW = ROOT / ".github/workflows/blazepisonet-softtimer-release.yml"


def job_block(content: str, name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        content,
    )
    if not match:
        raise AssertionError(f"missing release job: {name}")
    return match.group(1)


def with_job_condition(content: str, name: str, condition: str) -> str:
    """Return a fixture with one exact job-level condition, replacing any prior one."""
    block = job_block(content, name)
    existing = re.search(r"(?m)^    if: .+$", block)
    replacement = f"    if: {condition}"
    if existing is not None:
        return content.replace(existing.group(0), replacement, 1)

    marker = f"  {name}:\n"
    if marker not in content:
        raise AssertionError(f"missing workflow job: {name}")
    return content.replace(marker, marker + replacement + "\n", 1)


def workflow_default_permissions(content: str) -> dict[str, str]:
    """Read only the top-level workflow permissions, not job overrides."""
    lines = content.splitlines()
    try:
        start = lines.index("permissions:")
    except ValueError:
        return {}

    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index] and not lines[index][0].isspace()
        ),
        len(lines),
    )
    permissions = {}
    for line in lines[start + 1 : end]:
        if line.startswith("  ") and not line.startswith("    ") and line.strip():
            key, separator, value = line.strip().partition(":")
            if separator:
                permissions[key] = value.strip()
    return permissions


def require_read_only_workflow_default(content: str) -> None:
    """Reject workflow-wide write scope that would be inherited by jobs."""
    actual = workflow_default_permissions(content)
    if actual != {"contents": "read"}:
        raise AssertionError(
            "workflow-level permissions must be exactly contents: read; "
            f"found {actual!r}"
        )


def require_softtimer_signing_steps_are_protected(content: str) -> None:
    """Require every production Authenticode step to retain its full release gate."""
    expected_names = (
        "RELEASE-SIGN sign portable executables before NSIS",
        "RELEASE-SIGN sign native Setup after metadata verification",
        "RELEASE-SIGN verify final signed packages before upload",
    )
    actual_names = tuple(
        re.findall(
            r"(?m)^      - name: (RELEASE-SIGN (?:sign|verify)[^\n]*)$",
            content,
        )
    )
    if actual_names != expected_names:
        raise AssertionError(
            "the SoftTimer workflow must expose exactly the three reviewed production "
            f"sign/verify steps in order; found {actual_names!r}"
        )

    expected_condition = (
        "github.event_name == 'push' && github.ref == 'refs/heads/main' "
        "&& github.ref_protected == true && env.VERSION != '0.4.0' "
        "&& vars.SOFTTIMER_RELEASE_APPROVED == 'true'"
    )
    for name in expected_names:
        marker = f"      - name: {name}\n"
        start = content.find(marker)
        if start < 0:
            raise AssertionError(f"missing SoftTimer signing step: {name}")
        end = content.find("\n      - name:", start + len(marker))
        if end < 0:
            end = len(content)
        block = content[start:end]
        condition = re.search(r"(?m)^        if: (.+)$", block)
        if condition is None or condition.group(1) != expected_condition:
            raise AssertionError(
                f"{name} must require the explicit protected-main release gate "
                "(push, protected main, non-0.4.0 version and SOFTTIMER_RELEASE_APPROVED)"
            )


class ReleaseWorkflowConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = WORKFLOW.read_text(encoding="utf-8")
        cls.windows_content = WINDOWS_WORKFLOW.read_text(encoding="utf-8")

    def test_running_push_or_dispatch_release_is_not_cancelled(self):
        self.assertIn(
            "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
            self.content,
            "only superseded PR validation runs may be cancelled; push/dispatch "
            "runs can contain publication-capable jobs",
        )
        self.assertNotIn("cancel-in-progress: true", self.content)

    def test_every_write_privileged_release_job_remains_branch_gated(self):
        cases = (
            ("production_import_signed_apk", "refs/heads/blazepwifi-v0.3.0-production", "[import-sign]"),
            ("publish_prerelease", "refs/heads/blazepwifi-v0.3.0-design", "[release]"),
            ("publish_release", "refs/heads/blazepwifi-v0.3.0-production", "[release]"),
            ("publish_v060_lab_preview", "refs/heads/blazepwifi-v0.6.0-audit-foundation", "[v060-lab-release]"),
        )
        for job, ref, marker in cases:
            with self.subTest(job=job):
                block = job_block(self.content, job)
                self.assertIn(f"github.ref == '{ref}'", block)
                self.assertIn(f"'{marker}'", block)
                self.assertIn("permissions:\n      contents: write", block)

    def test_windows_build_is_explicitly_read_only_and_publisher_isolated(self):
        build = job_block(self.windows_content, "build-windows")
        publisher = job_block(self.windows_content, "publish-release")

        self.assertIn(
            "permissions:\n      contents: read",
            build,
            "the Windows build job handles candidate binaries and signing inputs "
            "but must never inherit write scope from a future workflow-level change",
        )
        self.assertNotIn("contents: write", build)
        self.assertIn("permissions:\n      contents: write", publisher)
        self.assertEqual(
            self.windows_content.count("contents: write"),
            1,
            "only the separately gated publisher may receive repository write permission",
        )
        self.assertIn(
            "if: github.event_name == 'push' && github.ref == 'refs/heads/main' "
            "&& github.ref_protected == true && vars.SOFTTIMER_RELEASE_APPROVED == 'true' "
            "&& needs.build-windows.outputs.future_release_eligible == 'true'",
            publisher,
        )


    def test_windows_sdk_is_exactly_pinned_and_verified(self):
        marker = "      - name: Pin .NET 8 SDK"
        start = self.windows_content.find(marker)
        self.assertNotEqual(start, -1, "missing exact .NET SDK pin step")
        end = self.windows_content.find("      - name:", start + len(marker))
        if end < 0:
            end = len(self.windows_content)
        sdk_step = self.windows_content[start:end]
        self.assertIn('"version": "8.0.425"', sdk_step)
        self.assertIn('"rollForward": "disable"', sdk_step)
        self.assertIn(
            "$sdkVersion = (dotnet --version).Trim()",
            sdk_step,
            "the selected SDK must be observed, not inferred from setup-dotnet input",
        )
        self.assertIn(
            "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }",
            sdk_step,
            "a failed dotnet invocation must stop the workflow",
        )
        self.assertIn(
            "if ($sdkVersion -ne '8.0.425')",
            sdk_step,
            "unexpected SDK roll-forward must fail closed before restore/build",
        )


    def test_every_write_privileged_pisowifi_publisher_requires_protected_ref_and_approval(self):
        cases = (
            ("production_import_signed_apk", "BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED"),
            ("publish_prerelease", "BLAZEPWIFI_PRERELEASE_APPROVED"),
            ("publish_release", "BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED"),
            ("publish_v060_lab_preview", "BLAZEPWIFI_LAB_PREVIEW_APPROVED"),
        )
        expected_jobs = {job for job, _ in cases}
        actual_write_jobs = {
            name
            for name in re.findall(r"(?m)^  ([A-Za-z0-9_-]+):\n", self.content)
            if "permissions:\n      contents: write" in job_block(self.content, name)
        }
        self.assertEqual(
            actual_write_jobs,
            expected_jobs,
            "every write-privileged BlazePwifi job must be covered by the approval guard",
        )
        for job, approval_variable in cases:
            with self.subTest(job=job):
                block = job_block(self.content, job)
                condition = re.search(r"(?m)^    if: (.+)$", block)
                self.assertIsNotNone(condition, f"{job} must have an explicit job-level gate")
                expression = condition.group(1)
                self.assertIn("github.event_name == 'push'", expression)
                self.assertIn("github.ref_protected == true", expression)
                self.assertIn(f"vars.{approval_variable} == 'true'", expression)


    def test_blazepwifi_workflow_default_token_scope_is_read_only(self):
        require_read_only_workflow_default(self.content)

    def test_workflow_default_permission_guard_rejects_inherited_write_mutation(self):
        unsafe = self.content.replace(
            "permissions:\n  contents: read",
            "permissions:\n  contents: write",
            1,
        )
        self.assertNotEqual(unsafe, self.content)
        with self.assertRaisesRegex(AssertionError, "workflow-level permissions"):
            require_read_only_workflow_default(unsafe)


    def test_every_softtimer_production_signing_step_requires_protected_main_and_release_approval(self):
        require_softtimer_signing_steps_are_protected(self.windows_content)

        # Prove the guard catches a one-step approval-gate regression without
        # changing or executing any signing command or accessing credentials.
        unsafe = self.windows_content.replace(
            "&& vars.SOFTTIMER_RELEASE_APPROVED == 'true'",
            "&& vars.SOFTTIMER_RELEASE_APPROVED != 'true'",
            1,
        )
        self.assertNotEqual(unsafe, self.windows_content)
        with self.assertRaisesRegex(AssertionError, "explicit protected-main release gate"):
            require_softtimer_signing_steps_are_protected(unsafe)


    def test_negative_selftest_receives_shared_build_workflow_in_same_scope(self):
        cases = (
            (
                "RELEASE-SIGN test fail-closed negative controls",
                '. "$env:PROJECT_DIR/tests/ReleaseSigning/negative-selftest.ps1"',
            ),
            (
                "RELEASE-SIGN reject actual unsigned Setup in PR",
                '. "$env:PROJECT_DIR/tests/ReleaseSigning/negative-selftest.ps1" -ActualUnsignedSetup "release/BlazePisonet-SoftTimer-Setup-v$env:VERSION.exe"',
            ),
        )
        for step_name, invocation in cases:
            with self.subTest(step=step_name):
                marker = f"      - name: {step_name}"
                start = self.windows_content.find(marker)
                self.assertNotEqual(start, -1, f"missing release step: {step_name}")
                next_step = self.windows_content.find("\n      - name:", start + len(marker))
                if next_step < 0:
                    next_step = len(self.windows_content)
                block = self.windows_content[start:next_step]

                required = (
                    "$buildWorkflowPath = Join-Path $env:GITHUB_WORKSPACE '.github/workflows/blazepwifi-build.yml'",
                    "if (-not (Test-Path -LiteralPath $buildWorkflowPath -PathType Leaf))",
                    "$buildWorkflow = Get-Content -LiteralPath $buildWorkflowPath -Raw",
                    "if ([string]::IsNullOrWhiteSpace($buildWorkflow))",
                    invocation,
                )
                positions = tuple(block.find(fragment) for fragment in required)
                self.assertTrue(
                    all(position >= 0 for position in positions),
                    "the release-owned invocation must load and validate the exact shared "
                    "build workflow and define $buildWorkflow before dot-sourcing the existing "
                    "PISONET negative self-test",
                )
                self.assertEqual(
                    positions,
                    tuple(sorted(positions)),
                    "the shared workflow must be loaded and validated before the PISONET test runs",
                )
                self.assertNotIn(
                    'pwsh -NoProfile -File "$env:PROJECT_DIR/tests/ReleaseSigning/negative-selftest.ps1"',
                    block,
                    "a child pwsh -File process cannot inherit the caller's $buildWorkflow variable",
                )

    def test_pr_negative_selftest_stubs_git_tag_lookup_without_network(self):
        marker = "      - name: RELEASE-SIGN reject actual unsigned Setup in PR"
        start = self.windows_content.find(marker)
        self.assertNotEqual(start, -1, "missing PR-only negative self-test step")
        next_step = self.windows_content.find("\n      - name:", start + len(marker))
        if next_step < 0:
            next_step = len(self.windows_content)
        block = self.windows_content[start:next_step]

        required = (
            "if: github.event_name == 'pull_request'",
            "function gh {",
            "-notmatch '/git/ref/tags/'",
            "Write-Output 'HTTP/2.0 404 Not Found'",
            "$global:LASTEXITCODE = 1",
            '. "$env:PROJECT_DIR/tests/ReleaseSigning/negative-selftest.ps1" -ActualUnsignedSetup',
        )
        positions = tuple(block.find(fragment) for fragment in required)
        self.assertTrue(
            all(position >= 0 for position in positions),
            "the PR-only negative self-test must use a local gh function that admits only "
            "the synthetic missing-tag Git-ref response",
        )
        self.assertEqual(
            positions,
            tuple(sorted(positions)),
            "the local GitHub CLI stub must be defined before the PISONET test is dot-sourced",
        )
        function_start = block.find("function gh {")
        invocation_start = block.find(required[-1])
        function_body = block[function_start:invocation_start]
        self.assertIn(
            'throw "Unexpected GitHub CLI call in synthetic negative self-test:',
            function_body,
            "the local gh stub must reject unexpected commands instead of falling through to the real executable",
        )
        self.assertNotIn(
            "Get-Command gh",
            block,
            "the negative self-test must not resolve or invoke the real GitHub CLI",
        )

def require_softtimer_tag_ref_absence_before_publish(content: str) -> None:
    """Require an absent Git tag ref, not merely an absent Release object."""
    publisher = job_block(content, "publish-release")
    required = (
        '$tagLookupOutput = gh api -i "repos/$env:GITHUB_REPOSITORY/git/ref/tags/$releaseTag" 2>&1 | Out-String',
        "$tagLookupExit = $LASTEXITCODE",
        "if ($tagLookupExit -eq 0) {",
        "$tagHttpStatuses = @([regex]::Matches($tagLookupOutput, '(?m)^HTTP/[0-9.]+ ([0-9]{3})(?:\\s|$)'))",
        "if ($tagHttpStatuses.Count -ne 1 -or $tagHttpStatuses[0].Groups[1].Value -ne '404') {",
        "gh release create $releaseTag",
    )
    positions = tuple(publisher.find(fragment) for fragment in required)
    if any(position < 0 for position in positions):
        raise AssertionError(
            "SoftTimer publisher must prove the Git tag ref is absent with one unambiguous "
            "HTTP 404 before creating a release"
        )
    if positions != tuple(sorted(positions)):
        raise AssertionError(
            "SoftTimer Git-tag absence check must complete before gh release create"
        )


class SoftTimerTagAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.windows_content = WINDOWS_WORKFLOW.read_text(encoding="utf-8")

    def test_publisher_requires_absent_git_tag_ref_before_release_creation(self):
        require_softtimer_tag_ref_absence_before_publish(self.windows_content)

    def test_publisher_rejects_ambiguous_or_non_404_tag_lookup(self):
        status_predicate = (
            "if ($tagHttpStatuses.Count -ne 1 -or "
            "$tagHttpStatuses[0].Groups[1].Value -ne '404') {"
        )
        self.assertIn(status_predicate, self.windows_content)

        unsafe_status = self.windows_content.replace(
            status_predicate,
            status_predicate.replace("-ne '404'", "-ne '200'"),
            1,
        )
        self.assertNotEqual(unsafe_status, self.windows_content)
        with self.assertRaisesRegex(AssertionError, "one unambiguous HTTP 404"):
            require_softtimer_tag_ref_absence_before_publish(unsafe_status)

        unsafe_ambiguous = self.windows_content.replace(
            status_predicate,
            status_predicate.replace("Count -ne 1", "Count -lt 1"),
            1,
        )
        self.assertNotEqual(unsafe_ambiguous, self.windows_content)
        with self.assertRaisesRegex(AssertionError, "one unambiguous HTTP 404"):
            require_softtimer_tag_ref_absence_before_publish(unsafe_ambiguous)




SIGN_WORKFLOW = ROOT / ".github/workflows/blazerental-v053-lineage2-sign.yml"
RELEASE_STAGE_WORKFLOW = ROOT / ".github/workflows/blazepwifi-v053-release.yml"


def require_v053_manual_signing_gate(content: str) -> None:
    """Keep the Lineage 2 secret-bearing job on approved protected main only."""
    expected_default = {"contents": "read", "actions": "read"}
    if workflow_default_permissions(content) != expected_default:
        raise AssertionError(
            "v0.5.3 signing workflow defaults must remain contents: read and actions: read"
        )

    sign = job_block(content, "sign")
    if "contents: write" in sign:
        raise AssertionError("v0.5.3 signing job must not receive repository write permission")

    expected_condition = (
        "github.event_name == 'workflow_dispatch' "
        "&& github.ref == 'refs/heads/main' "
        "&& github.ref_protected == true "
        "&& vars.BLAZERENTAL_PRODUCTION_SIGNING_APPROVED == 'true'"
    )
    condition = re.search(r"(?m)^    if: (.+)$", sign)
    if condition is None or condition.group(1) != expected_condition:
        raise AssertionError(
            "v0.5.3 signing job must require workflow_dispatch on protected main "
            "and explicit BLAZERENTAL_PRODUCTION_SIGNING_APPROVED=true"
        )


def require_v053_release_permissions_are_isolated(content: str) -> None:
    """Keep write scope out of candidate staging and confine it to opt-in publication."""
    expected_default = {"contents": "read", "actions": "read"}
    actual_default = workflow_default_permissions(content)
    if actual_default != expected_default:
        raise AssertionError(
            "v0.5.3 release workflow defaults must be contents: read and actions: read; "
            f"found {actual_default!r}"
        )

    stage = job_block(content, "stage")
    publish = job_block(content, "publish")
    if "permissions:\n      contents: read\n      actions: read" not in stage:
        raise AssertionError("v0.5.3 stage job must explicitly remain read-only")
    if "permissions:\n      contents: write\n      actions: read" not in publish:
        raise AssertionError("only the opt-in publish job may receive contents: write")

    jobs_match = re.search(r"(?ms)^jobs:\n(.*)\Z", content)
    if jobs_match is None:
        raise AssertionError("missing v0.5.3 release jobs section")
    job_names = re.findall(r"(?m)^  ([A-Za-z0-9_-]+):\n", jobs_match.group(1))
    write_jobs = {
        name
        for name in job_names
        if "permissions:\n      contents: write" in job_block(content, name)
    }
    if write_jobs != {"publish"}:
        raise AssertionError(
            "the v0.5.3 publish job must be the only write-privileged job; "
            f"found {sorted(write_jobs)!r}"
        )

    expected_publish_condition = (
        "inputs.publish == true "
        "&& github.event_name == 'workflow_dispatch' "
        "&& github.ref == 'refs/heads/main' "
        "&& github.ref_protected == true "
        "&& vars.BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED == 'true'"
    )
    publish_condition = re.search(r"(?m)^    if: (.+)$", publish)
    if (
        "needs: stage" not in publish
        or publish_condition is None
        or publish_condition.group(1) != expected_publish_condition
    ):
        raise AssertionError(
            "v0.5.3 publisher must depend on successful staging, explicit opt-in, "
            "protected main and BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED=true"
        )
    if "gh release create" in stage or "gh release upload" in stage:
        raise AssertionError("candidate staging must not execute release publication commands")

    required = (
        'gh run download "$GITHUB_RUN_ID" --repo "$GITHUB_REPOSITORY" '
        "--name BlazePwifi-v0.5.3-release-stage --dir release-out",
        "sha256sum -c SHA256SUMS",
        'test "$(jq -r .commit release-out/RELEASE-MANIFEST.json)" = "$SHA"',
        'test "$(jq -r .signing_run_id release-out/RELEASE-MANIFEST.json)" = "$SIGN_RUN"',
        "gh release create",
        "gh release upload",
    )
    positions = tuple(publish.find(value) for value in required)
    if any(position < 0 for position in positions):
        raise AssertionError(
            "publisher must download the current run's stage artifact, recheck its "
            "checksum/manifest identity, then publish the staged README and assets"
        )
    if positions != tuple(sorted(positions)):
        raise AssertionError("publisher must verify the staged artifact before any release mutation")
    if "NOTES=release-out/README.md" not in publish:
        raise AssertionError("publisher must use the staged release notes, not a second checkout")
    expected_expressions = (
        "GH_TOKEN: " + chr(36) + "{{ github.token }}",
        "SHA: " + chr(36) + "{{ inputs.candidate_sha }}",
        "SIGN_RUN: " + chr(36) + "{{ inputs.signing_run_id }}",
    )
    if any(expression not in publish for expression in expected_expressions):
        raise AssertionError("publish job must use live GitHub expressions, not escaped literal strings")


class BlazePwifiV053PublishPermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = RELEASE_STAGE_WORKFLOW.read_text(encoding="utf-8")
        cls.sign_content = SIGN_WORKFLOW.read_text(encoding="utf-8")

    def test_manual_v053_signer_requires_protected_main_and_explicit_approval(self):
        require_v053_manual_signing_gate(self.sign_content)

    def test_signing_gate_guard_rejects_each_missing_admission_control(self):
        expected = (
            "github.event_name == 'workflow_dispatch' "
            "&& github.ref == 'refs/heads/main' "
            "&& github.ref_protected == true "
            "&& vars.BLAZERENTAL_PRODUCTION_SIGNING_APPROVED == 'true'"
        )
        safe = with_job_condition(self.sign_content, "sign", expected)
        require_v053_manual_signing_gate(safe)
        mutations = (
            ("github.event_name == 'workflow_dispatch'", "github.event_name == 'push'"),
            ("github.ref == 'refs/heads/main'", "github.ref == 'refs/heads/feature'"),
            ("github.ref_protected == true", "github.ref_protected == false"),
            (
                "vars.BLAZERENTAL_PRODUCTION_SIGNING_APPROVED == 'true'",
                "vars.BLAZERENTAL_PRODUCTION_SIGNING_APPROVED != 'true'",
            ),
        )
        for old, new in mutations:
            with self.subTest(mutation=old):
                unsafe = safe.replace(old, new, 1)
                self.assertNotEqual(unsafe, safe)
                with self.assertRaisesRegex(AssertionError, "protected main"):
                    require_v053_manual_signing_gate(unsafe)

    def test_only_opt_in_publish_job_has_write_scope_and_revalidates_stage(self):
        require_v053_release_permissions_are_isolated(self.content)

    def test_guard_rejects_workflow_wide_write_permission(self):
        old = "permissions:\n  contents: read\n  actions: read"
        unsafe = self.content.replace(
            old,
            "permissions:\n  contents: write\n  actions: read",
            1,
        )
        self.assertNotEqual(unsafe, self.content)
        with self.assertRaisesRegex(AssertionError, "defaults must be contents: read"):
            require_v053_release_permissions_are_isolated(unsafe)

    def test_guard_rejects_write_permission_on_staging_job(self):
        old = "permissions:\n      contents: read\n      actions: read"
        unsafe = self.content.replace(
            old,
            "permissions:\n      contents: write\n      actions: read",
            1,
        )
        self.assertNotEqual(unsafe, self.content)
        with self.assertRaisesRegex(AssertionError, "stage job must explicitly remain read-only"):
            require_v053_release_permissions_are_isolated(unsafe)

    def test_guard_rejects_publisher_without_explicit_opt_in(self):
        old = "    if: inputs.publish == true"
        unsafe = self.content.replace(old, "    if: inputs.publish == false", 1)
        self.assertNotEqual(unsafe, self.content)
        with self.assertRaisesRegex(AssertionError, "explicit opt-in"):
            require_v053_release_permissions_are_isolated(unsafe)

    def test_guard_rejects_publisher_without_protected_main_or_approval(self):
        expected = (
            "inputs.publish == true "
            "&& github.event_name == 'workflow_dispatch' "
            "&& github.ref == 'refs/heads/main' "
            "&& github.ref_protected == true "
            "&& vars.BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED == 'true'"
        )
        safe = with_job_condition(self.content, "publish", expected)
        require_v053_release_permissions_are_isolated(safe)
        mutations = (
            ("github.event_name == 'workflow_dispatch'", "github.event_name == 'push'"),
            ("github.ref == 'refs/heads/main'", "github.ref == 'refs/heads/feature'"),
            ("github.ref_protected == true", "github.ref_protected == false"),
            (
                "vars.BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED == 'true'",
                "vars.BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED != 'true'",
            ),
        )
        for old, new in mutations:
            with self.subTest(mutation=old):
                unsafe = safe.replace(old, new, 1)
                self.assertNotEqual(unsafe, safe)
                with self.assertRaisesRegex(AssertionError, "protected main"):
                    require_v053_release_permissions_are_isolated(unsafe)


def workflow_step_block(content: str, job_name: str, step_name: str) -> str:
    """Return one named step from a release workflow job."""
    job = job_block(content, job_name)
    marker = f"      - name: {step_name}\\n"
    start = job.find(marker)
    if start < 0:
        raise AssertionError(f"missing {job_name} step: {step_name}")
    end = job.find("\\n      - name:", start + len(marker))
    if end < 0:
        end = len(job)
    return job[start:end]


def require_run_identity(step: str, variable: str, workflow_path: str, event: str) -> None:
    """Require an Actions run ID to identify the intended workflow, event and ref."""
    required = (
        f'test "$(printf \'%s\' "${variable}" | jq -r .path)" = "{workflow_path}"',
        f'test "$(printf \'%s\' "${variable}" | jq -r .event)" = "{event}"',
        f'test "$(printf \'%s\' "${variable}" | jq -r .head_branch)" = "main"',
    )
    missing = tuple(fragment for fragment in required if fragment not in step)
    if missing:
        raise AssertionError(
            f"{variable} must be a {event} run of {workflow_path} from main; "
            f"missing checks: {missing!r}"
        )


def require_v053_signer_candidate_run_identity(content: str) -> None:
    """Reject PR/feature or unrelated workflow runs as production APK candidates."""
    step = workflow_step_block(content, "sign", "Verify exact green v0.5.3 candidate")
    require_run_identity(
        step,
        "B",
        ".github/workflows/blazepwifi-build.yml",
        "push",
    )


def require_v053_stage_run_identities(content: str) -> None:
    """Bind staging to the canonical main build and exact main signer workflow run."""
    step = workflow_step_block(content, "stage", "Verify exact candidate and signing runs")
    require_run_identity(
        step,
        "B",
        ".github/workflows/blazepwifi-build.yml",
        "push",
    )
    require_run_identity(
        step,
        "S",
        ".github/workflows/blazerental-v053-lineage2-sign.yml",
        "workflow_dispatch",
    )
    exact_signer_source = 'test "$(printf \'%s\' "$S" | jq -r .head_sha)" = "$GITHUB_SHA"'
    if exact_signer_source not in step:
        raise AssertionError(
            "the signer run must use the same protected-main workflow source commit as staging"
        )


class BlazePwifiV053RunProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sign_content = SIGN_WORKFLOW.read_text(encoding="utf-8")
        cls.stage_content = RELEASE_STAGE_WORKFLOW.read_text(encoding="utf-8")

    def test_signer_accepts_only_canonical_main_push_build_run(self):
        require_v053_signer_candidate_run_identity(self.sign_content)

    def test_stage_accepts_only_canonical_main_build_and_exact_main_signer_runs(self):
        require_v053_stage_run_identities(self.stage_content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
