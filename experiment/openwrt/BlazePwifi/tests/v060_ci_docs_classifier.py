#!/usr/bin/env python3
"""CI-0701 nonproduction negative test: never hide source or a missing green gate."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from v060_ci_docs_classifier import (  # noqa: E402
    WORKFLOW_NAME,
    confirmed_full_run,
    is_documentation,
    may_skip,
    only_documentation,
)

sha_good = "a" * 40
sha_before = "b" * 40
sha_after = "c" * 40
docs = [
    "experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md",
    "experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md",
    "experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md",
    "experiment/openwrt/BlazePwifi/docs/handover/archive/old.md",
]
money = "experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
rent = "experiment/openwrt/BlazePwifi/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
workflow = ".github/workflows/blazepwifi-build.yml"
tool = "experiment/openwrt/BlazePwifi/tools/v060_ci_docs_classifier.py"
test = "experiment/openwrt/BlazePwifi/tests/v060_ci_docs_classifier.py"
assert only_documentation(docs)
assert all(is_documentation(p) for p in docs)
assert not only_documentation([])
for path in (money, rent, workflow, tool, test, "some-new-unrecognized-file"):
    assert not is_documentation(path)
    assert not only_documentation(docs + [path])

valid_run = {
    "workflow_runs": [
        {
            "head_sha": sha_good,
            "name": WORKFLOW_NAME,
            "status": "completed",
            "conclusion": "success",
        }
    ]
}
assert confirmed_full_run(valid_run, sha_good)
for bad in (
    {},
    [],
    {"workflow_runs": [None]},
    {"workflow_runs": [{**valid_run["workflow_runs"][0], "head_sha": sha_before}]},
    {"workflow_runs": [{**valid_run["workflow_runs"][0], "name": "Other workflow"}]},
    {"workflow_runs": [{**valid_run["workflow_runs"][0], "conclusion": "skipped"}]},
    {"workflow_runs": [{**valid_run["workflow_runs"][0], "conclusion": "failure"}]},
    {"workflow_runs": [{**valid_run["workflow_runs"][0], "status": "queued"}]},
):
    assert not confirmed_full_run(bad, sha_good), f"accepted bad Full CI evidence: {bad!r}"

kwargs = dict(
    event="pull_request",
    action="synchronize",
    before=sha_before,
    after=sha_after,
    actual_head=sha_after,
    verified_sha=sha_good,
    latest_paths=docs,
    since_verified=docs,
    previous_full_green=True,
)
assert may_skip(**kwargs), "could not skip a truly checked docs-only sync"
for modification in (
    {"event": "push"},
    {"event": "workflow_dispatch"},
    {"action": "opened"},
    {"action": "reopened"},
    {"before": "not-a-commit"},
    {"after": "not-a-commit"},
    {"actual_head": sha_before},
    {"verified_sha": "unverified"},
    {"before": sha_after},
    {"latest_paths": []},
    {"latest_paths": docs + [money]},
    {"latest_paths": docs + [rent]},
    {"latest_paths": docs + [workflow]},
    {"latest_paths": docs + [tool]},
    {"since_verified": docs + [money]},
    {"since_verified": docs + [test]},
    {"previous_full_green": False},
):
    test_kwargs = kwargs | modification
    assert not may_skip(**test_kwargs), f"dangerously skipped CI with {modification!r}"

print("CI-0701 PASS: only already-green docs-only sync can skip; unknown/source/failed evidence runs Full")
print("CUSTOMER_INSTALL_AUTHORIZED=0 PRODUCTION_RELEASE_APPROVED=0")
