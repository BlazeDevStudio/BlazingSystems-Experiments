package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class AdminGestureControllerTest {
    @Test public void shortPressDoesNotTrigger() {
        AdminGestureController g = new AdminGestureController(4000L);
        g.onDown(100L);
        assertFalse(g.onUp(4099L));
    }

    @Test public void configuredHoldTriggers() {
        AdminGestureController g = new AdminGestureController(4000L);
        g.onDown(100L);
        assertTrue(g.shouldTrigger(4100L));
        assertTrue(g.onUp(4100L));
    }
}
