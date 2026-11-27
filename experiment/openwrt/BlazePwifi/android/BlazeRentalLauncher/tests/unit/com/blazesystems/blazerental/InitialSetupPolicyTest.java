package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class InitialSetupPolicyTest {
    @Test public void freshInstallRequiresInitialSetup() {
        assertTrue(InitialSetupPolicy.needsInitialSetup(false, false));
    }

    @Test public void enrolledWithoutAdminVerifierStillRequiresSetup() {
        assertTrue(InitialSetupPolicy.needsInitialSetup(true, false));
    }

    @Test public void configuredDeviceUsesNormalAdminGate() {
        assertFalse(InitialSetupPolicy.needsInitialSetup(true, true));
    }

    @Test public void transferResetForcesSetupAgain() {
        assertTrue(InitialSetupPolicy.needsInitialSetup(false, true));
    }
}
