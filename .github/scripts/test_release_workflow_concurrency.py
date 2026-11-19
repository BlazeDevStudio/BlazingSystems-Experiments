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
                self.assertIn(f"if: github.ref == '{ref}'", block)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
