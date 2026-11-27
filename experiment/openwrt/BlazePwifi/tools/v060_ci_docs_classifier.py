#!/usr/bin/env python3
"""CI-0701: fail-closed exemption from *redundant* Full PR-synchronize builds.

Only cheap job classification: never changes release gates or financial state.
GitHub PR path filters use cumulative 3-dot comparisons, so repeated
documentation-only syncs can restart every platform build. Skip expensive jobs
only when the source tree is identical to a *previously verified Full run*.
Unknown data => RUN full validation, not silent exemption.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

PROJECT = pathlib.Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
LIVE = PROJECT / "docs/handover/CURRENT_STATE.md"
SHA = re.compile(r"^[0-9a-f]{40}$")
DOC_EXACT = {
    "experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md",
    "experiment/openwrt/BlazePwifi/AUDIT.md",
    "experiment/openwrt/BlazePwifi/README.md",
}
DOC_PREFIX = "experiment/openwrt/BlazePwifi/docs/"
WORKFLOW_NAME = "BlazePwifi build"


def is_documentation(path: str) -> bool:
    # Full CI safety contract: any new executable/config/test path is source.
    return path in DOC_EXACT or path.startswith(DOC_PREFIX)


def only_documentation(paths: list[str]) -> bool:
    return bool(paths) and all(is_documentation(p) for p in paths)


def confirmed_full_run(payload: object, sha: str) -> bool:
    if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
        return False
    return any(
        isinstance(run, dict)
        and run.get("head_sha") == sha
        and run.get("name") == WORKFLOW_NAME
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        for run in payload["workflow_runs"]
    )


def may_skip(
    *,
    event: str,
    action: str,
    before: str,
    after: str,
    actual_head: str,
    verified_sha: str,
    latest_paths: list[str],
    since_verified: list[str],
    previous_full_green: bool,
) -> bool:
    # No authorization from arbitrary commit message, filename, or self-claim.
    return (
        event == "pull_request"
        and action == "synchronize"
        and all(SHA.fullmatch(s) for s in (before, after, actual_head, verified_sha))
        and before != after
        and after == actual_head
        and only_documentation(latest_paths)
        and all(is_documentation(p) for p in since_verified)
        and previous_full_green
    )


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO), *args], text=True, stderr=subprocess.DEVNULL
    ).strip()


def diff_files(a: str, b: str) -> list[str]:
    # --no-renames means a move from source into docs still exposes deletion.
    return git("diff", "--no-renames", "--name-only", a, b, "--").splitlines()


def previous_run_verified(repo: str, sha: str, token: str) -> bool:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        return False
    if not token:
        return False
    url = f"https://api.github.com/repos/{repo}/actions/runs?head_sha={sha}&per_page=100"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return confirmed_full_run(json.load(response), sha)


def classify() -> tuple[bool, str]:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_name != "pull_request":
        return False, "manual/push events always require Full"
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as fh:
        payload = json.load(fh)
    if payload.get("action") != "synchronize":
        return False, "new/reopened PR always requires Full"
    before, after = payload.get("before", ""), payload.get("after", "")
    head = payload.get("pull_request", {}).get("head", {}).get("sha", "")
    if not all(isinstance(x, str) and SHA.fullmatch(x) for x in (before, after, head)):
        return False, "unverifiable PR synchronization SHA"
    if after != head or before == after:
        return False, "head mismatch or no change"
    # For a modified PR head, require real, reachable ancestor relationships.
    git("merge-base", "--is-ancestor", before, after)
    latest = diff_files(before, after)
    if not only_documentation(latest):
        return False, "latest update includes source/config/test/workflow or unknown paths"

    status = LIVE.read_text(encoding="utf-8")
    marker = re.search(r"(?m)^\*\*Integrated source revision:\*\* `([0-9a-f]{40})`", status)
    if not marker:
        return False, "missing verified source SHA in active handover"
    baseline = marker.group(1)
    git("merge-base", "--is-ancestor", baseline, after)
    changed_since = diff_files(baseline, after)
    if any(not is_documentation(p) for p in changed_since):
        return False, "new source relative to last Full success (must validate)"
    if not previous_run_verified(
        os.environ.get("GITHUB_REPOSITORY", ""), baseline, os.environ.get("GITHUB_TOKEN", "")
    ):
        return False, "source SHA has no verified completed successful Full run"
    if not may_skip(
        event=event_name,
        action=payload["action"],
        before=before,
        after=after,
        actual_head=head,
        verified_sha=baseline,
        latest_paths=latest,
        since_verified=changed_since,
        previous_full_green=True,
    ):
        return False, "failed closed in pure decision contract"
    return True, f"docs-only; exact Full run previously green at {baseline}"


def main() -> None:
    # Fail open for running tests, never for skipping. Missing event context,
    # GitHub API errors, malformed anchors, or unavailable git history => Full.
    try:
        skip, reason = classify()
    except Exception as exc:
        skip, reason = False, f"unverifiable safety evidence ({type(exc).__name__})"
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        print("CI-0701: GITHUB_OUTPUT missing; refuse standalone authority", file=sys.stderr)
        sys.exit(2)
    with open(output, "a", encoding="utf-8") as fh:
        fh.write(f"run_heavy={'false' if skip else 'true'}\n")
    print(f"CI-0701 {'SKIP_REDUNDANT_HEAVY' if skip else 'RUN_FULL'}: {reason}")
    print("PRODUCTION_RELEASE_APPROVED=0 PHYSICAL_POWER_CUT_VERIFIED=0")


if __name__ == "__main__":
    main()
