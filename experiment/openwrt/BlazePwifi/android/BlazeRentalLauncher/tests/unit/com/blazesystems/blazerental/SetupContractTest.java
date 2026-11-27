package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class SetupContractTest {
    @Test public void safeControlsContainRequestedRentalControls() {
        assertTrue(QuickControlController.safeControls().contains(
                QuickControlController.BLUETOOTH_TOGGLE));
        assertTrue(QuickControlController.safeControls().contains(
                QuickControlController.FLASHLIGHT));
        assertFalse(QuickControlController.containsDangerousSettingsBridge());
    }
}
