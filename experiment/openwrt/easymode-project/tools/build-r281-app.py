#!/usr/bin/env python3
"""Build the current R281 overlay update from its reviewed source tree."""

import argparse
import gzip
import hashlib
import io
import json
import pathlib
import re
import tarfile

PROJECT = pathlib.Path(__file__).resolve().parents[1]
RELEASE = PROJECT / "releases/v10.2.0-r281-candidate"
ARCHIVE = RELEASE / "openwrt/EasyMode-v10.2.0-R281-app-update-candidate.tar.gz"
SIDECAR = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")
TOP = ("AUDIT.md", "FEATURE-GAP.md", "HANDOFF.md", "README.md", "VERSION", "install.sh")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def files():
    paths = [RELEASE / name for name in TOP]
    paths += [p for folder in ("root", "tests") for p in (RELEASE / folder).rglob("*") if p.is_file()]
    paths = sorted(paths, key=lambda p: p.relative_to(RELEASE).as_posix())
    previous = json.loads((RELEASE / "SOURCE-MANIFEST.json").read_text())
    modes = {item["path"]: int(item["mode"], 8) for item in previous["files"]}
    records, contents = [], {}
    for path in paths:
        name = path.relative_to(RELEASE).as_posix()
        data = path.read_bytes()
        if name.startswith(("root/etc/config/", "root/etc/dropbear/", "root/root/")) or name in ("root/etc/shadow", "root/etc/passwd", "root/etc/uhttpd.key"):
            raise ValueError(f"private router path cannot enter the public application updater: {name}")
        if re.search(rb"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----)", data):
            raise ValueError(f"private key or token marker in public application source: {name}")
        mode = modes.get(name, 0o755 if name == "install.sh" or name.startswith(("root/etc/init.d/", "root/usr/libexec/", "tests/")) else 0o644)
        contents[name] = (data, mode)
        records.append({"path": name, "mode": f"{mode:04o}", "bytes": len(data), "sha256": sha(data)})
    manifest = {key: previous[key] for key in ("version", "kind", "board", "openwrt")}
    manifest["files"] = records
    contents["SOURCE-MANIFEST.json"] = ((json.dumps(manifest, indent=2) + "\n").encode(), 0o644)
    sums = "".join(f"{sha(data)}  {name}\n" for name, (data, _) in sorted(contents.items()))
    contents["SHA256SUMS"] = (sums.encode(), 0o644)
    return contents


def archive(contents):
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0, filename="") as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT) as tar:
            for name, (data, mode) in sorted(contents.items()):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = mode
                info.uid = info.gid = info.mtime = 0
                tar.addfile(info, io.BytesIO(data))
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify committed metadata and archive")
    args = parser.parse_args()
    contents = files()
    data = archive(contents)
    sidecar = f"{sha(data)}  {ARCHIVE.name}\n".encode()
    generated = {
        RELEASE / "SOURCE-MANIFEST.json": contents["SOURCE-MANIFEST.json"][0],
        RELEASE / "SHA256SUMS": contents["SHA256SUMS"][0],
        ARCHIVE: data,
        SIDECAR: sidecar,
    }
    if args.check:
        stale = [str(path.relative_to(PROJECT)) for path, content in generated.items() if not path.exists() or path.read_bytes() != content]
        if stale:
            parser.error("outdated R281 application files: " + ", ".join(stale))
    else:
        for path, content in generated.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print(f"PASS: {len(contents) - 1} checked R281 application files; archive SHA-256 {sha(data)}")


if __name__ == "__main__":
    main()
