package com.blazesystems.blazerental;

/**
 * Fail-closed policy revision gate for authenticated Rental status responses.
 * A response is not allowed to grant time if its policy revision moves
 * backwards or omits the revision after the device has accepted versioned
 * policy. Repeated signed responses at the same revision may refresh time,
 * but must not reapply mutable operator settings.
 */
final class LeaseSyncStateGuard {
    private LeaseSyncStateGuard() {}

    static boolean acceptRevision(boolean versioned, long received, long stored) {
        if (versioned) {
            return received >= 0L && received >= stored;
        }
        // Unversioned protocol support is for fresh legacy clients only.
        return stored < 0L;
    }

    static boolean shouldApplyRevision(boolean versioned, long received, long stored) {
        return acceptRevision(versioned, received, stored)
                && (versioned ? received > stored : stored < 0L);
    }
}
