"""Full common.sh and real CGI form decoding in disposable Linux state."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1] / "openwrt/rootfs"
LIB = ROOT / "usr/lib/blazepwifi"
CGI = ROOT / "www/blazepwifi/cgi-bin"
LOCALES = ()
VALUES = (
    (b"plain", "plain"), (b"caf%C3%A9", "caf\u00e9"),
    (b"%E7%81%AB", "\u706b"), (b"%F0%9F%94%A5", "\U0001f525"),
    (b"Cafe%CC%81", "Cafe\u0301"), (b"one+two%2bthree", "one two+three"),
    (b"%22A%22%5c", '"A"\\'), (b"literal%5Cnliteral%5Ctliteral", r"literal\nliteral\tliteral"),
    (b"a%26label%3Db%3Bc", "a&label=b;c"), (b"%2526", "%26"),
    (b"100%", "100%"), (b"%2", "%2"), (b"%GG%2G%G2%20ok", "%GG%2G%G2 ok"),
)


class Fixture:
    def __init__(self, root, locale):
        self.state = root / "state"
        self.run = root / "run"
        tools = root / "bin"
        for path in (self.state, self.run, tools):
            path.mkdir()
        uci = tools / "uci"
        uci.write_text("""#!/bin/sh
case "$*" in
  '-q get blazepwifi.main.admin_port') printf '8443\\n' ;;
  '-q get blazepwifi.main.vendo_port') printf '4455\\n' ;;
  '-q get blazepwifi.main.vendo_key') printf 'fixture-vendo-key\\n' ;;
  '-q get blazepwifi.main.durable_sync') printf '0\\n' ;;
  *) exit 1 ;;
