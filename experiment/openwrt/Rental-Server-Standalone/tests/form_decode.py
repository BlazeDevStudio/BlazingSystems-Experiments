"""Read-only product audit: exact source functions and CGIs in disposable state."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest

import label_utf8 as fixtures

ROOT = Path(__file__).resolve().parents[1]
# Literal form bytes and expected text, independent of the decoder implementation.
VALUES = [
    (b'Plain', 'Plain'), (b'caf%C3%A9', 'caf\u00e9'),
    (b'%e7%81%ab', '\u706b'), (b'%F0%9F%94%A5', '\U0001f525'),
    (b'Cafe%CC%81', 'Cafe\u0301'), (b'One+Two%2bThree', 'One Two+Three'),
    (b'O%27Brien%20%5c%22A%22', 'O\'Brien \\"A"'),
    (b'a%26action%3Drevoke%3Bx', 'a&action=revoke;x'),
    (b'%2526', '%26'), (b'100%', '100%'), (b'%2', '%2'),
    (b'%GG', '%GG'), (b'%2G', '%2G'), (b'%G2%20ok', '%G2 ok'),
    (b'line%5Cnliteral', r'line\nliteral'), (b'tab%5ctliteral', r'tab\tliteral'),
    (b'Trailing%5c', 'Trailing\\'),
]
LOCALES = ()


class FormDecode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not LOCALES:
            raise RuntimeError('Run this audit script directly to inventory required locales first.')

    def setUp(self):
        self.fixture = fixtures.LabelBytes()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def run_bytes(self, command, value, locale, **extra):
        env = os.environ.copy()
        env.update(LC_ALL=locale, **extra)
        result = subprocess.run(command, input=value, env=env, capture_output=True,
                                timeout=20, check=True)
        self.assertEqual(result.stderr, b'', 'tool errors must not masquerade as decoding results')
        return result.stdout

    def call(self, endpoint, body, locale, want_ok=True, query='', header='fixture-admin'):
        raw = self.run_bytes(['sh', str(ROOT / 'root/www/cgi-bin' / endpoint)], body + b'\n', locale,
                             BLAZE_RENTAL_BASE=str(self.fixture.base), REQUEST_METHOD='POST',
                             QUERY_STRING=query, HTTP_X_BLAZE_RENTAL_ADMIN=header)
        reply = json.loads(raw.decode('utf-8').split('\r\n\r\n', 1)[1])
        self.assertIs(reply.get('ok'), want_ok)
        return reply

    def extracted(self, endpoint, form=False):
        source = (ROOT / 'root/www/cgi-bin' / endpoint).read_text(encoding='utf-8')
        start = source.index('url_decode(){')
        end = source.index('\natomic_replace(){' if endpoint == 'rental-admin' else '\nhmac(){', start)
        path = self.fixture.base / ('form-' + endpoint + '.sh')
        if form:
            program = source[start:end] + '\nparam label\n'
        else:
            end = source.index('\nBODY=', start)
            program = source[start:end] + '\nvalue="$(cat)"\nurl_decode "$value"\n'
        path.write_text(program, encoding='utf-8', newline='\n')
        return path

    def test_exact_decoder_bytes(self):
        for endpoint in ('rental-admin', 'rental'):
            path = self.extracted(endpoint)
            for locale in LOCALES:
                for encoded, expected in VALUES:
                    with self.subTest(endpoint=endpoint, locale=locale, value=encoded):
                        raw = self.run_bytes(['sh', str(path)], encoded, locale)
                        self.assertEqual(raw, expected.encode('utf-8'))
                        self.assertEqual(raw.decode('utf-8'), expected)

    def test_exact_form_selection(self):
        # Characterize existing raw-key/first-value selection, not a new API policy.
        cases = [
            (b'label=first&label=second', 'POST', 'label=query', b'first'),
            (b'label=&label=second', 'POST', '', b''),
            (b'lab%65l=encoded&label=exact', 'POST', '', b'exact'),
            (b'label=body', 'GET', 'label=query%2Bvalue', b'query+value'),
            (b'other=label%3Dfake', 'POST', 'label=query', b''),
            (b'label=a%26label%3Db', 'POST', '', b'a&label=b'),
        ]
        for endpoint in ('rental-admin', 'rental'):
            path = self.extracted(endpoint, form=True)
            for locale in LOCALES:
                for body, method, query, expected in cases:
                    with self.subTest(endpoint=endpoint, locale=locale, body=body, method=method):
                        raw = self.run_bytes(['sh', str(path)], body + b'\n', locale,
                                             REQUEST_METHOD=method, QUERY_STRING=query)
                        self.assertEqual(raw, expected)

    def test_actual_admin_label_and_receipt_replay(self):
        f = self.fixture
        for locale in LOCALES:
            f.extra_env['LC_ALL'] = locale
            for encoded, expected in VALUES:
                with self.subTest(locale=locale, value=encoded):
                    f.seed()
                    self.call('rental-admin', b'action=rename&device_id=' + fixtures.DID.encode() +
                              b'&label=' + encoded, locale)
                    f.assert_device(expected)  # Strict raw JSON and TSV bytes.
                    first = self.call('rental-admin', b'action=enroll_create&ttl=900&request_id=' +
                                      fixtures.RID.encode() + b'&label=' + encoded, locale)
                    rows = (f.state / 'enroll.tsv').read_bytes().decode('utf-8').splitlines()
                    live = next(row.split('\t') for row in rows if not row.startswith('@'))
                    receipt = next(row.split('\t') for row in rows if row.startswith('@create'))
                    self.assertEqual(live[3], expected)
                    self.assertEqual(receipt[6], expected)
                    before = f.authority()
                    second = self.call('rental-admin', b'action=enroll_create&ttl=900&request_id=' +
                                       fixtures.RID.encode() + b'&label=' + encoded, locale)
                    self.assertIs(second.get('replayed'), True)
                    self.assertEqual(second['token'], first['token'])
                    self.assertEqual(f.authority(), before)

    def test_actual_app_encoded_ascii_enrollment(self):
        f = self.fixture
        def escaped(value):
            return ''.join('%%%02x' % byte for byte in value.encode('ascii')).encode('ascii')
        for locale in LOCALES:
            with self.subTest(locale=locale):
                f.seed()
                (f.state / 'devices.tsv').write_bytes(b'')
                label = 'Cafe\u0301 \u706b \U0001f525'
                (f.state / 'enroll.tsv').write_bytes(
                    f'{fixtures.EID}\t{fixtures.ESECRET}\t{int(time.time()) + 900}\t{label}\n'.encode())
                token, nonce = fixtures.EID + '.' + fixtures.ESECRET, 'abcdefgh'
                sig = hmac.new(token.encode(), f'enroll|{nonce}|{token}'.encode(), hashlib.sha256).hexdigest()
                body = (b'action=' + escaped('enroll') + b'&enroll_id=' + escaped(fixtures.EID) +
                        b'&nonce=' + escaped(nonce) + b'&sig=' + escaped(sig))
                first = self.call('rental', body, locale)
                f.extra_env['LC_ALL'] = locale
                f.assert_device(label)  # Label was seeded, not accepted from an app form.
                before = f.authority()
                second = self.call('rental', body, locale)
                self.assertIs(second.get('replayed'), True)
                self.assertEqual(second['device_id'], first['device_id'])
                self.assertEqual(second['device_secret'], first['device_secret'])
                self.assertEqual(f.authority(), before)
                bad = body.rsplit(b'&sig=', 1)[0] + b'&sig=' + escaped('0' * 64)
                refusal = self.call('rental', bad, locale, want_ok=False)
                self.assertEqual(refusal['error'], 'authentication failed')
                self.assertNotIn('device_secret', refusal)
                self.assertEqual(f.authority(), before)

    def test_actual_body_auth_and_post_selection(self):
        f = self.fixture
        for locale in LOCALES:
            with self.subTest(locale=locale):
                f.seed()
                before = f.authority()
                self.call('rental-admin', b'action=health&admin_token=fixture%2Dadmin', locale,
                          header='', query='action=revoke')
                reply = self.call('rental-admin', b'action=health&admin_token=wrong%25', locale,
                                  header='', want_ok=False)
                self.assertEqual(reply['error'], 'unauthorized')
                self.assertEqual(f.authority(), before)


if __name__ == '__main__':
    if sys.platform != 'linux':
        raise SystemExit('This form audit requires the actual Linux fixture toolchain.')
    result = subprocess.run(['locale', '-a'], capture_output=True, timeout=10, check=True)
    if result.stderr:
        raise SystemExit('locale inventory emitted an error')
    available = result.stdout.decode('ascii').splitlines()
    utf8 = [name for name in available if name.lower().replace('-', '').endswith('.utf8')]
    if 'C' not in available or not utf8:
        raise SystemExit('C and at least one UTF-8 locale are required; no passing skip')
    LOCALES = ('C', utf8[0])
    charmaps = {}
    for name in LOCALES:
        env = os.environ.copy()
        env['LC_ALL'] = name
        result = subprocess.run(['locale', 'charmap'], env=env, capture_output=True,
                                timeout=10, check=True)
        if result.stderr:
            raise SystemExit('locale charmap emitted an error')
        charmaps[name] = result.stdout.decode('ascii').strip()
    if charmaps[LOCALES[1]].upper().replace('-', '') != 'UTF8':
        raise SystemExit('Selected locale does not report a UTF-8 charmap')
    tools = {}
    for name in ('sh', 'awk', 'tr', 'sed', 'openssl'):
        path = shutil.which(name)
        if path is None:
            raise SystemExit('Missing fixture tool: ' + name)
        tools[name] = {'path': path, 'resolved': os.path.realpath(path),
                       'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}
    print(json.dumps({'locales': charmaps, 'values': len(VALUES), 'tools': tools}), flush=True)
    unittest.main(verbosity=2)
