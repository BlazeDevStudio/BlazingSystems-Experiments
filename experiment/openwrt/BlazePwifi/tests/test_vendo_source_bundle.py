#!/usr/bin/env python3
"""Run the actual firmware packaging steps without downloading Arduino cores."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
PROJECT = Path("experiment/openwrt/BlazePwifi")
WORKFLOW = REPO / ".github/workflows/blazepwifi-build.yml"
TARGETS = (
    ("esp8266", "BlazePwifiVendo", "Compile BlazePwifi Vendo"),
    ("esp32", "BlazePwifiVendo32", "Compile BlazePwifi Vendo ESP32"),
)


def repository_bytes(relative):
    path = REPO / relative
    if path.exists():
        return path.read_bytes()
    return subprocess.check_output(["git", "show", "HEAD:" + relative.as_posix()], cwd=REPO)


class VendoSourceBundle(unittest.TestCase):
    def test_firmware_artifacts_include_the_source_they_compile(self):
        shell = os.environ.get("BLAZE_TEST_SHELL") or shutil.which("bash") or shutil.which("sh")
        self.assertIsNotNone(shell, "a POSIX shell is needed to execute the workflow's packaging commands")
        blocks = dict(re.findall(
            r"^      - name: ([^\n]+)\n        run: \|\n((?:          [^\n]*\n)+)",
            WORKFLOW.read_text(encoding="utf-8"), re.MULTILINE))
        tracked = subprocess.check_output([
            "git", "ls-tree", "-r", "--name-only", "HEAD", "--",
            (PROJECT / "esp").as_posix(), (PROJECT / "esp8266").as_posix(),
            (PROJECT / "esp32").as_posix(),
        ], cwd=REPO, text=True).splitlines()
        for target, sketch, step in TARGETS:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                stage = Path(directory)
                for relative in map(Path, tracked):
                    destination = stage / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(repository_bytes(relative))
                for relative in (PROJECT / "tools/package-vendo-source.py", PROJECT / "esp/REBUILD.md"):
                    if (REPO / relative).exists():
                        destination = stage / relative
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes((REPO / relative).read_bytes())
                commands = "\n".join(line[10:] for line in blocks[step].splitlines())
                fake_bin = stage / "bin"
                fake_bin.mkdir()
                (fake_bin / "arduino-cli").write_text(
                    '#!/bin/sh\nprintf "%s\\n" "$@" > "$BLAZE_COMPILER_ARGS"\n'
                    'while [ "$#" -gt 0 ]; do\n'
                    '  if [ "$1" = --output-dir ]; then output="$2"; shift; fi\n'
                    '  shift\ndone\nmkdir -p "$output"\nprintf fixture > "$output/fixture.bin"\n',
                    encoding="utf-8")
                (fake_bin / "python3").write_text(
                    "#!/bin/sh\nexec '" + sys.executable.replace("'", "'\\''") + "' \"$@\"\n",
                    encoding="utf-8")
                if not shutil.which("sha256sum"):
                    # Minimal Windows Git distributions omit this core utility.
                    # CI uses the real sha256sum; this fallback still hashes bytes.
                    (fake_bin / "sha256sum").write_text(
                        "#!/bin/sh\nexec python3 -c 'import hashlib,sys\n"
                        "for p in sys.argv[1:]:\n"
                        " print(hashlib.sha256(open(p,\"rb\").read()).hexdigest()+\"  \"+p)' \"$@\"\n",
                        encoding="utf-8")
                for path in fake_bin.iterdir():
                    path.chmod(0o755)
                environment = os.environ.copy()
                environment["PATH"] = os.pathsep.join((str(fake_bin), str(Path(shell).parent), environment["PATH"]))
                environment["BLAZE_COMPILER_ARGS"] = str(stage / "compiler-args")
                result = subprocess.run([shell, "-eu", "-o", "pipefail", "-c", commands],
                                        cwd=stage, env=environment, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                artifact = stage / PROJECT / "dist" / target
                header = artifact / "source/libraries/BlazePendingSequence/src/v060_pending_sequence.h"
                self.assertTrue(header.is_file(), "published sketch cannot rebuild: pending-sequence header is absent")
                self.assertEqual(header.read_bytes(), repository_bytes(
                    PROJECT / "esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h"))
                properties = artifact / "source/libraries/BlazePendingSequence/library.properties"
                self.assertEqual(properties.read_bytes(), repository_bytes(
                    PROJECT / "esp/libraries/BlazePendingSequence/library.properties"))
                original = repository_bytes(PROJECT / target / sketch / (sketch + ".ino"))
                self.assertEqual((artifact / "source" / sketch / (sketch + ".ino")).read_bytes(), original)
                self.assertEqual((artifact / (sketch + ".ino")).read_bytes(), original)
                self.assertTrue((artifact / "source/README.md").is_file())
                arguments = (stage / "compiler-args").read_text().splitlines()
                for argument in (arguments[-1], arguments[arguments.index("--libraries") + 1]):
                    self.assertTrue((stage / argument).resolve().is_relative_to(artifact / "source"),
                                    "CI must compile the shipped source instead of checkout-only dependencies")
                checked = set()
                for record in (artifact / "SHA256SUMS").read_text().splitlines():
                    digest, relative = record.split(maxsplit=1)
                    relative = relative.lstrip("*")
                    checked.add(relative.removeprefix("./"))
                    self.assertEqual(hashlib.sha256((artifact / relative).read_bytes()).hexdigest(), digest)
                expected_files = {path.relative_to(artifact).as_posix()
                                  for path in artifact.rglob("*")
                                  if path.is_file() and path.name != "SHA256SUMS"}
                self.assertEqual(checked, expected_files, "manifest must cover source and firmware outputs")


if __name__ == "__main__":
    unittest.main()
