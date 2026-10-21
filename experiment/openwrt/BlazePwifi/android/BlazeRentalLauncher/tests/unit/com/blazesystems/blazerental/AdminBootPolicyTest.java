package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class AdminBootPolicyTest {
    @Test public void noPriorLockoutStaysUnlockedAfterReboot() {
        assertEquals(0L, AdminBootPolicy.lockedUntilAfterReboot(0L, 1200L));
    }

    @Test public void priorLockoutRestartsFromNewUptime() {
        assertEquals(901200L,
                AdminBootPolicy.lockedUntilAfterReboot(43200000L, 1200L));
    }

    @Test public void expiredLockoutRecordDoesNotGrantAdminAccess() {
        assertEquals(901200L,
                AdminBootPolicy.lockedUntilAfterReboot(900000L, 1200L));
    }

    @Test public void negativeOrInvalidLockoutStateIsCleared() {
        assertEquals(0L, AdminBootPolicy.lockedUntilAfterReboot(-10L, 2000L));
    }
}
