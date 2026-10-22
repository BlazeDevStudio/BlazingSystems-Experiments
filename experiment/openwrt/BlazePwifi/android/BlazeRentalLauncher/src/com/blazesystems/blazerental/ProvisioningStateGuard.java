package com.blazesystems.blazerental;

/**
 * Pure state-machine policy for Android Device Owner provisioning callbacks.
 *
 * The first accepted provisioning identity is pinned until it becomes a
 * permanent device identity or an explicit reset/transfer clears local state.
 * Setup Wizard may replay the exact same extras; any changed server, token or
 * certificate pin must fail closed.
 */
final class ProvisioningStateGuard {
    private static final String DEVICE_OWNER_SOURCE = "device_owner_provisioning";

    private ProvisioningStateGuard() {}

    static boolean isProvisioningSource(String source) {
        return DEVICE_OWNER_SOURCE.equals(clean(source));
    }

    static boolean canAccept(String existingSource,
                             String existingServer,
                             String existingToken,
                             String existingPin,
                             String existingDeviceId,
                             String existingDeviceSecret,
                             String newServer,
                             String newToken,
                             String newPin) {
        if (nonEmpty(existingDeviceId) || nonEmpty(existingDeviceSecret)) {
            return false;
        }

        // Only a completely empty local enrollment slot may take a new
        // provisioning identity. Interrupted writes, old schema migration
        // and torn state can leave a server/pin behind without source/token.
        // Accepting new extras over such residue would silently switch the
        // destination or trust anchor. Require explicit reset/transfer.
        boolean hasAnyEnrollmentState = nonEmpty(existingSource)
                || nonEmpty(existingServer)
                || nonEmpty(existingToken)
                || nonEmpty(existingPin);
        if (!hasAnyEnrollmentState) {
            return nonEmpty(newServer) && nonEmpty(newToken) && nonEmpty(newPin);
        }

        return isExactReplay(existingSource, existingServer, existingToken,
                existingPin, newServer, newToken, newPin);
    }

    static boolean isExactReplay(String existingSource,
                                 String existingServer,
                                 String existingToken,
                                 String existingPin,
                                 String newServer,
                                 String newToken,
                                 String newPin) {
        return DEVICE_OWNER_SOURCE.equals(clean(existingSource))
                && clean(existingServer).equals(clean(newServer))
                && clean(existingToken).equals(clean(newToken))
                && clean(existingPin).equals(clean(newPin))
                && nonEmpty(existingServer)
                && nonEmpty(existingToken)
                && nonEmpty(existingPin);
    }

    private static boolean nonEmpty(String value) {
        return clean(value).length() > 0;
    }

    private static String clean(String value) {
        return value == null ? "" : value.trim();
    }
}
