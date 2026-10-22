package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class LeaseSyncStateGuardTest {
    @Test public void freshDeviceAcceptsFirstSignedRevision() {
        assertTrue(LeaseSyncStateGuard.acceptRevision(true, 0L, -1L));
        assertTrue(LeaseSyncStateGuard.shouldApplyRevision(true, 0L, -1L));
    }
    @Test public void repeatedSignedRevisionCanRefreshLeaseButCannotRewritePolicy() {
        assertTrue(LeaseSyncStateGuard.acceptRevision(true, 7L, 7L));
        assertFalse(LeaseSyncStateGuard.shouldApplyRevision(true, 7L, 7L));
    }
    @Test public void rollbackRevisionIsRejected() {
        assertFalse(LeaseSyncStateGuard.acceptRevision(true, 6L, 7L));
        assertFalse(LeaseSyncStateGuard.shouldApplyRevision(true, 6L, 7L));
    }
    @Test public void invalidNegativeRevisionIsRejected() {
        assertFalse(LeaseSyncStateGuard.acceptRevision(true, -2L, -1L));
    }
    @Test public void unversionedDowngradeCannotReplaceModernPolicy() {
        assertFalse(LeaseSyncStateGuard.acceptRevision(false, 0L, 7L));
        assertTrue(LeaseSyncStateGuard.acceptRevision(false, 0L, -1L));
    }
}
