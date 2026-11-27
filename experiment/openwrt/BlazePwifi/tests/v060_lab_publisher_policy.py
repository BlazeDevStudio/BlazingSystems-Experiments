#!/usr/bin/env python3
"""REL-0634: execute the publisher's real embedded draft verifier with synthetic data.

Offline only. No remote release API, credentials, customer records or published
assets. This intentionally executes the exact inline Python extracted from the
workflow instead of testing an unrelated copy of its algorithm.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap

PROJECT = Path(__file__).resolve().parents[4]
WORKFLOW = PROJECT / ".github/workflows/blazepwifi-build.yml"
source = WORKFLOW.read_text(encoding="utf-8")
upload_marker = "      - name: Upload and verify draft lab artifacts before publication\n"
publish_marker = "      - name: Publish verified lab-only prerelease and verify visibility\n"
assert source.count(upload_marker) == source.count(publish_marker) == 1
upload = source.split(upload_marker, 1)[1].split(publish_marker, 1)[0]
publish = source.split(publish_marker, 1)[1]
assert "gh api \"repos/$GITHUB_REPOSITORY/releases?per_page=100\"" in upload
assert "/releases/tags/$LAB_TAG" not in upload, "Private draft cannot be fetched by public tag"
assert "gh api --method PATCH" in publish
assert "releases/$LAB_DRAFT_RELEASE_ID" in publish
assert publish.index("gh api --method PATCH") < publish.index("releases/tags/$LAB_TAG")
assert "test -n \"${LAB_DRAFT_RELEASE_ID:-}\"" in publish
embedded = re.search(r"(?ms)^          python3 - <<'PY'\n(.*?)^          PY\s*$", upload)
assert embedded, "Could not extract actual in-workflow Python verifier"
script = textwrap.dedent(embedded.group(1))

ASSET_ZIPS = [
    "BlazePwifi-bundle-LAB-ONLY.zip",
    "BlazePwifi-android-current-LAB-ONLY.zip",
    "BlazePwifi-esp8266-firmware-LAB-ONLY.zip",
    "BlazePwifi-esp32-firmware-LAB-ONLY.zip",
    "BlazePwifi-ruijie-firmware-LAB-ONLY.zip",
    "BlazePwifi-x86_64-firmware-LAB-ONLY.zip",
    "BlazePwifi-orangepi_zero3-firmware-LAB-ONLY.zip",
    "BlazePwifi-current-update-LAB-ONLY.zip",
    "BlazePisonet-SoftTimer-v0.4.0-win-x64-LAB-ONLY.zip",
]
SHA = "89" * 20
TAG = "v0.6.0-alpha.4"


def execute_fixture(kind):
    with tempfile.TemporaryDirectory(prefix="blaze-lab-release-fixture-") as directory:
        root = Path(directory)
        lab = root / "lab-release"
        lab.mkdir()
        for i, name in enumerate(ASSET_ZIPS):
            (lab / name).write_bytes((name + "\n").encode() * (i + 1))
        (lab / "RELEASE_NOTES.md").write_text("Synthetic disposable lab only\n", encoding="utf-8")
        (lab / "SHA256SUMS").write_text("Synthetic checksums\n", encoding="utf-8")
        (lab / "MANIFEST.json").write_text(
            json.dumps({"tag": TAG, "commit": SHA,
                        "customer_install_authorized": False,
                        "production_signed": False}) + "\n",
            encoding="utf-8",
        )
        assets = [
            {"name": p.name, "state": "uploaded",
             "size": p.stat().st_size,
             "digest": "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in lab.iterdir()
        ]
        release = {"id": 411122233, "tag_name": TAG, "target_commitish": SHA,
                   "draft": True, "prerelease": True, "assets": assets}
        releases = [release]
        if kind == "bad-digest":
            assets[0]["digest"] = "sha256:" + "0" * 64
        elif kind == "missing-digest":
            del assets[0]["digest"]
        elif kind == "wrong-source":
            release["target_commitish"] = "00" * 20
        elif kind == "not-draft":
            release["draft"] = False
        elif kind == "duplicate-draft":
            releases.append(dict(release))
        elif kind == "missing-file":
            (lab / ASSET_ZIPS[0]).unlink()
        elif kind == "positive":
            pass
        else:
            raise ValueError(kind)
        (root / "created-releases.json").write_text(json.dumps(releases), encoding="utf-8")
        envfile = root / "github-env"
        env = dict(os.environ, LAB_TAG=TAG, GITHUB_SHA=SHA, GITHUB_ENV=str(envfile))
        program = root / "actual-publisher-verifier.py"
        program.write_text(script, encoding="utf-8")
        run = subprocess.run(
            [sys.executable, str(program)],
            cwd=root, env=env, capture_output=True, text=True, timeout=15,
        )
        if kind == "positive":
            assert run.returncode == 0, f"valid draft refused: {run.stderr}"
            assert envfile.read_bytes() == b"LAB_DRAFT_RELEASE_ID=411122233\n", (
                "GitHub environment export not terminated with a real newline"
            )
        else:
            assert run.returncode != 0, f"unsafe {kind} release accepted"
        return kind


for mode in ("positive", "bad-digest", "missing-digest", "wrong-source",
             "not-draft", "duplicate-draft", "missing-file"):
    execute_fixture(mode)

print("REL-0634 PASS: exact embedded draft verifier accepts 12 files and rejects "
      "mismatched/missing SHA, wrong source, published/duplicate draft and missing asset; "
      "numeric release ID exported with a real newline")
print("SYNTHETIC ONLY: this is release-policy source validation, not a live GitHub upload")
