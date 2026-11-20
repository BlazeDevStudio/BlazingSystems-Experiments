"""Pure host-JVM-independent contract checks; no APK/device execution claims."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "verify_apk_contract.py"
spec = importlib.util.spec_from_file_location("verify_apk_contract", MODULE)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

BADGING = "package: name='com.blazesystems.blazerental' versionCode='50300' versionName='0.5.3'\nsdkVersion:'21'\ntargetSdkVersion:'27'\n"
SIGNING = ("Verifies\nVerified using v1 scheme (JAR signing): true\n"
           "Verified using v2 scheme (APK Signature Scheme v2): true\n"
           "Number of signers: 1\nSigner #1 certificate SHA-256 digest: "
           + checker.LINEAGE2_SHA256 + "\n")


class ApkContractTest(unittest.TestCase):
    def validate(self, badging=BADGING, signing=SIGNING, **overrides):
        return checker.inspect_text(badging, signing, mode="production", **overrides)

    def test_valid_lineage2_production_api21(self):
        output = self.validate()
        self.assertEqual(output["minSdk"], 21)
        self.assertEqual(output["versionCode"], 50300)
        self.assertTrue(output["v1SigningVerified"])

    def test_android8_min_sdk_rejected_for_android5(self):
        with self.assertRaisesRegex(checker.ContractError, "excludes required API"):
            self.validate(BADGING.replace("sdkVersion:'21'", "sdkVersion:'26'"))

    def test_v2_only_apk_rejected_for_android5(self):
        with self.assertRaisesRegex(checker.ContractError, "requires verified v1"):
            self.validate(signing=SIGNING.replace("JAR signing): true", "JAR signing): false"))

    def test_mismatched_production_signer_rejected(self):
        with self.assertRaisesRegex(checker.ContractError, "differs from Lineage 2"):
            self.validate(signing=SIGNING.replace(checker.LINEAGE2_SHA256, "f" * 64))

    def test_versioncode_rollback_rejected(self):
        with self.assertRaisesRegex(checker.ContractError, "below required floor"):
            self.validate(BADGING.replace("versionCode='50300'", "versionCode='30002'"))

    def test_release_cannot_use_debug_package(self):
        with self.assertRaisesRegex(checker.ContractError, "not expected"):
            self.validate(BADGING.replace("name='com.blazesystems.blazerental'",
                                          "name='com.blazesystems.blazerental.debug'"))

    def test_debug_cannot_impersonate_production_package(self):
        with self.assertRaisesRegex(checker.ContractError, "not expected"):
            checker.inspect_text(BADGING, SIGNING, mode="debug")

    def test_debug_accepts_distinct_signer(self):
        debug_badging = BADGING.replace("name='com.blazesystems.blazerental'",
                                        "name='com.blazesystems.blazerental.debug'")
        result = checker.inspect_text(debug_badging, SIGNING.replace(
            checker.LINEAGE2_SHA256, "a" * 64), mode="debug")
        self.assertEqual(result["package"], "com.blazesystems.blazerental.debug")

    def test_required_arm_abi_must_be_packaged_when_native_present(self):
        with self.assertRaisesRegex(checker.ContractError, "arm64-v8a"):
            self.validate(required_abis=["arm64-v8a"], embedded_abis=["armeabi-v7a"])

    def test_no_native_libraries_does_not_claim_abi_execution(self):
        result = self.validate(required_abis=["arm64-v8a"], embedded_abis=[])
        self.assertTrue(result["noNativeLibraries"])
        self.assertIn("NOT EXECUTED", result["note"])

    def test_more_than_one_signer_rejected(self):
        with self.assertRaisesRegex(checker.ContractError, "exactly one"):
            self.validate(signing=SIGNING.replace("Number of signers: 1", "Number of signers: 2"))

    def test_missing_sdk_observation_rejected(self):
        with self.assertRaisesRegex(checker.ContractError, "missing manifest"):
            self.validate("package: name='com.blazesystems.blazerental' versionCode='50300'\n")


if __name__ == "__main__":
    unittest.main()
