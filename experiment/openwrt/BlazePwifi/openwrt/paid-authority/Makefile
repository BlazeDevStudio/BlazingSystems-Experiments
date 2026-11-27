# PAY-0743: installable member+rental v2 authority runtime.
# No key, ledger, migration marker, or production activation is provisioned here.
include $(TOPDIR)/rules.mk

PKG_NAME:=blazepwifi-paid-authority
PKG_VERSION:=0.6.0
PKG_RELEASE:=1
PKG_LICENSE:=MIT
PKG_MAINTAINER:=BlazingSystems
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKG_BUILD_DEPENDS:=openssl

include $(INCLUDE_DIR)/package.mk

define Package/blazepwifi-paid-authority
  SECTION:=utils
  CATEGORY:=Utilities
  TITLE:=BlazePwifi durable member and rental authority
  DEPENDS:=+libopenssl
  DEFAULT:=n
endef

define Package/blazepwifi-paid-authority/description
  Installs the single-snapshot member+rental journal engine. The package
  creates no financial state or credentials and does not enable cutover.
  Transactions still require separately admitted controller identity,
  migration, antirollback witness, and response-signing integration.
endef

define Build/Prepare
	$(RM) -r $(PKG_BUILD_DIR)
	$(INSTALL_DIR) $(PKG_BUILD_DIR)
	$(CP) $(CURDIR)/src/v060_journal_authority.c $(PKG_BUILD_DIR)/paid-authority.c
endef

define Build/Configure
endef

define Build/Compile
	$(TARGET_CC) $(TARGET_CFLAGS) $(TARGET_CPPFLAGS) \
		-I$(STAGING_DIR)/usr/include -std=c11 -Wall -Wextra -Werror -O2 \
		-DBLAZE_RUNTIME_AUTHORITY $(PKG_BUILD_DIR)/paid-authority.c \
		-o $(PKG_BUILD_DIR)/blazepwifi-paid-authority \
		$(TARGET_LDFLAGS) -L$(STAGING_DIR)/usr/lib -lcrypto
endef

define Package/blazepwifi-paid-authority/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/blazepwifi-paid-authority $(1)/usr/sbin/
endef

$(eval $(call BuildPackage,blazepwifi-paid-authority))
