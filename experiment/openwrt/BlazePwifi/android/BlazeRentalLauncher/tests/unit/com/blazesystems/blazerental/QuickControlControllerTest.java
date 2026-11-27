package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class QuickControlControllerTest {
    @Test public void safeControlsNeverExposeSettingsBridge() {
        assertFalse(QuickControlController.containsDangerousSettingsBridge());
        assertTrue(QuickControlController.safeControls().contains(
                QuickControlController.FLOATING_TIMER));
    }
}
