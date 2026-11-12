#!/usr/bin/env python3
"""Check the standalone uninstall's requested operations without deleting anything."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
APP = "./www/cgi-bin/rental"
ADMIN = "./www/cgi-bin/rental-admin"
DASHBOARD = "./www/rental"
INDEX = f"{DASHBOARD}/index.html"
STATE = "./etc/blazepwifi-rental"
UNINSTALL_END = b"\n[ -f /etc/openwrt_release ]"

COMMANDS = b"""
id() { [ "$#" = 1 ] && [ "$1" = -u ] && printf '0\\n'; }
rm() {
  printf 'rm'
  printf '\\t%s' "$@"
  printf '\\n'
} >> "$UNINSTALL_TRACE"
rmdir() {
  printf 'rmdir'
  printf '\\t%s' "$@"
  printf '\\n'
  return "$UNINSTALL_RMDIR_STATUS"
} >> "$UNINSTALL_TRACE"
"""


def snapshot(root):
    entries = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            value = ("link", os.readlink(path))
        elif path.is_dir():
            value = ("directory",)
        else:
            value = ("file", path.read_bytes())
        entries[path.relative_to(root)] = value
    return entries


class UninstallScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform != "linux":
            raise RuntimeError("This test requires Linux filesystem semantics")
        cls.shell = shutil.which("sh")
        cls.grep = shutil.which("grep")
        if not cls.shell or not cls.grep:
            raise RuntimeError("sh and grep are required")

        source = (PROJECT / "install.sh").read_bytes()
        uninstall, boundary, _ = source.partition(UNINSTALL_END)
        if not boundary or not uninstall.endswith(b"  exit 0\nfi\n"):
            raise RuntimeError("Cannot isolate the uninstall branch")
        # Use relative paths inside the fixture and a PATH containing only grep.
        uninstall = uninstall.replace(b"/www", b"./www")
        uninstall = uninstall.replace(b"/etc/blazepwifi-rental", b"./etc/blazepwifi-rental")
        cls.script = COMMANDS + uninstall
        print(f"Installer SHA-256 {hashlib.sha256(source).hexdigest()}", flush=True)
        print(f"Shell {Path(cls.shell).resolve()}, grep {Path(cls.grep).resolve()}", flush=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rental-uninstall-")
        self.addCleanup(temporary.cleanup)
        scratch = Path(temporary.name).resolve(strict=True)
        self.root = scratch / "root"
        self.root.mkdir(mode=0o700)
        self.assertEqual(self.root.resolve(strict=True), self.root)
        self.bin = scratch / "bin"
        self.bin.mkdir()
        (self.bin / "grep").symlink_to(self.grep)
        self.trace = scratch / "operations"
        self.trace.touch()
        self.seed(f"{STATE}/state/devices.tsv", b"fixture authority\n")
        self.seed(f"{STATE}/admin.token", b"fixture identity\n")
        self.seed("./root/blazepwifi-rental-backups/previous/index.html", b"backup\n")
        self.seed("./www/index.html", b"main dashboard\n")

    def seed(self, path, content):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def install_fixture(self, *paths):
        for path in paths:
            self.seed(path, (PROJECT / "root" / path).read_bytes())

    def check_uninstall(self, expected, *flags, rmdir_status=0):
        before = snapshot(self.root)
        result = subprocess.run(
            [self.shell, "-s", "--", "--uninstall", *flags],
            input=self.script,
            cwd=self.root,
            env={"PATH": str(self.bin), "LC_ALL": "C", "UNINSTALL_TRACE": str(self.trace),
                 "UNINSTALL_RMDIR_STATUS": str(rmdir_status)},
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(snapshot(self.root), before, "fixture contents changed")
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
        self.assertEqual(result.stderr, b"")
        self.assertIn(b"Uninstall complete.", result.stdout)
        self.assertEqual(b"Rental state preserved" in result.stdout, "--purge" not in flags)
        operations = [tuple(line.split("\t")) for line in self.trace.read_text().splitlines()]
        self.assertEqual(operations, expected)

    def test_remove_marked_files_and_preserve_dashboard_siblings(self):
        self.install_fixture(APP, ADMIN, INDEX)
        self.seed(f"{DASHBOARD}/other/app.html", b"unrelated application\n")
        self.check_uninstall([
            ("rm", "-f", APP), ("rm", "-f", ADMIN),
            ("rm", "-f", INDEX), ("rmdir", DASHBOARD),
        ], rmdir_status=1)

    def test_clean_up_empty_dashboard_directory(self):
        self.install_fixture(INDEX)
        self.check_uninstall([("rm", "-f", INDEX), ("rmdir", DASHBOARD)])

    def test_keep_unmarked_index_and_app_cgi(self):
        self.install_fixture(ADMIN)
        self.seed(APP, b"another CGI\n")
        self.seed(INDEX, b"another dashboard\n")
        self.check_uninstall([("rm", "-f", ADMIN)], "--force")

    def test_keep_unmarked_admin_cgi_and_missing_index(self):
        self.install_fixture(APP)
        self.seed(ADMIN, b"another admin CGI\n")
        self.seed(f"{DASHBOARD}/other.html", b"another dashboard\n")
        self.check_uninstall([("rm", "-f", APP)])

    def test_keep_symlinked_dashboard_directory(self):
        self.install_fixture(INDEX)
        (self.root / DASHBOARD).rename(self.root / "www/other")
        (self.root / DASHBOARD).symlink_to("other", target_is_directory=True)
        self.check_uninstall([])

    def test_keep_symlinked_dashboard_index(self):
        self.install_fixture(INDEX)
        (self.root / INDEX).rename(self.root / "www/other.html")
        (self.root / INDEX).symlink_to("../other.html")
        self.check_uninstall([], "--force")

    def test_accept_existing_document_root_symlink(self):
        self.install_fixture(APP, INDEX)
        (self.root / "www").rename(self.root / "document-root")
        (self.root / "www").symlink_to("document-root", target_is_directory=True)
        self.check_uninstall([("rm", "-f", APP), ("rm", "-f", INDEX), ("rmdir", DASHBOARD)])

    def test_purge_only_explicit_rental_state(self):
        self.seed(INDEX, b"another dashboard\n")
        self.seed("./etc/config/uhttpd", b"fixture web configuration\n")
        self.check_uninstall([("rm", "-rf", STATE)], "--purge")


if __name__ == "__main__":
    unittest.main(verbosity=2)
