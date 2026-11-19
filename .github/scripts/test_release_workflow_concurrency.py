#!/usr/bin/env python3
"""Guard release-capable OpenWrt runs against unsafe concurrency cancellation."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/blazepwifi-build.yml"


def job_block(content: str, name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  [A-Za-z0-9_]+:\n|\Z)",
        content,
    )
    if not match:
        raise AssertionError(f"missing release job: {name}")
    return match.group(1)


class ReleaseWorkflowConcurrencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = WORKFLOW.read_text(encoding="utf-8")

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
