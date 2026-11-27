#!/usr/bin/env python3
"""Stage an offline BlazeFusion EasyMode preview; NEVER install to a router.

The historical R281 v4.2.3 source tree is read-only. A fresh staging
directory is required, so the operation cannot overwrite existing files.
"""
import argparse
import pathlib
import shutil
import tempfile

BASE = pathlib.Path(__file__).resolve().parent
PROJECT = BASE.parents[1]
RELEASE = PROJECT / "releases" / "v4.2.3-r281-experiment" / "root" / "www"
STYLE = BASE / "blazefusion.css"
SCRIPT = BASE / "blazefusion.js"
LINK = '<link rel="stylesheet" href="/easy/style.css?v=4.1.0">'
LOGOUT = '<button id="logout" class="ghost">Sign out</button>'
MARKER = '<!-- BlazeFusion EasyMode preview; no RPC or login changes -->'
EXTRA_LINK = '<link rel="stylesheet" href="/easy/blazefusion/blazefusion.css?v=0.6-preview">'
EXTRA_SCRIPT = '<script defer src="/easy/blazefusion/blazefusion.js?v=0.6-preview"></script>'
CONTROL = (
    '<label class="blazefusion-appearance" for="blazefusion-appearance">'
    'Appearance <select id="blazefusion-appearance" aria-label="EasyMode appearance">'
    '<option value="fusion">BlazeFusion</option>'
    '<option value="compact">Compact</option>'
    '<option value="comfort">Comfort</option></select></label>'
)

def build(output: pathlib.Path) -> None:
    source = (RELEASE / "index.html").read_text(encoding="utf-8")
    assert source.count(LINK) == 1, "Unsupported EasyMode stylesheet anchor"
    assert source.count(LOGOUT) == 1, "Unsupported EasyMode logout anchor"
    assert MARKER not in source, "Source release must not already be modified"
    assert "v4.2.3" in source, "Only audited 4.2.3 R281 preview is supported"
    assert not output.exists(), "Output must be a NEW directory; refusing overwrite"
    assert not output.is_relative_to(RELEASE.resolve()), "Cannot stage inside frozen release"
    assert not output.is_relative_to(BASE.resolve()), "Cannot stage on top of preview sources"
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".blazefusion-build-", dir=output.parent) as temp:
        staged = pathlib.Path(temp) / "www"
        shutil.copytree(RELEASE, staged)
        index = source.replace(LINK, LINK + MARKER + EXTRA_LINK + EXTRA_SCRIPT)
        index = index.replace(LOGOUT, CONTROL + LOGOUT)
        (staged / "index.html").write_text(index, encoding="utf-8")
        folder = staged / "easy" / "blazefusion"
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(STYLE, folder / STYLE.name)
        shutil.copyfile(SCRIPT, folder / SCRIPT.name)
        staged.rename(output)
    print(f"Staged offline EasyMode 4.2.3 BlazeFusion preview: {output}")
    print("No deployed router, runtime authentication, UBus API, or frozen release was modified.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New staging directory only")
    args = parser.parse_args()
    build(pathlib.Path(args.output).expanduser().resolve())
