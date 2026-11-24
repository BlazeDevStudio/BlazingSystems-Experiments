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
        next_step = self.windows_content.find("\\n      - name:", start + len(marker))
        if next_step < 0:
            next_step = len(self.windows_content)
        block = self.windows_content[start:next_step]

        required = (
            "if: github.event_name == 'pull_request'",
            "function gh {",
            "-notmatch '/git/ref/tags/'",
            "Write-Output 'HTTP/2.0 404 Not Found'",
            "$global:LASTEXITCODE = 1",
            'throw "Unexpected GitHub CLI call in synthetic negative self-test:',
            '. \"$env:PROJECT_DIR/tests/ReleaseSigning/negative-selftest.ps1\" -ActualUnsignedSetup',
        )
        positions = tuple(block.find(fragment) for fragment in required)
        self.assertTrue(
            all(position >= 0 for position in positions),
            "the PR-only negative self-test must use a local gh function that admits only "
            "the synthetic missing-tag Git-ref response and rejects every other CLI call",
        )
        self.assertEqual(
            positions,
            tuple(sorted(positions)),
            "the local GitHub CLI stub must be defined before the PISONET test is dot-sourced",
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



if __name__ == "__main__":
    unittest.main(verbosity=2)
