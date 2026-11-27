package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class FloatingTimerPolicyTest {
    @Test public void requiresPaidEnabledAllowedAndPermission() {
        assertTrue(FloatingTimerPolicy.shouldShow(true, true, true, true));
        assertFalse(FloatingTimerPolicy.shouldShow(false, true, true, true));
        assertFalse(FloatingTimerPolicy.shouldShow(true, false, true, true));
        assertFalse(FloatingTimerPolicy.shouldShow(true, true, false, true));
        assertFalse(FloatingTimerPolicy.shouldShow(true, true, true, false));
    }
}
