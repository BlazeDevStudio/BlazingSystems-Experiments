#!/usr/bin/env python3
"""Exercise the exact backup block with synthetic files and a fixed clock."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
FILES = ("www/cgi-bin/rental", "www/cgi-bin/rental-admin", "www/rental/index.html")
ARCHIVES = "root/blazepwifi-rental-backups"
STAMP = "20261113-090000"
BACKUP_START = b'STAMP="$(date +%Y%m%d-%H%M%S)"\n'
REPLACEMENT_START = b'\ncp "$TMP/root/www/cgi-bin/rental" /www/cgi-bin/rental\n'
SHIMS = b"""
TMP=./staging
date() {
  [ "$#" = 1 ] && [ "$1" = '+%Y%m%d-%H%M%S' ] || exit 98
  printf '%s\\n' "$FIXTURE_STAMP"
}
cp() {
  [ "$#" = 3 ] && [ "$1" = -p ] || exit 98
  case "$2" in
    ./www/cgi-bin/rental|./www/cgi-bin/rental-admin|./www/rental/index.html) ;;
    *) exit 98 ;;
  esac
  case "$3" in ./root/blazepwifi-rental-backups/*) ;; *) exit 98 ;; esac
  if [ "$2" = "$FIXTURE_FAIL" ]; then
    echo 'simulated backup copy failure' >&2
    return 1
  fi
  command cp "$@"
}
rm() {
  [ "$#" = 3 ] && [ "$1" = -rf ] && [ "$2" = ./staging ] || exit 98
  case "$3" in
    "./root/blazepwifi-rental-backups/$FIXTURE_STAMP."??????) command rm "$@" ;;
    *) exit 98 ;;
  esac
}
"""


class InstallerBackup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shell = shutil.which("sh")
        if not cls.shell:
            raise RuntimeError("sh is required")
        # Git stores this shell file as LF. Windows may check it out as CRLF.
        source = (PROJECT / "install.sh").read_bytes().replace(b"\r\n", b"\n")
        if source.count(BACKUP_START) != 1 or source.count(REPLACEMENT_START) != 1:
            raise RuntimeError("Cannot isolate the installer backup block")
        _, start, tail = source.partition(BACKUP_START)
        block, end, _ = tail.partition(REPLACEMENT_START)
        if not end:
            raise RuntimeError("Backup block does not precede payload replacement")
        block = (start + block).replace(b"/www", b"./www")
        block = block.replace(b"/root/blazepwifi-rental-backups", b"./root/blazepwifi-rental-backups")
        block = block.replace(b"/etc/blazepwifi-rental", b"./etc/blazepwifi-rental")
        cls.script = b"set -eu\n" + SHIMS + block + b"\nprintf 'replacement boundary reached\\n'\n"
        print(f"Installer SHA-256 (LF) {hashlib.sha256(source).hexdigest()}", flush=True)
        print(f"Shell {Path(cls.shell).resolve()}", flush=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rental-backup-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve(strict=True)
        self.assertEqual(list(self.root.iterdir()), [])
        (self.root / "staging").mkdir()

    def seed(self, generation):
        expected = {}
        for name in FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = f"{generation}: {name}\n".encode()
            path.write_bytes(payload)
            expected[path.name] = payload
        return expected

    def run_backup(self, fail=""):
        return subprocess.run(
            [self.shell, "-s"], cwd=self.root, input=self.script, capture_output=True, timeout=10,
            env={**os.environ, "FIXTURE_STAMP": STAMP, "FIXTURE_FAIL": fail, "LC_ALL": "C"},
        )

    def archives(self):
        return {
            directory.name: {file.name: file.read_bytes() for file in directory.iterdir()}
            for directory in (self.root / ARCHIVES).iterdir()
        }

    def assert_replacement_reached(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"replacement boundary reached\n")

    def test_same_timestamp_keeps_both_generations(self):
        first = self.seed("before first install")
        self.assert_replacement_reached(self.run_backup())
        original = self.archives()
        self.assertEqual(list(original.values()), [first])
        second = self.seed("before second install")
        self.assert_replacement_reached(self.run_backup())
        current = self.archives()
        self.assertEqual({name: current.get(name) for name in original}, original,
                         "the first backup was overwritten")
        self.assertEqual(list({name: files for name, files in current.items()
                               if name not in original}.values()), [second])

    def test_copy_failure_stops_before_replacement(self):
        self.seed("original")
        self.assert_replacement_reached(self.run_backup())
        original = self.archives()
        current = self.seed("current")
        result = self.run_backup(fail=f"./{FILES[1]}")
        self.assertIn(b"simulated backup copy failure", result.stderr)
        self.assertNotIn(b"replacement boundary reached", result.stdout)
        self.assertNotEqual(result.returncode, 0, "a failed backup allowed replacement")
        self.assertEqual(self.archives(), original)
        self.assertEqual({Path(name).name: (self.root / name).read_bytes() for name in FILES},
                         current)

    def test_missing_files_are_valid_on_first_install(self):
        self.assert_replacement_reached(self.run_backup())
        self.assertEqual(list(self.archives().values()), [{}])


if __name__ == "__main__":
    unittest.main(verbosity=2)
