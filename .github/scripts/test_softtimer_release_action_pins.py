#!/usr/bin/env python3
"""Static release-owned guards for the SoftTimer publisher workflow.

This checks the workflow itself; it does not execute signing or publication.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "blazepisonet-softtimer-release.yml"

EXPECTED_ACTIONS = {
    "actions/checkout": "11bd71901bbe5b1630ceea73d27597364c9af683",
    "actions/setup-dotnet": "67a3573c9a986a3f9c594539f4ab511d57bb3ce9",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact": "d3f86a106a0bac45b974a628896c90dbdf5c8093",
}


def _action_references(workflow: str) -> list[str]:
    """Return every external action reference in workflow step syntax."""
    return re.findall(
        r"(?m)^[ \t]*(?:-[ \t]*)?uses:[ \t]*([^\s#]+)[ \t]*$",
        workflow,
    )


def _step_blocks(workflow: str) -> list[str]:
    """Split job steps at the workflow's six-space step indentation."""
    starts = [
        match.start()
        for match in re.finditer(r"(?m)^      - (?:name:|uses:)", workflow)
    ]
    return [
        workflow[start : starts[index + 1] if index + 1 < len(starts) else len(workflow)]
        for index, start in enumerate(starts)
    ]


class SoftTimerReleaseActionPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_every_external_action_uses_its_reviewed_immutable_commit(self):
        references = _action_references(self.workflow)
        problems = []
        if not references:
            problems.append("no external action references were found")

        observed: dict[str, set[str]] = {}
        for reference in references:
            if "@" not in reference:
                problems.append(f"action has no immutable ref: {reference}")
                continue
            repository, revision = reference.rsplit("@", 1)
            if not re.fullmatch(r"[0-9a-f]{40}", revision):
                problems.append(f"action ref is not a full lowercase commit SHA: {reference}")
                continue
            observed.setdefault(repository, set()).add(revision)
            expected = EXPECTED_ACTIONS.get(repository)
            if expected is None:
                problems.append(f"unreviewed external action repository: {repository}")
            elif revision != expected:
                problems.append(
                    f"{repository} uses {revision}; reviewed commit is {expected}"
                )

        missing = sorted(set(EXPECTED_ACTIONS) - set(observed))
        if missing:
            problems.append("expected action repositories missing: " + ", ".join(missing))
        for repository, revisions in sorted(observed.items()):
            if len(revisions) != 1:
                problems.append(
                    f"{repository} is pinned inconsistently: {', '.join(sorted(revisions))}"
                )

        self.assertFalse(problems, "\n".join(problems))

    def test_every_checkout_step_disables_persisted_credentials(self):
        checkout_blocks = [
            block
            for block in _step_blocks(self.workflow)
            if re.search(r"(?m)^      - uses: actions/checkout@", block)
        ]
        self.assertEqual(
            len(checkout_blocks),
            3,
            "the handover, build and isolated publisher jobs must each have one checkout",
        )

        missing = [
            index
            for index, block in enumerate(checkout_blocks, start=1)
            if not re.search(
                r"(?m)^[ \t]+persist-credentials:[ \t]*false[ \t]*$",
                block,
            )
        ]
        self.assertFalse(
            missing,
            "checkout steps still persist GITHUB_TOKEN credentials: "
            + ", ".join(str(index) for index in missing),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
