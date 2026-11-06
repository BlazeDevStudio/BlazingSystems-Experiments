"""Actual CGI label bytes in disposable state; no server or installer is run."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
DID, SECRET, RID = '1' * 24, '2' * 48, '3' * 32
EID, ESECRET = '4' * 12, '5' * 36
A = 'a'
# Hand-checked longest complete UTF-8 prefixes within the existing byte ceiling.
CASES = [
    ('ascii80', A * 80, A * 80), ('ascii81', A * 81, A * 80),
    ('short Unicode', 'Cafe\u0301 \u706b \U0001f525', 'Cafe\u0301 \u706b \U0001f525'),
    ('quotes slash', "O'Brien \\ \"A\" & <B>", "O'Brien \\ \"A\" & <B>"),
    ('2byte fits', A * 78 + '\u00e9', A * 78 + '\u00e9'),
    ('2byte splits', A * 79 + '\u00e9', A * 79),
    ('3byte fits', A * 77 + '\u706b', A * 77 + '\u706b'),
    ('3byte splits2', A * 78 + '\u706b', A * 78),
    ('3byte splits1', A * 79 + '\u706b', A * 79),
    ('4byte fits', A * 76 + '\U0001f525', A * 76 + '\U0001f525'),
    ('4byte splits3', A * 77 + '\U0001f525', A * 77),
    ('4byte splits2', A * 78 + '\U0001f525', A * 78),
    ('4byte splits1', A * 79 + '\U0001f525', A * 79),
]


class LabelBytes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='rental-label-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.state = self.base / 'state'
        self.state.mkdir()
        self.extra_env = {}
        (self.base / 'admin.token').write_text('fixture-admin\n')

    def seed(self, label='Initial phone'):
        (self.state / 'devices.tsv').write_bytes(f'{DID}\t{SECRET}\t0\t{label}\t0\n'.encode())
        for name in ('enroll.tsv', 'policy.tsv', 'events.tsv'):
            (self.state / name).write_bytes(b'')

    def call(self, endpoint, want_ok=True, **data):
        env = os.environ.copy()
        env.update(BLAZE_RENTAL_BASE=str(self.base), REQUEST_METHOD='POST',
                   HTTP_X_BLAZE_RENTAL_ADMIN='fixture-admin', LC_ALL='C')
        env.update(self.extra_env)
        result = subprocess.run(['sh', str(ROOT / 'root/www/cgi-bin' / endpoint)],
                                input=(urlencode(data) + '\n').encode('ascii'),
                                capture_output=True, env=env, timeout=20, check=True)
        self.assertEqual(result.stderr, b'', 'CGI fixture must not hide tool errors')
        # Decode strictly before parsing: browser replacement decoding can hide bad bytes.
        text = result.stdout.decode('utf-8')
        body = text.split('\r\n\r\n', 1)[1]
        reply = json.loads(body)
        self.assertEqual(reply.get('ok'), want_ok, reply)
        return reply

    def authority(self):
        return {name: (self.state / name).read_bytes()
                for name in ('devices.tsv', 'enroll.tsv', 'policy.tsv', 'events.tsv')}

    def refuse_normalizer(self):
        # Fail only the new normalizer, leaving real state readers/validators intact.
        awk = shutil.which('awk')
        self.assertIsNotNone(awk)
        tools = self.base / 'tools'
        tools.mkdir()
        wrapper = tools / 'awk'
        wrapper.write_text("#!/bin/sh\ncase \"${1:-}\" in\n"
                           "  *'s=substr($0,1,80)'*) exit 17;;\nesac\n"
                           'exec ' + shlex.quote(awk) + ' "$@"\n')
        wrapper.chmod(0o700)
        self.extra_env['PATH'] = str(tools) + os.pathsep + os.environ['PATH']

    def assert_device(self, expected):
        devices = self.call('rental-admin', action='list')['devices']
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['label'], expected)
        rows = (self.state / 'devices.tsv').read_bytes().decode('utf-8').splitlines()
        device = next(row.split('\t') for row in rows if not row.startswith('@'))
        self.assertEqual(device[3], expected)
        self.assertLessEqual(len(device[3].encode()), 80)

    def test_rename_and_raw_list_response(self):
        for name, label, expected in CASES:
            with self.subTest(case=name):
                self.seed()
                self.call('rental-admin', action='rename', device_id=DID, label=label)
                self.assert_device(expected)
                row = (self.state / 'devices.tsv').read_text().split('\t')
                self.assertEqual(row[:3], [DID, SECRET, '0'])

    def test_existing_label_through_time_writer(self):
        for name, label, expected in CASES:
            with self.subTest(case=name):
                self.seed(label)
                self.call('rental-admin', action='set_time', device_id=DID, seconds=0, request_id=RID)
                self.assert_device(expected)
                before = (self.state / 'devices.tsv').read_bytes()
                replay = self.call('rental-admin', action='set_time', device_id=DID, seconds=0, request_id=RID)
                self.assertTrue(replay['replayed'])
                self.assertEqual((self.state / 'devices.tsv').read_bytes(), before)

    def test_creation_and_same_request_replay(self):
        for name, label, expected in CASES:
            with self.subTest(case=name):
                self.seed()
                first = self.call('rental-admin', action='enroll_create', label=label, ttl=900, request_id=RID)
                rows = (self.state / 'enroll.tsv').read_bytes().decode('utf-8').splitlines()
                token = next(row.split('\t') for row in rows if not row.startswith('@'))
                receipt = next(row.split('\t') for row in rows if row.startswith('@create'))
                self.assertEqual(token[3], expected)
                self.assertEqual(receipt[6], expected)
                self.assertLessEqual(len(token[3].encode()), 80)
                before = (self.state / 'enroll.tsv').read_bytes()
                second = self.call('rental-admin', action='enroll_create', label=label, ttl=900, request_id=RID)
                self.assertTrue(second['replayed'])
                self.assertEqual(second['token'], first['token'])
                self.assertEqual((self.state / 'enroll.tsv').read_bytes(), before)

    def test_app_enrollment_writer_and_identity_replay(self):
        for name, label, expected in CASES:
            with self.subTest(case=name):
                self.seed()
                (self.state / 'devices.tsv').write_bytes(b'')
                expiry = int(time.time()) + 900
                (self.state / 'enroll.tsv').write_bytes(f'{EID}\t{ESECRET}\t{expiry}\t{label}\n'.encode())
                token, nonce = EID + '.' + ESECRET, 'abcdefgh'
                signature = hmac.new(token.encode(), f'enroll|{nonce}|{token}'.encode(), hashlib.sha256).hexdigest()
                first = self.call('rental', action='enroll', enroll_id=EID, nonce=nonce, sig=signature)
                self.assert_device(expected)
                before = (self.state / 'devices.tsv').read_bytes()
                second = self.call('rental', action='enroll', enroll_id=EID, nonce=nonce, sig=signature)
                self.assertTrue(second['replayed'])
                self.assertEqual(second['device_id'], first['device_id'])
                self.assertEqual(second['device_secret'], first['device_secret'])
                self.assertEqual((self.state / 'devices.tsv').read_bytes(), before)

    def test_legacy_split_receipt_conflicts_without_reissuing(self):
        self.seed()
        expiry = int(time.time()) + 900
        digest = hashlib.sha256((EID + '.' + ESECRET).encode()).hexdigest()
        # Retain actual old cut output, including its incomplete final byte.
        old_label = b'a' * 79 + b'\xc3'
        (self.state / 'enroll.tsv').write_bytes(
            f'{EID}\t{ESECRET}\t{expiry}\t'.encode() + old_label + b'\n' +
            f'@create\t{RID}\t{EID}\t{digest}\t{expiry}\t900\t'.encode() + old_label + b'\n')
        before = self.authority()
        reply = self.call('rental-admin', want_ok=False, action='enroll_create',
                          label='a' * 79 + '\u00e9', ttl=900, request_id=RID)
        self.assertEqual(reply['error'], 'request id conflict')
        self.assertNotIn('token', reply)
        self.assertEqual(self.authority(), before)

    def test_admin_normalizer_failure_preserves_authority(self):
        self.refuse_normalizer()
        for action in ('rename', 'set_time', 'enroll_create'):
            with self.subTest(action=action):
                self.seed()
                before = self.authority()
                self.call('rental-admin', want_ok=False, action=action, device_id=DID,
                          seconds=0, label='New phone', ttl=900, request_id=RID)
                self.assertEqual(self.authority(), before)

    def test_app_normalizer_failure_preserves_authority(self):
        self.seed()
        (self.state / 'devices.tsv').write_bytes(b'')
        (self.state / 'enroll.tsv').write_bytes(
            f'{EID}\t{ESECRET}\t{int(time.time()) + 900}\tNew phone\n'.encode())
        token, nonce = EID + '.' + ESECRET, 'abcdefgh'
        signature = hmac.new(token.encode(), f'enroll|{nonce}|{token}'.encode(), hashlib.sha256).hexdigest()
        self.refuse_normalizer()
        before = self.authority()
        reply = self.call('rental', want_ok=False, action='enroll', enroll_id=EID,
                          nonce=nonce, sig=signature)
        self.assertNotIn('device_secret', reply)
        self.assertEqual(self.authority(), before)


if __name__ == '__main__':
    if sys.platform != 'linux':
        raise SystemExit('This raw CGI regression requires the Linux fixture toolchain.')
    unittest.main(verbosity=2)
