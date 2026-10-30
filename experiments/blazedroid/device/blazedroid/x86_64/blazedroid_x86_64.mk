# BlazeDroid 16 PREVIEW downstream product; uses the existing Android 16 x86-64 device.
# Do not use this file to impersonate a certified Google device.
$(call inherit-product, device/generic/x86_64_tablet/lineage_x86_64_tablet.mk)

PRODUCT_NAME := blazedroid_x86_64
PRODUCT_BRAND := BlazeDroid
PRODUCT_DEVICE := x86_64_tablet
PRODUCT_MODEL := BlazeDroid 16 Preview
PRODUCT_MANUFACTURER := BlazeDevStudio

PRODUCT_SYSTEM_PROPERTIES += \
    ro.blazedroid.version=16.0.0 \
    ro.blazedroid.channel=preview