esac
""", encoding="utf-8")
        uci.chmod(0o700)
        self.env = dict(PATH=str(tools) + os.pathsep + os.environ["PATH"], LC_ALL=locale,
                        BP_STATE=str(self.state), BP_RUN=str(self.run), BP_LIB=str(LIB / "common.sh"),
                        BP_AUTH_LIB=str(LIB / "auth.sh"), BP_RENTAL_LIB=str(LIB / "rental.sh"),
                        BP_CONTROLLER_LIB=str(LIB / "controller.sh"), BP_MEMBER_LIB=str(LIB / "member.sh"),
                        REQUEST_METHOD="POST", REMOTE_ADDR="192.0.2.8", QUERY_STRING="label=ignored")

    def execute(self, args, body=b"", **overrides):
        result = subprocess.run(["sh", *args], input=body + b"\n", env=self.env | overrides,
                                capture_output=True, check=True, timeout=25)
        if result.stderr:
            raise AssertionError(result.stderr.decode("utf-8", errors="backslashreplace"))
        return result.stdout

    def request(self, endpoint, port, **fields):
        raw = self.execute([str(CGI / endpoint)], urlencode(fields).encode("ascii"),
                           SERVER_PORT=str(port))
        headers, body = raw.decode("utf-8", errors="strict").split("\r\n\r\n", 1)
        return headers, json.loads(body)

    def state_bytes(self):
        return {p.relative_to(self.state): p.read_bytes() for p in self.state.rglob("*") if p.is_file()}


class FormDecoder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not LOCALES:
            raise RuntimeError("Run directly with inventoried Linux locales")

    def test_exact_common_form_bytes(self):
        cases = [(b"label=" + encoded, expected) for encoded, expected in VALUES]
        cases += [(b"lab%65l=ignored&label=first&label=second", "first"),
                  (b"label=&label=second", ""), (b"other=label%3Dfake", "")]
        for locale in LOCALES:
            with tempfile.TemporaryDirectory() as tmp:
                fixture = Fixture(Path(tmp), locale)
                for body, expected in cases:
                    with self.subTest(locale=locale, body=body):
                        raw = fixture.execute(["-c", '. "$BP_LIB"; bp_param label'], body)
                        self.assertEqual(raw, expected.encode("utf-8"))

    def test_admin_login_with_literal_password_bytes(self):
        for locale in LOCALES:
            for password in ("fixture-ascii", "fixture-caf\u00e9-\u706b-\U0001f525"):
                with self.subTest(locale=locale, unicode=not password.isascii()), tempfile.TemporaryDirectory() as tmp:
                    fixture = Fixture(Path(tmp), locale)
                    salt = "0123456789abcdef"
                    digest = hashlib.sha256(f"{salt}|{password}|{salt}".encode()).hexdigest()
                    row = f"fixture-admin\tadmin\tsha256i\t{salt}\t{digest}\t1\t0\n".encode()
                    users = fixture.state / "admin-users.tsv"
                    users.write_bytes(row)
                    headers, denied = fixture.request("admin-login", 8443, username="fixture-admin",
                                                      password="wrong-fixture-password")
                    self.assertIs(denied.get("ok"), False)
                    self.assertEqual(denied.get("error"), "invalid credentials")
                    self.assertNotIn("Set-Cookie", headers)
                    self.assertEqual((fixture.run / "admin-sessions.tsv").read_bytes(), b"")
                    headers, reply = fixture.request("admin-login", 8443, username="fixture-admin", password=password)
                    self.assertIs(reply.get("ok"), True, reply.get("error"))
                    self.assertEqual(reply.get("username"), "fixture-admin")
                    self.assertRegex(reply.get("csrf", ""), r"^[a-f0-9]{48}$")
                    self.assertRegex(headers, r"Set-Cookie: blaze_admin=[a-f0-9]{64}; Path=/; Secure; HttpOnly; SameSite=Strict")
                    self.assertEqual(users.read_bytes(), row)

    def test_zero_pulse_vendo_ping_signature(self):
        for locale in LOCALES:
            for target in ("fixture-target", "caf\u00e9-\u706b-\U0001f525"):
                with self.subTest(locale=locale, unicode=not target.isascii()), tempfile.TemporaryDirectory() as tmp:
                    fixture = Fixture(Path(tmp), locale)
                    fixture.execute(["-c", '. "$BP_LIB"; . "$BP_RENTAL_LIB"; . "$BP_CONTROLLER_LIB"; '
                                     '. "$BP_MEMBER_LIB"; bp_rental_init; bp_controller_init; bp_member_init'],
                                    REQUEST_METHOD="GET")
                    (fixture.state / "controllers.tsv").write_bytes(
                        b"fixture-vendo\t0\t0\t0\t0\t-1\t-1\t-1\t1\t1\t1\t40\t400\t6\t1\n")
                    before = fixture.state_bytes()
                    fields = dict(action="ping", id="fixture-vendo", nonce="a1b2c3d4", pulses=0, target=target)
                    _, denied = fixture.request("vendo", 4455, **fields, sig="0" * 64)
                    self.assertIs(denied.get("ok"), False)
                    self.assertEqual(denied.get("error"), "bad signature")
                    self.assertEqual((fixture.run / "vendos.tsv").read_bytes(), b"")
                    self.assertEqual(fixture.state_bytes(), before)
                    digest = hashlib.sha256(
                        f"fixture-vendo-key|ping|fixture-vendo|a1b2c3d4|0|{target}|fixture-vendo-key".encode()
                    ).hexdigest()
                    _, reply = fixture.request("vendo", 4455, **fields, sig=digest)
                    self.assertIs(reply.get("ok"), True, reply.get("error"))
                    self.assertTrue((fixture.run / "vendos.tsv").read_bytes().startswith(b"fixture-vendo\t"))
                    self.assertEqual(fixture.state_bytes(), before)


if __name__ == "__main__":
    if sys.platform != "linux":
        raise SystemExit("Full form validation requires Linux")
    available = subprocess.check_output(["locale", "-a"], text=True, timeout=10).splitlines()
    utf8 = next((name for name in available if name.lower().replace("-", "").endswith(".utf8")), None)
    if "C" not in available or not utf8:
        raise SystemExit("C and UTF-8 locales are required")
    LOCALES = ("C", utf8)
    for locale in LOCALES:
        result = subprocess.run(["locale", "charmap"], env=os.environ | {"LC_ALL": locale},
                                capture_output=True, text=True, check=True, timeout=10)
        if result.stderr or (locale == utf8 and result.stdout.strip() != "UTF-8"):
            raise SystemExit("Locale charmap inventory failed")
        print(locale, result.stdout.strip(), flush=True)
    for tool in ("sh", "awk", "tr", "sed", "sha256sum", "flock"):
        path = Path(shutil.which(tool)).resolve()
        print(tool, path, hashlib.sha256(path.read_bytes()).hexdigest(), flush=True)
    unittest.main(verbosity=2)
