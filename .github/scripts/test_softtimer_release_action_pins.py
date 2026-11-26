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
        for match in re.finditer(r"(?m)^      - ", workflow)
    ]
    return [
        workflow[start : starts[index + 1] if index + 1 < len(starts) else len(workflow)]
        for index, start in enumerate(starts)
    ]


def _checkout_step_blocks(workflow: str) -> list[str]:
    """Return checkout steps regardless of which mapping key appears first."""
    return [
        block
        for block in _step_blocks(workflow)
        if re.search(
            r"(?m)^(?:      - uses:|        uses:)[ \\t]*actions/checkout@",
            block,
        )
    ]


def _checkout_has_read_only_credentials(block: str) -> bool:
    """Require persist-credentials to be a direct key under the checkout with mapping."""
    lines = block.splitlines()
    with_indexes = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(r" {8}with:[ \t]*(?:#.*)?", line)
    ]
    if len(with_indexes) != 1:
        return False

    mapping_lines = []
    for line in lines[with_indexes[0] + 1 :]:
        if line.strip():
            indentation = len(line) - len(line.lstrip(" "))
            if indentation <= 8:
                break
        mapping_lines.append(line)

    credential_entries = [
        line
        for line in mapping_lines
        if re.match(r"^ {10}persist-credentials:", line)
    ]
    return (
        len(credential_entries) == 1
        and re.fullmatch(
            r" {10}persist-credentials:[ \t]*false[ \t]*(?:#.*)?",
            credential_entries[0],
        )
        is not None
    )


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
        checkout_blocks = _checkout_step_blocks(self.workflow)
        self.assertEqual(
            len(checkout_blocks),
            3,
            "the handover, build and isolated publisher jobs must each have one checkout",
        )

        missing = [
            index
            for index, block in enumerate(checkout_blocks, start=1)
            if not _checkout_has_read_only_credentials(block)
        ]
        self.assertFalse(
            missing,
            "checkout steps still persist GITHUB_TOKEN credentials: "
            + ", ".join(str(index) for index in missing),
        )


    def test_checkout_guard_does_not_accept_run_script_text_as_with_setting(self):
        malformed_workflow = (
            "      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n"
            "        run: |\n"
            "          persist-credentials: false\n"
            "      - name: Later step\n"
            "        run: echo later\n"
        )
        block = _step_blocks(malformed_workflow)[0]
        self.assertFalse(
            _checkout_has_read_only_credentials(block),
            "run-script text must not satisfy the checkout with-mapping guard",
        )

    def test_checkout_guard_accepts_direct_with_mapping_setting(self):
        valid_workflow = (
            "      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n"
            "        with:\n"
            "          persist-credentials: false\n"
            "      - name: Later step\n"
            "        run: echo later\n"
        )
        block = _step_blocks(valid_workflow)[0]
        self.assertTrue(_checkout_has_read_only_credentials(block))


    def test_checkout_step_discovery_counts_id_first_action_steps(self):
        valid_step = (
            "      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\\n"
            "        with:\\n"
            "          persist-credentials: false\\n"
        )
        workflow = valid_step * 3 + (
            "      - id: additional-checkout\\n"
            "        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\\n"
            "        with:\\n"
            "          persist-credentials: true\\n"
        )
        checkout_blocks = _checkout_step_blocks(workflow)
        self.assertEqual(
            len(checkout_blocks),
            4,
            "id-first steps with a later uses: actions/checkout key must be counted",
        )
        self.assertFalse(
            _checkout_has_read_only_credentials(checkout_blocks[-1]),
            "id-first checkout steps must also disable persisted credentials",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
