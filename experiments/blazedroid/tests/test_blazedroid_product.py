"""BlazeDroid must be an Android product, not merely an ISO filename."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "device" / "blazedroid" / "x86_64"


class BlazeProductTests(unittest.TestCase):
    def test_product_registered_for_lunch(self):
        products = (PRODUCT / "AndroidProducts.mk").read_text()
        self.assertIn("$(LOCAL_DIR)/blazedroid_x86_64.mk", products)
        self.assertIn("blazedroid_x86_64-userdebug", products)

    def test_product_inherits_existing_android16_x86_hardware(self):
        product = (PRODUCT / "blazedroid_x86_64.mk").read_text()
        self.assertIn(
            "$(call inherit-product, device/generic/x86_64_tablet/lineage_x86_64_tablet.mk)",
            product,
        )
        for line in (
            "PRODUCT_NAME := blazedroid_x86_64",
            "PRODUCT_BRAND := BlazeDroid",
            "PRODUCT_MODEL := BlazeDroid 16 Preview",
            "PRODUCT_MANUFACTURER := BlazeDevStudio",
            "ro.blazedroid.version=16.0.0",
            "ro.blazedroid.channel=preview",
        ):
            with self.subTest(line=line):
                self.assertIn(line, product)

    def test_build_installs_local_product_and_uses_it(self):
        script = (ROOT / "scripts" / "build-iso.sh").read_text()
        self.assertIn('cp -a -- "$HERE/device/blazedroid/." "$SRC/device/blazedroid/"', script)
        self.assertIn("lunch blazedroid_x86_64-userdebug", script)
        self.assertNotIn("lunch lineage_x86_64_tablet-userdebug", script)


if __name__ == "__main__":
    unittest.main()
