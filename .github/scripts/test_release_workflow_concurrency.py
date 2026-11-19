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

    def test_both_publishers_remain_explicitly_branch_gated_and_write_scoped(self):
        cases = (
            ("publish_prerelease", "refs/heads/blazepwifi-v0.3.0-design"),
            ("publish_release", "refs/heads/blazepwifi-v0.3.0-production"),
        )
        for job, ref in cases:
            with self.subTest(job=job):
                block = job_block(self.content, job)
                self.assertIn(f"if: github.ref == '{ref}'", block)
                self.assertIn("permissions:\n      contents: write", block)


if __name__ == "__main__":
    unittest.main(verbosity=2)
