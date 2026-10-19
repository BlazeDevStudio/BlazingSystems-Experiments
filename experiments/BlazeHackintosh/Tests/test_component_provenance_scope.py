"""CI-safe synthetic metadata and archive trust boundary regression tests."""
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import component_provenance as p


class ProvenanceScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((ROOT / 'docs/UPSTREAM-ASSET-METADATA-20261019.json').read_text())

    def manifest(self):
        return copy.deepcopy(self.reference)

    def test_five_components_structurally_valid(self):
        r = p.inspect_manifest(self.manifest())
        self.assertTrue(r['metadata_structure_valid'], r)
        self.assertEqual(r['component_count'], 5)
        self.assertFalse(r['component_auth_gate_satisfied'])

    def test_false_publisher_claim(self):
        m = self.manifest()
        m['components'][0]['independently_authenticated_publisher'] = True
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_false_license_claim(self):
        m = self.manifest()
        m['components'][0]['binary_redistribution_cleared'] = True
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_spoofed_gate_key(self):
        m = self.manifest()
        m['production_ready'] = True
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_non_exact_asset_url(self):
        m = self.manifest()
        m['components'][0]['asset_url'] = 'https://github.com.evil.test/path'
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_source_url_credentials(self):
        m = self.manifest()
        m['components'][0]['source_license_url'] = 'https://user:pass@github.com/acidanthera/X'
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_wrong_digest_pin(self):
        m = self.manifest()
        m['components'][0]['github_api_sha256'] = 'F' * 64
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_invalid_size_bool(self):
        m = self.manifest()
        m['components'][0]['github_api_asset_size'] = True
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_duplicate_component(self):
        m = self.manifest()
        m['components'][1]['repository'] = m['components'][0]['repository']
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_unknown_component(self):
        self.assertFalse(p.inspect_asset(self.manifest(), 'Unknown', '/tmp/none')['component_auth_gate_satisfied'])

    def test_invalid_iso_date(self):
        m = self.manifest()
        m['observed_on'] = '2026-02-30'
        self.assertFalse(p.inspect_manifest(m)['metadata_structure_valid'])

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):
            p.parse_manifest(b'{"x":1,"x":2}')

    def test_nan_json_rejected(self):
        with self.assertRaises(ValueError):
            p.parse_manifest(b'{"x":NaN}')

    def test_empty_manifest_rejected(self):
        with self.assertRaises(ValueError):
            p.parse_manifest(b'')

    def test_overlarge_manifest_rejected(self):
        with self.assertRaises(ValueError):
            p.parse_manifest(b' ' * (p.MAX_MANIFEST+1))

    def test_no_auth_from_real_local_zip_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'sample.zip'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('EFI/BOOT/BOOTX64.EFI',b'SYNTHETIC')
            b=path.read_bytes()
            m=self.manifest()
            m['components'][0]['github_api_sha256']=hashlib.sha256(b).hexdigest()
            m['components'][0]['github_api_asset_size']=len(b)
            r=p.inspect_asset(m,m['components'][0]['repository'],path)
            self.assertTrue(r['zip_structure_valid'],r)
            self.assertFalse(r['component_auth_gate_satisfied'])
            self.assertFalse(r['publisher_identity_independently_verified'])

    def test_corrupt_local_asset_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'notzip'
            path.write_bytes(b'bad')
            m=self.manifest()
            m['components'][0]['github_api_sha256']=hashlib.sha256(b'bad').hexdigest()
            m['components'][0]['github_api_asset_size']=3
            r=p.inspect_asset(m,m['components'][0]['repository'],path)
            self.assertFalse(r['zip_structure_valid'])

    def test_excluded_driver_is_not_claimed_cleared(self):
        m=self.manifest()
        self.assertIn('HfsPlus.efi',[x['name'] for x in m['excluded_components']])
        self.assertFalse(p.inspect_manifest(m)['license_redistribution_cleared'])


if __name__=='__main__':
    unittest.main()
