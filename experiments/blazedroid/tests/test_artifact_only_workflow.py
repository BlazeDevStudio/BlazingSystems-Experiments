"""The owner requested a downloadable PREVIEW artifact, not a GitHub Release."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT.parent.parent / ".github" / "workflows" / "blazedroid-foundation.yml"
# File lives at repository root rather than under experiments/.
WORKFLOW = ROOT.parents[1] / ".github" / "workflows" / "blazedroid-foundation.yml"


class ArtifactOnlyWorkflowTests(unittest.TestCase):
    def test_downloadable_artifact_requires_actual_android_build(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("full_build:", workflow)
        self.assertIn("runs-on: [self-hosted, linux, x64, blazedroid-aosp]", workflow)
        self.assertIn("uses: actions/upload-artifact@v4", workflow)
        self.assertIn("if-no-files-found: error", workflow)

    def test_no_github_release_is_created(self):
        workflow = WORKFLOW.read_text()
        for forbidden in (
            "softprops/action-gh-release",
            "publish-preview:",
            "publish_preview:",
            "redistribution_approved:",
            "tag_name:",
            "gh release create",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, workflow)


if __name__ == "__main__":
    unittest.main()
