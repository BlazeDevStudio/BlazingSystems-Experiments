# PHX-MASTER — coordination verifier filesystem-boundary audit (2026-11-16 UTC13)

Status: **BLOCKED / PRODUCTION NO-GO**. Scope: `coordination/phoenix/` only. This is a source-inspection finding and a proposed regression, **not** an executed exploit, passing test, or migration authorization.

## Reproducible finding

At Master draft PR #288 HEAD `2df11e6186fb6227043357e47120f70d9e8a914d`, `verify_coordination.py` accepts lexical paths through `safe_repo_path()` and then checks `(repo_root / source.rstrip('/')).exists()`, `.is_dir()`, or `.is_file()`. These `pathlib` predicates follow symbolic links. There is no resolved-path containment test. Consequently, in a locally modified or untrusted checkout, a syntactically safe source path can resolve outside the repository. This is a **coordination integrity gap** (false-positive source-presence check), not demonstrated remote execution or an existing malicious symlink in Git.

## Narrow remediation for PHX-MASTER review

1. For every source route, resolve `repo_root` and the candidate path, then require `candidate.resolve(strict=True).is_relative_to(repo_root.resolve(strict=True))` (or `os.path.commonpath` for older Python). Reject escaping links, broken links and unexpected filesystem types with a clear error. Decide explicitly whether **in-repository** symlinks are permitted; if not, reject them too.
2. Add negative regression using `tempfile.TemporaryDirectory()`: make a valid lexical `outside_link/` inside the checkout pointing to an existing directory outside it; assert `validate_routes` reports a containment error. Add a positive in-tree directory fixture and a broken-link fixture. Never follow or write through the link.
3. Run `python3 -m py_compile coordination/phoenix/verify_coordination.py` and `python3 -m unittest discover -s coordination/phoenix -p 'test*.py' -v` at the exact updated SHA, and request independent PHX-QA review. This finding alone must not be marked test-passing.

## Current integration context

Experiments main/base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; COE main/base `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE draft #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`. Destination workflows at this SHA: five distinct queued workflows, no success conclusion. Source/destination blob and license parity remain unapproved. The private Drive v11 registry was located through its restricted Project-Registry folder and parsed successfully **off GitHub**; no private contents or IDs are published here.

## Human next action

PHX-MASTER: implement the scoped path containment guard plus fixtures on existing PR #288, then run exact-head tests. PHX-QA: independently verify both negative and positive fixtures and destination parity. COE integration owner: diagnose queued workflows. Keep original histories and the Rental parent-route `copy_permitted=false` collision guard intact. No subsystem branch edits, merge, release, hardware, signing or financial actions.
