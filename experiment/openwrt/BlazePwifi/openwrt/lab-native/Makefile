# V2TARGET-0670: synthetic v2 native journal cross-compilation only.
# This is a LAB-ONLY opt-in SDK package, not a production integration.
# It must NEVER be included by BlazePwifi firmware ImageBuilder packages.
include $(TOPDIR)/rules.mk

PKG_NAME:=blazepwifi-v2-native-lab
PKG_VERSION:=0.6.0
PKG_RELEASE:=1
PKG_LICENSE:=MIT
PKG_MAINTAINER:=BlazingSystems
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKG_BUILD_DEPENDS:=openssl

include $(INCLUDE_DIR)/package.mk

define Package/blazepwifi-v2-native-lab
  SECTION:=utils
  CATEGORY:=Utilities
  TITLE:=BlazePwifi synthetic-only native journal cross-compile laboratory
  DEPENDS:=+libopenssl
  DEFAULT:=n
endef

define Package/blazepwifi-v2-native-lab/description
  Development-only binary with compile-time BLAZE_FIXTURE_ONLY.
  Only explicitly marked disposable /tmp/blaze-v2-native-* fixtures work.
  Not a live payment endpoint, updater component, or production migration.
endef

define Build/Prepare
	$(RM) -r $(PKG_BUILD_DIR)
	$(INSTALL_DIR) $(PKG_BUILD_DIR)
	$(CP) ./src/v060_journal_authority_native.c $(PKG_BUILD_DIR)/
	$(CP) ./src/v060_p256_target_capability_probe.c $(PKG_BUILD_DIR)/
endef

define Build/Configure
endef

define Build/Compile
	$(TARGET_CC) $(TARGET_CFLAGS) $(TARGET_CPPFLAGS) \
		-I$(STAGING_DIR)/usr/include -std=c11 -Wall -Wextra -Werror -O2 \
		-DBLAZE_FIXTURE_ONLY $(PKG_BUILD_DIR)/v060_journal_authority_native.c \
		-o $(PKG_BUILD_DIR)/v2-native-fixture \
		$(TARGET_LDFLAGS) -L$(STAGING_DIR)/usr/lib -lcrypto
	$(TARGET_CC) $(TARGET_CFLAGS) $(TARGET_CPPFLAGS) \
		-I$(STAGING_DIR)/usr/include -std=c11 -Wall -Wextra -Werror -O2 \
		-DBLAZE_V2_P256_CAPABILITY_LAB_ONLY $(PKG_BUILD_DIR)/v060_p256_target_capability_probe.c \
		-o $(PKG_BUILD_DIR)/p256-primitive-probe \
		$(TARGET_LDFLAGS) -L$(STAGING_DIR)/usr/lib -lcrypto
endef

define Package/blazepwifi-v2-native-lab/install
	$(INSTALL_DIR) $(1)/usr/libexec/blazepwifi-lab
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/v2-native-fixture $(1)/usr/libexec/blazepwifi-lab/
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/p256-primitive-probe $(1)/usr/libexec/blazepwifi-lab/
endef

$(eval $(call BuildPackage,blazepwifi-v2-native-lab))
